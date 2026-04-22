from sqlalchemy import (
    Table, Column, Integer, String, DateTime, Text, Index
)
from etl.db.engine import metadata
from etl.db.schemas import STAGING_SCHEMA


stg_baby = Table(
    'stg_baby',
    metadata,
    Column('row_hash', String(64)),
    Column('source_id', Integer),
    Column('name', String),
    Column('timezone', String),
    Column('job_id', Integer, nullable=False),
    Column('loaded_at', DateTime(timezone=True), nullable=False),
    schema = STAGING_SCHEMA
)

stg_sleep = Table(
    'stg_sleep',
    metadata,
    Column('row_hash', String(64)),
    Column('source_id', Integer),
    Column('sleep_start', DateTime(timezone=True)),
    Column('sleep_duration', Integer),
    Column('baby_id', Integer),
    Column('job_id', Integer, nullable=False),
    Column('loaded_at', DateTime(timezone=True), nullable=False),
    schema = STAGING_SCHEMA
)

stg_diaper = Table(
    'stg_diaper',
    metadata,
    Column('row_hash', String(64)),
    Column('source_id', Integer),
    Column('change_time', DateTime(timezone=True)),
    Column('status', String),
    Column('baby_id', Integer),
    Column('job_id', Integer, nullable=False),
    Column('loaded_at', DateTime(timezone=True), nullable=False),
    schema = STAGING_SCHEMA
)

stg_formula = Table(
    'stg_formula',
    metadata,
    Column('row_hash', String(64)),
    Column('source_id', Text),
    Column('amount_ml', Integer),
    Column('feed_time', DateTime(timezone=True)),
    Column('baby_id', Integer),
    Column('job_id', Integer, nullable=False),
    Column('loaded_at', DateTime(timezone=True), nullable=False),
    schema = STAGING_SCHEMA
)

Index(
    'idx_stg_baby_job_id',
    stg_baby.c.job_id,
)

Index(
    'idx_stg_sleep_job_id',
    stg_sleep.c.job_id,
)

Index(
    'idx_stg_diaper_job_id',
    stg_diaper.c.job_id,
)

Index(
    'idx_stg_formula_job_id',
    stg_formula.c.job_id,
)
