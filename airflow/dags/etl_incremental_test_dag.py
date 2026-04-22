from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.timezone import datetime

from utils import notify_failure

from etl.runners.stg_runners.stg_incremental_extract_run import (
    run_baby_incremental_extract,
    run_diaper_incremental_extract,
    run_formula_incremental_extract,
    run_sleep_incremental_extract
)
from etl.runners.core_runners.core_incremental_load_run import (
    run_formula_data_incremental_transform_load,
    run_diaper_data_incremental_transform_load,
    run_sleep_data_incremental_transform_load,
    run_diaper_status_incremental_transform_load,
    run_baby_incremental_transform_load
)
from datetime import timedelta


default_args = {
    "owner": "yuliana",
    "retries": 0,
    "on_failure_callback": notify_failure
}



with DAG(
    dag_id="test_incremental_stg",
    start_date=datetime(2026, 1, 1),
    schedule=None,                  # manual trigger only
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["test", "incremental", "stg"],
) as stg_dag:

    test_to_stg_baby = PythonOperator(
        task_id="to_stg_baby",
        python_callable=run_baby_incremental_extract,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    test_to_stg_diaper = PythonOperator(
        task_id="to_stg_diaper",
        python_callable=run_diaper_incremental_extract,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    test_to_stg_sleep = PythonOperator(
        task_id="to_stg_sleep",
        python_callable=run_sleep_incremental_extract,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    test_to_stg_formula = PythonOperator(
        task_id="to_stg_formula",
        python_callable=run_formula_incremental_extract,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    stg_done = EmptyOperator(task_id="stg_done")

    [test_to_stg_baby, test_to_stg_diaper, test_to_stg_sleep, test_to_stg_formula] >> stg_done




with DAG(
    dag_id="test_incremental_core",
    start_date=datetime(2026, 1, 1),
    schedule=None,                  # manual trigger only
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["test", "incremental", "core"],
) as core_dag:

    test_to_core_dim_baby = PythonOperator(
        task_id="to_core_dim_baby",
        python_callable=run_baby_incremental_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    test_to_core_dim_diaper_status = PythonOperator(
        task_id="to_core_dim_diaper_status",
        python_callable=run_diaper_status_incremental_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    test_to_core_fact_diaper = PythonOperator(
        task_id="to_core_fact_diaper",
        python_callable=run_diaper_data_incremental_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    test_to_core_fact_sleep = PythonOperator(
        task_id="to_core_fact_sleep",
        python_callable=run_sleep_data_incremental_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    test_to_core_fact_formula = PythonOperator(
        task_id="to_core_fact_formula",
        python_callable=run_formula_data_incremental_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    dim_tasks = [test_to_core_dim_baby, test_to_core_dim_diaper_status]
    fact_tasks = [test_to_core_fact_diaper, test_to_core_fact_sleep, test_to_core_fact_formula]

    dim_done = EmptyOperator(task_id="dim_done")

    dim_tasks >> dim_done >> fact_tasks
