from etl.extract.abstract_models.entity_interface import BaseEntity

from dataclasses import dataclass
from datetime import datetime

import hashlib

@dataclass
class BabyDataEntity(BaseEntity):
    source_id: int | None = None
    name: str | None = None
    timezone: str | None = None
    job_id: int | None = None
    loaded_at: datetime | None = None

@dataclass
class DiaperDataEntity(BaseEntity):
    source_id: int | None = None
    change_time: datetime | None = None
    status: str | None = None
    baby_id: int | None = None
    job_id: int | None = None
    loaded_at: datetime | None = None

@dataclass
class SleepDataEntity(BaseEntity):
    source_id: int | None = None
    sleep_start: datetime | None = None
    sleep_duration: int | None = None
    baby_id: int | None = None
    job_id: int | None = None
    loaded_at: datetime | None = None

@dataclass
class FormulaDataEntity(BaseEntity):
    source_id: str | None = None
    feed_time: datetime | None = None
    amount_ml: int | None = None
    baby_id: int | None = None
    job_id: int | None = None
    loaded_at: datetime | None = None

    def __post_init__(self):
        if self.baby_id is None:
            self.baby_id = 1
        if self.source_id is None:
            self.source_id = self._create_source_id()
        super().__post_init__()

    def _create_source_id(self) -> str:
        feed_time_str = self.feed_time.isoformat() if self.feed_time else "None"
        baby_id_str = str(self.baby_id) if self.baby_id is not None else "None"
        raw = f"{feed_time_str}|{baby_id_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]




