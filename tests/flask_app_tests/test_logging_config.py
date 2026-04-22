"""Unit tests for :mod:`flask_app.logging_config`.

These tests mutate process-wide logging state, so each test must:
- redirect ``LOG_DIR`` / ``CSV_LOG_FILE`` to a temp directory,
- reset the module's one-time ``_configured`` guard,
- restore the ``csv_loader`` logger's original handlers on teardown.
"""

import logging
from pathlib import Path

import pytest

from flask_app import logging_config


@pytest.fixture()
def isolated_logging(tmp_path: Path, monkeypatch):
    """Redirect logging output to ``tmp_path`` and restore state after the test."""
    log_dir = tmp_path / "logs"
    log_file = log_dir / "csvInitialLoader_errors.log"

    monkeypatch.setattr(logging_config, "LOG_DIR", log_dir)
    monkeypatch.setattr(logging_config, "CSV_LOG_FILE", log_file)
    monkeypatch.setattr(logging_config, "_configured", False)

    csv_logger = logging.getLogger("csv_loader")
    original_handlers = list(csv_logger.handlers)
    original_level = csv_logger.level
    original_propagate = csv_logger.propagate

    yield log_dir, log_file

    for handler in list(csv_logger.handlers):
        csv_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass
    for handler in original_handlers:
        csv_logger.addHandler(handler)
    csv_logger.setLevel(original_level)
    csv_logger.propagate = original_propagate


class TestConfigureLogging:
    def test_creates_log_directory(self, isolated_logging):
        log_dir, _ = isolated_logging
        assert not log_dir.exists()

        logging_config.configure_logging()

        assert log_dir.is_dir()

    def test_attaches_file_handler_to_csv_loader(self, isolated_logging):
        _, log_file = isolated_logging

        logging_config.configure_logging()

        csv_logger = logging.getLogger("csv_loader")
        file_handlers = [
            h for h in csv_logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert Path(file_handlers[0].baseFilename) == log_file.resolve()

    def test_logger_level_and_propagation(self, isolated_logging):
        logging_config.configure_logging()

        csv_logger = logging.getLogger("csv_loader")
        assert csv_logger.level == logging.WARNING
        assert csv_logger.propagate is False

    def test_warning_writes_to_file(self, isolated_logging):
        _, log_file = isolated_logging
        logging_config.configure_logging()

        csv_logger = logging.getLogger("csv_loader")
        csv_logger.warning("sample-message")

        for handler in csv_logger.handlers:
            handler.flush()

        assert log_file.exists()
        contents = log_file.read_text(encoding="utf-8")
        assert "sample-message" in contents
        assert "[WARNING]" in contents

    def test_one_time_guard_prevents_duplicate_handlers(self, isolated_logging):
        logging_config.configure_logging()
        logging_config.configure_logging()
        logging_config.configure_logging()

        csv_logger = logging.getLogger("csv_loader")
        file_handlers = [
            h for h in csv_logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert logging_config._configured is True

    def test_guard_sets_flag_only_after_success(self, isolated_logging):
        assert logging_config._configured is False
        logging_config.configure_logging()
        assert logging_config._configured is True
