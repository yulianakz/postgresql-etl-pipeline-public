"""Unit tests for :class:`StagingExtractRunnerTemplate`.

These tests exercise the full ``extract_run`` flow with in-memory fakes
instead of Airflow + a real database so we can verify the control flow
(dedup skip, job id reuse, truncate on full reload, csv file-already-loaded
skip, metadata update, finish_job propagation, and exception re-raise).
"""

from datetime import datetime, timezone

import pytest

from airflow.exceptions import AirflowSkipException

from etl.extract.abstract_models.stg_job_runner_interface import StagingExtractRunnerTemplate
from etl.extract.domain.entities.extract_entities import BabyDataEntity


class _FakeMetaRepo:
    def __init__(
        self,
        dedup=False,
        running_id=None,
        start_id=1,
        is_file_loaded=False,
    ):
        self.dedup = dedup
        self.running_id = running_id
        self.start_id = start_id
        self.is_file_loaded_flag = is_file_loaded
        self.calls = []

    def dedup_job_done(self, dag_id, task_id, logical_date):
        self.calls.append(("dedup_job_done", dag_id, task_id, logical_date))
        return self.dedup

    def find_running_job(self, dag_id, task_id, logical_date):
        self.calls.append(("find_running_job",))
        return self.running_id

    def start_job(self, dag_id, task_id, logical_date):
        self.calls.append(("start_job", dag_id, task_id, logical_date))
        return self.start_id

    def add_job_metadata(self, **kwargs):
        self.calls.append(("add_job_metadata", kwargs))

    def finish_job(
        self,
        job_id,
        status,
        rows_affected_count,
        rows_inserted_count,
        error_message,
        last_loaded_event_ts_watermark=None,
    ):
        self.calls.append(
            (
                "finish_job",
                job_id,
                status,
                rows_affected_count,
                rows_inserted_count,
                error_message,
                last_loaded_event_ts_watermark,
            )
        )

    def is_file_loaded(self, file_path):
        self.calls.append(("is_file_loaded", file_path))
        return self.is_file_loaded_flag


class _FakeStgRepo:
    def __init__(self):
        self.truncated = []

    def do_truncate(self, entity_type):
        self.truncated.append(entity_type)

    def get_job_max_watermark(self, entity_type, job_id, watermark_column):
        return None


class _FakeExtractor:
    def extract(self):
        return iter([])


class _Runner(StagingExtractRunnerTemplate):
    """Concrete runner used to test the template."""

    def __init__(
        self,
        meta_repo,
        stg_repo,
        *,
        load_type_value="initial",
        source_type_value="db",
        source_path_value="public.baby",
        raise_on_extract: Exception | None = None,
        rows_loaded: int = 5,
    ):
        super().__init__(meta_repo, extractor_factory=None, stg_repo=stg_repo, engine=None)
        self._load_type = load_type_value
        self._source_type = source_type_value
        self._source_path = source_path_value
        self._raise_on_extract = raise_on_extract
        self._rows_loaded = rows_loaded

    def pipeline_stage(self):
        return "extract"

    def source_type(self):
        return self._source_type

    def source_path(self):
        return self._source_path

    def entity_type(self):
        return BabyDataEntity

    def destination_table_name(self):
        return "stg_baby"

    def mapper(self):
        return lambda row: row

    def load_type(self):
        return self._load_type

    def get_watermark(self):
        return None

    def watermark_column(self):
        return "loaded_at"

    def build_extractor(self):
        return _FakeExtractor()

    def _extracting(self, job_id):
        if self._raise_on_extract:
            raise self._raise_on_extract
        return self._rows_loaded


LOGICAL_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestStgRunnerHappyPath:
    def test_initial_run_end_to_end(self):
        meta = _FakeMetaRepo()
        stg = _FakeStgRepo()
        runner = _Runner(meta, stg)

        runner.extract_run("d", "t", LOGICAL_DATE)

        call_names = [c[0] for c in meta.calls]
        assert call_names == [
            "dedup_job_done",
            "find_running_job",
            "start_job",
            "add_job_metadata",
            "finish_job",
        ]

        finish_call = meta.calls[-1]
        assert finish_call[1] == 1  # job_id
        assert finish_call[2] == "success"
        assert finish_call[3] == 5  # rows_affected_count
        assert finish_call[4] == 5  # rows_inserted_count
        assert finish_call[5] is None  # no error
        assert finish_call[6] is None  # no watermark
        assert stg.truncated == []  # initial, not full_reload

    def test_full_reload_truncates_first(self):
        meta = _FakeMetaRepo()
        stg = _FakeStgRepo()
        runner = _Runner(meta, stg, load_type_value="full_reload")

        runner.extract_run("d", "t", LOGICAL_DATE)

        assert stg.truncated == [BabyDataEntity]

    def test_reuses_existing_running_job_id(self):
        meta = _FakeMetaRepo(running_id=77)
        stg = _FakeStgRepo()
        runner = _Runner(meta, stg)

        runner.extract_run("d", "t", LOGICAL_DATE)

        call_names = [c[0] for c in meta.calls]
        assert "start_job" not in call_names
        finish = [c for c in meta.calls if c[0] == "finish_job"][0]
        assert finish[1] == 77


class TestStgRunnerSkips:
    def test_dedup_skip_before_any_metadata(self):
        meta = _FakeMetaRepo(dedup=True)
        stg = _FakeStgRepo()
        runner = _Runner(meta, stg)

        with pytest.raises(AirflowSkipException):
            runner.extract_run("d", "t", LOGICAL_DATE)

        call_names = [c[0] for c in meta.calls]
        assert call_names == ["dedup_job_done"]

    def test_csv_incremental_file_already_loaded_raises_skip(self):
        meta = _FakeMetaRepo(is_file_loaded=True, start_id=1)
        stg = _FakeStgRepo()
        runner = _Runner(
            meta,
            stg,
            load_type_value="incremental",
            source_type_value="csv",
            source_path_value="etl/data_files/formula.csv",
        )

        with pytest.raises(AirflowSkipException):
            runner.extract_run("d", "t", LOGICAL_DATE)

        # job_id was assigned before the skip, so the finally block still
        # closes out the job record; status stays None (neither success/failed)
        finish_calls = [c for c in meta.calls if c[0] == "finish_job"]
        assert len(finish_calls) == 1
        assert finish_calls[0][1] == 1  # job_id
        assert finish_calls[0][2] is None  # status never set
        # add_job_metadata must not have been called yet
        assert not any(c[0] == "add_job_metadata" for c in meta.calls)

    def test_csv_incremental_unloaded_file_proceeds(self):
        meta = _FakeMetaRepo(is_file_loaded=False)
        stg = _FakeStgRepo()
        runner = _Runner(
            meta,
            stg,
            load_type_value="incremental",
            source_type_value="csv",
            source_path_value="etl/data_files/formula.csv",
        )

        runner.extract_run("d", "t", LOGICAL_DATE)
        finish = [c for c in meta.calls if c[0] == "finish_job"][0]
        assert finish[2] == "success"


class TestStgRunnerErrors:
    def test_extract_failure_marks_job_failed_and_reraises(self):
        meta = _FakeMetaRepo()
        stg = _FakeStgRepo()
        runner = _Runner(meta, stg, raise_on_extract=RuntimeError("boom"))

        with pytest.raises(RuntimeError, match="boom"):
            runner.extract_run("d", "t", LOGICAL_DATE)

        finish = [c for c in meta.calls if c[0] == "finish_job"][0]
        assert finish[2] == "failed"
        assert "boom" in finish[5]
        assert "extract" in finish[5]  # step tag included
