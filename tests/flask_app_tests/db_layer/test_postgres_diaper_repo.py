"""DB-layer tests for :class:`PostgresDiaperRepository`."""

from datetime import datetime, timezone

import pytest

from flask_app.db.repositories.postgres_diaper_repo import PostgresDiaperRepository
from flask_app.domain.entities.diaper import Diaper

from ._fake_engine import FakeConnection, FakeEngine, FakeExecResult


def _row(diaper_id: int = 1, baby_id: int = 1, status: str = "wet") -> dict:
    return {
        "id": diaper_id,
        "change_time": datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
        "status": status,
        "baby_id": baby_id,
    }


def _engine(result: FakeExecResult) -> FakeEngine:
    return FakeEngine(FakeConnection(result))


class TestToEntity:
    def test_maps_row(self):
        entity = PostgresDiaperRepository._to_entity(_row(2, 4, "dirty"))
        assert entity.id == 2
        assert entity.baby_id == 4
        assert entity.status == "dirty"

    def test_missing_column_raises_key_error(self):
        with pytest.raises(KeyError):
            PostgresDiaperRepository._to_entity({"id": 1})


class TestCreateDiaper:
    def test_happy_path(self):
        repo = PostgresDiaperRepository(_engine(FakeExecResult(one_value=_row(7))))
        diaper = Diaper(None, datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc), "wet", 1)
        assert repo.create_diaper(diaper).id == 7


class TestGetByBabyId:
    def test_returns_all_rows(self):
        repo = PostgresDiaperRepository(
            _engine(FakeExecResult(all_values=[_row(1), _row(2, status="dirty")]))
        )
        diapers = repo.get_by_baby_id(1)
        assert len(diapers) == 2
        assert diapers[1].status == "dirty"

    def test_empty(self):
        repo = PostgresDiaperRepository(_engine(FakeExecResult(all_values=[])))
        assert repo.get_by_baby_id(1) == []


class TestGetByDiaperId:
    def test_happy_path(self):
        repo = PostgresDiaperRepository(
            _engine(FakeExecResult(one_or_none_value=_row(5)))
        )
        assert repo.get_by_diaper_id(5).id == 5

    def test_returns_none(self):
        repo = PostgresDiaperRepository(_engine(FakeExecResult(one_or_none_value=None)))
        assert repo.get_by_diaper_id(5) is None


class TestUpdateDiaper:
    def test_happy_path(self):
        repo = PostgresDiaperRepository(
            _engine(FakeExecResult(one_or_none_value=_row(5, status="mixed")))
        )
        diaper = Diaper(5, datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc), "mixed", 1)
        assert repo.update_diaper(diaper).status == "mixed"

    def test_returns_none_when_missing(self):
        repo = PostgresDiaperRepository(_engine(FakeExecResult(one_or_none_value=None)))
        diaper = Diaper(99, datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc), "wet", 1)
        assert repo.update_diaper(diaper) is None


class TestDeleteDiaper:
    def test_happy_path(self):
        repo = PostgresDiaperRepository(
            _engine(FakeExecResult(one_or_none_value=_row(5)))
        )
        assert repo.delete_diaper(5).id == 5

    def test_returns_none_when_missing(self):
        repo = PostgresDiaperRepository(_engine(FakeExecResult(one_or_none_value=None)))
        assert repo.delete_diaper(404) is None
