"""Unit tests for the broken-rows JSON logger."""

import json
from pathlib import Path

import pytest

from etl.extract.domain.mappers import broken_rows_logger
from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity, log_bad_row


def test_broken_entity_dataclass_defaults():
    broken = BrokenEntity(raw_row={"id": 1}, error_message="boom")
    assert broken.raw_row == {"id": 1}
    assert broken.error_message == "boom"
    assert broken.mapper_name is None


def test_log_bad_row_writes_json_line(monkeypatch, tmp_path: Path):
    log_dir = tmp_path / "logs"
    monkeypatch.setattr(broken_rows_logger, "LOG_DIR", log_dir)
    monkeypatch.setattr(broken_rows_logger, "LOG_FILE", log_dir / "mapper.log")

    log_bad_row(
        row={"id": 1, "name": "Adi"},
        error_message="boom",
        job_id=42,
        mapper_name="api_baby_mapper",
    )

    log_file = log_dir / "mapper.log"
    assert log_file.exists()
    written = log_file.read_text(encoding="utf-8").splitlines()
    assert len(written) == 1

    parsed = json.loads(written[0])
    assert parsed["job_id"] == 42
    assert parsed["mapper"] == "api_baby_mapper"
    assert parsed["error_message"] == "boom"
    assert parsed["row"] == {"id": 1, "name": "Adi"}
    assert "timestamp" in parsed


def test_log_bad_row_appends_multiple_lines(monkeypatch, tmp_path: Path):
    log_dir = tmp_path / "logs"
    monkeypatch.setattr(broken_rows_logger, "LOG_DIR", log_dir)
    monkeypatch.setattr(broken_rows_logger, "LOG_FILE", log_dir / "mapper.log")

    log_bad_row(row={"a": 1}, error_message="err1")
    log_bad_row(row={"b": 2}, error_message="err2")

    lines = (log_dir / "mapper.log").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
