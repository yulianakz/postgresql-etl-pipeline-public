from etl.extract.abstract_models.entity_interface import BaseEntity
from etl.db.repository_interfaces.stg_repo_interface import StgRepositoryInterface
from etl.db.tables.staging_tables import stg_baby,stg_formula,stg_diaper,stg_sleep
from etl.extract.domain.entities.extract_entities import BabyDataEntity, DiaperDataEntity, SleepDataEntity, FormulaDataEntity
from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity, log_bad_row

from typing import Iterable
from datetime import datetime
from dataclasses import asdict

from sqlalchemy.engine import Engine
from sqlalchemy import insert, text, select, func

import pendulum


class StgPostgresRepository(StgRepositoryInterface):

    TABLE_MAPPING = {
        BabyDataEntity: stg_baby,
        DiaperDataEntity: stg_diaper,
        FormulaDataEntity: stg_formula,
        SleepDataEntity: stg_sleep,
    }

    def __init__(self, engine: Engine):
        self.engine = engine

    def _get_table(self, entity_type: type[BaseEntity]):
        table = self.TABLE_MAPPING.get(entity_type)
        if table is None:
            raise ValueError(f"No table for {entity_type}")

        return table

    def do_truncate(self,entity_type):
        table = self._get_table(entity_type)
        full_table_name = f"{table.schema}.{table.name}"

        with self.engine.begin() as conn:
            stmt = text(f'TRUNCATE TABLE {full_table_name}')
            conn.execute(stmt)

    def chunk_load(
            self,
            job_id: int,
            entity_type: type[BaseEntity],
            entities: Iterable[BaseEntity|BrokenEntity],
            chunk_size: int = 1000
    ) -> int:
        """Bulk-insert entities in chunks. ``loaded_at`` is one timestamp per flush (chunk), not per row."""
        rows_loaded = 0
        chunk = []
        table = self._get_table(entity_type)
        chunk_loaded_at = pendulum.now('UTC')

        with self.engine.begin() as conn:

            for e in entities:

                if e is None:
                    continue

                if isinstance(e, BrokenEntity):
                    log_bad_row(
                        row=e.raw_row,
                        error_message=e.error_message,
                        job_id=job_id,
                        mapper_name=e.mapper_name
                    )
                    continue

                e.job_id = job_id
                e.loaded_at = chunk_loaded_at

                chunk.append(asdict(e))
                rows_loaded += 1

                if len(chunk) >= chunk_size:
                    conn.execute(insert(table), chunk)
                    chunk.clear()

                    chunk_loaded_at = pendulum.now('UTC')

            if chunk:
                conn.execute(insert(table), chunk)

        return rows_loaded

    def get_job_max_watermark(
            self,
            entity_type: type[BaseEntity],
            job_id: int,
            watermark_column: str
    ) -> datetime | None:

        table = self._get_table(entity_type)
        column = table.c.get(watermark_column)

        if column is None:
            raise ValueError(f"Unknown watermark column '{watermark_column}' for table {table.name}")

        stmt = (
            select(func.max(column))
            .where(table.c.job_id == job_id)
        )

        with self.engine.begin() as conn:
            return conn.execute(stmt).scalar_one_or_none()



