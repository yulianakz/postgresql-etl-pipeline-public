"""create core tables

Revision ID: 22c69d7e7113
Revises: 040908a780e9
Create Date: 2026-01-13 12:03:34.137117

"""
from typing import Sequence, Union

from alembic import op

from etl.db.tables.core_tables import dim_diaper_status, dim_baby, dim_date, dim_time


# revision identifiers, used by Alembic.
revision: str = '22c69d7e7113'
down_revision: Union[str, Sequence[str], None] = '040908a780e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Covers source history from 2022-12 through the end of 2027.
PARTITION_START = "2022-12-01"
PARTITION_END_EXCLUSIVE = "2028-01-01"

DIM_TABLES = [dim_diaper_status, dim_baby, dim_date, dim_time]


def _create_monthly_partitions(
    parent_table_name: str,
    partition_prefix: str,
) -> None:
    op.execute(
        f"""
        DO $$
        DECLARE
            d DATE := DATE '{PARTITION_START}';
        BEGIN
            WHILE d < DATE '{PARTITION_END_EXCLUSIVE}' LOOP
                EXECUTE format(
                    'CREATE TABLE IF NOT EXISTS core.{partition_prefix}_%s PARTITION OF core.{parent_table_name}
                     FOR VALUES FROM (%s) TO (%s)',
                    to_char(d, 'YYYY_MM'),
                    to_char(d, 'YYYYMMDD')::INTEGER,
                    to_char((d + INTERVAL '1 month')::DATE, 'YYYYMMDD')::INTEGER
                );
                d := (d + INTERVAL '1 month')::DATE;
            END LOOP;
        END $$;
        """
    )


def upgrade() -> None:
    for table in DIM_TABLES:
        op.create_table(
            table.name,
            *table.columns,
            schema=table.schema
        )

    op.execute(
        """
        CREATE TABLE core.fact_sleep (
            baby_sk BIGINT,
            sleep_start_date_sk INTEGER,
            sleep_start_time_sk INTEGER,
            duration_minutes INTEGER,
            job_id INTEGER NOT NULL,
            loaded_at TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (baby_sk, sleep_start_date_sk, sleep_start_time_sk)
        ) PARTITION BY RANGE (sleep_start_date_sk)
        """
    )
    op.execute(
        """
        CREATE TABLE core.fact_diaper (
            baby_sk BIGINT,
            change_date_sk INTEGER,
            change_time_sk INTEGER,
            diaper_status_sk VARCHAR,
            job_id INTEGER NOT NULL,
            loaded_at TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (baby_sk, change_date_sk, change_time_sk)
        ) PARTITION BY RANGE (change_date_sk)
        """
    )
    op.execute(
        """
        CREATE TABLE core.fact_formula_feed (
            baby_sk BIGINT,
            f_feeding_date_sk INTEGER,
            f_feeding_time_sk INTEGER,
            amount_ml INTEGER,
            job_id INTEGER NOT NULL,
            loaded_at TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (baby_sk, f_feeding_date_sk, f_feeding_time_sk)
        ) PARTITION BY RANGE (f_feeding_date_sk)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS core.fact_sleep_default
        PARTITION OF core.fact_sleep DEFAULT
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS core.fact_diaper_default
        PARTITION OF core.fact_diaper DEFAULT
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS core.fact_formula_feed_default
        PARTITION OF core.fact_formula_feed DEFAULT
        """
    )

    _create_monthly_partitions("fact_sleep", "fact_sleep")
    _create_monthly_partitions("fact_diaper", "fact_diaper")
    _create_monthly_partitions("fact_formula_feed", "fact_formula_feed")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS core.fact_formula_feed CASCADE")
    op.execute("DROP TABLE IF EXISTS core.fact_diaper CASCADE")
    op.execute("DROP TABLE IF EXISTS core.fact_sleep CASCADE")

    for table in reversed(DIM_TABLES):
        op.drop_table(table.name, schema=table.schema)
