from etl.extract.abstract_models.extractor_interface import ExtractorInterface
from etl.extract.abstract_models.stg_job_runner_interface import StagingExtractRunnerTemplate
from etl.extract.domain.entities.extract_entities import SleepDataEntity
from etl.extract.domain.mappers.entities_mappers import SleepDataEntityMapper
from etl.sql.sql_loader import load_sql


class SleepStgFullExtractRunner(StagingExtractRunnerTemplate):

    def pipeline_stage(self) -> str:
        return 'extract'

    def source_type(self) -> str:
        return 'db'

    def source_path(self) -> str:
        return 'public.sleep_data'

    def entity_type(self):
        return SleepDataEntity

    def destination_table_name(self) -> str:
        return 'stg_sleep'

    def mapper(self):
        return SleepDataEntityMapper().db_sleep_mapper

    def load_type(self):
        return 'initial'

    def get_watermark(self):
        return None

    def watermark_column(self) -> str | None:
        return 'sleep_start'

    def build_extractor(self) -> ExtractorInterface:
        raw_sql = load_sql('stg/initial/sleep_initial.sql')

        return self.extractor_factory.get_extractor(
            source_type=self.source_type(),
            mapper=self.mapper(),
            raw_sql = raw_sql,
            engine=self.engine
        )