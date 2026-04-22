"""Unit tests for :class:`etl.extract.domain.mappers.exceptions.MapperError`."""

from etl.extract.domain.mappers.exceptions import MapperError


def test_mapper_error_stores_all_fields():
    original = ValueError("bad")
    err = MapperError(value="abc", expected_type="int", original_error=original)
    assert err.value == "abc"
    assert err.expected_type == "int"
    assert err.original_error is original
    assert err.row is None


def test_mapper_error_message_includes_context():
    err = MapperError(value="abc", expected_type="int", original_error=ValueError("bad"))
    msg = str(err)
    assert "'abc'" in msg
    assert "int" in msg
    assert "bad" in msg


def test_mapper_error_accepts_row():
    err = MapperError(
        value=None,
        expected_type="datetime",
        original_error=ValueError(),
        row={"id": 1},
    )
    assert err.row == {"id": 1}
