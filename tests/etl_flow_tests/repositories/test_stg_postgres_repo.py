"""Unit tests for :class:`StgPostgresRepository`."""

from datetime import datetime

import pytest

from etl.db.repositories.stg_postgres_repo import StgPostgresRepository
from etl.db.tables.staging_tables import stg_baby, stg_diaper, stg_formula, stg_sleep
from etl.extract.domain.entities.extract_entities import (
    BabyDataEntity,
    DiaperDataEntity,
    FormulaDataEntity,
    SleepDataEntity,
)
from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity

from ._fake_engine import FakeConnection, FakeEngine, FakeResult


class TestGetTable:
    @pytest.mark.parametrize(
        "entity_type, expected_table",
        [
            (BabyDataEntity, stg_baby),
            (SleepDataEntity, stg_sleep),
            (DiaperDataEntity, stg_diaper),
            (FormulaDataEntity, stg_formula),
        ],
    )
    def test_maps_entity_to_table(self, entity_type, expected_table):
        repo = StgPostgresRepository(engine=FakeEngine())
        assert repo._get_table(entity_type) is expected_table

    def test_unknown_entity_raises(self):
        repo = StgPostgresRepository(engine=FakeEngine())
        with pytest.raises(ValueError, match="No table"):
            repo._get_table(str)


class TestDoTruncate:
    def test_executes_truncate_statement(self):
        conn = FakeConnection()
        repo = StgPostgresRepository(engine=FakeEngine(connections=[conn]))

        repo.do_truncate(BabyDataEntity)

        assert len(conn.executed) == 1
        stmt = conn.executed[0][0]
        rendered = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "TRUNCATE TABLE staging.stg_baby" in rendered


class TestChunkLoad:
    def _make_entity(self, source_id: int) -> BabyDataEntity:
        return BabyDataEntity(source_id=source_id, name=f"n{source_id}", timezone="UTC")

    def test_happy_path_inserts_once_for_small_batch(self):
        conn = FakeConnection()
        repo = StgPostgresRepository(engine=FakeEngine(connections=[conn]))

        entities = [self._make_entity(i) for i in range(3)]
        rows_loaded = repo.chunk_load(job_id=1, entity_type=BabyDataEntity, entities=entities)

        assert rows_loaded == 3
        assert len(conn.executed) == 1  # one final insert flush

    def test_chunking_flushes_at_chunk_size(self):
        conn = FakeConnection()
        repo = StgPostgresRepository(engine=FakeEngine(connections=[conn]))

        entities = [self._make_entity(i) for i in range(5)]
        rows_loaded = repo.chunk_load(
            job_id=1, entity_type=BabyDataEntity, entities=entities, chunk_size=2
        )

        assert rows_loaded == 5
        # 2 + 2 chunks, then a tail of 1 = 3 flushes
        assert len(conn.executed) == 3

    def test_none_entries_are_skipped(self):
        conn = FakeConnection()
        repo = StgPostgresRepository(engine=FakeEngine(connections=[conn]))

        entities = [self._make_entity(1), None, self._make_entity(2)]
        assert repo.chunk_load(1, BabyDataEntity, entities) == 2
        assert len(conn.executed) == 1

    def test_broken_entities_are_logged_not_inserted(self, monkeypatch):
        calls = []

        def fake_log(row, error_message, job_id, mapper_name):
            calls.append({"row": row, "error_message": error_message,
                          "job_id": job_id, "mapper_name": mapper_name})

        from etl.db.repositories import stg_postgres_repo

        monkeypatch.setattr(stg_postgres_repo, "log_bad_row", fake_log)

        conn = FakeConnection()
        repo = StgPostgresRepository(engine=FakeEngine(connections=[conn]))

        broken = BrokenEntity(raw_row={"id": 0}, error_message="bad", mapper_name="m")
        entities = [self._make_entity(1), broken, self._make_entity(2)]

        rows_loaded = repo.chunk_load(job_id=7, entity_type=BabyDataEntity, entities=entities)

        assert rows_loaded == 2
        assert len(calls) == 1
        assert calls[0] == {
            "row": {"id": 0},
            "error_message": "bad",
            "job_id": 7,
            "mapper_name": "m",
        }

    def test_empty_input_does_not_execute(self):
        conn = FakeConnection()
        repo = StgPostgresRepository(engine=FakeEngine(connections=[conn]))
        assert repo.chunk_load(1, BabyDataEntity, iter([])) == 0
        assert conn.executed == []

    def test_assigns_job_id_and_loaded_at_on_entity(self):
        conn = FakeConnection()
        repo = StgPostgresRepository(engine=FakeEngine(connections=[conn]))

        entity = self._make_entity(1)
        repo.chunk_load(job_id=99, entity_type=BabyDataEntity, entities=[entity])

        assert entity.job_id == 99
        assert entity.loaded_at is not None

    def test_unknown_entity_type_raises(self):
        repo = StgPostgresRepository(engine=FakeEngine(connections=[FakeConnection()]))
        with pytest.raises(ValueError, match="No table"):
            repo.chunk_load(1, str, [object()])


class TestGetJobMaxWatermark:
    def test_returns_max_watermark_for_job(self):
        expected = datetime(2026, 1, 2, 12, 0)
        conn = FakeConnection(results=[FakeResult(scalar_one_or_none=expected)])
        repo = StgPostgresRepository(engine=FakeEngine(connections=[conn]))

        result = repo.get_job_max_watermark(
            entity_type=SleepDataEntity,
            job_id=77,
            watermark_column="sleep_start",
        )

        assert result == expected
        assert len(conn.executed) == 1

    def test_unknown_watermark_column_raises(self):
        repo = StgPostgresRepository(engine=FakeEngine(connections=[FakeConnection()]))

        with pytest.raises(ValueError, match="Unknown watermark column"):
            repo.get_job_max_watermark(
                entity_type=SleepDataEntity,
                job_id=1,
                watermark_column="not_a_column",
            )
