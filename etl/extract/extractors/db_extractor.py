from etl.extract.abstract_models.entity_interface import BaseEntity
from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity
from etl.extract.abstract_models.extractor_interface import ExtractorInterface

from typing import Iterable, Callable
from sqlalchemy.engine import Engine
from sqlalchemy import text


class DbExtractor(ExtractorInterface):

    def __init__(self, engine:Engine, raw_sql: str, mapper: Callable, params: dict|None=None):
        self.engine = engine
        self.mapper = mapper
        self.raw_sql = raw_sql
        self.params = params or {}

    def extract(self) -> Iterable[BaseEntity|BrokenEntity]:

        stmt = text(self.raw_sql)

        with self.engine.connect() as conn:

            for row in conn.execution_options(stream_results=True).execute(stmt,self.params).mappings():
                try:
                    yield self.mapper(row)
                except Exception as e:
                    yield BrokenEntity(raw_row=dict(row), error_message=str(e), mapper_name=self.mapper.__name__)