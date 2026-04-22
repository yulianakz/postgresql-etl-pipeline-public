from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.timezone import datetime

from utils import notify_failure

from etl.runners.stg_runners.stg_initial_extract_run import (
    run_baby_initial_extract,
    run_diaper_initial_extract,
    run_formula_initial_extract,
    run_sleep_initial_extract
)
from etl.runners.core_runners.core_initial_load_run import (
    run_baby_initial_transform_load,
    run_date_initial_transform_load,
    run_time_initial_transform_load,
    run_diaper_data_transform_load,
    run_diaper_status_transform_load,
    run_formula_data_initial_transform_load,
    run_sleep_data_initial_transform_load
)
from datetime import timedelta


default_args = {
    "owner": "yuliana",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": notify_failure
}

with DAG(
    dag_id="initial_etl",
    start_date=datetime(2026, 1, 1),
    schedule ='@once',
    catchup=False,
    max_active_runs=1,
    default_args = default_args,
    tags=["staging-to-core", "initial", "etl"],
) as dag:

    to_stg_baby = PythonOperator(
        task_id="to_stg_baby",
        python_callable=run_baby_initial_extract,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    to_core_dim_baby= PythonOperator(
        task_id="to_core_dim_baby",
        python_callable=run_baby_initial_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    to_core_dim_date = PythonOperator(
        task_id="to_core_dim_date",
        python_callable=run_date_initial_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    to_core_dim_time = PythonOperator(
        task_id="to_core_dim_time",
        python_callable=run_time_initial_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    to_stg_diaper = PythonOperator(
        task_id="to_stg_diaper",
        python_callable=run_diaper_initial_extract,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    to_core_fact_diaper = PythonOperator(
        task_id="to_core_fact_diaper",
        python_callable=run_diaper_data_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)

    )

    to_core_dim_diaper_status = PythonOperator(
        task_id="to_core_dim_diaper_status",
        python_callable=run_diaper_status_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    to_stg_sleep = PythonOperator(
        task_id="to_stg_sleep",
        python_callable=run_sleep_initial_extract,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    to_core_fact_sleep = PythonOperator(
        task_id="to_core_fact_sleep",
        python_callable=run_sleep_data_initial_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    to_stg_formula = PythonOperator(
        task_id="to_stg_formula",
        python_callable=run_formula_initial_extract,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    to_core_fact_formula = PythonOperator(
        task_id="to_core_fact_formula",
        python_callable=run_formula_data_initial_transform_load,
        pool='postgres_pool',
        execution_timeout=timedelta(minutes=15)
    )

    stg_tasks = [
        to_stg_baby,
        to_stg_diaper,
        to_stg_sleep,
        to_stg_formula
    ]

    dim_pre_baby_tasks = [
        to_core_dim_date,
        to_core_dim_time,
        to_core_dim_diaper_status,
    ]

    fact_tasks = [
        to_core_fact_diaper,
        to_core_fact_sleep,
        to_core_fact_formula
    ]

    stg_done = EmptyOperator(task_id="stg_done")
    dim_intermediate_done = EmptyOperator(task_id="dim_intermediate_done")
    dim_done = EmptyOperator(task_id="dim_done")

    stg_tasks >> stg_done >> dim_pre_baby_tasks >> dim_intermediate_done
    dim_intermediate_done >> to_core_dim_baby >> dim_done >> fact_tasks