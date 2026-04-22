"""Unit tests for :class:`etl.extract.extractors.db_extractor.DbExtractor`."""

from contextlib import contextmanager

from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity
from etl.extract.extractors.db_extractor import DbExtractor


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return iter(self._rows)


class _FakeConnection:
    def __init__(self, rows):
        self._rows = rows
        self.executed = None
        self.params = None

    def execution_options(self, **_kwargs):
        return self

    def execute(self, stmt, params):
        self.executed = stmt
        self.params = params
        return _FakeResult(self._rows)


class _FakeEngine:
    def __init__(self, rows):
        self._rows = rows
        self.last_connection: _FakeConnection | None = None

    @contextmanager
    def connect(self):
        self.last_connection = _FakeConnection(self._rows)
        yield self.last_connection


def _identity(row):
    return dict(row)


_identity.__name__ = "identity"


def _raise_on_two(row):
    if row["id"] == 2:
        raise ValueError("bad 2")
    return dict(row)


_raise_on_two.__name__ = "raise_on_two"


class TestDbExtractor:
    def test_happy_path_yields_all_rows(self):
        engine = _FakeEngine(rows=[{"id": 1}, {"id": 2}, {"id": 3}])
        extractor = DbExtractor(
            engine=engine, raw_sql="SELECT 1", mapper=_identity, params={"a": 1}
        )

        rows = list(extractor.extract())
        assert rows == [{"id": 1}, {"id": 2}, {"id": 3}]
        assert engine.last_connection.params == {"a": 1}

    def test_defaults_params_to_empty_dict(self):
        engine = _FakeEngine(rows=[{"id": 1}])
        extractor = DbExtractor(engine=engine, raw_sql="SELECT 1", mapper=_identity)
        list(extractor.extract())
        assert engine.last_connection.params == {}

    def test_broken_row_wrapped_in_broken_entity(self):
        engine = _FakeEngine(rows=[{"id": 1}, {"id": 2}, {"id": 3}])
        extractor = DbExtractor(engine=engine, raw_sql="SELECT 1", mapper=_raise_on_two)

        rows = list(extractor.extract())

        assert rows[0] == {"id": 1}
        assert isinstance(rows[1], BrokenEntity)
        assert rows[1].raw_row == {"id": 2}
        assert rows[1].mapper_name == "raise_on_two"
        assert rows[2] == {"id": 3}

    def test_empty_result_yields_nothing(self):
        engine = _FakeEngine(rows=[])
        extractor = DbExtractor(engine=engine, raw_sql="SELECT 1", mapper=_identity)
        assert list(extractor.extract()) == []
