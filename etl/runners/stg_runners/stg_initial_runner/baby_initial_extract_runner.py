from etl.extract.abstract_models.extractor_interface import ExtractorInterface
from etl.extract.abstract_models.stg_job_runner_interface import StagingExtractRunnerTemplate
from etl.extract.domain.entities.extract_entities import BabyDataEntity
from etl.extract.domain.mappers.entities_mappers import BabyDataEntityMapper
from etl.sql.sql_loader import load_sql


class BabyStgFullExtractRunner(StagingExtractRunnerTemplate):

    def pipeline_stage(self) -> str:
        return 'extract'

    def source_type(self) -> str:
        return 'db'

    def source_path(self) -> str:
        return 'public.baby_info'

    def entity_type(self):
        return BabyDataEntity

    def destination_table_name(self) -> str:
        return 'stg_baby'

    def mapper(self):
        return BabyDataEntityMapper().db_baby_mapper

    def load_type(self):
        return 'initial'

    def get_watermark(self):
        return None

    def watermark_column(self) -> str | None:
        return None

    def build_extractor(self) -> ExtractorInterface:
        raw_sql = load_sql("stg/initial/baby_initial.sql")

        return self.extractor_factory.get_extractor(
            source_type=self.source_type(),
            mapper=self.mapper(),
            raw_sql=raw_sql,
            engine=self.engine
        )

