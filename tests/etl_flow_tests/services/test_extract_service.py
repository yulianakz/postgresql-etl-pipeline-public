"""Unit tests for :class:`etl.extract.services.extract_service.ExtractService`."""

from etl.extract.domain.entities.extract_entities import BabyDataEntity
from etl.extract.services.extract_service import ExtractService


class _FakeExtractor:
    def __init__(self, rows):
        self._rows = rows
        self.extract_called = False

    def extract(self):
        self.extract_called = True
        yield from self._rows


class _FakeRepo:
    def __init__(self, rows_loaded: int = 3):
        self.rows_loaded = rows_loaded
        self.called_with = None

    def chunk_load(self, job_id, entity_type, entities):
        self.called_with = (job_id, entity_type, list(entities))
        return self.rows_loaded


def test_extractor_run_delegates_to_repo():
    repo = _FakeRepo(rows_loaded=7)
    extractor = _FakeExtractor(rows=[BabyDataEntity(source_id=1, name="Adi", timezone="UTC")])
    service = ExtractService(repo=repo, job_id=42)

    result = service.extractor_run(
        job_id=42, extractor=extractor, entity_type=BabyDataEntity
    )

    assert result == 7
    assert repo.called_with[0] == 42
    assert repo.called_with[1] is BabyDataEntity
    assert len(repo.called_with[2]) == 1
    assert extractor.extract_called is True


def test_extractor_run_forwards_empty_stream():
    repo = _FakeRepo(rows_loaded=0)
    service = ExtractService(repo=repo, job_id=1)
    result = service.extractor_run(1, _FakeExtractor(rows=[]), BabyDataEntity)
    assert result == 0
    assert repo.called_with[2] == []
