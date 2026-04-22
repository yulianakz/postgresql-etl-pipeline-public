"""Unit tests for :class:`etl.extract.extractors.api_extractor.ApiExtractor`.

These tests monkeypatch both ``requests.get`` (so no real HTTP traffic is
made) and ``ijson.items`` (so the fake response stream can be iterated
without parsing actual bytes).
"""

from types import SimpleNamespace

import pytest

from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity
from etl.extract.extractors import api_extractor
from etl.extract.extractors.api_extractor import ApiExtractor


class _FakeAuth:
    def __init__(self):
        self.headers = {"Authorization": "Bearer abc"}


def _fake_response(raise_exc: Exception | None = None):
    raw = object()
    def raise_for_status():
        if raise_exc:
            raise raise_exc
    return SimpleNamespace(raw=raw, raise_for_status=raise_for_status)


def _identity(row):
    return dict(row)


_identity.__name__ = "identity"


class TestApiExtractor:
    def test_happy_path(self, monkeypatch):
        captured = {}

        def fake_get(url, headers, params, stream):
            captured["url"] = url
            captured["headers"] = headers
            captured["params"] = params
            captured["stream"] = stream
            return _fake_response()

        monkeypatch.setattr(api_extractor.requests, "get", fake_get)
        monkeypatch.setattr(
            api_extractor.ijson,
            "items",
            lambda _raw, _pattern: iter([{"id": 1}, {"id": 2}]),
        )

        extractor = ApiExtractor(
            base_url="https://host/",
            endpoint="baby/1/diaper",
            auth_client=_FakeAuth(),
            mapper=_identity,
            params={"x": 1},
            headers={"X-Test": "y"},
        )

        rows = list(extractor.extract())

        assert rows == [{"id": 1}, {"id": 2}]
        assert captured["url"] == "https://host/baby/1/diaper"
        assert captured["headers"] == {"Authorization": "Bearer abc", "X-Test": "y"}
        assert captured["params"] == {"x": 1}
        assert captured["stream"] is True

    def test_raises_for_http_error(self, monkeypatch):
        class Boom(Exception):
            pass

        monkeypatch.setattr(
            api_extractor.requests,
            "get",
            lambda *a, **kw: _fake_response(raise_exc=Boom("404")),
        )
        monkeypatch.setattr(api_extractor.ijson, "items", lambda *a, **kw: iter([]))

        extractor = ApiExtractor(
            base_url="https://host/",
            endpoint="x",
            auth_client=_FakeAuth(),
            mapper=_identity,
        )

        with pytest.raises(Boom):
            list(extractor.extract())

    def test_broken_row_wrapped(self, monkeypatch):
        monkeypatch.setattr(
            api_extractor.requests,
            "get",
            lambda *a, **kw: _fake_response(),
        )
        monkeypatch.setattr(
            api_extractor.ijson,
            "items",
            lambda *a, **kw: iter([{"id": 1}, {"id": 2}]),
        )

        def bad_mapper(row):
            if row["id"] == 2:
                raise ValueError("bad")
            return dict(row)

        bad_mapper.__name__ = "bad_mapper"

        extractor = ApiExtractor(
            base_url="https://host/",
            endpoint="x",
            auth_client=_FakeAuth(),
            mapper=bad_mapper,
        )

        rows = list(extractor.extract())
        assert rows[0] == {"id": 1}
        assert isinstance(rows[1], BrokenEntity)
        assert rows[1].mapper_name == "bad_mapper"
