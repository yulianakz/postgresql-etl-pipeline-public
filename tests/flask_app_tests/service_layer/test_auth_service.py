"""Service-layer tests for :class:`AuthService`.

The JWT creation helpers need a Flask application context, so tests that
exercise ``login`` or ``refresh_access_token`` rely on the shared ``app``
fixture provided by ``conftest.py``.
"""

from unittest.mock import MagicMock

import pytest
from flask_jwt_extended import create_refresh_token, decode_token

from flask_app.application.services.auth_service import AuthService
from flask_app.domain.entities.user import Role, User


def _make_user(user_id: int = 1, password: str = "secret") -> User:
    return User(
        user_id=user_id,
        user_name="yulia",
        password_hash=AuthService._hash_password(password),
        role=Role.ADMIN,
        created_at=None,
    )


class TestRegister:
    def test_delegates_to_user_service_with_hashed_password(self):
        user_service = MagicMock()
        user_service.create_user.return_value = "created"

        auth_service = AuthService(user_service)
        result = auth_service.register("yulia", "plain-text", Role.GUEST)

        assert result == "created"
        user_service.create_user.assert_called_once()
        kwargs = user_service.create_user.call_args.kwargs
        assert kwargs["user_name"] == "yulia"
        assert kwargs["role"] == Role.GUEST
        assert kwargs["password_hash"] != "plain-text"
        assert AuthService._verify_password("plain-text", kwargs["password_hash"])

    def test_bubbles_up_user_service_errors(self):
        user_service = MagicMock()
        user_service.create_user.side_effect = ValueError("boom")

        auth_service = AuthService(user_service)
        with pytest.raises(ValueError, match="boom"):
            auth_service.register("yulia", "plain", Role.GUEST)


class TestLogin:
    def test_happy_path_returns_access_and_refresh_tokens(self, app):
        user = _make_user(password="correct-horse")
        user_service = MagicMock()
        user_service.get_user_by_username.return_value = user

        auth_service = AuthService(user_service)
        with app.app_context():
            tokens = auth_service.login("yulia", "correct-horse")

        assert set(tokens.keys()) == {"access_token", "refresh_token"}
        with app.app_context():
            decoded = decode_token(tokens["access_token"])
        assert decoded["sub"] == "1"
        assert decoded["role"] == "admin"

    def test_unknown_user_raises_value_error(self, app):
        user_service = MagicMock()
        user_service.get_user_by_username.return_value = None

        auth_service = AuthService(user_service)
        with app.app_context():
            with pytest.raises(ValueError, match="does not exist"):
                auth_service.login("ghost", "whatever")

    def test_wrong_password_raises_value_error(self, app):
        user = _make_user(password="right")
        user_service = MagicMock()
        user_service.get_user_by_username.return_value = user

        auth_service = AuthService(user_service)
        with app.app_context():
            with pytest.raises(ValueError, match="Incorrect password"):
                auth_service.login("yulia", "wrong")


class TestRefreshAccessToken:
    def test_refresh_returns_new_access_token(self, app, client):
        auth_service = AuthService(MagicMock())

        with app.app_context():
            refresh = create_refresh_token(
                identity="42",
                additional_claims={"role": "admin"},
            )

        with app.test_request_context(
            headers={"Authorization": f"Bearer {refresh}"},
        ):
            from flask_jwt_extended import verify_jwt_in_request

            verify_jwt_in_request(refresh=True)
            result = auth_service.refresh_access_token()

        assert "access_token" in result
        with app.app_context():
            decoded = decode_token(result["access_token"])
        assert decoded["sub"] == "42"
        assert decoded["role"] == "admin"


def test_password_hash_and_verify_round_trip():
    hashed = AuthService._hash_password("s3cret!")
    assert AuthService._verify_password("s3cret!", hashed)
    assert not AuthService._verify_password("other", hashed)
