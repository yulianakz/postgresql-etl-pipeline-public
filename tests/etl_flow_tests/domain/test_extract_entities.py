"""Unit tests for :mod:`etl.extract.domain.entities.extract_entities`.

Validates the ``row_hash`` behavior that :class:`BaseEntity` provides plus
the ``FormulaDataEntity`` source-id derivation in ``__post_init__``.
"""

import hashlib
from datetime import datetime

from etl.extract.abstract_models.entity_interface import META_FIELDS, BaseEntity
from etl.extract.domain.entities.extract_entities import (
    BabyDataEntity,
    DiaperDataEntity,
    FormulaDataEntity,
    SleepDataEntity,
)


class TestBaseEntityHash:
    def test_meta_fields_constant(self):
        assert META_FIELDS == {"job_id", "row_hash", "loaded_at"}

    def test_hash_computed_when_not_provided(self):
        baby = BabyDataEntity(source_id=1, name="Adi", timezone="UTC")
        assert baby.row_hash is not None
        assert len(baby.row_hash) == 64

    def test_hash_preserved_when_provided(self):
        baby = BabyDataEntity(
            source_id=1, name="Adi", timezone="UTC", row_hash="precomputed"
        )
        assert baby.row_hash == "precomputed"

    def test_hash_changes_with_content(self):
        a = BabyDataEntity(source_id=1, name="Adi", timezone="UTC")
        b = BabyDataEntity(source_id=1, name="Adriana", timezone="UTC")
        assert a.row_hash != b.row_hash

    def test_hash_equal_for_equal_business_content(self):
        a = BabyDataEntity(source_id=1, name="Adi", timezone="UTC")
        b = BabyDataEntity(source_id=1, name="Adi", timezone="UTC")
        assert a.row_hash == b.row_hash

    def test_meta_fields_do_not_affect_hash(self):
        a = BabyDataEntity(
            source_id=1, name="Adi", timezone="UTC", job_id=None, loaded_at=None
        )
        b = BabyDataEntity(
            source_id=1,
            name="Adi",
            timezone="UTC",
            job_id=999,
            loaded_at=datetime(2026, 1, 1),
        )
        assert a.row_hash == b.row_hash


class TestSpecificEntityHashes:
    def test_diaper_hash(self):
        d = DiaperDataEntity(
            source_id=1,
            change_time=datetime(2026, 1, 1, 8, 0),
            status="wet",
            baby_id=1,
        )
        assert d.row_hash is not None

    def test_sleep_hash(self):
        s = SleepDataEntity(
            source_id=1,
            sleep_start=datetime(2026, 1, 1, 8, 0),
            sleep_duration=60,
            baby_id=1,
        )
        assert s.row_hash is not None


class TestFormulaDataEntityPostInit:
    def test_baby_id_defaults_to_1(self):
        f = FormulaDataEntity(feed_time=datetime(2026, 1, 1, 8, 0), amount_ml=120)
        assert f.baby_id == 1

    def test_source_id_is_derived_when_missing(self):
        f = FormulaDataEntity(feed_time=datetime(2026, 1, 1, 8, 0), amount_ml=120, baby_id=7)
        expected = hashlib.sha256(
            f"{datetime(2026, 1, 1, 8, 0).isoformat()}|7".encode("utf-8")
        ).hexdigest()[:16]
        assert f.source_id == expected

    def test_explicit_source_id_preserved(self):
        f = FormulaDataEntity(
            source_id="explicit",
            feed_time=datetime(2026, 1, 1, 8, 0),
            amount_ml=120,
            baby_id=7,
        )
        assert f.source_id == "explicit"

    def test_missing_feed_time_still_produces_source_id(self):
        f = FormulaDataEntity(feed_time=None, amount_ml=None, baby_id=None)
        assert f.source_id is not None
        assert f.baby_id == 1


def test_baseentity_is_abstract_via_fields_only():
    assert issubclass(BabyDataEntity, BaseEntity)
