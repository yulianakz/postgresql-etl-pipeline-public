from etl.runners.stg_runners.stg_initial_runner.baby_initial_extract_runner import BabyStgFullExtractRunner
from etl.runners.stg_runners.stg_initial_runner.diaper_initial_extract_runner import DiaperStgFullExtractRunner
from etl.runners.stg_runners.stg_initial_runner.sleep_initial_extract_runner import SleepStgFullExtractRunner
from etl.runners.stg_runners.stg_initial_runner.formula_initial_extract_runner import FormulaStgFullExtractRunner
from etl.runners.stg_runners.stg_init_common import (
    init_repo,
    init_auth,
    extract_context_vars
)


def run_baby_initial_extract(**context):
    db_engine, meta_repo, stg_repo, factory = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    BabyStgFullExtractRunner(
        meta_repo=meta_repo,
        extractor_factory=factory,
        stg_repo=stg_repo,
        engine=db_engine
    ).extract_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_sleep_initial_extract(**context):
    db_engine, meta_repo, stg_repo, factory = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    SleepStgFullExtractRunner(
        meta_repo=meta_repo,
        extractor_factory=factory,
        stg_repo=stg_repo,
        engine=db_engine
    ).extract_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_formula_initial_extract(**context):
    db_engine, meta_repo, stg_repo, factory = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    FormulaStgFullExtractRunner(
        meta_repo=meta_repo,
        extractor_factory=factory,
        stg_repo=stg_repo,
        engine=db_engine
    ).extract_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_diaper_initial_extract(**context):
    db_engine, meta_repo, stg_repo, factory = init_repo()
    api_auth = init_auth()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    DiaperStgFullExtractRunner(
        meta_repo=meta_repo,
        extractor_factory=factory,
        stg_repo=stg_repo,
        auth_client=api_auth,
        engine=db_engine
    ).extract_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)





