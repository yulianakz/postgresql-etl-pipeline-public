from abc import ABC, abstractmethod
from etl.extract.abstract_models.entity_interface import BaseEntity
from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity
from typing import Iterable


class ExtractorInterface(ABC):

    @abstractmethod
    def extract(self) -> Iterable[BaseEntity|BrokenEntity]:
        pass