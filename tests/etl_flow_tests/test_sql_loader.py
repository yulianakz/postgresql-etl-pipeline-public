"""Unit tests for :func:`etl.sql.sql_loader.load_sql`."""

from pathlib import Path

import pytest

from etl.sql.sql_loader import load_sql


def test_loads_existing_sql_file():
    content = load_sql("core/initial/dimensions/dim_baby_initial.sql")
    assert isinstance(content, str)
    assert content.strip() != ""


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_sql("does/not/exist.sql")
