"""Reusable fake SQLAlchemy engine for ETL repository tests."""

from contextlib import contextmanager
from typing import Any


class FakeResult:
    def __init__(
        self,
        scalar: Any = None,
        scalar_one: Any = None,
        scalar_one_or_none: Any = None,
        rowcount: int = 0,
    ):
        self._scalar = scalar
        self._scalar_one = scalar_one
        self._scalar_one_or_none = scalar_one_or_none
        self.rowcount = rowcount

    def scalar(self):
        return self._scalar

    def scalar_one(self):
        return self._scalar_one

    def scalar_one_or_none(self):
        return self._scalar_one_or_none


class FakeConnection:
    def __init__(self, results: list[FakeResult] | None = None):
        self._results = list(results or [])
        self.executed: list[tuple[Any, dict | None]] = []

    def execute(self, stmt, params=None):
        self.executed.append((stmt, params))
        if self._results:
            return self._results.pop(0)
        return FakeResult()


class FakeEngine:
    def __init__(self, connections: list[FakeConnection] | None = None):
        self._connections = list(connections or [])
        self.used: list[FakeConnection] = []

    def _next(self) -> FakeConnection:
        conn = self._connections.pop(0) if self._connections else FakeConnection()
        self.used.append(conn)
        return conn

    @contextmanager
    def begin(self):
        yield self._next()

    @contextmanager
    def connect(self):
        yield self._next()
