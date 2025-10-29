from abc import ABC

import pytest

from src.brazil.cvm.fundamental_stocks_data.application.interfaces import (
    FileExtractorRepository,
)


@pytest.mark.unit
class TestFileExtractorInterface:
    def test_is_abstract_base_class(self):
        assert issubclass(FileExtractorRepository, ABC)

    def test_has_extract_method(self):
        assert hasattr(FileExtractorRepository, "extract")

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            FileExtractorRepository()

    def test_extract_is_abstract_method(self):
        # Verify that extract is indeed abstract
        assert hasattr(FileExtractorRepository.extract, "__isabstractmethod__")
        assert FileExtractorRepository.extract.__isabstractmethod__


@pytest.mark.unit
class TestFileExtractorContract:
    def test_concrete_implementation_must_implement_extract(self):
        # Create incomplete implementation
        class IncompleteExtractor(FileExtractorRepository):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteExtractor()

    def test_concrete_implementation_with_extract_works(self):
        # Create complete implementation
        class CompleteExtractor(FileExtractorRepository):
            def extract(self, source_path: str, destination_dir: str) -> None:
                pass

        extractor = CompleteExtractor()
        assert isinstance(extractor, FileExtractorRepository)
        assert callable(extractor.extract)

    def test_extract_method_signature_in_concrete_class(self):
        class ConcreteExtractor(FileExtractorRepository):
            def extract(self, source_path: str, destination_dir: str) -> None:
                return None

        extractor = ConcreteExtractor()
        # Should accept exactly 2 parameters (plus self)
        assert extractor.extract.__code__.co_argcount == 3


@pytest.mark.unit
class TestFileExtractorDocumentation:
    def test_class_has_docstring(self):
        assert FileExtractorRepository.__doc__ is not None
        assert len(FileExtractorRepository.__doc__) > 0

    def test_extract_method_has_docstring(self):
        assert FileExtractorRepository.extract.__doc__ is not None
        assert len(FileExtractorRepository.extract.__doc__) > 0

    def test_docstring_mentions_extraction(self):
        doc = FileExtractorRepository.__doc__
        assert "extract" in doc.lower() or "extraction" in doc.lower()

    def test_extract_docstring_mentions_parameters(self):
        doc = FileExtractorRepository.extract.__doc__
        assert "source" in doc.lower() or "path" in doc.lower()
        assert "destination" in doc.lower() or "dest" in doc.lower()


@pytest.mark.unit
class TestFileExtractorConcreteImplementations:
    def test_simple_concrete_extractor(self):
        class SimpleExtractor(FileExtractorRepository):
            def __init__(self):
                self.extracted_files = []

            def extract(self, source_path: str, destination_dir: str) -> None:
                self.extracted_files.append((source_path, destination_dir))

        extractor = SimpleExtractor()
        extractor.extract("/source/file.zip", "/dest/dir")

        assert len(extractor.extracted_files) == 1
        assert extractor.extracted_files[0] == ("/source/file.zip", "/dest/dir")

    def test_extractor_with_custom_logic(self):
        class CustomExtractor(FileExtractorRepository):
            def __init__(self):
                self.call_count = 0

            def extract(self, source_path: str, destination_dir: str) -> None:
                self.call_count += 1
                # Custom logic here
                if not source_path:
                    raise ValueError("Source path cannot be empty")

        extractor = CustomExtractor()

        extractor.extract("/file.zip", "/dest")
        assert extractor.call_count == 1

        with pytest.raises(ValueError):
            extractor.extract("", "/dest")

        assert extractor.call_count == 2

    def test_extractor_can_raise_exceptions(self):
        class FailingExtractor(FileExtractorRepository):
            def extract(self, source_path: str, destination_dir: str) -> None:
                raise RuntimeError("Extraction failed")

        extractor = FailingExtractor()

        with pytest.raises(RuntimeError, match="Extraction failed"):
            extractor.extract("/file.zip", "/dest")


@pytest.mark.unit
class TestFileExtractorPolymorphism:
    def test_can_use_extractor_polymorphically(self):
        class ExtractorA(FileExtractorRepository):
            def extract(self, source_path: str, destination_dir: str) -> None:
                return None

        class ExtractorB(FileExtractorRepository):
            def extract(self, source_path: str, destination_dir: str) -> None:
                return None

        extractors = [ExtractorA(), ExtractorB()]

        for extractor in extractors:
            assert isinstance(extractor, FileExtractorRepository)
            # Should be able to call extract on all
            extractor.extract("/file.zip", "/dest")

    def test_dependency_injection_with_interface(self):
        class MockExtractor(FileExtractorRepository):
            def __init__(self):
                self.extracted = False

            def extract(self, source_path: str, destination_dir: str) -> None:
                self.extracted = True

        # Simulate dependency injection
        def process_files(extractor: FileExtractorRepository, files: list):
            for file in files:
                extractor.extract(file, "/dest")

        mock = MockExtractor()
        process_files(mock, ["/file1.zip", "/file2.zip"])

        assert mock.extracted is True


@pytest.mark.unit
class TestFileExtractorMethodContract:
    def test_extract_returns_none(self):
        class NoneReturningExtractor(FileExtractorRepository):
            def extract(self, source_path: str, destination_dir: str) -> None:
                return None

        extractor = NoneReturningExtractor()
        result = extractor.extract("/file.zip", "/dest")

        assert result is None

    def test_extract_accepts_string_parameters(self):
        class TypeCheckingExtractor(FileExtractorRepository):
            def extract(self, source_path: str, destination_dir: str) -> None:
                assert isinstance(source_path, str)
                assert isinstance(destination_dir, str)

        extractor = TypeCheckingExtractor()
        extractor.extract("/file.zip", "/dest")  # Should not raise


@pytest.mark.unit
class TestFileExtractorMultipleInheritance:
    def test_can_inherit_from_multiple_classes(self):
        class LoggingMixin:
            def log(self, message: str):
                pass

        class LoggingExtractor(LoggingMixin, FileExtractorRepository):
            def extract(self, source_path: str, destination_dir: str) -> None:
                self.log(f"Extracting {source_path}")

        extractor = LoggingExtractor()
        assert isinstance(extractor, FileExtractorRepository)
        assert isinstance(extractor, LoggingMixin)
        assert hasattr(extractor, "extract")
        assert hasattr(extractor, "log")


@pytest.mark.unit
class TestFileExtractorInstanceChecks:
    def test_isinstance_check_works(self):
        class ConcreteExtractor(FileExtractorRepository):
            def extract(self, source_path: str, destination_dir: str) -> None:
                pass

        extractor = ConcreteExtractor()
        assert isinstance(extractor, FileExtractorRepository)

    def test_issubclass_check_works(self):
        class ConcreteExtractor(FileExtractorRepository):
            def extract(self, source_path: str, destination_dir: str) -> None:
                pass

        assert issubclass(ConcreteExtractor, FileExtractorRepository)

    def test_non_extractor_not_instance(self):
        class NotAnExtractor:
            def extract(self, source_path: str, destination_dir: str) -> None:
                pass

        obj = NotAnExtractor()
        assert not isinstance(obj, FileExtractorRepository)
