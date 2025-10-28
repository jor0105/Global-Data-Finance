import os
import tempfile

import pytest

from src.brazil.cvm.fundamental_stocks_data import (
    DownloadDocsCVMRepository,
    DownloadDocumentsUseCase,
    DownloadResult,
    InvalidDocName,
    InvalidFirstYear,
    InvalidRepositoryTypeError,
)
from src.macro_exceptions import InvalidDestinationPathError


class MockRepository(DownloadDocsCVMRepository):
    def __init__(self):
        self.download_docs_called = False
        self.last_docs_paths = None
        self.last_dict_zips = None

    def download_docs(
        self, dict_zip_to_download: dict, docs_paths: dict
    ) -> DownloadResult:
        self.download_docs_called = True
        self.last_docs_paths = docs_paths
        self.last_dict_zips = dict_zip_to_download

        return DownloadResult(successful_downloads=["DFP_2020", "DFP_2021"])


@pytest.mark.unit
class TestDownloadDocumentsUseCaseOrchestration:
    def test_orchestrator_calls_repository(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2023,
        )

        # Repository should be called
        assert mock_repo.download_docs_called
        assert mock_repo.last_docs_paths is not None
        assert isinstance(mock_repo.last_dict_zips, dict)

    def test_orchestrator_passes_validated_data_to_repository(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP", "ITR"],
            initial_year=2020,
            last_year=2022,
        )

        # Should have generated URLs for both doc types
        assert mock_repo.last_dict_zips is not None
        assert len(mock_repo.last_dict_zips) >= 1

    def test_orchestrator_returns_download_result(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2023,
        )

        assert isinstance(result, DownloadResult)
        assert result.success_count > 0

    def test_orchestrator_creates_directory_via_validator(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "new_dir")

            mock_repo = MockRepository()
            use_case = DownloadDocumentsUseCase(mock_repo)

            use_case.execute(
                destination_path=new_path,
                list_docs=["DFP"],
                initial_year=2020,
                last_year=2020,
            )

            # Directory should be created by validator
            assert os.path.exists(new_path)

    def test_orchestrator_generates_correct_urls(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2021,
        )

        # URLs should be generated
        assert "DFP" in mock_repo.last_dict_zips
        assert len(mock_repo.last_dict_zips["DFP"]) == 2  # 2020, 2021
        # URLs should contain CVM domain
        for url in mock_repo.last_dict_zips["DFP"]:
            assert "dados.cvm.gov.br" in url


@pytest.mark.unit
class TestDownloadDocumentsUseCaseBackwardCompatibility:
    def test_same_interface_as_before(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        # Should work with same parameters as old implementation
        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2023,
        )

        assert isinstance(result, DownloadResult)

    def test_handles_none_doc_types(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=None,
            initial_year=2020,
            last_year=2020,
        )

        assert isinstance(result, DownloadResult)
        # Should have called repository with multiple doc types
        assert len(mock_repo.last_dict_zips) > 1

    def test_handles_none_years(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=None,
            last_year=None,
        )

        assert isinstance(result, DownloadResult)
        # Should have generated URLs with default years
        assert mock_repo.download_docs_called

    def test_creates_directory_if_not_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "new_dir")

            mock_repo = MockRepository()
            use_case = DownloadDocumentsUseCase(mock_repo)

            use_case.execute(
                destination_path=new_path,
                list_docs=["DFP"],
                initial_year=2020,
                last_year=2020,
            )

            # Directory should be created
            assert os.path.exists(new_path)


@pytest.mark.unit
class TestDownloadDocumentsUseCaseErrorHandling:
    def test_validation_error_stops_execution(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        with pytest.raises(InvalidDocName):
            use_case.execute(
                destination_path=str(tmp_path),
                list_docs=["INVALID"],
                initial_year=2020,
                last_year=2023,
            )

        # Repository should NOT be called
        assert not mock_repo.download_docs_called

    def test_invalid_year_error_stops_execution(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        with pytest.raises(InvalidFirstYear):
            use_case.execute(
                destination_path=str(tmp_path),
                list_docs=["DFP"],
                initial_year=1990,
                last_year=2020,
            )

        # Repository should NOT be called
        assert not mock_repo.download_docs_called

    def test_invalid_path_error_stops_execution(self):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        with pytest.raises(InvalidDestinationPathError):
            use_case.execute(
                destination_path="",  # Invalid
                list_docs=["DFP"],
                initial_year=2020,
                last_year=2023,
            )

        # Repository should NOT be called
        assert not mock_repo.download_docs_called

    def test_repository_error_is_propagated(self, tmp_path):
        class ErrorRepository(DownloadDocsCVMRepository):
            def download_docs(self, path, dict_zip):
                raise RuntimeError("Download failed")

        error_repo = ErrorRepository()
        use_case = DownloadDocumentsUseCase(error_repo)

        with pytest.raises(RuntimeError, match="Download failed"):
            use_case.execute(
                destination_path=str(tmp_path),
                list_docs=["DFP"],
                initial_year=2020,
                last_year=2020,
            )


@pytest.mark.unit
class TestDownloadDocumentsUseCaseInitialization:
    def test_init_with_valid_repository(self):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        assert use_case is not None
        assert use_case._DownloadDocumentsUseCase__repository is mock_repo

    def test_init_with_invalid_repository_raises_error(self):
        with pytest.raises(InvalidRepositoryTypeError, match="Repository must be"):
            DownloadDocumentsUseCase("not a repository")

    def test_init_with_none_repository_raises_error(self):
        with pytest.raises(InvalidRepositoryTypeError):
            DownloadDocumentsUseCase(None)

    def test_init_creates_sub_use_cases(self):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        assert hasattr(use_case, "_DownloadDocumentsUseCase__url_generator")
        assert hasattr(use_case, "_DownloadDocumentsUseCase__range_years_generator")
        assert use_case._DownloadDocumentsUseCase__url_generator is not None
        assert use_case._DownloadDocumentsUseCase__range_years_generator is not None


@pytest.mark.unit
class TestDownloadDocumentsUseCaseLogging:
    def test_logs_orchestration_start(self, tmp_path, caplog):
        import logging

        caplog.set_level(logging.INFO)

        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2020,
        )

        assert any(
            "orchestration" in record.message.lower() for record in caplog.records
        )

    def test_logs_download_completion(self, tmp_path, caplog):
        import logging

        caplog.set_level(logging.INFO)

        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2020,
            last_year=2020,
        )

        assert any("completed" in record.message.lower() for record in caplog.records)


@pytest.mark.unit
class TestDownloadDocumentsUseCaseIntegrationWithRealSubUseCases:
    def test_full_integration_with_real_sub_use_cases(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP"],
            initial_year=2022,
            last_year=2023,
        )

        # Should complete successfully
        assert isinstance(result, DownloadResult)

        # Repository should receive correct data
        assert mock_repo.last_docs_paths is not None
        assert "DFP" in mock_repo.last_dict_zips
        assert len(mock_repo.last_dict_zips["DFP"]) == 2  # 2022, 2023

    def test_integration_with_multiple_docs_and_years(self, tmp_path):
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            list_docs=["DFP", "ITR", "FRE"],
            initial_year=2020,
            last_year=2022,
        )

        assert isinstance(result, DownloadResult)
        assert len(mock_repo.last_dict_zips) == 3
        assert all(len(urls) == 3 for urls in mock_repo.last_dict_zips.values())
