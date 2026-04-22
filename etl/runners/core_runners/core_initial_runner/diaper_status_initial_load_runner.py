from etl.transform_load.abstract_models.core_job_runner_interface import CoreExtractRunnerTemplate
from etl.sql.sql_loader import load_sql


class DiaperStatusCoreInitialExtractRunner(CoreExtractRunnerTemplate):

    def pipeline_stage(self) -> str:
        return 'transform_load'

    def source_type(self) -> str:
        return 'db'

    def source_path(self) -> str:
        return 'staging.stg_diaper'

    def destination_table_name(self) -> str:
        return 'dim_diaper_status'

    def load_type(self):
        return 'initial'

    def get_sql(self) -> str:
        return load_sql("core/initial/dimensions/dim_diaper_status_initial.sql")

    def get_sql_params(self, job_id: int) -> dict:
        return {
            'job_id': job_id
        }

