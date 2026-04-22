"""Unit tests for :mod:`etl.extract.domain.mappers.entities_mappers`."""

from datetime import datetime

import pytest

from etl.extract.domain.entities.extract_entities import (
    BabyDataEntity,
    DiaperDataEntity,
    FormulaDataEntity,
    SleepDataEntity,
)
from etl.extract.domain.mappers.entities_mappers import (
    BabyDataEntityMapper,
    DiaperDataEntityMapper,
    FormulaDataEntityMapper,
    SleepDataEntityMapper,
)
from etl.extract.domain.mappers.exceptions import MapperError


class TestBabyDataEntityMapper:
    def test_api_happy_path(self):
        entity = BabyDataEntityMapper.api_baby_mapper(
            {"id": "1", "name": "  Adi  ", "timezone": "Europe/Chisinau"}
        )
        assert isinstance(entity, BabyDataEntity)
        assert entity.source_id == 1
        assert entity.name == "Adi"
        assert entity.timezone == "Europe/Chisinau"
        assert entity.job_id is None
        assert entity.row_hash is not None  # set via BaseEntity.__post_init__

    def test_db_happy_path(self):
        entity = BabyDataEntityMapper.db_baby_mapper(
            {"id": 7, "name": "Adi", "timezone": "UTC"}
        )
        assert entity.source_id == 7
        assert entity.name == "Adi"

    def test_missing_keys_produce_none_values(self):
        entity = BabyDataEntityMapper.api_baby_mapper({})
        assert entity.source_id is None
        assert entity.name is None
        assert entity.timezone is None

    def test_invalid_id_raises_mapper_error(self):
        with pytest.raises(MapperError):
            BabyDataEntityMapper.api_baby_mapper(
                {"id": "abc", "name": "Adi", "timezone": "UTC"}
            )


class TestDiaperDataEntityMapper:
    def test_api_happy_path_uses_explicit_baby_id(self):
        entity = DiaperDataEntityMapper.api_diaper_mapper(
            {"id": 9, "change_time": "2026-01-01 08:00", "status": "wet"},
            baby_id=42,
        )
        assert isinstance(entity, DiaperDataEntity)
        assert entity.source_id == 9
        assert entity.baby_id == 42
        assert entity.change_time == datetime(2026, 1, 1, 8, 0)
        assert entity.status == "wet"

    def test_api_falls_back_to_row_baby_id(self):
        entity = DiaperDataEntityMapper.api_diaper_mapper(
            {"id": 9, "change_time": "2026-01-01 08:00", "status": "dirty", "baby_id": 77}
        )
        assert entity.baby_id == 77

    def test_db_happy_path(self):
        entity = DiaperDataEntityMapper.db_diaper_mapper(
            {
                "id": 3,
                "change_time": datetime(2026, 1, 1, 8, 0),
                "status": "mixed",
                "baby_id": 2,
            }
        )
        assert entity.baby_id == 2
        assert entity.status == "mixed"

    def test_api_invalid_change_time_raises(self):
        with pytest.raises(MapperError):
            DiaperDataEntityMapper.api_diaper_mapper(
                {"id": 1, "change_time": "not-a-date", "status": "wet"},
                baby_id=1,
            )


class TestSleepDataEntityMapper:
    def test_db_happy_path(self):
        entity = SleepDataEntityMapper.db_sleep_mapper(
            {
                "id": 1,
                "sleep_start": datetime(2026, 1, 1, 8, 0),
                "sleep_duration": 60,
                "baby_id": 1,
            }
        )
        assert isinstance(entity, SleepDataEntity)
        assert entity.sleep_duration == 60

    def test_api_happy_path_uses_start_duration_keys(self):
        entity = SleepDataEntityMapper.api_sleep_mapper(
            {
                "id": 1,
                "start": "2026-01-01 08:00",
                "duration": 60,
                "baby_id": 1,
            }
        )
        assert entity.sleep_start == datetime(2026, 1, 1, 8, 0)
        assert entity.sleep_duration == 60

    def test_api_invalid_duration_raises(self):
        with pytest.raises(MapperError):
            SleepDataEntityMapper.api_sleep_mapper(
                {
                    "id": 1,
                    "start": "2026-01-01 08:00",
                    "duration": "sixty",
                    "baby_id": 1,
                }
            )


class TestFormulaDataEntityMapper:
    def test_csv_happy_path(self):
        entity = FormulaDataEntityMapper.csv_formula_mapper(
            {
                "ID": "5",
                "Time": "01.02.2026, 08:00",
                "Amount (ml)": "120",
                "Baby ID": "7",
            }
        )
        assert isinstance(entity, FormulaDataEntity)
        assert entity.feed_time == datetime(2026, 2, 1, 8, 0)
        assert entity.amount_ml == 120
        assert entity.baby_id == 7
        # source_id is normally derived inside __post_init__ but safe_int kept a number here
        assert entity.source_id == 5

    def test_missing_baby_id_defaults_to_one(self):
        entity = FormulaDataEntityMapper.csv_formula_mapper(
            {"ID": "5", "Time": "01.02.2026, 08:00", "Amount (ml)": "120"}
        )
        assert entity.baby_id == 1

    def test_invalid_amount_raises(self):
        with pytest.raises(MapperError):
            FormulaDataEntityMapper.csv_formula_mapper(
                {
                    "ID": "5",
                    "Time": "01.02.2026, 08:00",
                    "Amount (ml)": "lots",
                    "Baby ID": "7",
                }
            )
