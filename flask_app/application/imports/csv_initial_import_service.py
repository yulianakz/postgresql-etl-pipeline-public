from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import logging

from flask_app.application.imports.csv_reader_service import CsvReader
from flask_app.application.services.baby_service import BabyService
from flask_app.application.services.diaper_service import DiaperService
from flask_app.application.services.sleep_service import SleepService

logger = logging.getLogger("csv_loader")

MOLDOVA_TZ = ZoneInfo("Europe/Chisinau")

class CsvInitialImportService:

    def __init__(self, baby_service: BabyService, sleep_service: SleepService, diaper_service: DiaperService):
        self.baby_service = baby_service
        self.sleep_service = sleep_service
        self.diaper_service = diaper_service
        self.baby_id: int | None = None

    @staticmethod
    def _map_sleep_row(row: dict) -> dict:
        try:
            dt = datetime.strptime(row["Time"], "%d.%m.%Y, %H:%M")
            dtz = dt.replace(tzinfo=MOLDOVA_TZ)
            dtz_utc = dtz.astimezone(timezone.utc)

            return {
                "sleep_start": dtz_utc,
                "sleep_duration": int(row["Duration(minutes)"]),
            }
        except Exception as e:
            raise ValueError(f"Invalid sleep CSV row: {row}") from e

    @staticmethod
    def _map_diaper_row(row: dict) -> dict:
        try:
            dt = datetime.strptime(row["Time"], "%d.%m.%Y, %H:%M")
            dtz = dt.replace(tzinfo=MOLDOVA_TZ)
            dtz_utc = dtz.astimezone(timezone.utc)

            return {
                "change_time": dtz_utc,
                "status": row["Status"]
            }
        except Exception as e:
            raise ValueError(f"Invalid diaper CSV row: {row}") from e

    def _create_baby_once(self, baby_name: str, tz: str) -> None:
        baby = self.baby_service.create_baby(baby_name, tz)
        self.baby_id = baby.id

    def import_sleep_for_baby(self, filename: str):
        if self.baby_id is None:
            raise RuntimeError("Baby must be created before importing data")

        inserted = 0
        failed = 0

        for idx,row in enumerate(CsvReader.read_csv_by_row(filename), start=1):
            try:
                data = self._map_sleep_row(row)
                self.sleep_service.create_sleep(
                    baby_id = self.baby_id,
                    sleep_start = data["sleep_start"],
                    sleep_duration = data["sleep_duration"]
                )
                inserted += 1

            except Exception as e:
                failed += 1
                logger.warning(f"Sleep CSV row with {idx} failed: {e}")

        print(f"Imported {inserted} rows. Failed {failed} rows.")

    def import_diaper_for_baby(self, filename: str):
        if self.baby_id is None:
            raise RuntimeError("Baby must be created before importing data")

        inserted = 0
        failed = 0

        for idx, row in enumerate(CsvReader.read_csv_by_row(filename), start=1):
            try:
                data = self._map_diaper_row(row)
                self.diaper_service.create_diaper(
                    baby_id=self.baby_id,
                    change_time=data["change_time"],
                    status=data["status"]
                )
                inserted += 1

            except Exception as e:
                failed += 1
                logger.warning(f"Diaper CSV row with {idx} failed: {e}")

        print(f"Imported {inserted} rows. Failed {failed} rows.")

    def import_all_for_baby(self, baby_name: str, tz: str, sleep_csv: str, diaper_csv: str):

        self._create_baby_once(baby_name, tz)
        self.import_sleep_for_baby(sleep_csv)
        self.import_diaper_for_baby(diaper_csv)

