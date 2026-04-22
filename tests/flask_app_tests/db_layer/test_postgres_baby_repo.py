"""DB-layer tests for :class:`PostgresBabyRepository`.

We stub out the SQLAlchemy engine so each test exercises statement
construction and the ``_to_entity`` row mapping without requiring a
real Postgres instance.
"""

import pytest

from flask_app.db.repositories.postgres_baby_repo import PostgresBabyRepository
from flask_app.domain.entities.baby import Baby

from ._fake_engine import FakeConnection, FakeEngine, FakeExecResult


def _engine(result: FakeExecResult) -> tuple[FakeEngine, FakeConnection]:
    conn = FakeConnection(result)
    return FakeEngine(conn), conn


class TestToEntity:
    def test_maps_row_to_baby(self):
        baby = PostgresBabyRepository._to_entity(
            {"id": 7, "name": "Adi", "timezone": "UTC"}
        )
        assert isinstance(baby, Baby)
        assert baby.id == 7
        assert baby.name == "Adi"
        assert baby.timezone == "UTC"

    def test_missing_column_raises_key_error(self):
        with pytest.raises(KeyError):
            PostgresBabyRepository._to_entity({"id": 1, "name": "Adi"})


class TestCreateBaby:
    def test_happy_path(self):
        row = {"id": 1, "name": "Adriana", "timezone": "Europe/Chisinau"}
        engine, conn = _engine(FakeExecResult(one_value=row))
        repo = PostgresBabyRepository(engine)

        created = repo.create_baby(Baby(None, "Adriana", "Europe/Chisinau"))

        assert (created.id, created.name, created.timezone) == (
            1, "Adriana", "Europe/Chisinau"
        )
        assert conn.executed_stmt is not None


class TestGetAll:
    def test_returns_list_of_entities(self):
        rows = [
            {"id": 1, "name": "Adi", "timezone": "UTC"},
            {"id": 2, "name": "Maria", "timezone": "Europe/Paris"},
        ]
        engine, _ = _engine(FakeExecResult(all_values=rows))
        repo = PostgresBabyRepository(engine)

        babies = repo.get_all()

        assert [b.id for b in babies] == [1, 2]

    def test_empty_db_returns_empty_list(self):
        engine, _ = _engine(FakeExecResult(all_values=[]))
        repo = PostgresBabyRepository(engine)
        assert repo.get_all() == []


class TestGetById:
    def test_happy_path(self):
        row = {"id": 1, "name": "Adi", "timezone": "UTC"}
        engine, _ = _engine(FakeExecResult(one_or_none_value=row))
        repo = PostgresBabyRepository(engine)

        assert repo.get_by_id(1).name == "Adi"

    def test_returns_none_when_missing(self):
        engine, _ = _engine(FakeExecResult(one_or_none_value=None))
        repo = PostgresBabyRepository(engine)
        assert repo.get_by_id(999) is None


class TestUpdateBaby:
    def test_happy_path(self):
        row = {"id": 1, "name": "Adi2", "timezone": "UTC"}
        engine, _ = _engine(FakeExecResult(one_or_none_value=row))
        repo = PostgresBabyRepository(engine)

        result = repo.update_baby(Baby(1, "Adi2", "UTC"))

        assert result is not None
        assert result.name == "Adi2"

    def test_returns_none_when_missing(self):
        engine, _ = _engine(FakeExecResult(one_or_none_value=None))
        repo = PostgresBabyRepository(engine)
        assert repo.update_baby(Baby(999, "x", "UTC")) is None


class TestDeleteBaby:
    def test_happy_path(self):
        row = {"id": 1, "name": "Adi", "timezone": "UTC"}
        engine, _ = _engine(FakeExecResult(one_or_none_value=row))
        repo = PostgresBabyRepository(engine)

        deleted = repo.delete_baby(1)
        assert deleted is not None
        assert deleted.id == 1

    def test_returns_none_when_missing(self):
        engine, _ = _engine(FakeExecResult(one_or_none_value=None))
        repo = PostgresBabyRepository(engine)
        assert repo.delete_baby(999) is None
