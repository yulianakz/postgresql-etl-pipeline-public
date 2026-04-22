from etl.extract.abstract_models.extractor_interface import ExtractorInterface
from etl.extract.extractors.api_extractor import ApiExtractor
from etl.extract.extractors.db_extractor import DbExtractor
from etl.extract.extractors.csv_extractor import CsvExtractor


class ExtractorFactory:

    extractor_map = {
        "csv": CsvExtractor,
        "api": ApiExtractor,
        "db": DbExtractor,
    }

    def get_extractor(self, source_type: str, **kwargs) -> ExtractorInterface:

        extractor_cls = self.extractor_map.get(source_type.lower())

        if not extractor_cls:
            raise ValueError(f"Unsupported source type: {source_type}")

        return extractor_cls(**kwargs)