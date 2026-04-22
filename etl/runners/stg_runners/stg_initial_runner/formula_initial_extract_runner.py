from etl.extract.abstract_models.extractor_interface import ExtractorInterface
from etl.extract.abstract_models.stg_job_runner_interface import StagingExtractRunnerTemplate
from etl.extract.domain.entities.extract_entities import FormulaDataEntity
from etl.extract.domain.mappers.entities_mappers import FormulaDataEntityMapper

import os

class FormulaStgFullExtractRunner(StagingExtractRunnerTemplate):

    def pipeline_stage(self) -> str:
        return 'extract'

    def source_type(self) -> str:
        return 'csv'

    def source_path(self) -> str:
        base_dir = os.getenv("DATA_FILES_DIR", "etl/data_files/")
        return os.path.join(base_dir, "formula_data_to_stg_test.csv")

    def entity_type(self):
        return FormulaDataEntity

    def destination_table_name(self) -> str:
        return 'stg_formula'

    def mapper(self):
        return FormulaDataEntityMapper().csv_formula_mapper

    def load_type(self):
        return 'initial'

    def get_watermark(self):
        return None

    def watermark_column(self) -> str | None:
        return 'feed_time'

    def build_extractor(self) -> ExtractorInterface:
        return self.extractor_factory.get_extractor(
            source_type=self.source_type(),
            mapper=self.mapper(),
            file_path=self.source_path()
        )

