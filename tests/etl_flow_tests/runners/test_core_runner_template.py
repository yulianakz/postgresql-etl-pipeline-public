"""Unit tests for :class:`CoreExtractRunnerTemplate`."""

from datetime import datetime, timezone

import pytest

from airflow.exceptions import AirflowSkipException

from etl.transform_load.abstract_models.core_job_runner_interface import (
    CoreExtractRunnerTemplate,
)


class _FakeMetaRepo:
    def __init__(
        self,
        dedup=False,
        running_id=None,
        start_id=10,
        last_success_id=None,
    ):
        self.dedup = dedup
        self.running_id = running_id
        self.start_id = start_id
        self.last_success_id = last_success_id
        self.calls = []

    def dedup_job_done(self, dag_id, task_id, logical_date):
        self.calls.append(("dedup",))
        return self.dedup

    def find_running_job(self, dag_id, task_id, logical_date):
        return self.running_id

    def start_job(self, dag_id, task_id, logical_date):
        self.calls.append(("start_job",))
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
    ):
        self.calls.append(
            (
                "finish_job",
                job_id,
                status,
                rows_affected_count,
                rows_inserted_count,
                error_message,
            )
        )

    def get_last_successful_job_id(
        self, destination_schema, destination_table_name, pipeline_stage
    ):
        self.calls.append(
            ("get_last_successful_job_id", destination_schema, destination_table_name, pipeline_stage)
        )
        return self.last_success_id


class _FakeCoreRepo:
    def __init__(self, rows_affected=4, rows_inserted=2):
        self.truncated = []
        self.rows_affected = rows_affected
        self.rows_inserted = rows_inserted
        self.last_sql = None
        self.last_params = None

    def do_truncate(self, table_name):
        self.truncated.append(table_name)

    def raw_sql_load(self, raw_sql, params):
        self.last_sql = raw_sql
        self.last_params = params
        return self.rows_affected

    def count_rows_by_job_id(self, table_name, job_id):
        return self.rows_inserted


class _Runner(CoreExtractRunnerTemplate):
    def __init__(
        self,
        meta_repo,
        core_repo,
        *,
        load_type_value="initial",
        source_path_value="staging.stg_baby",
        dest_table="dim_baby",
    ):
        super().__init__(meta_repo, core_repo)
        self._load_type = load_type_value
        self._source_path = source_path_value
        self._dest_table = dest_table

    def pipeline_stage(self):
        return "transform_load"

    def source_type(self):
        return "db"

    def source_path(self):
        return self._source_path

    def destination_table_name(self):
        return self._dest_table

    def load_type(self):
        return self._load_type

    def get_sql(self):
        return "SELECT :job_id"

    def get_sql_params(self, job_id):
        return {"job_id": job_id}


LOGICAL_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestCoreRunnerHappyPath:
    def test_initial_truncates_and_loads(self):
        meta = _FakeMetaRepo(last_success_id=77)
        core = _FakeCoreRepo(rows_affected=10)
        runner = _Runner(meta, core)

        runner.transform_load_run("d", "t", LOGICAL_DATE)

        assert core.truncated == ["dim_baby"]
        assert core.last_sql == "SELECT :job_id"
        assert core.last_params == {"job_id": 10}

        finish = [c for c in meta.calls if c[0] == "finish_job"][0]
        assert finish[2] == "success"
        assert finish[3] == 10
        assert finish[4] == 2

        # Parent job id was resolved from the last successful staging extract
        meta_call = [c for c in meta.calls if c[0] == "add_job_metadata"][0][1]
        assert meta_call["parent_job_id"] == 77
        assert meta_call["destination_schema"] == "core"

    def test_full_reload_also_truncates(self):
        meta = _FakeMetaRepo()
        core = _FakeCoreRepo()
        runner = _Runner(meta, core, load_type_value="full_reload")
        runner.transform_load_run("d", "t", LOGICAL_DATE)
        assert core.truncated == ["dim_baby"]

    def test_incremental_does_not_truncate(self):
        meta = _FakeMetaRepo(last_success_id=5)
        core = _FakeCoreRepo()
        runner = _Runner(meta, core, load_type_value="incremental")
        runner.transform_load_run("d", "t", LOGICAL_DATE)
        assert core.truncated == []

    def test_full_reload_does_not_resolve_parent_job(self):
        meta = _FakeMetaRepo()
        core = _FakeCoreRepo()
        runner = _Runner(meta, core, load_type_value="full_reload")
        runner.transform_load_run("d", "t", LOGICAL_DATE)

        assert not any(c[0] == "get_last_successful_job_id" for c in meta.calls)
        meta_call = [c for c in meta.calls if c[0] == "add_job_metadata"][0][1]
        assert meta_call["parent_job_id"] is None

    def test_dedup_skip_short_circuits(self):
        meta = _FakeMetaRepo(dedup=True)
        core = _FakeCoreRepo()
        runner = _Runner(meta, core)
        with pytest.raises(AirflowSkipException):
            runner.transform_load_run("d", "t", LOGICAL_DATE)

        assert core.truncated == []
        assert core.last_sql is None

    def test_none_rows_affected_becomes_zero(self):
        meta = _FakeMetaRepo()
        core = _FakeCoreRepo(rows_affected=None)
        runner = _Runner(meta, core)
        runner.transform_load_run("d", "t", LOGICAL_DATE)
        finish = [c for c in meta.calls if c[0] == "finish_job"][0]
        assert finish[3] == 0
        assert finish[4] == 2

    def test_none_rows_inserted_falls_back_to_rows_affected(self):
        meta = _FakeMetaRepo()
        core = _FakeCoreRepo(rows_affected=6, rows_inserted=None)
        runner = _Runner(meta, core, dest_table="dim_time")
        runner.transform_load_run("d", "t", LOGICAL_DATE)

        finish = [c for c in meta.calls if c[0] == "finish_job"][0]
        assert finish[3] == 6
        assert finish[4] == 6


class TestCoreRunnerErrors:
    def test_load_failure_marks_failed_and_reraises(self):
        class BoomRepo(_FakeCoreRepo):
            def raw_sql_load(self, raw_sql, params):
                raise RuntimeError("boom")

        meta = _FakeMetaRepo(last_success_id=1)
        runner = _Runner(meta, BoomRepo())

        with pytest.raises(RuntimeError, match="boom"):
            runner.transform_load_run("d", "t", LOGICAL_DATE)

        finish = [c for c in meta.calls if c[0] == "finish_job"][0]
        assert finish[2] == "failed"
        assert finish[3] == 0
        assert finish[4] == 0
        assert "boom" in finish[5]
        assert "transform_load" in finish[5]

    def test_parent_job_lookup_uses_last_path_segment(self):
        meta = _FakeMetaRepo(last_success_id=1)
        core = _FakeCoreRepo()
        runner = _Runner(meta, core, source_path_value="staging.stg_diaper")

        runner.transform_load_run("d", "t", LOGICAL_DATE)

        call = [c for c in meta.calls if c[0] == "get_last_successful_job_id"][0]
        assert call[1] == "staging"
        assert call[2] == "stg_diaper"
        assert call[3] == "extract"
