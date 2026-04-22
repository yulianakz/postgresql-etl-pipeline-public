"""Unit tests for :class:`MetadataPostgresRepository`."""

from datetime import datetime, timezone

import pytest

from etl.db.repositories.meta_postgres_repo import MetadataPostgresRepository

from ._fake_engine import FakeConnection, FakeEngine, FakeResult


class TestStartJob:
    def test_inserts_and_returns_job_id(self):
        conn = FakeConnection(results=[FakeResult(scalar_one=99)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))

        job_id = repo.start_job(
            dag_id="d",
            task_id="t",
            logical_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        assert job_id == 99
        assert len(conn.executed) == 1


class TestAddJobMetadata:
    def test_update_statement_executed(self):
        conn = FakeConnection()
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))

        repo.add_job_metadata(
            job_id=42,
            pipeline_stage="extract",
            data_source_type="csv",
            data_source_path="/x/y",
            destination_schema="staging",
            destination_table_name="stg_formula",
        )

        assert len(conn.executed) == 1


class TestFinishJob:
    def test_success_update_passes(self):
        conn = FakeConnection(results=[FakeResult(rowcount=1)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        repo.finish_job(job_id=1, status="success", rows_affected_count=10)

    def test_failed_update_passes(self):
        conn = FakeConnection(results=[FakeResult(rowcount=1)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        repo.finish_job(job_id=1, status="failed", error_message="boom")

    def test_success_update_with_watermark_passes(self):
        conn = FakeConnection(results=[FakeResult(rowcount=1)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        watermark = datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc)

        repo.finish_job(
            job_id=1,
            status="success",
            rows_affected_count=10,
            rows_inserted_count=8,
            last_loaded_event_ts_watermark=watermark,
        )

    def test_invalid_status_raises_value_error(self):
        repo = MetadataPostgresRepository(engine=FakeEngine())
        with pytest.raises(ValueError, match="Invalid status"):
            repo.finish_job(job_id=1, status="wrong-status")

    def test_zero_rowcount_raises_runtime_error(self):
        conn = FakeConnection(results=[FakeResult(rowcount=0)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        with pytest.raises(RuntimeError, match="before start_job"):
            repo.finish_job(job_id=1, status="success")


class TestDedupAndLookups:
    def test_dedup_true(self):
        conn = FakeConnection(results=[FakeResult(scalar=True)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        assert repo.dedup_job_done("d", "t", datetime(2026, 1, 1, tzinfo=timezone.utc)) is True

    def test_dedup_false(self):
        conn = FakeConnection(results=[FakeResult(scalar=False)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        assert repo.dedup_job_done("d", "t", datetime(2026, 1, 1, tzinfo=timezone.utc)) is False

    def test_find_running_returns_id(self):
        conn = FakeConnection(results=[FakeResult(scalar_one_or_none=55)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        assert (
            repo.find_running_job("d", "t", datetime(2026, 1, 1, tzinfo=timezone.utc)) == 55
        )

    def test_find_running_returns_none(self):
        conn = FakeConnection(results=[FakeResult(scalar_one_or_none=None)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        assert (
            repo.find_running_job("d", "t", datetime(2026, 1, 1, tzinfo=timezone.utc)) is None
        )

    def test_is_file_loaded(self):
        conn = FakeConnection(results=[FakeResult(scalar=True)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        assert repo.is_file_loaded("/x/y") is True

    def test_get_last_successful_job_id(self):
        conn = FakeConnection(results=[FakeResult(scalar_one_or_none=7)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        assert (
            repo.get_last_successful_job_id(
                destination_schema="staging",
                destination_table_name="stg_formula",
                pipeline_stage="extract",
            )
            == 7
        )

    def test_get_last_successful_job_id_none(self):
        conn = FakeConnection(results=[FakeResult(scalar_one_or_none=None)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        assert (
            repo.get_last_successful_job_id(
                destination_schema="staging",
                destination_table_name="stg_missing",
                pipeline_stage="extract",
            )
            is None
        )

    def test_get_last_successful_watermark(self):
        watermark = datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc)
        conn = FakeConnection(results=[FakeResult(scalar_one_or_none=watermark)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        assert (
            repo.get_last_successful_watermark(
                destination_schema="staging",
                destination_table_name="stg_sleep",
                pipeline_stage="extract",
            )
            == watermark
        )

    def test_get_last_successful_watermark_none(self):
        conn = FakeConnection(results=[FakeResult(scalar_one_or_none=None)])
        repo = MetadataPostgresRepository(engine=FakeEngine(connections=[conn]))
        assert (
            repo.get_last_successful_watermark(
                destination_schema="staging",
                destination_table_name="stg_missing",
                pipeline_stage="extract",
            )
            is None
        )
