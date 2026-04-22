"""Service-layer tests for :class:`SleepService`."""

from datetime import datetime, timedelta, timezone

import pytest

from flask_app.application.services.sleep_service import SleepService
from flask_app.domain.entities.sleep import Sleep


class FakeSleepRepo:
    def __init__(self, existing: dict[int, Sleep] | None = None):
        self._store: dict[int, Sleep] = dict(existing or {})
        self._next_id = max(self._store, default=0) + 1
        self.create_calls: list[Sleep] = []
        self.update_calls: list[Sleep] = []
        self.delete_calls: list[int] = []

    def create_sleep(self, sleep: Sleep) -> Sleep:
        sleep.id = self._next_id
        self._next_id += 1
        self._store[sleep.id] = sleep
        self.create_calls.append(sleep)
        return sleep

    def get_by_baby_id(self, baby_id: int) -> list[Sleep]:
        return [s for s in self._store.values() if s.baby_id == baby_id]

    def get_by_sleep_id(self, sleep_id: int) -> Sleep | None:
        return self._store.get(sleep_id)

    def update_sleep(self, sleep: Sleep) -> Sleep | None:
        if sleep.id not in self._store:
            return None
        self._store[sleep.id] = sleep
        self.update_calls.append(sleep)
        return sleep

    def delete_sleep(self, sleep_id: int) -> Sleep | None:
        self.delete_calls.append(sleep_id)
        return self._store.pop(sleep_id, None)


class FakeBabyRepo:
    def __init__(self, existing_ids: set[int]):
        self.existing_ids = set(existing_ids)

    def get_by_id(self, baby_id: int):
        return object() if baby_id in self.existing_ids else None


@pytest.fixture()
def sleep_repo() -> FakeSleepRepo:
    return FakeSleepRepo()


@pytest.fixture()
def baby_repo() -> FakeBabyRepo:
    return FakeBabyRepo(existing_ids={1})


@pytest.fixture()
def service(sleep_repo: FakeSleepRepo, baby_repo: FakeBabyRepo) -> SleepService:
    return SleepService(sleep_repo, baby_repo)


def _past_utc(minutes: int = 60) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes)


class TestCreateSleep:
    def test_happy_path_utc_aware(self, service: SleepService, sleep_repo: FakeSleepRepo):
        start = _past_utc()
        created = service.create_sleep(start, 45, 1)

        assert created.start == start
        assert created.duration == 45
        assert created.baby_id == 1
        assert sleep_repo.create_calls == [created]

    def test_happy_path_naive_treated_as_utc(self, service: SleepService):
        naive = datetime(2026, 1, 1, 8, 30, 0)
        created = service.create_sleep(naive, 30, 1)

        assert created.start.tzinfo == timezone.utc

    def test_happy_path_non_utc_is_converted(self, service: SleepService):
        from datetime import timezone as tz

        offset = tz(timedelta(hours=2))
        aware = datetime.now(offset) - timedelta(hours=1)
        created = service.create_sleep(aware, 60, 1)

        assert created.start.tzinfo == timezone.utc

    def test_rejects_zero_duration(self, service: SleepService):
        with pytest.raises(ValueError, match="positive"):
            service.create_sleep(_past_utc(), 0, 1)

    def test_rejects_negative_duration(self, service: SleepService):
        with pytest.raises(ValueError, match="positive"):
            service.create_sleep(_past_utc(), -15, 1)

    def test_rejects_future_start(self, service: SleepService):
        future = datetime.now(timezone.utc) + timedelta(minutes=5)
        with pytest.raises(ValueError, match="future"):
            service.create_sleep(future, 30, 1)

    def test_rejects_invalid_baby_id(self, service: SleepService):
        with pytest.raises(ValueError, match="Invalid baby id"):
            service.create_sleep(_past_utc(), 30, 0)

    def test_rejects_unknown_baby(self, service: SleepService):
        with pytest.raises(ValueError, match="does not exist"):
            service.create_sleep(_past_utc(), 30, 999)

    def test_wrong_duration_type_raises_type_error(self, service: SleepService):
        with pytest.raises(TypeError):
            service.create_sleep(_past_utc(), "30", 1)  # type: ignore[arg-type]


class TestGetSleepByBabyId:
    def test_happy_path(self, service: SleepService):
        service.create_sleep(_past_utc(), 30, 1)
        service.create_sleep(_past_utc(30), 60, 1)

        sleeps = service.get_sleep_by_baby_id(1)
        assert len(sleeps) == 2

    def test_rejects_invalid_baby_id(self, service: SleepService):
        with pytest.raises(ValueError, match="Invalid baby id"):
            service.get_sleep_by_baby_id(0)

    def test_rejects_unknown_baby(self, service: SleepService):
        with pytest.raises(ValueError, match="does not exist"):
            service.get_sleep_by_baby_id(777)


class TestGetSleepBySleepId:
    def test_happy_path(self, service: SleepService):
        sleep = service.create_sleep(_past_utc(), 30, 1)
        assert service.get_sleep_by_sleep_id(1, sleep.id) is sleep

    def test_returns_none_when_missing(self, service: SleepService):
        assert service.get_sleep_by_sleep_id(1, 404) is None

    def test_rejects_invalid_sleep_id(self, service: SleepService):
        with pytest.raises(ValueError, match="Invalid sleep id"):
            service.get_sleep_by_sleep_id(1, 0)

    def test_rejects_invalid_baby_id(self, service: SleepService):
        with pytest.raises(ValueError, match="Invalid baby id"):
            service.get_sleep_by_sleep_id(0, 5)

    def test_raises_permission_error_on_foreign_baby(self, service: SleepService):
        sleep = service.create_sleep(_past_utc(), 30, 1)
        with pytest.raises(PermissionError, match="does not belong"):
            service.get_sleep_by_sleep_id(2, sleep.id)


class TestUpdateSleep:
    def test_happy_path(self, service: SleepService):
        sleep = service.create_sleep(_past_utc(), 30, 1)

        new_start = _past_utc(120)
        updated = service.update_sleep(1, sleep.id, new_start, 120)

        assert updated is not None
        assert updated.duration == 120

    def test_returns_none_when_missing(self, service: SleepService):
        assert service.update_sleep(1, 999, _past_utc(), 30) is None

    def test_rejects_non_positive_duration(self, service: SleepService):
        with pytest.raises(ValueError, match="positive"):
            service.update_sleep(1, 1, _past_utc(), 0)

    def test_rejects_future_start(self, service: SleepService):
        with pytest.raises(ValueError, match="future"):
            service.update_sleep(
                1, 1, datetime.now(timezone.utc) + timedelta(minutes=5), 30
            )


class TestDeleteSleep:
    def test_happy_path(self, service: SleepService, sleep_repo: FakeSleepRepo):
        sleep = service.create_sleep(_past_utc(), 30, 1)

        deleted = service.delete_sleep_by_id(1, sleep.id)

        assert deleted is sleep
        assert sleep_repo.delete_calls == [sleep.id]

    def test_returns_none_when_missing(self, service: SleepService):
        assert service.delete_sleep_by_id(1, 999) is None

    def test_rejects_non_positive_ids(self, service: SleepService):
        with pytest.raises(ValueError, match="Invalid id"):
            service.delete_sleep_by_id(0, 1)
        with pytest.raises(ValueError, match="Invalid id"):
            service.delete_sleep_by_id(1, 0)
