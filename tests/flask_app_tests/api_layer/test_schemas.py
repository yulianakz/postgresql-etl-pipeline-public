"""Schema-level validation tests for every Flask-app input schema.

Covers:
- happy path loads that return the dataclass instance,
- rejection of unknown/missing fields,
- rejection of wrong data types.

Some marshmallow-dataclass versions raise a ``TypeError`` from the
generated ``__init__`` rather than a ``marshmallow.ValidationError`` when
required fields are missing, so ``_assert_invalid_payload`` accepts both.
"""

import pytest
from marshmallow import ValidationError

from flask_app.api.schemas.auth_schema import LoginInputSchema, RegisterInputSchema
from flask_app.api.schemas.baby_schema import BabyInputSchema
from flask_app.api.schemas.diaper_schema import DiaperInputSchema
from flask_app.api.schemas.sleep_schema import SleepInputSchema


def _assert_invalid_payload(schema, payload):
    with pytest.raises((ValidationError, TypeError)):
        schema.load(payload)


class TestRegisterSchema:
    def test_happy_path(self):
        schema = RegisterInputSchema()
        data = schema.load({"user_name": "yulia", "password": "secret-pass"})
        assert data.user_name == "yulia"
        assert data.password == "secret-pass"

    def test_rejects_unknown_role_field(self):
        schema = RegisterInputSchema()
        with pytest.raises(ValidationError):
            schema.load(
                {"user_name": "yulia", "password": "secret-pass", "role": "admin"}
            )

    def test_requires_user_name(self):
        _assert_invalid_payload(RegisterInputSchema(), {"password": "secret"})

    def test_requires_password(self):
        _assert_invalid_payload(RegisterInputSchema(), {"user_name": "yulia"})


class TestLoginSchema:
    def test_happy_path(self):
        data = LoginInputSchema().load({"user_name": "yulia", "password": "pw"})
        assert data.user_name == "yulia"
        assert data.password == "pw"

    def test_rejects_unknown_field(self):
        with pytest.raises(ValidationError):
            LoginInputSchema().load(
                {"user_name": "yulia", "password": "pw", "extra": "x"}
            )

    def test_requires_password(self):
        _assert_invalid_payload(LoginInputSchema(), {"user_name": "yulia"})


class TestBabyInputSchema:
    def test_happy_path(self):
        data = BabyInputSchema().load({"name": "Adriana", "timezone": "UTC"})
        assert data.name == "Adriana"
        assert data.timezone == "UTC"

    def test_requires_name(self):
        _assert_invalid_payload(BabyInputSchema(), {"timezone": "UTC"})

    def test_requires_timezone(self):
        _assert_invalid_payload(BabyInputSchema(), {"name": "Adriana"})


class TestSleepInputSchema:
    def test_happy_path(self):
        data = SleepInputSchema().load(
            {"sleep_start": "2026-01-01T10:00:00+00:00", "sleep_duration": 60}
        )
        assert data.sleep_duration == 60
        assert data.sleep_start.year == 2026

    def test_rejects_wrong_duration_type(self):
        with pytest.raises(ValidationError):
            SleepInputSchema().load(
                {"sleep_start": "2026-01-01T10:00:00+00:00", "sleep_duration": "sixty"}
            )

    def test_rejects_malformed_datetime(self):
        with pytest.raises(ValidationError):
            SleepInputSchema().load(
                {"sleep_start": "not-a-date", "sleep_duration": 30}
            )

    def test_requires_sleep_duration(self):
        _assert_invalid_payload(
            SleepInputSchema(), {"sleep_start": "2026-01-01T10:00:00+00:00"}
        )


class TestDiaperInputSchema:
    def test_happy_path(self):
        data = DiaperInputSchema().load(
            {"change_time": "2026-01-01T10:00:00+00:00", "status": "wet"}
        )
        assert data.status == "wet"

    def test_rejects_wrong_status_type(self):
        with pytest.raises(ValidationError):
            DiaperInputSchema().load(
                {"change_time": "2026-01-01T10:00:00+00:00", "status": 123}
            )

    def test_requires_change_time(self):
        _assert_invalid_payload(DiaperInputSchema(), {"status": "wet"})
