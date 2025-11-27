from abc import ABC
from typing import List, Tuple

import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data import (
    DownloadDocsCVMRepositoryCVM,
    DownloadResultCVM,
)


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryInterface:
    def test_is_abstract_base_class(self):
        assert issubclass(DownloadDocsCVMRepositoryCVM, ABC)

    def test_has_download_docs_method(self):
        assert hasattr(DownloadDocsCVMRepositoryCVM, 'download_docs')

    def test_cannot_instantiate_directly(self):
        with pytest.raises(
            TypeError, match="Can't instantiate abstract class"
        ):
            DownloadDocsCVMRepositoryCVM()

    def test_download_docs_is_abstract_method(self):
        assert hasattr(
            DownloadDocsCVMRepositoryCVM.download_docs, '__isabstractmethod__'
        )
        assert DownloadDocsCVMRepositoryCVM.download_docs.__isabstractmethod__


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryContract:
    def test_concrete_implementation_must_implement_download_docs(self):
        class IncompleteRepository(DownloadDocsCVMRepositoryCVM):
            pass

        with pytest.raises(
            TypeError, match="Can't instantiate abstract class"
        ):
            IncompleteRepository()

    def test_concrete_implementation_with_download_docs_works(self):
        class CompleteRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                return DownloadResultCVM()

        repository = CompleteRepository()
        assert isinstance(repository, DownloadDocsCVMRepositoryCVM)
        assert callable(repository.download_docs)

    def test_download_docs_method_signature(self):
        class ConcreteRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                return DownloadResultCVM()

        repository = ConcreteRepository()
        assert repository.download_docs.__code__.co_argcount == 2


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryDocumentation:
    def test_class_has_docstring(self):
        assert DownloadDocsCVMRepositoryCVM.__doc__ is not None
        assert len(DownloadDocsCVMRepositoryCVM.__doc__) > 0

    def test_download_docs_method_has_docstring(self):
        assert DownloadDocsCVMRepositoryCVM.download_docs.__doc__ is not None
        assert len(DownloadDocsCVMRepositoryCVM.download_docs.__doc__) > 0

    def test_docstring_mentions_download(self):
        doc = DownloadDocsCVMRepositoryCVM.__doc__
        assert 'download' in doc.lower() or 'cvm' in doc.lower()

    def test_download_docs_docstring_mentions_parameters(self):
        doc = DownloadDocsCVMRepositoryCVM.download_docs.__doc__
        assert 'tasks' in doc.lower() or 'url' in doc.lower()

    def test_download_docs_docstring_mentions_return(self):
        doc = DownloadDocsCVMRepositoryCVM.download_docs.__doc__
        assert 'return' in doc.lower() or 'downloadresult' in doc.lower()


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryConcreteImplementations:
    def test_simple_concrete_repository(self):
        class SimpleRepository(DownloadDocsCVMRepositoryCVM):
            def __init__(self):
                self.downloads = []

            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                self.downloads.append(tasks)
                return DownloadResultCVM()

        repository = SimpleRepository()
        tasks = [
            ('http://example.com/dfp2020', 'dfp_2020', '2020', '/path/2020'),
            ('http://example.com/dfp2021', 'dfp_2021', '2021', '/path/2021'),
        ]

        result = repository.download_docs(tasks)

        assert isinstance(result, DownloadResultCVM)
        assert len(repository.downloads) == 1
        assert repository.downloads[0] == tasks

    def test_repository_with_successful_downloads(self):
        class SuccessRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                result = DownloadResultCVM()
                for url, doc_name, year, path in tasks:
                    result.add_success_downloads(f'{doc_name}_{year}')
                return result

        repository = SuccessRepository()
        tasks = [
            ('http://example.com/dfp2020', 'dfp', '2020', '/path/2020'),
            ('http://example.com/dfp2021', 'dfp', '2021', '/path/2021'),
            ('http://example.com/itr2020', 'itr', '2020', '/path/2020'),
        ]

        result = repository.download_docs(tasks)

        assert result.success_count_downloads == 3
        assert result.error_count_downloads == 0

    def test_repository_with_errors(self):
        class ErrorRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                result = DownloadResultCVM()
                result.add_error_downloads('DFP_2020', 'Connection timeout')
                return result

        repository = ErrorRepository()
        tasks = [
            ('http://example.com/dfp2020', 'dfp', '2020', '/path/2020'),
        ]

        result = repository.download_docs(tasks)

        assert result.error_count_downloads == 1
        assert 'DFP_2020' in result.failed_downloads

    def test_repository_can_raise_exceptions(self):
        class FailingRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                raise RuntimeError('Download failed')

        repository = FailingRepository()
        tasks = [
            ('http://example.com/dfp2020', 'dfp', '2020', '/path/2020'),
        ]

        with pytest.raises(RuntimeError, match='Download failed'):
            repository.download_docs(tasks)


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryPolymorphism:
    def test_can_use_repository_polymorphically(self):
        class RepoA(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                return DownloadResultCVM()

        class RepoB(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                return DownloadResultCVM()

        repositories = [RepoA(), RepoB()]
        tasks = [
            ('http://example.com/dfp2020', 'dfp', '2020', '/path/2020'),
        ]

        for repo in repositories:
            assert isinstance(repo, DownloadDocsCVMRepositoryCVM)
            result = repo.download_docs(tasks)
            assert isinstance(result, DownloadResultCVM)

    def test_dependency_injection_with_interface(self):
        class MockRepository(DownloadDocsCVMRepositoryCVM):
            def __init__(self):
                self.called = False

            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                self.called = True
                return DownloadResultCVM()

        def execute_download(
            repository: DownloadDocsCVMRepositoryCVM,
            tasks: List[Tuple[str, str, str, str]],
        ) -> DownloadResultCVM:
            return repository.download_docs(tasks)

        mock = MockRepository()
        tasks = [
            ('http://example.com/dfp2020', 'dfp', '2020', '/path/2020'),
        ]
        result = execute_download(mock, tasks)

        assert mock.called is True
        assert isinstance(result, DownloadResultCVM)


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryReturnType:
    def test_download_docs_returns_download_result(self):
        class ConcreteRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                return DownloadResultCVM()

        repository = ConcreteRepository()
        tasks = [
            ('http://example.com/dfp2020', 'dfp', '2020', '/path/2020'),
        ]
        result = repository.download_docs(tasks)

        assert isinstance(result, DownloadResultCVM)

    def test_download_docs_returns_populated_result(self):
        class PopulatedRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                result = DownloadResultCVM()
                result.add_success_downloads('DFP_2020')
                result.add_success_downloads('DFP_2021')
                result.add_error_downloads('ITR_2020', 'Error message')
                return result

        repository = PopulatedRepository()
        tasks = [
            ('http://example.com/dfp2020', 'dfp', '2020', '/path/2020'),
            ('http://example.com/dfp2021', 'dfp', '2021', '/path/2021'),
            ('http://example.com/itr2020', 'itr', '2020', '/path/2020'),
        ]
        result = repository.download_docs(tasks)

        assert result.success_count_downloads == 2
        assert result.error_count_downloads == 1


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryParameterTypes:
    def test_tasks_parameter_accepts_list_of_tuples(self):
        class TypeCheckingRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                assert isinstance(tasks, list)
                for task in tasks:
                    assert isinstance(task, tuple)
                    assert len(task) == 4
                return DownloadResultCVM()

        repository = TypeCheckingRepository()
        tasks = [
            ('http://example.com/dfp2020', 'dfp', '2020', '/path/2020'),
            ('http://example.com/dfp2021', 'dfp', '2021', '/path/2021'),
        ]
        repository.download_docs(tasks)

    def test_tasks_parameter_tuple_elements_are_strings(self):
        class TypeCheckingRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                for task in tasks:
                    url, doc_name, year, path = task
                    assert isinstance(url, str)
                    assert isinstance(doc_name, str)
                    assert isinstance(year, str)
                    assert isinstance(path, str)
                return DownloadResultCVM()

        repository = TypeCheckingRepository()
        tasks = [
            ('http://example.com/dfp2020', 'dfp', '2020', '/path/2020'),
        ]
        repository.download_docs(tasks)


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryInstanceChecks:
    def test_isinstance_check_works(self):
        class ConcreteRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                return DownloadResultCVM()

        repository = ConcreteRepository()
        assert isinstance(repository, DownloadDocsCVMRepositoryCVM)

    def test_issubclass_check_works(self):
        class ConcreteRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                return DownloadResultCVM()

        assert issubclass(ConcreteRepository, DownloadDocsCVMRepositoryCVM)

    def test_non_repository_not_instance(self):
        class NotARepository:
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                return DownloadResultCVM()

        obj = NotARepository()
        assert not isinstance(obj, DownloadDocsCVMRepositoryCVM)


@pytest.mark.unit
class TestDownloadDocsCVMRepositoryEdgeCases:
    def test_repository_with_empty_tasks_list(self):
        class EmptyHandlingRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                return DownloadResultCVM()

        repository = EmptyHandlingRepository()
        result = repository.download_docs([])

        assert isinstance(result, DownloadResultCVM)
        assert result.success_count_downloads == 0

    def test_repository_with_many_tasks(self):
        class ManyTasksRepository(DownloadDocsCVMRepositoryCVM):
            def download_docs(
                self,
                tasks: List[Tuple[str, str, str, str]],
            ) -> DownloadResultCVM:
                result = DownloadResultCVM()
                for url, doc_name, year, path in tasks:
                    result.add_success_downloads(f'{doc_name}_{year}')
                return result

        repository = ManyTasksRepository()
        tasks = [
            ('http://example.com/dfp2020', 'dfp', '2020', '/path/2020'),
            ('http://example.com/dfp2021', 'dfp', '2021', '/path/2021'),
            ('http://example.com/dfp2022', 'dfp', '2022', '/path/2022'),
            ('http://example.com/itr2020', 'itr', '2020', '/path/2020'),
            ('http://example.com/itr2021', 'itr', '2021', '/path/2021'),
            ('http://example.com/fre2020', 'fre', '2020', '/path/2020'),
        ]

        result = repository.download_docs(tasks)

        assert result.success_count_downloads == 6
