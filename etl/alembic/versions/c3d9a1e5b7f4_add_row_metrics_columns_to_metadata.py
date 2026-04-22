"""add row metrics columns to metadata

Revision ID: c3d9a1e5b7f4
Revises: b91a9f3d2e4c
Create Date: 2026-04-21 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d9a1e5b7f4'
down_revision: Union[str, Sequence[str], None] = 'b91a9f3d2e4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'etl_job',
        'rows_loaded_count',
        new_column_name='rows_affected_count',
        schema='metadata',
    )
    op.add_column(
        'etl_job',
        sa.Column('rows_inserted_count', sa.Integer(), nullable=True),
        schema='metadata',
    )


def downgrade() -> None:
    op.drop_column('etl_job', 'rows_inserted_count', schema='metadata')
    op.alter_column(
        'etl_job',
        'rows_affected_count',
        new_column_name='rows_loaded_count',
        schema='metadata',
    )
