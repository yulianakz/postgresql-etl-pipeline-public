from etl.extract.abstract_models.extractor_interface import ExtractorInterface
from etl.extract.abstract_models.entity_interface import BaseEntity
from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity


from typing import Iterable, Callable
import csv


class CsvExtractor(ExtractorInterface):

    def __init__(self, file_path: str, mapper: Callable):
        self.file_path = file_path
        self.mapper = mapper

    def extract(self) -> Iterable[BaseEntity|BrokenEntity]:

        with open(self.file_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    yield self.mapper(row)
                except Exception as e:
                    yield BrokenEntity(raw_row=dict(row), error_message=str(e), mapper_name=self.mapper.__name__)
