from abc import ABC

import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data import (
    FileExtractorRepositoryCVM,
)


@pytest.mark.unit
class TestFileExtractorInterface:
    def test_is_abstract_base_class(self):
        assert issubclass(FileExtractorRepositoryCVM, ABC)

    def test_has_extract_method(self):
        assert hasattr(FileExtractorRepositoryCVM, "extract")

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            FileExtractorRepositoryCVM()

    def test_extract_is_abstract_method(self):
        assert hasattr(FileExtractorRepositoryCVM.extract, "__isabstractmethod__")
        assert FileExtractorRepositoryCVM.extract.__isabstractmethod__


@pytest.mark.unit
class TestFileExtractorContract:
    def test_concrete_implementation_must_implement_extract(self):
        class IncompleteExtractor(FileExtractorRepositoryCVM):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteExtractor()

    def test_concrete_implementation_with_extract_works(self):
        class CompleteExtractor(FileExtractorRepositoryCVM):
            def extract(self, source_path: str, destination_path: str) -> None:
                pass

        extractor = CompleteExtractor()
        assert isinstance(extractor, FileExtractorRepositoryCVM)
        assert callable(extractor.extract)

    def test_extract_method_signature_in_concrete_class(self):
        class ConcreteExtractor(FileExtractorRepositoryCVM):
            def extract(self, source_path: str, destination_path: str) -> None:
                return None

        extractor = ConcreteExtractor()
        assert extractor.extract.__code__.co_argcount == 3


@pytest.mark.unit
class TestFileExtractorDocumentation:
    def test_class_has_docstring(self):
        assert FileExtractorRepositoryCVM.__doc__ is not None
        assert len(FileExtractorRepositoryCVM.__doc__) > 0

    def test_extract_method_has_docstring(self):
        assert FileExtractorRepositoryCVM.extract.__doc__ is not None
        assert len(FileExtractorRepositoryCVM.extract.__doc__) > 0

    def test_docstring_mentions_extraction(self):
        doc = FileExtractorRepositoryCVM.__doc__
        assert "extract" in doc.lower() or "extraction" in doc.lower()

    def test_extract_docstring_mentions_parameters(self):
        doc = FileExtractorRepositoryCVM.extract.__doc__
        assert "source" in doc.lower() or "path" in doc.lower()
        assert "destination" in doc.lower() or "dest" in doc.lower()


@pytest.mark.unit
class TestFileExtractorConcreteImplementations:
    def test_simple_concrete_extractor(self):
        class SimpleExtractor(FileExtractorRepositoryCVM):
            def __init__(self):
                self.extracted_files = []

            def extract(self, source_path: str, destination_path: str) -> None:
                self.extracted_files.append((source_path, destination_path))

        extractor = SimpleExtractor()
        extractor.extract("/source/file.zip", "/dest/dir")

        assert len(extractor.extracted_files) == 1
        assert extractor.extracted_files[0] == ("/source/file.zip", "/dest/dir")

    def test_extractor_with_custom_logic(self):
        class CustomExtractor(FileExtractorRepositoryCVM):
            def __init__(self):
                self.call_count = 0

            def extract(self, source_path: str, destination_path: str) -> None:
                self.call_count += 1
                if not source_path:
                    raise ValueError("Source path cannot be empty")

        extractor = CustomExtractor()

        extractor.extract("/file.zip", "/dest")
        assert extractor.call_count == 1

        with pytest.raises(ValueError):
            extractor.extract("", "/dest")

        assert extractor.call_count == 2

    def test_extractor_can_raise_exceptions(self):
        class FailingExtractor(FileExtractorRepositoryCVM):
            def extract(self, source_path: str, destination_path: str) -> None:
                raise RuntimeError("Extraction failed")

        extractor = FailingExtractor()

        with pytest.raises(RuntimeError, match="Extraction failed"):
            extractor.extract("/file.zip", "/dest")


@pytest.mark.unit
class TestFileExtractorPolymorphism:
    def test_can_use_extractor_polymorphically(self):
        class ExtractorA(FileExtractorRepositoryCVM):
            def extract(self, source_path: str, destination_path: str) -> None:
                return None

        class ExtractorB(FileExtractorRepositoryCVM):
            def extract(self, source_path: str, destination_path: str) -> None:
                return None

        extractors = [ExtractorA(), ExtractorB()]

        for extractor in extractors:
            assert isinstance(extractor, FileExtractorRepositoryCVM)
            extractor.extract("/file.zip", "/dest")

    def test_dependency_injection_with_interface(self):
        class MockExtractor(FileExtractorRepositoryCVM):
            def __init__(self):
                self.extracted = False

            def extract(self, source_path: str, destination_path: str) -> None:
                self.extracted = True

        def process_files(extractor: FileExtractorRepositoryCVM, files: list):
            for file in files:
                extractor.extract(file, "/dest")

        mock = MockExtractor()
        process_files(mock, ["/file1.zip", "/file2.zip"])

        assert mock.extracted is True


@pytest.mark.unit
class TestFileExtractorMethodContract:
    def test_extract_returns_none(self):
        class NoneReturningExtractor(FileExtractorRepositoryCVM):
            def extract(self, source_path: str, destination_path: str) -> None:
                return None

        extractor = NoneReturningExtractor()
        result = extractor.extract("/file.zip", "/dest")

        assert result is None

    def test_extract_accepts_string_parameters(self):
        class TypeCheckingExtractor(FileExtractorRepositoryCVM):
            def extract(self, source_path: str, destination_path: str) -> None:
                assert isinstance(source_path, str)
                assert isinstance(destination_path, str)

        extractor = TypeCheckingExtractor()
        extractor.extract("/file.zip", "/dest")


@pytest.mark.unit
class TestFileExtractorMultipleInheritance:
    def test_can_inherit_from_multiple_classes(self):
        class LoggingMixin:
            def log(self, message: str):
                pass

        class LoggingExtractor(LoggingMixin, FileExtractorRepositoryCVM):
            def extract(self, source_path: str, destination_path: str) -> None:
                self.log(f"Extracting {source_path}")

        extractor = LoggingExtractor()
        assert isinstance(extractor, FileExtractorRepositoryCVM)
        assert isinstance(extractor, LoggingMixin)
        assert hasattr(extractor, "extract")
        assert hasattr(extractor, "log")


@pytest.mark.unit
class TestFileExtractorInstanceChecks:
    def test_isinstance_check_works(self):
        class ConcreteExtractor(FileExtractorRepositoryCVM):
            def extract(self, source_path: str, destination_path: str) -> None:
                pass

        extractor = ConcreteExtractor()
        assert isinstance(extractor, FileExtractorRepositoryCVM)

    def test_issubclass_check_works(self):
        class ConcreteExtractor(FileExtractorRepositoryCVM):
            def extract(self, source_path: str, destination_path: str) -> None:
                pass

        assert issubclass(ConcreteExtractor, FileExtractorRepositoryCVM)

    def test_non_extractor_not_instance(self):
        class NotAnExtractor:
            def extract(self, source_path: str, destination_path: str) -> None:
                pass

        obj = NotAnExtractor()
        assert not isinstance(obj, FileExtractorRepositoryCVM)
