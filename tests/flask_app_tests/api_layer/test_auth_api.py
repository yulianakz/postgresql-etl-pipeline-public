"""HTTP-level tests for the /auth blueprint."""

from flask_app.domain.entities.user import Role, User


def _user() -> User:
    return User(
        user_id=1,
        user_name="yulia",
        password_hash="x" * 60,
        role=Role.ADMIN,
        created_at=None,
    )


class TestRegister:
    def test_happy_path_returns_201(self, client, mock_services):
        mock_services["auth"].register.return_value = _user()

        resp = client.post(
            "/auth/register",
            json={"user_name": "yulia", "password": "plain-text"},
        )

        assert resp.status_code == 201
        assert resp.get_json()["user_name"] == "yulia"
        mock_services["auth"].register.assert_called_once()

    def test_value_error_returns_400(self, client, mock_services):
        mock_services["auth"].register.side_effect = ValueError("Username taken")

        resp = client.post(
            "/auth/register",
            json={"user_name": "yulia", "password": "plain-text"},
        )

        assert resp.status_code == 400
        assert "Username taken" in resp.get_json()["message"]

    def test_unknown_field_returns_422(self, client, mock_services):
        resp = client.post(
            "/auth/register",
            json={"user_name": "yulia", "password": "x", "role": "admin"},
        )
        assert resp.status_code == 422
        mock_services["auth"].register.assert_not_called()


class TestLogin:
    def test_happy_path_returns_tokens(self, client, mock_services):
        mock_services["auth"].login.return_value = {
            "access_token": "a", "refresh_token": "r"
        }

        resp = client.post(
            "/auth/login",
            json={"user_name": "yulia", "password": "plain"},
        )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body == {"access_token": "a", "refresh_token": "r"}

    def test_wrong_password_returns_400(self, client, mock_services):
        mock_services["auth"].login.side_effect = ValueError("Incorrect password")

        resp = client.post(
            "/auth/login",
            json={"user_name": "yulia", "password": "plain"},
        )

        assert resp.status_code == 400
        assert resp.get_json()["message"] == "Incorrect password"

    def test_unknown_field_returns_422(self, client, mock_services):
        resp = client.post(
            "/auth/login",
            json={"user_name": "yulia", "password": "pw", "extra": 1},
        )
        assert resp.status_code == 422
        mock_services["auth"].login.assert_not_called()


class TestRefresh:
    def test_requires_refresh_jwt(self, client, mock_services):
        resp = client.post("/auth/refresh")
        assert resp.status_code == 401
        mock_services["auth"].refresh_access_token.assert_not_called()

    def test_rejects_access_token_as_refresh(self, client, admin_headers, mock_services):
        resp = client.post("/auth/refresh", headers=admin_headers)
        assert resp.status_code == 422
        mock_services["auth"].refresh_access_token.assert_not_called()

    def test_happy_path_with_refresh_token(self, client, app, mock_services):
        from flask_jwt_extended import create_refresh_token

        mock_services["auth"].refresh_access_token.return_value = {
            "access_token": "new-access"
        }

        with app.app_context():
            refresh = create_refresh_token(
                identity="1", additional_claims={"role": "admin"}
            )

        resp = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh}"},
        )

        assert resp.status_code == 200
        assert resp.get_json() == {"access_token": "new-access"}
