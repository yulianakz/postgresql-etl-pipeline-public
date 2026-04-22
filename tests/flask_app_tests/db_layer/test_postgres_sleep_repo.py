"""DB-layer tests for :class:`PostgresSleepRepository`."""

from datetime import datetime, timezone

import pytest

from flask_app.db.repositories.postgres_sleep_repo import PostgresSleepRepository
from flask_app.domain.entities.sleep import Sleep

from ._fake_engine import FakeConnection, FakeEngine, FakeExecResult


def _row(sleep_id: int = 1, baby_id: int = 1) -> dict:
    return {
        "id": sleep_id,
        "sleep_start": datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
        "sleep_duration": 60,
        "baby_id": baby_id,
    }


def _engine(result: FakeExecResult) -> FakeEngine:
    return FakeEngine(FakeConnection(result))


class TestToEntity:
    def test_maps_row(self):
        entity = PostgresSleepRepository._to_entity(_row(3, 9))
        assert entity.id == 3
        assert entity.baby_id == 9
        assert entity.duration == 60

    def test_missing_column_raises_key_error(self):
        with pytest.raises(KeyError):
            PostgresSleepRepository._to_entity({"id": 1, "baby_id": 1})


class TestCreateSleep:
    def test_happy_path(self):
        repo = PostgresSleepRepository(_engine(FakeExecResult(one_value=_row(7))))
        sleep = Sleep(
            None,
            datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
            60,
            1,
        )
        created = repo.create_sleep(sleep)
        assert created.id == 7


class TestGetByBabyId:
    def test_returns_all_rows(self):
        repo = PostgresSleepRepository(
            _engine(FakeExecResult(all_values=[_row(1), _row(2)]))
        )
        assert [s.id for s in repo.get_by_baby_id(1)] == [1, 2]

    def test_returns_empty(self):
        repo = PostgresSleepRepository(_engine(FakeExecResult(all_values=[])))
        assert repo.get_by_baby_id(1) == []


class TestGetBySleepId:
    def test_happy_path(self):
        repo = PostgresSleepRepository(_engine(FakeExecResult(one_or_none_value=_row(5))))
        assert repo.get_by_sleep_id(5).id == 5

    def test_returns_none(self):
        repo = PostgresSleepRepository(
            _engine(FakeExecResult(one_or_none_value=None))
        )
        assert repo.get_by_sleep_id(5) is None


class TestUpdateSleep:
    def test_happy_path(self):
        repo = PostgresSleepRepository(_engine(FakeExecResult(one_or_none_value=_row(5))))
        sleep = Sleep(5, datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc), 90, 1)
        assert repo.update_sleep(sleep).id == 5

    def test_returns_none_when_missing(self):
        repo = PostgresSleepRepository(_engine(FakeExecResult(one_or_none_value=None)))
        sleep = Sleep(99, datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc), 30, 1)
        assert repo.update_sleep(sleep) is None


class TestDeleteSleep:
    def test_happy_path(self):
        repo = PostgresSleepRepository(_engine(FakeExecResult(one_or_none_value=_row(5))))
        assert repo.delete_sleep(5).id == 5

    def test_returns_none_when_missing(self):
        repo = PostgresSleepRepository(_engine(FakeExecResult(one_or_none_value=None)))
        assert repo.delete_sleep(404) is None
