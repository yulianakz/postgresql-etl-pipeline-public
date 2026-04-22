"""Unit tests for :class:`CorePostgresRepository`."""

import pytest

from etl.db.repositories.core_postgres_repo import CorePostgresRepository

from ._fake_engine import FakeConnection, FakeEngine, FakeResult


class TestCoreGetTable:
    @pytest.mark.parametrize(
        "table_name",
        ["dim_baby", "fact_sleep", "fact_diaper", "fact_formula_feed"],
    )
    def test_known_tables(self, table_name):
        repo = CorePostgresRepository(engine=FakeEngine())
        assert repo._get_table(table_name).name == table_name

    def test_unknown_table_raises(self):
        repo = CorePostgresRepository(engine=FakeEngine())
        with pytest.raises(ValueError):
            repo._get_table("nope")


class TestTruncate:
    def test_truncate_executes_statement(self):
        conn = FakeConnection()
        repo = CorePostgresRepository(engine=FakeEngine(connections=[conn]))

        repo.do_truncate("dim_baby")

        assert len(conn.executed) == 1
        stmt = conn.executed[0][0]
        rendered = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "TRUNCATE TABLE core.dim_baby" in rendered


class TestRawSqlLoad:
    def test_runs_each_split_statement_and_sums_rowcount(self):
        conn = FakeConnection(
            results=[
                FakeResult(rowcount=5),
                FakeResult(rowcount=3),
            ]
        )
        repo = CorePostgresRepository(engine=FakeEngine(connections=[conn]))

        rows = repo.raw_sql_load("INSERT INTO a VALUES (1); INSERT INTO b VALUES (2);")

        assert rows == 8
        assert len(conn.executed) == 2

    def test_ignores_negative_or_zero_rowcount(self):
        conn = FakeConnection(
            results=[FakeResult(rowcount=-1), FakeResult(rowcount=0), FakeResult(rowcount=2)]
        )
        repo = CorePostgresRepository(engine=FakeEngine(connections=[conn]))
        rows = repo.raw_sql_load("DDL1; DDL2; INSERT INTO a VALUES (1);")
        assert rows == 2

    def test_empty_sql_returns_zero(self):
        conn = FakeConnection()
        repo = CorePostgresRepository(engine=FakeEngine(connections=[conn]))
        assert repo.raw_sql_load("   ") == 0
        assert conn.executed == []

    def test_params_propagate(self):
        conn = FakeConnection(results=[FakeResult(rowcount=1)])
        repo = CorePostgresRepository(engine=FakeEngine(connections=[conn]))
        repo.raw_sql_load("SELECT :job_id;", params={"job_id": 42})
        assert conn.executed[0][1] == {"job_id": 42}

    def test_none_params_become_empty_dict(self):
        conn = FakeConnection(results=[FakeResult(rowcount=1)])
        repo = CorePostgresRepository(engine=FakeEngine(connections=[conn]))
        repo.raw_sql_load("SELECT 1;")
        assert conn.executed[0][1] == {}


class TestCountRowsByJobId:
    def test_counts_rows_for_table_and_job_id(self):
        conn = FakeConnection(results=[FakeResult(scalar_one=7)])
        repo = CorePostgresRepository(engine=FakeEngine(connections=[conn]))

        count = repo.count_rows_by_job_id("dim_baby", job_id=42)

        assert count == 7
        rendered = str(conn.executed[0][0])
        assert "FROM core.dim_baby" in rendered
        assert "job_id = :job_id" in rendered
        assert conn.executed[0][1] == {"job_id": 42}
