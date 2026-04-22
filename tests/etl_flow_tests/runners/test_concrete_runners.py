"""Smoke tests for the concrete staging/core runners.

These verify that each concrete class hard-codes the correct constants
(source/destination/load type) and that the build_extractor/get_sql methods
wire up the expected extractor class or SQL file.
"""

import os

import pytest

# Staging runners
from etl.runners.stg_runners.stg_initial_runner.baby_initial_extract_runner import (
    BabyStgFullExtractRunner,
)
from etl.runners.stg_runners.stg_initial_runner.sleep_initial_extract_runner import (
    SleepStgFullExtractRunner,
)
from etl.runners.stg_runners.stg_initial_runner.formula_initial_extract_runner import (
    FormulaStgFullExtractRunner,
)
from etl.runners.stg_runners.stg_initial_runner.diaper_initial_extract_runner import (
    DiaperStgFullExtractRunner,
)
from etl.runners.stg_runners.stg_incremental_runner.baby_incremental_extract_runner import (
    BabyStgIncrementalExtractRunner,
)
from etl.runners.stg_runners.stg_incremental_runner.sleep_incremental_extract_runner import (
    SleepStgIncrementalExtractRunner,
)
from etl.runners.stg_runners.stg_incremental_runner.diaper_incremental_extract_runner import (
    DiaperStgIncrementalExtractRunner,
)
from etl.runners.stg_runners.stg_incremental_runner.formula_incremental_extract_runner import (
    FormulaStgIncrementalExtractRunner,
)

# Core initial runners
from etl.runners.core_runners.core_initial_runner.baby_initial_load_runner import (
    BabyCoreInitialExtractRunner,
)
from etl.runners.core_runners.core_initial_runner.date_initial_load_runner import (
    DateCoreInitialExtractRunner,
)
from etl.runners.core_runners.core_initial_runner.time_initial_load_runner import (
    TimeCoreInitialExtractRunner,
)
from etl.runners.core_runners.core_initial_runner.diaper_status_initial_load_runner import (
    DiaperStatusCoreInitialExtractRunner,
)
from etl.runners.core_runners.core_initial_runner.diaper_data_initial_load_runner import (
    DiaperDataCoreInitialExtractRunner,
)
from etl.runners.core_runners.core_initial_runner.sleep_data_initial_load_runner import (
    SleepDataCoreInitialExtractRunner,
)
from etl.runners.core_runners.core_initial_runner.formula_data_initial_load_runner import (
    FormulaDataCoreInitialExtractRunner,
)

# Core incremental runners
from etl.runners.core_runners.core_incremental_runner.baby_incremental_load_runner import (
    BabyCoreIncrementalExtractRunner,
)
from etl.runners.core_runners.core_incremental_runner.diaper_incremental_load_runner import (
    DiaperCoreIncrementalExtractRunner,
)
from etl.runners.core_runners.core_incremental_runner.diaper_status_incremental_load_runner import (
    DiaperStatusCoreIncrementalExtractRunner,
)

from etl.extract.domain.entities.extract_entities import (
    BabyDataEntity,
    DiaperDataEntity,
    FormulaDataEntity,
    SleepDataEntity,
)
from etl.extract.extract_factory.extract_factory import ExtractorFactory
from etl.extract.extractors.csv_extractor import CsvExtractor
from etl.extract.extractors.db_extractor import DbExtractor


class _FakeEngine:
    pass


class _FakeMetaRepo:
    def get_last_successful_watermark(self, destination_schema, destination_table_name, pipeline_stage):
        return None


STG_EXPECTATIONS = [
    (
        BabyStgFullExtractRunner,
        {
            "pipeline_stage": "extract",
            "source_type": "db",
            "source_path": "public.baby_info",
            "destination_table_name": "stg_baby",
            "load_type": "initial",
            "entity_type": BabyDataEntity,
        },
    ),
    (
        SleepStgFullExtractRunner,
        {
            "pipeline_stage": "extract",
            "source_type": "db",
            "source_path": "public.sleep_data",
            "destination_table_name": "stg_sleep",
            "load_type": "initial",
            "entity_type": SleepDataEntity,
        },
    ),
    (
        FormulaStgFullExtractRunner,
        {
            "pipeline_stage": "extract",
            "source_type": "csv",
            "destination_table_name": "stg_formula",
            "load_type": "initial",
            "entity_type": FormulaDataEntity,
        },
    ),
    (
        BabyStgIncrementalExtractRunner,
        {
            "pipeline_stage": "extract",
            "source_type": "db",
            "source_path": "public.baby_info",
            "destination_table_name": "stg_baby",
            "load_type": "full_reload",
            "entity_type": BabyDataEntity,
        },
    ),
    (
        SleepStgIncrementalExtractRunner,
        {
            "source_type": "db",
            "source_path": "public.sleep_data",
            "destination_table_name": "stg_sleep",
            "load_type": "incremental",
            "entity_type": SleepDataEntity,
        },
    ),
    (
        DiaperStgIncrementalExtractRunner,
        {
            "source_type": "db",
            "source_path": "public.diaper_data",
            "destination_table_name": "stg_diaper",
            "load_type": "incremental",
            "entity_type": DiaperDataEntity,
        },
    ),
    (
        FormulaStgIncrementalExtractRunner,
        {
            "source_type": "csv",
            "destination_table_name": "stg_formula",
            "load_type": "incremental",
            "entity_type": FormulaDataEntity,
        },
    ),
]


@pytest.mark.parametrize("runner_cls, expected", STG_EXPECTATIONS)
def test_stg_runner_constants(runner_cls, expected):
    if runner_cls is DiaperStgFullExtractRunner:
        runner = runner_cls(
            meta_repo=None,
            extractor_factory=ExtractorFactory(),
            stg_repo=None,
            auth_client=None,
            engine=_FakeEngine(),
        )
    else:
        runner = runner_cls(
            meta_repo=None,
            extractor_factory=ExtractorFactory(),
            stg_repo=None,
            engine=_FakeEngine(),
        )
    for key, val in expected.items():
        assert getattr(runner, key)() == val


class TestStgBuildExtractor:
    def test_baby_initial_builds_db_extractor(self):
        runner = BabyStgFullExtractRunner(
            meta_repo=None,
            extractor_factory=ExtractorFactory(),
            stg_repo=None,
            engine=_FakeEngine(),
        )
        extractor = runner.build_extractor()
        assert isinstance(extractor, DbExtractor)

    def test_sleep_incremental_builds_db_extractor(self):
        runner = SleepStgIncrementalExtractRunner(
            meta_repo=_FakeMetaRepo(),
            extractor_factory=ExtractorFactory(),
            stg_repo=None,
            engine=_FakeEngine(),
        )
        assert isinstance(runner.build_extractor(), DbExtractor)

    def test_formula_initial_builds_csv_extractor(self):
        runner = FormulaStgFullExtractRunner(
            meta_repo=None,
            extractor_factory=ExtractorFactory(),
            stg_repo=None,
            engine=_FakeEngine(),
        )
        assert isinstance(runner.build_extractor(), CsvExtractor)

    def test_formula_incremental_source_path_is_fixed_csv(self):
        runner = FormulaStgIncrementalExtractRunner(
            meta_repo=None,
            extractor_factory=ExtractorFactory(),
            stg_repo=None,
            engine=_FakeEngine(),
        )
        path = runner.source_path()
        assert os.path.basename(path) == "incremental_formula_data_to_stg_test.csv"

    def test_diaper_initial_build_extractor_raises(self):
        runner = DiaperStgFullExtractRunner(
            meta_repo=None,
            extractor_factory=ExtractorFactory(),
            stg_repo=None,
            auth_client=None,
            engine=_FakeEngine(),
        )
        with pytest.raises(NotImplementedError):
            runner.build_extractor()


CORE_EXPECTATIONS = [
    (
        BabyCoreInitialExtractRunner,
        {
            "pipeline_stage": "transform_load",
            "destination_table_name": "dim_baby",
            "load_type": "initial",
            "source_path": "staging.stg_baby",
        },
    ),
    (
        DateCoreInitialExtractRunner,
        {"destination_table_name": "dim_date", "load_type": "initial", "source_path": "no path"},
    ),
    (
        TimeCoreInitialExtractRunner,
        {"destination_table_name": "dim_time", "load_type": "initial"},
    ),
    (
        DiaperStatusCoreInitialExtractRunner,
        {
            "destination_table_name": "dim_diaper_status",
            "source_path": "staging.stg_diaper",
            "load_type": "initial",
        },
    ),
    (
        DiaperDataCoreInitialExtractRunner,
        {
            "destination_table_name": "fact_diaper",
            "source_path": "staging.stg_diaper",
            "load_type": "initial",
        },
    ),
    (
        SleepDataCoreInitialExtractRunner,
        {
            "destination_table_name": "fact_sleep",
            "source_path": "staging.stg_sleep",
            "load_type": "initial",
        },
    ),
    (
        FormulaDataCoreInitialExtractRunner,
        {
            "destination_table_name": "fact_formula_feed",
            "source_path": "staging.stg_formula",
            "load_type": "initial",
        },
    ),
    (
        BabyCoreIncrementalExtractRunner,
        {
            "destination_table_name": "dim_baby",
            "source_path": "staging.stg_baby",
            "load_type": "incremental",
        },
    ),
    (
        DiaperCoreIncrementalExtractRunner,
        {
            "destination_table_name": "fact_diaper",
            "source_path": "staging.stg_diaper",
            "load_type": "incremental",
        },
    ),
    (
        DiaperStatusCoreIncrementalExtractRunner,
        {
            "destination_table_name": "dim_diaper_status",
            "source_path": "staging.stg_diaper",
            "load_type": "incremental",
        },
    ),
]


@pytest.mark.parametrize("runner_cls, expected", CORE_EXPECTATIONS)
def test_core_runner_constants(runner_cls, expected):
    runner = runner_cls(meta_repo=None, core_repo=None)
    for key, val in expected.items():
        assert getattr(runner, key)() == val


@pytest.mark.parametrize(
    "runner_cls",
    [
        BabyCoreInitialExtractRunner,
        DiaperStatusCoreInitialExtractRunner,
        DiaperDataCoreInitialExtractRunner,
        SleepDataCoreInitialExtractRunner,
        FormulaDataCoreInitialExtractRunner,
        BabyCoreIncrementalExtractRunner,
        DiaperCoreIncrementalExtractRunner,
        DiaperStatusCoreIncrementalExtractRunner,
    ],
)
def test_core_runner_sql_is_non_empty(runner_cls):
    runner = runner_cls(meta_repo=None, core_repo=None)
    sql = runner.get_sql()
    assert isinstance(sql, str)
    assert sql.strip() != ""


def test_date_and_time_runners_have_none_params():
    assert DateCoreInitialExtractRunner(None, None).get_sql_params(1) is None
    assert TimeCoreInitialExtractRunner(None, None).get_sql_params(1) is None


def test_baby_initial_sql_params_forward_job_id():
    params = BabyCoreInitialExtractRunner(None, None).get_sql_params(42)
    assert params == {"job_id": 42}
