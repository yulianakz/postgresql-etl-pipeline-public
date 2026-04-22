"""Unit tests for :mod:`etl.extract.domain.mappers.utils`."""

from datetime import datetime

import pytest

from etl.extract.domain.mappers.exceptions import MapperError
from etl.extract.domain.mappers.utils import _normalize, safe_datetime, safe_int, safe_str


class TestNormalize:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (None, None),
            ("", None),
            ("   ", None),
            ("hello", "hello"),
            ("  trimmed  ", "trimmed"),
            (42, "42"),
            (0, "0"),
        ],
    )
    def test_normalize(self, value, expected):
        assert _normalize(value) == expected


class TestSafeInt:
    def test_happy_path_from_str(self):
        assert safe_int("42") == 42

    def test_happy_path_from_int(self):
        assert safe_int(42) == 42

    def test_strips_whitespace(self):
        assert safe_int("  42  ") == 42

    def test_returns_none_for_none(self):
        assert safe_int(None) is None

    def test_returns_none_for_empty_string(self):
        assert safe_int("") is None
        assert safe_int("   ") is None

    def test_raises_mapper_error_on_invalid(self):
        with pytest.raises(MapperError) as exc_info:
            safe_int("not-an-int")
        assert exc_info.value.expected_type == "int"
        assert exc_info.value.value == "not-an-int"


class TestSafeDatetime:
    def test_pass_through_datetime(self):
        dt = datetime(2026, 1, 1, 8, 30)
        assert safe_datetime(dt) is dt

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("2026-01-01 08:30", datetime(2026, 1, 1, 8, 30)),
            ("2026-01-01 08:30:00", datetime(2026, 1, 1, 8, 30, 0)),
            ("2026-01-01T08:30", datetime(2026, 1, 1, 8, 30)),
            ("2026-01-01T08:30:00", datetime(2026, 1, 1, 8, 30, 0)),
            ("01.02.2026, 08:30", datetime(2026, 2, 1, 8, 30)),
            ("01.02.2026 08:30", datetime(2026, 2, 1, 8, 30)),
        ],
    )
    def test_parses_common_formats(self, raw, expected):
        assert safe_datetime(raw) == expected

    def test_custom_format_tried_first(self):
        assert safe_datetime("01.02.2026, 08:30", fmt="%d.%m.%Y, %H:%M") == datetime(
            2026, 2, 1, 8, 30
        )

    def test_returns_none_for_blank(self):
        assert safe_datetime(None) is None
        assert safe_datetime("") is None
        assert safe_datetime("   ") is None

    def test_raises_mapper_error_on_invalid(self):
        with pytest.raises(MapperError) as exc_info:
            safe_datetime("garbage-timestamp")
        assert exc_info.value.expected_type == "datetime"


class TestSafeStr:
    def test_happy_path(self):
        assert safe_str("hello") == "hello"

    def test_trims_whitespace(self):
        assert safe_str("  hello  ") == "hello"

    def test_blank_becomes_none(self):
        assert safe_str("") is None
        assert safe_str("   ") is None

    def test_none_stays_none(self):
        assert safe_str(None) is None

    def test_non_str_coerced(self):
        assert safe_str(42) == "42"
