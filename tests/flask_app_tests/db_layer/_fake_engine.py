"""Minimal SQLAlchemy ``Engine``/``Connection`` stand-ins for unit testing.

These fakes let repository tests exercise mapping logic (statement
construction + ``_to_entity`` conversion) without spinning up Postgres.
"""

from contextlib import contextmanager


class FakeExecResult:
    def __init__(
        self,
        one_value: dict | None = None,
        all_values: list[dict] | None = None,
        one_or_none_value: dict | None = None,
    ):
        self._one_value = one_value
        self._all_values = all_values or []
        self._one_or_none_value = one_or_none_value

    def mappings(self):
        return self

    def one(self):
        if self._one_value is None:
            raise AssertionError(".one() called but no row configured")
        return self._one_value

    def all(self):
        return self._all_values

    def one_or_none(self):
        return self._one_or_none_value


class FakeConnection:
    def __init__(self, result: FakeExecResult):
        self._result = result
        self.executed_stmt = None

    def execute(self, stmt):
        self.executed_stmt = stmt
        return self._result


class FakeEngine:
    """Yields the same connection regardless of ``begin()`` / ``connect()``."""

    def __init__(self, connection: FakeConnection):
        self._connection = connection

    @contextmanager
    def begin(self):
        yield self._connection

    @contextmanager
    def connect(self):
        yield self._connection

    @property
    def connection(self) -> FakeConnection:
        return self._connection
