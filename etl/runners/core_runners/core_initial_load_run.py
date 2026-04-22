from etl.runners.core_runners.core_initial_runner.baby_initial_load_runner import BabyCoreInitialExtractRunner
from etl.runners.core_runners.core_initial_runner.date_initial_load_runner import DateCoreInitialExtractRunner
from etl.runners.core_runners.core_initial_runner.time_initial_load_runner import TimeCoreInitialExtractRunner
from etl.runners.core_runners.core_initial_runner.diaper_status_initial_load_runner import DiaperStatusCoreInitialExtractRunner
from etl.runners.core_runners.core_initial_runner.diaper_data_initial_load_runner import DiaperDataCoreInitialExtractRunner
from etl.runners.core_runners.core_initial_runner.formula_data_initial_load_runner import FormulaDataCoreInitialExtractRunner
from etl.runners.core_runners.core_initial_runner.sleep_data_initial_load_runner import SleepDataCoreInitialExtractRunner
from etl.runners.core_runners.core_init_common import (
    init_repo,
    extract_context_vars
)


def run_baby_initial_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    BabyCoreInitialExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_date_initial_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    DateCoreInitialExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_time_initial_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    TimeCoreInitialExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_diaper_status_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    DiaperStatusCoreInitialExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_diaper_data_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    DiaperDataCoreInitialExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_sleep_data_initial_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    SleepDataCoreInitialExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_formula_data_initial_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    FormulaDataCoreInitialExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)

