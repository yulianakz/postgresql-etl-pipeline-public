"""Shared fixtures for the Flask-app test suite.

Sets JWT env before importing the Flask app and exposes:
- ``app`` / ``client`` fixtures backed by a real Flask test client,
- ``mock_services`` that replaces every view's service with a ``MagicMock`` so
  API tests stay isolated from the DB,
- ``admin_headers`` / ``guest_headers`` that return valid JWTs for each role.
"""

import os
from typing import Iterator
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")

from flask import Flask
from flask_jwt_extended import create_access_token

from flask_app.app import create_app
from flask_app.api.routes.baby_api import BabyListRequests, BabyByIdRequests
from flask_app.api.routes.sleep_api import BabySleepListRequests, SleepListRequests
from flask_app.api.routes.diaper_api import BabyDiaperListRequests, DiaperListRequests
from flask_app.api.routes.auth_api import Login, Register, Refresh
from flask_app.domain.entities.user import Role


@pytest.fixture(scope="session")
def app() -> Flask:
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


@pytest.fixture()
def mock_services() -> Iterator[dict[str, MagicMock]]:
    """Replace every view's service with a MagicMock for the duration of a test."""
    originals = {
        "baby_list": BabyListRequests.baby_service,
        "baby_by_id": BabyByIdRequests.baby_service,
        "sleep_list": SleepListRequests.sleep_service,
        "baby_sleep_list": BabySleepListRequests.sleep_service,
        "diaper_list": DiaperListRequests.diaper_service,
        "baby_diaper_list": BabyDiaperListRequests.diaper_service,
        "login": Login.auth_service,
        "register": Register.auth_service,
        "refresh": Refresh.auth_service,
    }

    baby_service = MagicMock(name="BabyService")
    sleep_service = MagicMock(name="SleepService")
    diaper_service = MagicMock(name="DiaperService")
    auth_service = MagicMock(name="AuthService")

    BabyListRequests.baby_service = baby_service
    BabyByIdRequests.baby_service = baby_service
    SleepListRequests.sleep_service = sleep_service
    BabySleepListRequests.sleep_service = sleep_service
    DiaperListRequests.diaper_service = diaper_service
    BabyDiaperListRequests.diaper_service = diaper_service
    Login.auth_service = auth_service
    Register.auth_service = auth_service
    Refresh.auth_service = auth_service

    yield {
        "baby": baby_service,
        "sleep": sleep_service,
        "diaper": diaper_service,
        "auth": auth_service,
    }

    BabyListRequests.baby_service = originals["baby_list"]
    BabyByIdRequests.baby_service = originals["baby_by_id"]
    SleepListRequests.sleep_service = originals["sleep_list"]
    BabySleepListRequests.sleep_service = originals["baby_sleep_list"]
    DiaperListRequests.diaper_service = originals["diaper_list"]
    BabyDiaperListRequests.diaper_service = originals["baby_diaper_list"]
    Login.auth_service = originals["login"]
    Register.auth_service = originals["register"]
    Refresh.auth_service = originals["refresh"]


def _auth_header(app: Flask, role: Role) -> dict[str, str]:
    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": role.value},
        )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(app: Flask) -> dict[str, str]:
    return _auth_header(app, Role.ADMIN)


@pytest.fixture()
def guest_headers(app: Flask) -> dict[str, str]:
    return _auth_header(app, Role.GUEST)
