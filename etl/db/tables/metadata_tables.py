from sqlalchemy import (
    Table, Column, String, DateTime, Integer, Enum, Index, text
)
from etl.db.engine import metadata
from etl.db.schemas import METADATA_SCHEMA


etl_job = Table(
    'etl_job',
    metadata,
    Column('job_id', Integer, primary_key=True, autoincrement=True),
    Column('dag_id', String),
    Column('task_id', String),
    Column('logical_date', DateTime(timezone=True)),
    Column('pipeline_stage', String),
    Column('parent_job_id', Integer),
    Column('data_source_type', String),
    Column('data_source_path', String),
    Column('destination_schema', String),
    Column('destination_table_name', String),
    Column('started_at', DateTime(timezone=True)),
    Column('ended_at', DateTime(timezone=True)),
    Column('status', Enum('running','success', 'failed', name='etl_status'), nullable=False),
    Column('error_message', String),
    Column('rows_affected_count', Integer),
    Column('rows_inserted_count', Integer),
    Column('last_loaded_event_ts_watermark', DateTime(timezone=True)),
    schema = METADATA_SCHEMA
)

Index(
    'idx_etl_job_dedup_lookup',
    etl_job.c.dag_id,
    etl_job.c.task_id,
    etl_job.c.logical_date,
    etl_job.c.status
)

Index(
    'idx_etl_job_latest_success',
    etl_job.c.destination_schema,
    etl_job.c.destination_table_name,
    etl_job.c.pipeline_stage,
    etl_job.c.status,
    etl_job.c.ended_at.desc(),
)

Index(
    'idx_etl_job_source_path_success',
    etl_job.c.data_source_path,
    postgresql_where=text("status = 'success'")
)