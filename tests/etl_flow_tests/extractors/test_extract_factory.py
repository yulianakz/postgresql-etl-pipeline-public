"""Unit tests for :class:`etl.extract.extract_factory.extract_factory.ExtractorFactory`."""

import pytest

from etl.extract.extractors.api_extractor import ApiExtractor
from etl.extract.extractors.csv_extractor import CsvExtractor
from etl.extract.extractors.db_extractor import DbExtractor
from etl.extract.extract_factory.extract_factory import ExtractorFactory


def _mapper(row):
    return row


class _FakeAuth:
    @property
    def headers(self):
        return {}


class _FakeEngine:  # not actually connected anywhere in these constructor tests
    pass


class TestExtractorFactory:
    def test_builds_csv_extractor(self):
        extractor = ExtractorFactory().get_extractor(
            "csv", file_path="x.csv", mapper=_mapper
        )
        assert isinstance(extractor, CsvExtractor)

    def test_builds_db_extractor(self):
        extractor = ExtractorFactory().get_extractor(
            "db", engine=_FakeEngine(), raw_sql="SELECT 1", mapper=_mapper
        )
        assert isinstance(extractor, DbExtractor)

    def test_builds_api_extractor(self):
        extractor = ExtractorFactory().get_extractor(
            "api",
            base_url="https://host/",
            endpoint="x",
            auth_client=_FakeAuth(),
            mapper=_mapper,
        )
        assert isinstance(extractor, ApiExtractor)

    def test_case_insensitive(self):
        extractor = ExtractorFactory().get_extractor(
            "CSV", file_path="x.csv", mapper=_mapper
        )
        assert isinstance(extractor, CsvExtractor)

    def test_unknown_source_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported source type"):
            ExtractorFactory().get_extractor("parquet", file_path="x.parquet")
