from etl.runners.core_runners.core_incremental_runner.baby_incremental_load_runner import BabyCoreIncrementalExtractRunner
from etl.runners.core_runners.core_incremental_runner.diaper_incremental_load_runner import DiaperCoreIncrementalExtractRunner
from etl.runners.core_runners.core_incremental_runner.diaper_status_incremental_load_runner import DiaperStatusCoreIncrementalExtractRunner
from etl.runners.core_runners.core_incremental_runner.formula_incremental_load_runner import FormulaCoreIncrementalExtractRunner
from etl.runners.core_runners.core_incremental_runner.sleep_incremental_load_runner import SleepCoreIncrementalExtractRunner
from etl.runners.core_runners.core_init_common import (
    init_repo,
    extract_context_vars
)


def run_baby_incremental_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    BabyCoreIncrementalExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_diaper_status_incremental_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    DiaperStatusCoreIncrementalExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_diaper_data_incremental_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    DiaperCoreIncrementalExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_sleep_data_incremental_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    SleepCoreIncrementalExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)


def run_formula_data_incremental_transform_load(**context):
    meta_repo, core_repo = init_repo()
    dag_id, task_id, logical_date = extract_context_vars(**context)

    FormulaCoreIncrementalExtractRunner(
        meta_repo=meta_repo,
        core_repo=core_repo
    ).transform_load_run(dag_id=dag_id, task_id=task_id, logical_date=logical_date)

