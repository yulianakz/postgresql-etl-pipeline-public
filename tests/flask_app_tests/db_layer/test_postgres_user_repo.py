"""DB-layer tests for :class:`PostgresUserRepository`."""

from datetime import datetime, timezone

import pytest

from flask_app.db.repositories.postgres_user_repo import PostgresUserRepository
from flask_app.domain.entities.user import Role, User

from ._fake_engine import FakeConnection, FakeEngine, FakeExecResult


def _row(user_id: int = 1) -> dict:
    return {
        "id": user_id,
        "user_name": "yulia",
        "password_hash": "x" * 60,
        "role": Role.ADMIN,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }


def _engine(result: FakeExecResult) -> FakeEngine:
    return FakeEngine(FakeConnection(result))


class TestToEntity:
    def test_maps_row(self):
        user = PostgresUserRepository._to_entity(_row(7))
        assert user.id == 7
        assert user.user_name == "yulia"
        assert user.role == Role.ADMIN

    def test_missing_column_raises_key_error(self):
        with pytest.raises(KeyError):
            PostgresUserRepository._to_entity({"id": 1})


class TestCreateUser:
    def test_happy_path(self):
        repo = PostgresUserRepository(_engine(FakeExecResult(one_value=_row(7))))
        user = User(None, "yulia", "x" * 60, Role.ADMIN, None)
        assert repo.create_user(user).id == 7


class TestGetById:
    def test_happy_path(self):
        repo = PostgresUserRepository(_engine(FakeExecResult(one_or_none_value=_row(9))))
        assert repo.get_by_id(9).id == 9

    def test_returns_none(self):
        repo = PostgresUserRepository(_engine(FakeExecResult(one_or_none_value=None)))
        assert repo.get_by_id(9) is None


class TestGetByUsername:
    def test_happy_path(self):
        repo = PostgresUserRepository(_engine(FakeExecResult(one_or_none_value=_row())))
        assert repo.get_by_username("yulia").user_name == "yulia"

    def test_returns_none(self):
        repo = PostgresUserRepository(_engine(FakeExecResult(one_or_none_value=None)))
        assert repo.get_by_username("ghost") is None


class TestGetAll:
    def test_returns_all(self):
        repo = PostgresUserRepository(
            _engine(FakeExecResult(all_values=[_row(1), _row(2)]))
        )
        assert [u.id for u in repo.get_all()] == [1, 2]

    def test_empty(self):
        repo = PostgresUserRepository(_engine(FakeExecResult(all_values=[])))
        assert repo.get_all() == []
