from etl.extract.domain.entities.extract_entities import BabyDataEntity, DiaperDataEntity, SleepDataEntity, FormulaDataEntity
from etl.extract.domain.mappers.utils import safe_int, safe_datetime, safe_str


class BabyDataEntityMapper:

    @staticmethod
    def api_baby_mapper(row):
        return BabyDataEntity(
            source_id=safe_int(row.get("id")),
            name=safe_str(row.get("name")),
            timezone=safe_str(row.get("timezone")),
            job_id=None,
            loaded_at=None
        )

    @staticmethod
    def db_baby_mapper(row):
        return BabyDataEntity(
            source_id=safe_int(row.get("id")),
            name=safe_str(row.get("name")),
            timezone=safe_str(row.get("timezone")),
            job_id=None,
            loaded_at=None
        )


class DiaperDataEntityMapper:

    @staticmethod
    def api_diaper_mapper(row, *, baby_id: int | None = None):
        resolved_baby_id = baby_id if baby_id is not None else safe_int(row.get("baby_id"))
        return DiaperDataEntity(
            source_id=safe_int(row.get("id")),
            change_time=safe_datetime(row.get("change_time")),
            status=safe_str(row.get("status")),
            baby_id=resolved_baby_id,
            job_id=None,
            loaded_at=None
        )

    @staticmethod
    def db_diaper_mapper(row):
        return DiaperDataEntity(
            source_id=safe_int(row.get("id")),
            change_time=safe_datetime(row.get("change_time")),
            status=safe_str(row.get("status")),
            baby_id=safe_int(row.get("baby_id")),
            job_id=None,
            loaded_at=None
        )


class SleepDataEntityMapper:

    @staticmethod
    def db_sleep_mapper(row):
        return SleepDataEntity(
            source_id=safe_int(row.get("id")),
            sleep_start=safe_datetime(row.get("sleep_start")),
            sleep_duration=safe_int(row.get("sleep_duration")),
            baby_id=safe_int(row.get("baby_id")),
            job_id=None
        )

    @staticmethod
    def api_sleep_mapper(row):
        return SleepDataEntity(
            source_id=safe_int(row.get("id")),
            sleep_start=safe_datetime(row.get("start")),
            sleep_duration=safe_int(row.get("duration")),
            baby_id=safe_int(row.get("baby_id")),
            job_id=None,
            loaded_at=None
        )


class FormulaDataEntityMapper:

    @staticmethod
    def csv_formula_mapper(row):
        return FormulaDataEntity(
            source_id=safe_int(row.get("ID")),
            feed_time=safe_datetime(row.get("Time"), "%d.%m.%Y, %H:%M"),
            amount_ml=safe_int(row.get("Amount (ml)")),
            baby_id=safe_int(row.get("Baby ID")),
            job_id=None,
            loaded_at=None
        )
