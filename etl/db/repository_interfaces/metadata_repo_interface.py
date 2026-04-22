from abc import ABC, abstractmethod
from datetime import datetime


class MetadataRepositoryInterface(ABC):

    @abstractmethod
    def start_job(
            self,
            dag_id: str,
            task_id: str,
            logical_date: datetime
    ) -> int:
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def finish_job(
            self,
            job_id: int,
            status: str,
            rows_affected_count: int | None = None,
            rows_inserted_count: int | None = None,
            error_message: str | None = None,
            last_loaded_event_ts_watermark: datetime | None = None,
    ) -> None:
        pass

    @abstractmethod
    def dedup_job_done(
            self,
            dag_id: str,
            task_id: str,
            logical_date: datetime,
            status: str='success'
    ) -> bool:
        pass

    @abstractmethod
    def find_running_job(
            self,
            dag_id: str,
            task_id: str,
            logical_date: datetime,
            status: str = 'running'
    ) -> int:
        pass

    @abstractmethod
    def is_file_loaded(
            self,
            file_path: str,
            status: str = 'success'
    ) -> bool:
        pass

    @abstractmethod
    def get_last_successful_job_id(
            self,
            destination_schema: str,
            destination_table_name: str,
            pipeline_stage: str
    ) -> int | None:
        pass

    @abstractmethod
    def get_last_successful_watermark(
            self,
            destination_schema: str,
            destination_table_name: str,
            pipeline_stage: str
    ) -> datetime | None:
        pass


