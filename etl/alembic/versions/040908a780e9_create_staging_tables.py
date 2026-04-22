"""create staging tables

Revision ID: 040908a780e9
Revises: 58e74c96f68c
Create Date: 2026-01-13 12:02:27.381285

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from etl.db.tables.staging_tables import stg_baby,stg_sleep,stg_diaper,stg_formula


# revision identifiers, used by Alembic.
revision: str = '040908a780e9'
down_revision: Union[str, Sequence[str], None] = '58e74c96f68c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [stg_diaper,stg_formula,stg_baby,stg_sleep]

def upgrade() -> None:
    for table in TABLES:
        op.create_table(
            table.name,
            *table.columns,
            schema=table.schema)


def downgrade() -> None:
    for table in TABLES:
        op.drop_table(table.name, schema=table.schema)