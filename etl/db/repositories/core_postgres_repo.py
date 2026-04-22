from etl.db.repository_interfaces.core_repo_interface import CoreRepositoryInterface
from etl.db.tables.core_tables import (
    dim_baby,
    dim_date,
    dim_diaper_status,
    dim_time,
    fact_diaper,
    fact_formula_feed,
    fact_sleep,
)
from sqlalchemy.engine import Engine
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
import sqlparse


class CorePostgresRepository(CoreRepositoryInterface):
    TABLE_MAPPING = {
        'dim_baby': dim_baby,
        'dim_date': dim_date,
        'dim_time': dim_time,
        'dim_diaper_status': dim_diaper_status,
        'fact_sleep': fact_sleep,
        'fact_diaper': fact_diaper,
        'fact_formula_feed': fact_formula_feed
    }

    def __init__(self, engine: Engine):
        self.engine = engine

    def _get_table(self, table_name: str):

        table = self.TABLE_MAPPING.get(table_name)
        if table is None:
            raise ValueError(f"No table for {table_name}")
        return table

    def do_truncate(self,table_name) -> None:

        table = self._get_table(table_name)
        full_table_name = f"{table.schema}.{table.name}"

        with self.engine.begin() as conn:
            stmt = text(f'TRUNCATE TABLE {full_table_name}')
            conn.execute(stmt)

    def raw_sql_load(
            self,
            raw_sql: str,
            params: dict|None=None
    ) -> int | None:
        """Run a script of one or more SQL statements in one transaction.

        Statements are split with ``sqlparse.split`` (not naive ``;`` splitting),
        so semicolons inside strings, comments, or dollar-quoted blocks are
        less likely to break the script. Each non-empty chunk is executed in
        order; positive ``rowcount`` values are summed for the return value.
        """

        params = params or {}
        total_rowcount = 0

        statements = [s.strip() for s in sqlparse.split(raw_sql) if s.strip()]

        with self.engine.begin() as conn:
            for statement in statements:
                result = conn.execute(text(statement), params)
                if result.rowcount and result.rowcount > 0:
                    total_rowcount += result.rowcount

        return total_rowcount

    def count_rows_by_job_id(
            self,
            table_name: str,
            job_id: int
    ) -> int | None:
        table = self._get_table(table_name)
        full_table_name = f"{table.schema}.{table.name}"

        stmt = text(
            f"SELECT COUNT(*) FROM {full_table_name} WHERE job_id = :job_id"
        )

        with self.engine.begin() as conn:
            try:
                return conn.execute(stmt, {"job_id": job_id}).scalar_one()
            except ProgrammingError:
                return None
