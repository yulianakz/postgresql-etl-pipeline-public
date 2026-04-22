import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class BrokenEntity:
    raw_row: dict[str, Any]
    error_message: str
    mapper_name: Optional[str] = None

LOG_DIR = Path("etl") / "logs"
LOG_FILE = LOG_DIR/'mapper_broken_rows.log'

def log_bad_row(row: dict, error_message: str, job_id: int | None = None, mapper_name: str | None = None):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "job_id": job_id,
        "mapper": mapper_name,
        "error_message": error_message,
        "row": row,
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")