"""Unit tests for :class:`etl.extract.services.auth_client.ApiAuthClient`."""

from types import SimpleNamespace

import pytest
import requests as real_requests

from etl.extract.services import auth_client as auth_client_module
from etl.extract.services.auth_client import ApiAuthClient
from etl.extract.services.exceptions import AuthError


def _fake_response(status_code: int, json_data: dict | None = None, raise_exc: Exception | None = None):
    def raise_for_status():
        if raise_exc:
            raise raise_exc

    return SimpleNamespace(
        status_code=status_code,
        json=lambda: json_data or {},
        raise_for_status=raise_for_status,
    )


class TestApiAuthClient:
    def test_login_happy_path_stores_token(self, monkeypatch):
        monkeypatch.setattr(
            auth_client_module.requests,
            "post",
            lambda *a, **kw: _fake_response(200, {"access_token": "tok"}),
        )

        client = ApiAuthClient("https://h", "u", "p")
        client.login()

        assert client.token == "tok"
        assert client.headers == {"Authorization": "Bearer tok"}

    def test_login_http_error_raises_auth_error(self, monkeypatch):
        err = real_requests.HTTPError("401")
        monkeypatch.setattr(
            auth_client_module.requests,
            "post",
            lambda *a, **kw: _fake_response(401, raise_exc=err),
        )

        client = ApiAuthClient("https://h", "u", "p")
        with pytest.raises(AuthError) as exc_info:
            client.login()
        assert exc_info.value.status_code == 401
        assert client.token is None

    def test_login_missing_token_key_raises_auth_error(self, monkeypatch):
        monkeypatch.setattr(
            auth_client_module.requests,
            "post",
            lambda *a, **kw: _fake_response(200, {"nothing": "here"}),
        )

        client = ApiAuthClient("https://h", "u", "p")
        with pytest.raises(AuthError):
            client.login()

    def test_headers_raises_when_token_missing(self):
        client = ApiAuthClient("https://h", "u", "p")
        with pytest.raises(AuthError):
            _ = client.headers


def test_auth_error_message_includes_context():
    err = AuthError(url="https://h", status_code=401, original_error=Exception("boom"))
    msg = str(err)
    assert "https://h" in msg
    assert "401" in msg
    assert "boom" in msg
