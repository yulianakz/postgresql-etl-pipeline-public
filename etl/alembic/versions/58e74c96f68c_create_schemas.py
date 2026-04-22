"""create schemas

Revision ID: 58e74c96f68c
Revises: 
Create Date: 2026-01-13 11:35:16.583256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from etl.db.schemas import STAGING_SCHEMA, CORE_SCHEMA, METADATA_SCHEMA


# revision identifiers, used by Alembic.
revision: str = '58e74c96f68c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for schema in [STAGING_SCHEMA, CORE_SCHEMA, METADATA_SCHEMA]:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

def downgrade() -> None:
    for schema in [METADATA_SCHEMA, CORE_SCHEMA, STAGING_SCHEMA]:
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")