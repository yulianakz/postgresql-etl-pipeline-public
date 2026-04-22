"""add performance indexes

Revision ID: b91a9f3d2e4c
Revises: a450a23755b2
Create Date: 2026-04-20 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b91a9f3d2e4c'
down_revision: Union[str, Sequence[str], None] = 'a450a23755b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # core.dim_baby indexes (SCD2 current-row lookup + validity-range join support)
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_baby_current
        ON core.dim_baby (baby_nk)
        WHERE is_current = TRUE
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_dim_baby_nk_validity
        ON core.dim_baby (baby_nk, valid_from, valid_to)
        """
    )

    # metadata.etl_job indexes (dedup and latest-success lookup)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_etl_job_dedup_lookup
        ON metadata.etl_job (dag_id, task_id, logical_date, status)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_etl_job_latest_success
        ON metadata.etl_job
        (destination_schema, destination_table_name, pipeline_stage, status, ended_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_etl_job_source_path_success
        ON metadata.etl_job (data_source_path)
        WHERE status = 'success'
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_stg_baby_job_id
        ON staging.stg_baby (job_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_stg_sleep_job_id
        ON staging.stg_sleep (job_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_stg_diaper_job_id
        ON staging.stg_diaper (job_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_stg_formula_job_id
        ON staging.stg_formula (job_id)
        """
    )
def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS staging.idx_stg_formula_job_id")
    op.execute("DROP INDEX IF EXISTS staging.idx_stg_diaper_job_id")
    op.execute("DROP INDEX IF EXISTS staging.idx_stg_sleep_job_id")
    op.execute("DROP INDEX IF EXISTS staging.idx_stg_baby_job_id")
    op.execute("DROP INDEX IF EXISTS metadata.idx_etl_job_source_path_success")
    op.execute("DROP INDEX IF EXISTS metadata.idx_etl_job_latest_success")
    op.execute("DROP INDEX IF EXISTS metadata.idx_etl_job_dedup_lookup")
    op.execute("DROP INDEX IF EXISTS core.idx_dim_baby_nk_validity")
    op.execute("DROP INDEX IF EXISTS core.idx_dim_baby_current")
