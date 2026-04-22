from etl.runners.stg_runners.stg_incremental_runner.formula_incremental_extract_runner import FormulaStgIncrementalExtractRunner
from etl.runners.stg_runners.stg_incremental_runner.baby_incremental_extract_runner import BabyStgIncrementalExtractRunner
from etl.runners.stg_runners.stg_incremental_runner.sleep_incremental_extract_runner import SleepStgIncrementalExtractRunner
from etl.runners.stg_runners.stg_incremental_runner.diaper_incremental_extract_runner import DiaperStgIncrementalExtractRunner
from etl.runners.stg_runners.stg_init_common import (
    init_repo,
    extract_context_vars
)


def run_baby_incremental_extract(**context):
    db_engine, meta_repo, stg_repo, factory = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    BabyStgIncrementalExtractRunner(
        meta_repo=meta_repo,
        extractor_factory=factory,
        stg_repo=stg_repo,
        engine=db_engine
    ).extract_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_sleep_incremental_extract(**context):
    db_engine, meta_repo, stg_repo, factory = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    SleepStgIncrementalExtractRunner(
        meta_repo=meta_repo,
        extractor_factory=factory,
        stg_repo=stg_repo,
        engine=db_engine
    ).extract_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_formula_incremental_extract(**context):
    db_engine, meta_repo, stg_repo, factory = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    FormulaStgIncrementalExtractRunner(
        meta_repo=meta_repo,
        extractor_factory=factory,
        stg_repo=stg_repo,
        engine=db_engine
    ).extract_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_diaper_incremental_extract(**context):

    db_engine, meta_repo, stg_repo, factory = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    DiaperStgIncrementalExtractRunner(
        meta_repo=meta_repo,
        extractor_factory=factory,
        stg_repo=stg_repo,
        engine=db_engine
    ).extract_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)