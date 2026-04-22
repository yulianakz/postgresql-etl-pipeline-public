"""Service-layer tests for :class:`BabyService`.

Covers the happy path for every public method, all domain validation
rules (invalid name length, invalid id, invalid timezone), and edge
cases around missing records on update/delete.
"""

import pytest

from flask_app.application.services.baby_service import BabyService
from flask_app.domain.entities.baby import Baby


class FakeBabyRepo:
    """In-memory stand-in for :class:`BabyRepository`."""

    def __init__(self, existing: dict[int, Baby] | None = None):
        self._store: dict[int, Baby] = dict(existing or {})
        self._next_id = max(self._store, default=0) + 1
        self.create_calls: list[Baby] = []
        self.update_calls: list[Baby] = []
        self.delete_calls: list[int] = []

    def create_baby(self, baby: Baby) -> Baby:
        baby.id = self._next_id
        self._next_id += 1
        self._store[baby.id] = baby
        self.create_calls.append(baby)
        return baby

    def get_all(self) -> list[Baby]:
        return list(self._store.values())

    def get_by_id(self, baby_id: int) -> Baby | None:
        return self._store.get(baby_id)

    def update_baby(self, baby: Baby) -> Baby | None:
        if baby.id not in self._store:
            return None
        self._store[baby.id] = baby
        self.update_calls.append(baby)
        return baby

    def delete_baby(self, baby_id: int) -> Baby | None:
        self.delete_calls.append(baby_id)
        return self._store.pop(baby_id, None)


@pytest.fixture()
def repo() -> FakeBabyRepo:
    return FakeBabyRepo()


@pytest.fixture()
def service(repo: FakeBabyRepo) -> BabyService:
    return BabyService(repo)


class TestCreateBaby:
    def test_happy_path_trims_and_persists(self, service: BabyService, repo: FakeBabyRepo):
        baby = service.create_baby("  Adriana  ", "Europe/Chisinau")

        assert baby.name == "Adriana"
        assert baby.timezone == "Europe/Chisinau"
        assert baby.id == 1
        assert repo.create_calls == [baby]

    def test_accepts_min_length_name(self, service: BabyService):
        assert service.create_baby("Abc", "UTC").name == "Abc"

    def test_accepts_max_length_name(self, service: BabyService):
        long_name = "A" * 50
        assert service.create_baby(long_name, "UTC").name == long_name

    def test_rejects_empty_name(self, service: BabyService):
        with pytest.raises(ValueError, match="Invalid baby name"):
            service.create_baby("   ", "UTC")

    def test_rejects_short_name(self, service: BabyService):
        with pytest.raises(ValueError, match="Invalid baby name"):
            service.create_baby("ab", "UTC")

    def test_rejects_too_long_name(self, service: BabyService):
        with pytest.raises(ValueError, match="Invalid baby name"):
            service.create_baby("A" * 51, "UTC")

    def test_rejects_invalid_timezone(self, service: BabyService):
        with pytest.raises(ValueError, match="Invalid timezone"):
            service.create_baby("Adriana", "Mars/Phobos")

    def test_wrong_name_type_raises(self, service: BabyService):
        with pytest.raises(AttributeError):
            service.create_baby(None, "UTC")  # type: ignore[arg-type]


class TestGetBabyById:
    def test_happy_path(self, service: BabyService, repo: FakeBabyRepo):
        stored = service.create_baby("Adriana", "UTC")
        assert service.get_baby_by_id(stored.id) is stored

    def test_returns_none_when_missing(self, service: BabyService):
        assert service.get_baby_by_id(404) is None

    def test_rejects_zero_id(self, service: BabyService):
        with pytest.raises(ValueError, match="Invalid baby id"):
            service.get_baby_by_id(0)

    def test_rejects_negative_id(self, service: BabyService):
        with pytest.raises(ValueError, match="Invalid baby id"):
            service.get_baby_by_id(-5)


class TestUpdateBaby:
    def test_happy_path_updates_name_and_timezone(self, service: BabyService):
        baby = service.create_baby("Adriana", "UTC")

        updated = service.update_baby_info(baby.id, "  Adi  ", "  Europe/Chisinau  ")

        assert updated is not None
        assert updated.name == "Adi"
        assert updated.timezone == "Europe/Chisinau"

    def test_returns_none_when_baby_missing(self, service: BabyService):
        assert service.update_baby_info(42, "Name", "UTC") is None

    def test_rejects_invalid_new_name(self, service: BabyService):
        baby = service.create_baby("Adriana", "UTC")
        with pytest.raises(ValueError, match="Invalid baby name"):
            service.update_baby_info(baby.id, "x", "UTC")

    def test_rejects_invalid_new_timezone(self, service: BabyService):
        baby = service.create_baby("Adriana", "UTC")
        with pytest.raises(ValueError, match="Invalid timezone"):
            service.update_baby_info(baby.id, "Adriana", "Not/Real")

    def test_rejects_non_positive_id(self, service: BabyService):
        with pytest.raises(ValueError, match="Invalid baby id"):
            service.update_baby_info(0, "Adriana", "UTC")


class TestDeleteBaby:
    def test_happy_path(self, service: BabyService, repo: FakeBabyRepo):
        baby = service.create_baby("Adriana", "UTC")

        deleted = service.delete_baby_by_id(baby.id)

        assert deleted is baby
        assert repo.delete_calls == [baby.id]
        assert service.get_baby_by_id(baby.id) is None

    def test_returns_none_when_missing(self, service: BabyService):
        assert service.delete_baby_by_id(999) is None

    def test_rejects_non_positive_id(self, service: BabyService):
        with pytest.raises(ValueError, match="Invalid baby id"):
            service.delete_baby_by_id(0)


class TestGetAllBabies:
    def test_returns_empty_list(self, service: BabyService):
        assert service.get_all_babies() == []

    def test_returns_all_existing_babies(self, service: BabyService):
        service.create_baby("Adriana", "UTC")
        service.create_baby("Maria", "UTC")
        assert len(service.get_all_babies()) == 2
