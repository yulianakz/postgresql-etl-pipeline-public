from pathlib import Path
import logging.config


FLASK_APP_DIR = Path(__file__).resolve().parent
LOG_DIR = FLASK_APP_DIR / "logs"
CSV_LOG_FILE = LOG_DIR / "csvInitialLoader_errors.log"

_configured = False


def configure_logging() -> None:
    global _configured
    if _configured:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": "%(asctime)s [%(levelname)s] %(message)s"}
            },
            "handlers": {
                "csv_file": {
                    "class": "logging.FileHandler",
                    "filename": str(CSV_LOG_FILE),
                    "formatter": "default",
                    "encoding": "utf-8",
                }
            },
            "loggers": {
                "csv_loader": {
                    "level": "WARNING",
                    "handlers": ["csv_file"],
                    "propagate": False,
                }
            },
        }
    )

    _configured = True
