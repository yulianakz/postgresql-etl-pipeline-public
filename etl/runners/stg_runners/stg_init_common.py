from etl.db.repositories.stg_postgres_repo import StgPostgresRepository
from etl.db.repositories.meta_postgres_repo import MetadataPostgresRepository

from etl.extract.extract_factory.extract_factory import ExtractorFactory
from etl.extract.services.auth_client import ApiAuthClient

from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.http.hooks.http import HttpHook

from datetime import timezone


def init_repo(postgres_conn_id='postgres_baby_data'):

    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    db_engine = hook.get_sqlalchemy_engine(
        engine_kwargs={
            'pool_size': 5,
            'max_overflow': 2,
            'pool_recycle': 1800,
            'pool_timeout': 60
        }
    )
    meta_repo = MetadataPostgresRepository(db_engine)
    stg_repo = StgPostgresRepository(db_engine)
    factory = ExtractorFactory()

    return db_engine, meta_repo, stg_repo, factory

def init_auth(http_conn_id='baby_api'):

    http_hook = HttpHook(http_conn_id=http_conn_id)
    conn = http_hook.get_connection(http_hook.http_conn_id)
    host = conn.host
    if not host:
        raise RuntimeError("HTTP connection host is missing")

    schema = conn.schema
    port = f":{conn.port}" if conn.port else ""
    base_url = f"{schema}://{host}{port}"

    username = conn.login
    password = conn.password

    if not base_url or not username or not password:
        raise RuntimeError("Missing API connection configuration")

    api_auth = ApiAuthClient(
        base_url=base_url,
        username=username,
        password=password
    )
    return api_auth


def extract_context_vars(**context):

    ti = context["ti"]
    dag_id = ti.dag_id
    task_id = ti.task_id
    logical_date = context["logical_date"]
    dag = context.get("dag")

    if dag and dag.schedule_interval in ("@once", None):
        """
        # For @once/None: Use DAG start_date (stable) (note: dag start_date can be not tz aware)
        # For scheduled DAGs: Normalize based on schedule frequency
        # Daily or longer: normalize to midnight
        # Hourly/minutely: keep hour/minute, only normalize seconds/microseconds
        # Default: normalize to midnight (safe fallback)
        """

        logical_date = dag.start_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if logical_date.tzinfo is None:
            logical_date = logical_date.replace(tzinfo=timezone.utc)
    else:
        if dag and dag.schedule_interval:
            schedule_str = str(dag.schedule_interval).lower()
            if any(x in schedule_str for x in
                   ['@daily', '@weekly', '@monthly', '@yearly', 'day', 'week', 'month', 'year']):
                logical_date = logical_date.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                logical_date = logical_date.replace(second=0, microsecond=0)
        else:
            logical_date = logical_date.replace(hour=0, minute=0, second=0, microsecond=0)

    return dag_id, task_id, logical_date