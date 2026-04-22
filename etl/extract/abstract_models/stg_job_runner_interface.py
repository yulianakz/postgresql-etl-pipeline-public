from datetime import datetime
from abc import ABC, abstractmethod

from etl.extract.abstract_models.extractor_interface import ExtractorInterface
from etl.extract.services.extract_service import ExtractService

from airflow.exceptions import AirflowSkipException


class StagingExtractRunnerTemplate(ABC):

    def __init__(self, meta_repo, extractor_factory, stg_repo, engine):
        self.meta_repo = meta_repo
        self.extractor_factory = extractor_factory
        self.stg_repo = stg_repo
        self.engine = engine

    def extract_run(self, dag_id: str, task_id: str, logical_date: datetime) -> None:

        rows_loaded = 0
        last_loaded_event_ts_watermark = None
        job_id = None
        status = None
        error_message = None
        caught_exception = None
        _step = "init"

        try:

            _step = "dedup_check"
            self._check_duplicate_jobs(dag_id, task_id, logical_date)

            _step = "job_start"
            job_id = self._check_if_job_running(dag_id, task_id, logical_date)

            _step = "load_type_check"
            self._load_type_check()

            _step = "add_metadata"
            self.meta_repo.add_job_metadata(
                job_id = job_id,
                pipeline_stage=self.pipeline_stage(),
                data_source_type=self.source_type(),
                data_source_path=self.source_path(),
                destination_schema="staging",
                destination_table_name=self.destination_table_name()
            )

            _step = "extract"
            rows_loaded = self._extracting(job_id)

            _step = "watermark"
            watermark_column = self.watermark_column()
            if watermark_column is not None:
                last_loaded_event_ts_watermark = self.stg_repo.get_job_max_watermark(
                    entity_type=self.entity_type(),
                    job_id=job_id,
                    watermark_column=watermark_column
                )
            status = "success"

        except AirflowSkipException:
            raise
        except Exception as e:
            status = "failed"
            error_message = f"[step={_step}] {e}"
            caught_exception = e

        finally:
            if job_id is not None:
                self.meta_repo.finish_job(
                    job_id=job_id,
                    status=status,
                    rows_affected_count=rows_loaded,
                    rows_inserted_count=rows_loaded,
                    error_message=error_message,
                    last_loaded_event_ts_watermark=last_loaded_event_ts_watermark
                )

        if caught_exception is not None:
            raise caught_exception


    def _check_duplicate_jobs(self, dag_id: str, task_id: str, logical_date: datetime) -> bool|None:
        dedup_check = self.meta_repo.dedup_job_done(dag_id, task_id, logical_date)
        if dedup_check:
            raise AirflowSkipException(
                f"Job already succeeded for {dag_id}/{task_id}/{logical_date}"
            )

    def _check_if_job_running(self, dag_id: str, task_id: str, logical_date: datetime) -> int|None:
        job_id = self.meta_repo.find_running_job(dag_id, task_id, logical_date)
        if job_id is None:
            job_id = self.meta_repo.start_job(
                dag_id=dag_id,
                task_id=task_id,
                logical_date=logical_date
            )
        return job_id

    def _load_type_check(self):
        if self.load_type() == 'full_reload':
            self.stg_repo.do_truncate(self.entity_type())
        elif self.load_type() == 'incremental' and self.source_type() == 'csv':
            if self.meta_repo.is_file_loaded(self.source_path()):
                raise AirflowSkipException(
                    f"CSV file {self.source_path()} already loaded successfully"
                )
        elif self.load_type() == 'incremental' and self.source_type() == 'db':
            pass
        elif self.load_type() == 'initial':
            pass
        else:
            pass

    def _extracting(self, job_id: int) -> int:
        extractor = self.build_extractor()
        service = ExtractService(self.stg_repo, job_id)

        return service.extractor_run(job_id, extractor, self.entity_type())

    @abstractmethod
    def pipeline_stage(self) -> str:
        pass

    @abstractmethod
    def source_type(self) -> str:
        pass

    @abstractmethod
    def source_path(self) -> str:
        pass

    @abstractmethod
    def entity_type(self):
        pass

    @abstractmethod
    def destination_table_name(self) -> str:
        pass

    @abstractmethod
    def mapper(self):
        pass

    @abstractmethod
    def load_type(self):
        pass

    @abstractmethod
    def get_watermark(self):
        pass

    @abstractmethod
    def watermark_column(self) -> str | None:
        pass

    @abstractmethod
    def build_extractor(self) -> ExtractorInterface:
        pass

