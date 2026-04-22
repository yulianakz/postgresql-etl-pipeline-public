from etl.extract.abstract_models.extractor_interface import ExtractorInterface
from etl.extract.abstract_models.stg_job_runner_interface import StagingExtractRunnerTemplate
from etl.extract.domain.entities.extract_entities import DiaperDataEntity
from etl.extract.services.extract_service import ExtractService
from etl.sql.sql_loader import load_sql

from typing import Iterable

from sqlalchemy import text

from etl.extract.domain.mappers.entities_mappers import DiaperDataEntityMapper


class DiaperStgFullExtractRunner(StagingExtractRunnerTemplate):

    def __init__(self, meta_repo, extractor_factory, stg_repo, auth_client, engine):
        super().__init__(meta_repo, extractor_factory, stg_repo, engine)
        self.auth_client = auth_client

    def _extracting(self, job_id: int) -> int:
        self.auth_client.login()
        total_rows = 0

        for baby_id in self._get_baby_ids():
            extractor = self.build_diaper_api_extractor(baby_id)
            service = ExtractService(self.stg_repo, job_id)
            total_rows += service.extractor_run(job_id, extractor, self.entity_type())

        return total_rows

    def _get_baby_ids(self) -> Iterable[int]:
        stmt = text(load_sql("stg/initial/baby_list_per_diaper_initial.sql"))
        with self.engine.connect() as conn:
            return list(conn.execute(stmt).scalars())

    def build_diaper_api_extractor(self, baby_id: int) -> ExtractorInterface:
        base = self.auth_client.base_url.rstrip("/") + "/"

        def map_diaper_row(row):
            return DiaperDataEntityMapper.api_diaper_mapper(row, baby_id=baby_id)

        map_diaper_row.__name__ = "api_diaper_mapper"

        return self.extractor_factory.get_extractor(
            source_type="api",
            base_url=base,
            endpoint=f"baby/{baby_id}/diaper",
            auth_client=self.auth_client,
            mapper=map_diaper_row,
        )

    def pipeline_stage(self) -> str:
        return 'extract'

    def source_type(self) -> str:
        return 'api'

    def source_path(self) -> str:
        return '/baby/{baby_id}/diaper'

    def entity_type(self):
        return DiaperDataEntity

    def destination_table_name(self) -> str:
        return 'stg_diaper'

    def mapper(self):
        return DiaperDataEntityMapper().api_diaper_mapper

    def load_type(self):
        return 'initial'

    def get_watermark(self):
        return None

    def watermark_column(self) -> str | None:
        return 'change_time'

    def build_extractor(self) -> ExtractorInterface:
        raise NotImplementedError(
            "Diaper runner uses build_diaper_extractor"
        )

