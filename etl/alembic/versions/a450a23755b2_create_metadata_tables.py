"""create metadata tables

Revision ID: a450a23755b2
Revises: 22c69d7e7113
Create Date: 2026-01-13 12:04:01.352113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from etl.db.tables.metadata_tables import etl_job


# revision identifiers, used by Alembic.
revision: str = 'a450a23755b2'
down_revision: Union[str, Sequence[str], None] = '22c69d7e7113'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        etl_job.name,
        *etl_job.columns,
        schema=etl_job.schema
    )


def downgrade() -> None:
    op.drop_table(etl_job.name, schema=etl_job.schema)

