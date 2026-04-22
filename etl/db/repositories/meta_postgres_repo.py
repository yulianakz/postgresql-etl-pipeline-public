from etl.db.repository_interfaces.metadata_repo_interface import MetadataRepositoryInterface
from etl.db.tables.metadata_tables import etl_job

from sqlalchemy.engine import Engine
from sqlalchemy import insert, update, select, and_, exists

from datetime import datetime, timezone


class MetadataPostgresRepository(MetadataRepositoryInterface):

    METADATA_TABLE = etl_job

    def __init__(self, engine:Engine):
        self.engine = engine

    def start_job(
            self,
            dag_id: str,
            task_id: str,
            logical_date: datetime
    ) -> int:

        stmt = (
            insert(self.METADATA_TABLE)
            .values(
                dag_id=dag_id,
                task_id=task_id,
                logical_date=logical_date,
                status='running'
            )
            .returning(self.METADATA_TABLE.c.job_id)
        )

        with self.engine.begin() as conn:
            return conn.execute(stmt).scalar_one()


    def add_job_metadata(
            self,
            job_id: int,
            pipeline_stage: str,
            data_source_type: str,
            data_source_path: str,
            destination_schema: str,
            destination_table_name: str,
            parent_job_id: int | None = None,
    ) -> None:

        stmt = (
            update(self.METADATA_TABLE)
            .where(self.METADATA_TABLE.c.job_id == job_id)
            .values(
                pipeline_stage=pipeline_stage,
                data_source_type=data_source_type,
                data_source_path=data_source_path,
                destination_schema=destination_schema,
                destination_table_name=destination_table_name,
                parent_job_id=parent_job_id,
                started_at=datetime.now(timezone.utc),
                ended_at = None,
                error_message = None,
                rows_affected_count = None,
                rows_inserted_count = None
            )
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)


    def finish_job(
            self,
            job_id: int,
            status: str,
            rows_affected_count: int | None = None,
            rows_inserted_count: int | None = None,
            error_message: str | None = None,
            last_loaded_event_ts_watermark: datetime | None = None,
    ) -> None:

        if status not in {"success", "failed"}:
            raise ValueError(f"Invalid status: {status}")

        stmt = (
            update(self.METADATA_TABLE)
            .where(self.METADATA_TABLE.c.job_id == job_id)
            .values(
                status=status,
                ended_at=datetime.now(timezone.utc),
                rows_affected_count=rows_affected_count,
                rows_inserted_count=rows_inserted_count,
                error_message=error_message,
                last_loaded_event_ts_watermark=last_loaded_event_ts_watermark,
            )
        )

        with self.engine.begin() as conn:
            result = conn.execute(stmt)

            rows_affected = result.rowcount
            if rows_affected == 0:
                raise RuntimeError("finish_job called before start_job")


    def dedup_job_done(
            self,
            dag_id: str,
            task_id: str,
            logical_date: datetime,
            status: str = 'success'
    ) -> bool:

        inner_stmt = (
            select(1)
            .select_from(self.METADATA_TABLE)
            .where(and_(
                self.METADATA_TABLE.c.dag_id == dag_id,
                self.METADATA_TABLE.c.task_id == task_id,
                self.METADATA_TABLE.c.logical_date == logical_date,
                self.METADATA_TABLE.c.status == status
            ))
        )
        stmt = select(exists(inner_stmt))

        with self.engine.begin() as conn:
            return conn.execute(stmt).scalar()


    def find_running_job(
            self,
            dag_id: str,
            task_id: str,
            logical_date: datetime,
            status: str = 'running'
    ) -> int:

        stmt = (
            select(self.METADATA_TABLE.c.job_id)
            .where(and_(
                self.METADATA_TABLE.c.dag_id == dag_id,
                self.METADATA_TABLE.c.task_id == task_id,
                self.METADATA_TABLE.c.logical_date == logical_date,
                self.METADATA_TABLE.c.status == 'running'
            ))
            .order_by(self.METADATA_TABLE.c.job_id.desc())
            .limit(1)
        )

        with self.engine.begin() as conn:
            return conn.execute(stmt).scalar_one_or_none()


    def is_file_loaded(
            self,
            file_path: str,
            status: str = 'success'
    ) -> bool:

        inner_stmt = (
            select(1)
            .select_from(self.METADATA_TABLE)
            .where(and_(
                self.METADATA_TABLE.c.data_source_path == file_path,
                self.METADATA_TABLE.c.status == status
            ))
        )
        stmt = select(exists(inner_stmt))

        with self.engine.begin() as conn:
            return conn.execute(stmt).scalar()


    def get_last_successful_job_id(
            self,
            destination_schema: str,
            destination_table_name: str,
            pipeline_stage: str
    ) -> int | None:

        stmt = (
            select(self.METADATA_TABLE.c.job_id)
            .where(and_(
                self.METADATA_TABLE.c.destination_schema == destination_schema,
                self.METADATA_TABLE.c.destination_table_name == destination_table_name,
                self.METADATA_TABLE.c.pipeline_stage == pipeline_stage,
                self.METADATA_TABLE.c.status == 'success'
            ))
            .order_by(self.METADATA_TABLE.c.ended_at.desc())
            .limit(1)
        )

        with self.engine.begin() as conn:
            return conn.execute(stmt).scalar_one_or_none()

    def get_last_successful_watermark(
            self,
            destination_schema: str,
            destination_table_name: str,
            pipeline_stage: str
    ) -> datetime | None:
        stmt = (
            select(self.METADATA_TABLE.c.last_loaded_event_ts_watermark)
            .where(and_(
                self.METADATA_TABLE.c.destination_schema == destination_schema,
                self.METADATA_TABLE.c.destination_table_name == destination_table_name,
                self.METADATA_TABLE.c.pipeline_stage == pipeline_stage,
                self.METADATA_TABLE.c.status == 'success'
            ))
            .order_by(self.METADATA_TABLE.c.ended_at.desc())
            .limit(1)
        )

        with self.engine.begin() as conn:
            return conn.execute(stmt).scalar_one_or_none()


