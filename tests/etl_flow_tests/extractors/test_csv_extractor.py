"""Unit tests for :class:`etl.extract.extractors.csv_extractor.CsvExtractor`."""

from pathlib import Path

import pytest

from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity
from etl.extract.extractors.csv_extractor import CsvExtractor


def _write_csv(tmp_path: Path, contents: str) -> str:
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(contents, encoding="utf-8-sig")
    return str(csv_path)


def _passthrough(row: dict) -> dict:
    return {"row": dict(row)}


_passthrough.__name__ = "passthrough"


def _fail_on_id_zero(row: dict) -> dict:
    if row.get("id") == "0":
        raise ValueError("bad row")
    return {"row": dict(row)}


_fail_on_id_zero.__name__ = "fail_on_id_zero"


class TestCsvExtractor:
    def test_happy_path_yields_mapped_rows(self, tmp_path: Path):
        file_path = _write_csv(tmp_path, "id,name\n1,Adi\n2,Maria\n")
        extractor = CsvExtractor(file_path=file_path, mapper=_passthrough)

        rows = list(extractor.extract())

        assert rows == [
            {"row": {"id": "1", "name": "Adi"}},
            {"row": {"id": "2", "name": "Maria"}},
        ]

    def test_empty_csv_yields_nothing(self, tmp_path: Path):
        file_path = _write_csv(tmp_path, "id,name\n")
        extractor = CsvExtractor(file_path=file_path, mapper=_passthrough)
        assert list(extractor.extract()) == []

    def test_broken_row_wrapped_in_broken_entity(self, tmp_path: Path):
        file_path = _write_csv(tmp_path, "id,name\n0,bad\n1,good\n")
        extractor = CsvExtractor(file_path=file_path, mapper=_fail_on_id_zero)

        rows = list(extractor.extract())

        assert len(rows) == 2
        assert isinstance(rows[0], BrokenEntity)
        assert rows[0].raw_row == {"id": "0", "name": "bad"}
        assert rows[0].error_message == "bad row"
        assert rows[0].mapper_name == "fail_on_id_zero"
        assert rows[1] == {"row": {"id": "1", "name": "good"}}

    def test_missing_file_raises_file_not_found(self):
        extractor = CsvExtractor(file_path="does-not-exist.csv", mapper=_passthrough)
        with pytest.raises(FileNotFoundError):
            list(extractor.extract())

    def test_utf8_bom_is_stripped(self, tmp_path: Path):
        csv_path = tmp_path / "bom.csv"
        csv_path.write_text("\ufeffid,name\n1,Adi\n", encoding="utf-8")
        extractor = CsvExtractor(file_path=str(csv_path), mapper=_passthrough)
        rows = list(extractor.extract())
        assert rows == [{"row": {"id": "1", "name": "Adi"}}]
