from abc import ABC
from typing import Dict, List

import pytest

from src.brazil.cvm.fundamental_stocks_data.application.interfaces import (
    DownloadDocsCVMRepository,
)
from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryInterface:
    def test_is_abstract_base_class(self):
        assert issubclass(DownloadDocsCVMRepository, ABC)

    def test_has_download_docs_method(self):
        assert hasattr(DownloadDocsCVMRepository, "download_docs")

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            DownloadDocsCVMRepository()

    def test_download_docs_is_abstract_method(self):
        assert hasattr(DownloadDocsCVMRepository.download_docs, "__isabstractmethod__")
        assert DownloadDocsCVMRepository.download_docs.__isabstractmethod__


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryContract:
    def test_concrete_implementation_must_implement_download_docs(self):
        class IncompleteRepository(DownloadDocsCVMRepository):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteRepository()

    def test_concrete_implementation_with_download_docs_works(self):
        class CompleteRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                return DownloadResult()

        repository = CompleteRepository()
        assert isinstance(repository, DownloadDocsCVMRepository)
        assert callable(repository.download_docs)

    def test_download_docs_method_signature(self):
        class ConcreteRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                return DownloadResult()

        repository = ConcreteRepository()
        # Should accept exactly 2 parameters (plus self)
        assert repository.download_docs.__code__.co_argcount == 3


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryDocumentation:
    def test_class_has_docstring(self):
        assert DownloadDocsCVMRepository.__doc__ is not None
        assert len(DownloadDocsCVMRepository.__doc__) > 0

    def test_download_docs_method_has_docstring(self):
        assert DownloadDocsCVMRepository.download_docs.__doc__ is not None
        assert len(DownloadDocsCVMRepository.download_docs.__doc__) > 0

    def test_docstring_mentions_download(self):
        doc = DownloadDocsCVMRepository.__doc__
        assert "download" in doc.lower() or "cvm" in doc.lower()

    def test_download_docs_docstring_mentions_parameters(self):
        doc = DownloadDocsCVMRepository.download_docs.__doc__
        assert "dict_zip" in doc.lower() or "docs_paths" in doc.lower()

    def test_download_docs_docstring_mentions_return(self):
        doc = DownloadDocsCVMRepository.download_docs.__doc__
        assert "return" in doc.lower() or "downloadresult" in doc.lower()


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryConcreteImplementations:
    def test_simple_concrete_repository(self):
        class SimpleRepository(DownloadDocsCVMRepository):
            def __init__(self):
                self.downloads = []

            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                self.downloads.append((dict_zip_to_download, docs_paths))
                return DownloadResult()

        repository = SimpleRepository()
        dict_zip = {"DFP": ["url1", "url2"]}
        docs_paths = {"DFP": {2020: "/path/2020", 2021: "/path/2021"}}

        result = repository.download_docs(dict_zip, docs_paths)

        assert isinstance(result, DownloadResult)
        assert len(repository.downloads) == 1

    def test_repository_with_successful_downloads(self):
        class SuccessRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                result = DownloadResult()
                for doc_type, urls in dict_zip_to_download.items():
                    for idx, url in enumerate(urls):
                        result.add_success(f"{doc_type}_file_{idx}")
                return result

        repository = SuccessRepository()
        dict_zip = {"DFP": ["url1", "url2"], "ITR": ["url3"]}
        docs_paths = {"DFP": {2020: "/path", 2021: "/path"}, "ITR": {2020: "/path"}}

        result = repository.download_docs(dict_zip, docs_paths)

        assert result.success_count == 3
        assert result.error_count == 0

    def test_repository_with_errors(self):
        class ErrorRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                result = DownloadResult()
                result.add_error("DFP_2020", "Connection timeout")
                return result

        repository = ErrorRepository()
        dict_zip = {"DFP": ["url1"]}
        docs_paths = {"DFP": {2020: "/path"}}

        result = repository.download_docs(dict_zip, docs_paths)

        assert result.error_count == 1
        assert "DFP_2020" in result.failed_downloads

    def test_repository_can_raise_exceptions(self):
        class FailingRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                raise RuntimeError("Download failed")

        repository = FailingRepository()
        dict_zip = {"DFP": ["url1"]}
        docs_paths = {"DFP": {2020: "/path"}}

        with pytest.raises(RuntimeError, match="Download failed"):
            repository.download_docs(dict_zip, docs_paths)


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryPolymorphism:
    def test_can_use_repository_polymorphically(self):
        class RepoA(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                return DownloadResult()

        class RepoB(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                return DownloadResult()

        repositories = [RepoA(), RepoB()]
        dict_zip = {"DFP": ["url1"]}
        docs_paths = {"DFP": {2020: "/path"}}

        for repo in repositories:
            assert isinstance(repo, DownloadDocsCVMRepository)
            result = repo.download_docs(dict_zip, docs_paths)
            assert isinstance(result, DownloadResult)

    def test_dependency_injection_with_interface(self):
        class MockRepository(DownloadDocsCVMRepository):
            def __init__(self):
                self.called = False

            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                self.called = True
                return DownloadResult()

        # Simulate dependency injection in a use case
        def execute_download(
            repository: DownloadDocsCVMRepository, dict_zip: Dict, docs_paths: Dict
        ):
            return repository.download_docs(dict_zip, docs_paths)

        mock = MockRepository()
        result = execute_download(mock, {"DFP": ["url1"]}, {"DFP": {2020: "/path"}})

        assert mock.called is True
        assert isinstance(result, DownloadResult)


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryReturnType:
    def test_download_docs_returns_download_result(self):
        class ConcreteRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                return DownloadResult()

        repository = ConcreteRepository()
        result = repository.download_docs({"DFP": ["url1"]}, {"DFP": {2020: "/path"}})

        assert isinstance(result, DownloadResult)

    def test_download_docs_returns_populated_result(self):
        class PopulatedRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                result = DownloadResult()
                result.add_success("DFP_2020")
                result.add_success("DFP_2021")
                result.add_error("ITR_2020", "Error message")
                return result

        repository = PopulatedRepository()
        result = repository.download_docs(
            {"DFP": ["url1", "url2"], "ITR": ["url3"]},
            {"DFP": {2020: "/path", 2021: "/path"}, "ITR": {2020: "/path"}},
        )

        assert result.success_count == 2
        assert result.error_count == 1


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryParameterTypes:
    def test_dict_zip_parameter_accepts_dict(self):
        class TypeCheckingRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                assert isinstance(dict_zip_to_download, dict)
                return DownloadResult()

        repository = TypeCheckingRepository()
        repository.download_docs({"DFP": ["url1"]}, {"DFP": {2020: "/path"}})

    def test_docs_paths_parameter_accepts_nested_dict(self):
        class TypeCheckingRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                assert isinstance(docs_paths, dict)
                for doc_type, year_paths in docs_paths.items():
                    assert isinstance(year_paths, dict)
                return DownloadResult()

        repository = TypeCheckingRepository()
        repository.download_docs(
            {"DFP": ["url1"]}, {"DFP": {2020: "/path", 2021: "/path"}}
        )


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryInstanceChecks:
    def test_isinstance_check_works(self):
        class ConcreteRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                return DownloadResult()

        repository = ConcreteRepository()
        assert isinstance(repository, DownloadDocsCVMRepository)

    def test_issubclass_check_works(self):
        class ConcreteRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                return DownloadResult()

        assert issubclass(ConcreteRepository, DownloadDocsCVMRepository)

    def test_non_repository_not_instance(self):
        class NotARepository:
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                return DownloadResult()

        obj = NotARepository()
        assert not isinstance(obj, DownloadDocsCVMRepository)


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryEdgeCases:
    def test_repository_with_empty_dict_zip(self):
        class EmptyHandlingRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                return DownloadResult()

        repository = EmptyHandlingRepository()
        result = repository.download_docs({}, {})

        assert isinstance(result, DownloadResult)
        assert result.success_count == 0

    def test_repository_with_many_documents(self):
        class ManyDocsRepository(DownloadDocsCVMRepository):
            def download_docs(
                self,
                dict_zip_to_download: Dict[str, List[str]],
                docs_paths: Dict[str, Dict[int, str]],
            ) -> DownloadResult:
                result = DownloadResult()
                for doc_type, urls in dict_zip_to_download.items():
                    for idx, _ in enumerate(urls):
                        result.add_success(f"{doc_type}_file_{idx}")
                return result

        repository = ManyDocsRepository()
        dict_zip = {
            "DFP": ["url1", "url2", "url3"],
            "ITR": ["url4", "url5"],
            "FRE": ["url6"],
        }
        docs_paths = {
            "DFP": {2020: "/p", 2021: "/p", 2022: "/p"},
            "ITR": {2020: "/p", 2021: "/p"},
            "FRE": {2020: "/p"},
        }

        result = repository.download_docs(dict_zip, docs_paths)

        assert result.success_count == 6
