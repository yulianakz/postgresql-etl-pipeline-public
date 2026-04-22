from etl.extract.abstract_models.extractor_interface import ExtractorInterface
from etl.extract.abstract_models.entity_interface import BaseEntity
from etl.extract.domain.mappers.broken_rows_logger import BrokenEntity
from etl.extract.services.auth_client import ApiAuthClient

from typing import Iterable, Callable
import requests
import ijson


class ApiExtractor(ExtractorInterface):

    def __init__(self, base_url: str, endpoint: str, auth_client: ApiAuthClient, mapper: Callable, params: dict|None=None, headers: dict|None=None):
        self.base_url = base_url
        self.endpoint = endpoint
        self.auth = auth_client
        self.mapper = mapper
        self.params = params or {}
        self.extra_headers = headers or {}

    def extract(self) -> Iterable[BaseEntity|BrokenEntity]:

        url = f"{self.base_url}{self.endpoint}"

        all_headers = {
            **self.auth.headers,
            **self.extra_headers
        }

        response = requests.get(
            url,
            headers=all_headers,
            params=self.params,
            stream=True)

        response.raise_for_status()

        items = ijson.items(response.raw, 'item')

        for item in items:
            try:
                yield self.mapper(item)
            except Exception as e:
                yield BrokenEntity(raw_row=dict(item), error_message=str(e), mapper_name=self.mapper.__name__)

