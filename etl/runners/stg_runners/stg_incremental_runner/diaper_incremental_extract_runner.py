from etl.extract.abstract_models.extractor_interface import ExtractorInterface
from etl.extract.abstract_models.stg_job_runner_interface import StagingExtractRunnerTemplate
from etl.extract.domain.entities.extract_entities import DiaperDataEntity
from etl.extract.domain.mappers.entities_mappers import DiaperDataEntityMapper
from etl.sql.sql_loader import load_sql

class DiaperStgIncrementalExtractRunner(StagingExtractRunnerTemplate):

    def pipeline_stage(self) -> str:
        return 'extract'

    def source_type(self) -> str:
        return 'db'

    def source_path(self) -> str:
        return 'public.diaper_data'

    def entity_type(self):
        return DiaperDataEntity

    def destination_table_name(self) -> str:
        return 'stg_diaper'

    def mapper(self):
        return DiaperDataEntityMapper().db_diaper_mapper

    def load_type(self):
        return 'incremental'

    def get_watermark(self):
        return self.meta_repo.get_last_successful_watermark(
            destination_schema='staging',
            destination_table_name=self.destination_table_name(),
            pipeline_stage=self.pipeline_stage()
        )

    def watermark_column(self) -> str | None:
        return 'change_time'

    def build_extractor(self) -> ExtractorInterface:
        raw_sql = load_sql('stg/incremental/diaper_incremental.sql')
        watermark_ts = self.get_watermark()

        return self.extractor_factory.get_extractor(
            source_type=self.source_type(),
            mapper=self.mapper(),
            raw_sql=raw_sql,
            engine=self.engine,
            params={'watermark_ts': watermark_ts}
        )