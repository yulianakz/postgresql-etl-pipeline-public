from etl.db.repository_interfaces.stg_repo_interface import StgRepositoryInterface
from etl.extract.abstract_models.extractor_interface import ExtractorInterface
from etl.extract.abstract_models.entity_interface import BaseEntity


class ExtractService:

    def __init__(self, repo: StgRepositoryInterface, job_id: int):
        self.repo = repo
        self.job_id = job_id

    def extractor_run(self, job_id: int, extractor: ExtractorInterface, entity_type: type[BaseEntity]) -> int|None:

        entities = extractor.extract()
        return self.repo.chunk_load(job_id, entity_type, entities)