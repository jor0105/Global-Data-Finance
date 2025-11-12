import pytest

from src.brazil.dados_b3.historical_quotes.domain import ProcessingModeEnum
from src.brazil.dados_b3.historical_quotes.infra.extraction_service_factory import (
    ExtractionServiceFactory,
)


class DummyDependency:
    pass


def test_extraction_service_factory_creates_fast_service(monkeypatch):
    captured = {}

    class FakeService:
        def __init__(self, zip_reader, parser, data_writer, processing_mode):
            captured["zip_reader"] = zip_reader
            captured["parser"] = parser
            captured["data_writer"] = data_writer
            captured["processing_mode"] = processing_mode
            captured["instance"] = self

    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service_factory.ExtractionService",
        FakeService,
    )

    zip_reader = DummyDependency()
    parser = DummyDependency()
    writer = DummyDependency()

    result = ExtractionServiceFactory.create(
        zip_reader=zip_reader,
        parser=parser,
        data_writer=writer,
        processing_mode="FAST",
    )

    assert result is captured["instance"]
    assert captured["zip_reader"] is zip_reader
    assert captured["parser"] is parser
    assert captured["data_writer"] is writer
    assert captured["processing_mode"] == ProcessingModeEnum.FAST


def test_extraction_service_factory_creates_slow_service(monkeypatch):
    captured = {}

    class FakeService:
        def __init__(self, zip_reader, parser, data_writer, processing_mode):
            captured["processing_mode"] = processing_mode
            captured["instance"] = self

    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service_factory.ExtractionService",
        FakeService,
    )

    result = ExtractionServiceFactory.create(
        zip_reader=DummyDependency(),
        parser=DummyDependency(),
        data_writer=DummyDependency(),
        processing_mode="sLoW",
    )

    assert result is captured["instance"]
    assert captured["processing_mode"] == ProcessingModeEnum.SLOW


def test_extraction_service_factory_invalid_mode():
    with pytest.raises(ValueError) as exc_info:
        ExtractionServiceFactory.create(
            zip_reader=DummyDependency(),
            parser=DummyDependency(),
            data_writer=DummyDependency(),
            processing_mode="invalid",
        )

    assert "Invalid processing_mode" in str(exc_info.value)
    for allowed in ProcessingModeEnum:
        assert allowed.value in str(exc_info.value)
