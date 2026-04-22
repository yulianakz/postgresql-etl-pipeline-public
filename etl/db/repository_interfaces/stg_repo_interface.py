from abc import ABC, abstractmethod
from datetime import datetime
from etl.extract.abstract_models.entity_interface import BaseEntity
from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity
from typing import Iterable


class StgRepositoryInterface(ABC):

    @abstractmethod
    def chunk_load(
            self,
            job_id: int,
            entity_type: type[BaseEntity],
            entities: Iterable[BaseEntity|BrokenEntity],
            chunk_size: int=1000
    ) -> int|None:
        pass

    @abstractmethod
    def get_job_max_watermark(
            self,
            entity_type: type[BaseEntity],
            job_id: int,
            watermark_column: str
    ) -> datetime | None:
        pass