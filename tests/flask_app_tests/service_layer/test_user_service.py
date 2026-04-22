"""Service-layer tests for :class:`UserService`."""

import pytest

from flask_app.application.services.user_service import UserService
from flask_app.domain.entities.user import Role, User


class FakeUserRepo:
    def __init__(self):
        self._by_name: dict[str, User] = {}
        self._by_id: dict[int, User] = {}
        self._next_id = 1
        self.create_calls: list[User] = []

    def create_user(self, user: User) -> User:
        user.id = self._next_id
        self._next_id += 1
        self._by_id[user.id] = user
        self._by_name[user.user_name] = user
        self.create_calls.append(user)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        return self._by_id.get(user_id)

    def get_by_username(self, username: str) -> User | None:
        return self._by_name.get(username)

    def get_all(self) -> list[User]:
        return list(self._by_id.values())


@pytest.fixture()
def repo() -> FakeUserRepo:
    return FakeUserRepo()


@pytest.fixture()
def service(repo: FakeUserRepo) -> UserService:
    return UserService(repo)


VALID_HASH = "x" * 60


class TestCreateUser:
    def test_happy_path_lowers_and_trims(self, service: UserService, repo: FakeUserRepo):
        user = service.create_user("  Yulia ", VALID_HASH, Role.GUEST)

        assert user.user_name == "yulia"
        assert user.role == Role.GUEST
        assert repo.create_calls == [user]

    def test_rejects_short_username(self, service: UserService):
        with pytest.raises(ValueError, match="Invalid user name"):
            service.create_user("ab", VALID_HASH, Role.GUEST)

    def test_rejects_long_username(self, service: UserService):
        with pytest.raises(ValueError, match="Invalid user name"):
            service.create_user("a" * 51, VALID_HASH, Role.GUEST)

    def test_rejects_duplicate_username(self, service: UserService):
        service.create_user("yulia", VALID_HASH, Role.GUEST)
        with pytest.raises(ValueError, match="already exists"):
            service.create_user("Yulia", VALID_HASH, Role.GUEST)

    def test_rejects_short_hash(self, service: UserService):
        with pytest.raises(ValueError, match="Invalid password"):
            service.create_user("yulia", "short", Role.GUEST)

    def test_rejects_long_hash(self, service: UserService):
        with pytest.raises(ValueError, match="Invalid password"):
            service.create_user("yulia", "x" * 300, Role.GUEST)

    def test_rejects_non_role_value(self, service: UserService):
        with pytest.raises(ValueError, match="Invalid role"):
            service.create_user("yulia", VALID_HASH, "admin")  # type: ignore[arg-type]


class TestGetUserByUsername:
    def test_happy_path(self, service: UserService):
        created = service.create_user("yulia", VALID_HASH, Role.ADMIN)
        assert service.get_user_by_username("YULIA") is created

    def test_returns_none_when_missing(self, service: UserService):
        assert service.get_user_by_username("ghost") is None

    def test_rejects_invalid_username_length(self, service: UserService):
        with pytest.raises(ValueError, match="Invalid user name"):
            service.get_user_by_username("ab")


class TestGetUserById:
    def test_happy_path(self, service: UserService):
        created = service.create_user("yulia", VALID_HASH, Role.ADMIN)
        assert service.get_user_by_id(created.id) is created

    def test_returns_none_when_missing(self, service: UserService):
        assert service.get_user_by_id(999) is None

    def test_rejects_non_positive_id(self, service: UserService):
        with pytest.raises(ValueError, match="Invalid user id"):
            service.get_user_by_id(0)


def test_get_all_users_returns_every_row(service: UserService):
    service.create_user("yulia", VALID_HASH, Role.ADMIN)
    service.create_user("maria", VALID_HASH, Role.GUEST)
    assert len(service.get_all_users()) == 2
