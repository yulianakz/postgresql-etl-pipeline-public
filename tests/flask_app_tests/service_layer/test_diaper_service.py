"""Service-layer tests for :class:`DiaperService`."""

from datetime import datetime, timedelta, timezone

import pytest

from flask_app.application.services.diaper_service import DiaperService
from flask_app.domain.entities.diaper import Diaper


class FakeDiaperRepo:
    def __init__(self):
        self._store: dict[int, Diaper] = {}
        self._next_id = 1
        self.create_calls: list[Diaper] = []
        self.update_calls: list[Diaper] = []
        self.delete_calls: list[int] = []

    def create_diaper(self, diaper: Diaper) -> Diaper:
        diaper.id = self._next_id
        self._next_id += 1
        self._store[diaper.id] = diaper
        self.create_calls.append(diaper)
        return diaper

    def get_by_baby_id(self, baby_id: int) -> list[Diaper]:
        return [d for d in self._store.values() if d.baby_id == baby_id]

    def get_by_diaper_id(self, diaper_id: int) -> Diaper | None:
        return self._store.get(diaper_id)

    def update_diaper(self, diaper: Diaper) -> Diaper | None:
        if diaper.id not in self._store:
            return None
        self._store[diaper.id] = diaper
        self.update_calls.append(diaper)
        return diaper

    def delete_diaper(self, diaper_id: int) -> Diaper | None:
        self.delete_calls.append(diaper_id)
        return self._store.pop(diaper_id, None)


class FakeBabyRepo:
    def __init__(self, existing_ids: set[int]):
        self.existing_ids = set(existing_ids)

    def get_by_id(self, baby_id: int):
        return object() if baby_id in self.existing_ids else None


@pytest.fixture()
def diaper_repo() -> FakeDiaperRepo:
    return FakeDiaperRepo()


@pytest.fixture()
def service(diaper_repo: FakeDiaperRepo) -> DiaperService:
    return DiaperService(diaper_repo, FakeBabyRepo(existing_ids={1}))


def _past_utc(minutes: int = 10) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes)


class TestCreateDiaper:
    def test_happy_path(self, service: DiaperService, diaper_repo: FakeDiaperRepo):
        change_time = _past_utc()
        diaper = service.create_diaper(change_time, "wet", 1)

        assert diaper.status == "wet"
        assert diaper.baby_id == 1
        assert diaper_repo.create_calls == [diaper]

    def test_status_is_trimmed_and_lowered(self, service: DiaperService):
        diaper = service.create_diaper(_past_utc(), "  DIRTY  ", 1)
        assert diaper.status == "dirty"

    @pytest.mark.parametrize("status", ["wet", "dirty", "mixed"])
    def test_accepts_every_valid_status(self, service: DiaperService, status: str):
        assert service.create_diaper(_past_utc(), status, 1).status == status

    def test_rejects_invalid_status(self, service: DiaperService):
        with pytest.raises(ValueError, match="Invalid diaper status"):
            service.create_diaper(_past_utc(), "golden", 1)

    def test_rejects_future_change_time(self, service: DiaperService):
        future = datetime.now(timezone.utc) + timedelta(minutes=5)
        with pytest.raises(ValueError, match="future"):
            service.create_diaper(future, "wet", 1)

    def test_rejects_invalid_baby_id(self, service: DiaperService):
        with pytest.raises(ValueError, match="Invalid baby id"):
            service.create_diaper(_past_utc(), "wet", 0)

    def test_rejects_unknown_baby(self, service: DiaperService):
        with pytest.raises(ValueError, match="does not exist"):
            service.create_diaper(_past_utc(), "wet", 42)

    def test_wrong_status_type_raises_attribute_error(self, service: DiaperService):
        with pytest.raises(AttributeError):
            service.create_diaper(_past_utc(), None, 1)  # type: ignore[arg-type]


class TestGetDiapersByBabyId:
    def test_happy_path(self, service: DiaperService):
        service.create_diaper(_past_utc(), "wet", 1)
        service.create_diaper(_past_utc(5), "dirty", 1)
        assert len(service.get_diaper_by_baby_id(1)) == 2

    def test_rejects_invalid_baby_id(self, service: DiaperService):
        with pytest.raises(ValueError, match="Invalid baby id"):
            service.get_diaper_by_baby_id(0)

    def test_rejects_unknown_baby(self, service: DiaperService):
        with pytest.raises(ValueError, match="does not exist"):
            service.get_diaper_by_baby_id(777)


class TestGetDiaperById:
    def test_happy_path(self, service: DiaperService):
        diaper = service.create_diaper(_past_utc(), "wet", 1)
        assert service.get_diaper_by_diaper_id(1, diaper.id) is diaper

    def test_returns_none_when_missing(self, service: DiaperService):
        assert service.get_diaper_by_diaper_id(1, 777) is None

    def test_rejects_invalid_diaper_id(self, service: DiaperService):
        with pytest.raises(ValueError):
            service.get_diaper_by_diaper_id(1, 0)

    def test_rejects_invalid_baby_id(self, service: DiaperService):
        with pytest.raises(ValueError, match="Invalid baby id"):
            service.get_diaper_by_diaper_id(0, 1)

    def test_permission_error_when_baby_doesnt_own_diaper(self, service: DiaperService):
        diaper = service.create_diaper(_past_utc(), "wet", 1)
        with pytest.raises(PermissionError, match="does not belong"):
            service.get_diaper_by_diaper_id(2, diaper.id)


class TestUpdateDiaper:
    def test_happy_path(self, service: DiaperService):
        diaper = service.create_diaper(_past_utc(), "wet", 1)

        updated = service.update_diaper(1, diaper.id, _past_utc(1), "mixed")

        assert updated is not None
        assert updated.status == "mixed"

    def test_returns_none_when_missing(self, service: DiaperService):
        assert service.update_diaper(1, 999, _past_utc(), "wet") is None

    def test_rejects_future_time(self, service: DiaperService):
        future = datetime.now(timezone.utc) + timedelta(minutes=5)
        with pytest.raises(ValueError, match="future"):
            service.update_diaper(1, 1, future, "wet")

    def test_rejects_non_positive_ids(self, service: DiaperService):
        with pytest.raises(ValueError, match="Invalid id"):
            service.update_diaper(0, 1, _past_utc(), "wet")
        with pytest.raises(ValueError, match="Invalid id"):
            service.update_diaper(1, 0, _past_utc(), "wet")

    def test_rejects_invalid_status_on_update(self, service: DiaperService):
        diaper = service.create_diaper(_past_utc(), "wet", 1)
        with pytest.raises(ValueError, match="Invalid diaper status"):
            service.update_diaper(1, diaper.id, _past_utc(), "sparkly")

    def test_permission_error_on_foreign_baby(self, service: DiaperService):
        diaper = service.create_diaper(_past_utc(), "wet", 1)
        with pytest.raises(PermissionError, match="does not belong"):
            service.update_diaper(2, diaper.id, _past_utc(), "wet")


class TestDeleteDiaper:
    def test_happy_path(self, service: DiaperService, diaper_repo: FakeDiaperRepo):
        diaper = service.create_diaper(_past_utc(), "wet", 1)

        deleted = service.delete_diaper_by_id(1, diaper.id)

        assert deleted is diaper
        assert diaper_repo.delete_calls == [diaper.id]

    def test_returns_none_when_missing(self, service: DiaperService):
        assert service.delete_diaper_by_id(1, 999) is None

    def test_rejects_non_positive_ids(self, service: DiaperService):
        with pytest.raises(ValueError, match="Invalid id"):
            service.delete_diaper_by_id(0, 1)
        with pytest.raises(ValueError, match="Invalid id"):
            service.delete_diaper_by_id(1, 0)
