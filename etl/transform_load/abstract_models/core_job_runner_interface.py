from datetime import datetime
from abc import ABC, abstractmethod
from airflow.exceptions import AirflowSkipException


class CoreExtractRunnerTemplate(ABC):

    def __init__(self, meta_repo, core_repo):
        self.meta_repo = meta_repo
        self.core_repo = core_repo

    def transform_load_run(self, dag_id: str, task_id: str, logical_date: datetime) -> None:

        rows_affected = 0
        rows_inserted = 0
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

            _step = "add_parent_job_id"
            parent_job_id = self._resolve_parent_job_id()

            _step = "add_metadata"
            self.meta_repo.add_job_metadata(
                job_id = job_id,
                parent_job_id=parent_job_id,
                pipeline_stage=self.pipeline_stage(),
                data_source_type=self.source_type(),
                data_source_path=self.source_path(),
                destination_schema="core",
                destination_table_name=self.destination_table_name()
            )

            _step = "transform_load"
            rows_affected = self._transform_load(job_id)
            rows_inserted_count = self.core_repo.count_rows_by_job_id(
                table_name=self.destination_table_name(),
                job_id=job_id
            )
            rows_inserted = (
                rows_inserted_count
                if rows_inserted_count is not None
                else rows_affected
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
                    rows_affected_count=rows_affected,
                    rows_inserted_count=rows_inserted,
                    error_message=error_message
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
        # Initial and full_reload both (re)load core from staging as a full replace for
        # this table; truncating makes Airflow task retries idempotent after a failed run.
        if self.load_type() in ('full_reload', 'initial'):
            self.core_repo.do_truncate(self.destination_table_name())

    def _resolve_parent_job_id(self) -> int | None:
        """ Latest successful staging extract for this table (no logical_date filter).
        Acceptable here because the DAG runs core only after staging succeeds, so
        under normal linear runs that row is this run's extract; clearing/replaying
        tasks out of order can still point parent_job_id at a different logical_date.  """

        if self.load_type() in ('initial', 'incremental'):
            return self.meta_repo.get_last_successful_job_id(
                destination_schema='staging',
                destination_table_name=self.source_path().split('.')[-1],
                pipeline_stage='extract'
            )
        return None

    def _transform_load(self, job_id) -> int | None:
        rows_affected = self.core_repo.raw_sql_load(
            raw_sql=self.get_sql(),
            params=self.get_sql_params(job_id)
        )
        return rows_affected if rows_affected else 0


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
    def destination_table_name(self) -> str:
        pass

    @abstractmethod
    def load_type(self):
        pass

    @abstractmethod
    def get_sql(self) -> str:
        pass

    @abstractmethod
    def get_sql_params(self, job_id: int) -> dict|None:
        pass

