from sqlalchemy import (
    Table, Column, Integer, Date, Time, DateTime, String, Boolean, BigInteger, PrimaryKeyConstraint, Index, text
)
from etl.db.engine import metadata
from etl.db.schemas import CORE_SCHEMA


# One row per baby per sleep session; PK grain is start date + start time to the minute.
# Domain rule: a baby does not have two overlapping sessions with the same start minute, so
# ON CONFLICT DO NOTHING on this key is not expected to drop legitimate second rows.
fact_sleep = Table(
    'fact_sleep',
    metadata,
    Column('baby_sk', BigInteger),
    Column('sleep_start_date_sk', Integer),
    Column('sleep_start_time_sk', Integer),
    Column('duration_minutes', Integer),
    Column('job_id', Integer, nullable=False),
    Column('loaded_at', DateTime(timezone=True), nullable=False),
    PrimaryKeyConstraint('baby_sk', 'sleep_start_date_sk', 'sleep_start_time_sk'),
    schema=CORE_SCHEMA
)

#One row per baby per diaper change timestamp
fact_diaper = Table(
    'fact_diaper',
    metadata,
    Column('baby_sk', BigInteger),
    Column('change_date_sk', Integer),
    Column('change_time_sk', Integer),
    Column('diaper_status_sk', String),
    Column('job_id', Integer, nullable=False),
    Column('loaded_at', DateTime(timezone=True), nullable=False),
    PrimaryKeyConstraint('baby_sk', 'change_date_sk', 'change_time_sk'),
    schema=CORE_SCHEMA
)

#One row per baby per formula feed timestamp
fact_formula_feed = Table(
    'fact_formula_feed',
    metadata,
    Column('baby_sk', BigInteger),
    Column('f_feeding_date_sk', Integer),
    Column('f_feeding_time_sk', Integer),
    Column('amount_ml', Integer),
    Column('job_id', Integer, nullable=False),
    Column('loaded_at', DateTime(timezone=True), nullable=False),
    PrimaryKeyConstraint('baby_sk', 'f_feeding_date_sk', 'f_feeding_time_sk'),
    schema=CORE_SCHEMA
)

#junk dimension
dim_diaper_status = Table(
    'dim_diaper_status',
    metadata,
    Column('diaper_status_sk', String, primary_key=True),
    Column('diaper_status', String),
    Column('job_id', Integer, nullable=False),
    Column('loaded_at', DateTime(timezone=True), nullable=False),
    Column('updated_at', DateTime(timezone=True), nullable=True),
    schema=CORE_SCHEMA
)

#scd type 0
dim_date = Table(
    'dim_date',
    metadata,
    Column('date_sk', Integer, primary_key=True),
    Column('full_date', Date),
    Column('year', Integer),
    Column('month', Integer),
    Column('day', Integer),
    schema=CORE_SCHEMA
)

#scd type 0
dim_time = Table(
    'dim_time',
    metadata,
    Column('time_sk', Integer, primary_key=True),
    Column('full_time', Time),
    Column('hour',Integer),
    Column('minute',Integer),
    schema=CORE_SCHEMA
)

#scd type 2 for timezone
dim_baby = Table(
    'dim_baby',
    metadata,
    Column('baby_sk', BigInteger, primary_key=True, autoincrement=True),
    Column('baby_nk', Integer),
    Column('baby_name', String),
    Column('timezone_iana', String),
    Column('valid_from', DateTime, nullable=False),
    Column('valid_to', DateTime, nullable=False),
    Column('is_current', Boolean, nullable=False),
    Column('job_id', Integer, nullable=False),
    Column('loaded_at', DateTime(timezone=True), nullable=False),
    Column('updated_at', DateTime(timezone=True), nullable=True),
    schema=CORE_SCHEMA
)


Index( "idx_dim_baby_current",
       dim_baby.c.baby_nk,unique=True,postgresql_where=text("is_current = TRUE"))

Index(
    "idx_dim_baby_nk_validity",
    dim_baby.c.baby_nk,
    dim_baby.c.valid_from,
    dim_baby.c.valid_to,
)