"""Integration tests for refactored DownloadDocumentsUseCase.

This module tests the orchestration of sub-use cases and ensures
that the refactored use case maintains backward compatibility.
"""

import os
import tempfile

import pytest

from src.brazil.cvm.fundamental_stocks_data.application.interfaces import (
    DownloadDocsCVMRepository,
)
from src.brazil.cvm.fundamental_stocks_data.application.use_cases import (
    DownloadDocumentsUseCase,
)
from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult
from src.brazil.cvm.fundamental_stocks_data.exceptions import (
    InvalidDestinationPathError,
    InvalidDocName,
    InvalidFirstYear,
    InvalidRepositoryTypeError,
)


class MockRepository(DownloadDocsCVMRepository):
    """Mock repository for testing."""

    def __init__(self):
        self.download_docs_called = False
        self.last_path = None
        self.last_dict_zips = None

    def download_docs(self, path: str, dict_zip_to_download: dict) -> DownloadResult:
        self.download_docs_called = True
        self.last_path = path
        self.last_dict_zips = dict_zip_to_download

        # Return successful result
        return DownloadResult(successful_downloads={"DFP": [2020, 2021]}, errors=[])


class TestDownloadDocumentsUseCaseOrchestration:
    """Test that the orchestrator properly coordinates sub-use cases."""

    def test_orchestrator_calls_repository(self, tmp_path):
        """Test that orchestrator calls repository download_docs."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2020,
            end_year=2023,
        )

        # Repository should be called
        assert mock_repo.download_docs_called
        assert mock_repo.last_path == str(tmp_path)
        assert isinstance(mock_repo.last_dict_zips, dict)

    def test_orchestrator_passes_validated_data_to_repository(self, tmp_path):
        """Test that validated DTO data is passed to repository."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP", "ITR"],
            start_year=2020,
            end_year=2022,
        )

        # Should have generated URLs for both doc types
        assert mock_repo.last_dict_zips is not None
        assert len(mock_repo.last_dict_zips) >= 1

    def test_orchestrator_returns_download_result(self, tmp_path):
        """Test that orchestrator returns DownloadResult from repository."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2020,
            end_year=2023,
        )

        assert isinstance(result, DownloadResult)
        assert result.success_count > 0

    def test_orchestrator_creates_directory_via_validator(self):
        """Test that orchestrator creates directory through validator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "new_dir")

            mock_repo = MockRepository()
            use_case = DownloadDocumentsUseCase(mock_repo)

            use_case.execute(
                destination_path=new_path,
                doc_types=["DFP"],
                start_year=2020,
                end_year=2020,
            )

            # Directory should be created by validator
            assert os.path.exists(new_path)

    def test_orchestrator_generates_correct_urls(self, tmp_path):
        """Test that orchestrator generates correct CVM URLs."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2020,
            end_year=2021,
        )

        # URLs should be generated
        assert "DFP" in mock_repo.last_dict_zips
        assert len(mock_repo.last_dict_zips["DFP"]) == 2  # 2020, 2021
        # URLs should contain CVM domain
        for url in mock_repo.last_dict_zips["DFP"]:
            assert "dados.cvm.gov.br" in url


class TestDownloadDocumentsUseCaseBackwardCompatibility:
    """Test that refactored use case maintains backward compatibility."""

    def test_same_interface_as_before(self, tmp_path):
        """Test that execute() has the same signature as before."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        # Should work with same parameters as old implementation
        result = use_case.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2020,
            end_year=2023,
        )

        assert isinstance(result, DownloadResult)

    def test_handles_none_doc_types(self, tmp_path):
        """Test that None doc_types works (uses all docs)."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            doc_types=None,
            start_year=2020,
            end_year=2020,
        )

        assert isinstance(result, DownloadResult)
        # Should have called repository with multiple doc types
        assert len(mock_repo.last_dict_zips) > 1

    def test_handles_none_years(self, tmp_path):
        """Test that None years work (uses defaults)."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=None,
            end_year=None,
        )

        assert isinstance(result, DownloadResult)
        # Should have generated URLs with default years
        assert mock_repo.download_docs_called

    def test_creates_directory_if_not_exists(self):
        """Test that non-existent directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "new_dir")

            mock_repo = MockRepository()
            use_case = DownloadDocumentsUseCase(mock_repo)

            use_case.execute(
                destination_path=new_path,
                doc_types=["DFP"],
                start_year=2020,
                end_year=2020,
            )

            # Directory should be created
            assert os.path.exists(new_path)


class TestDownloadDocumentsUseCaseErrorHandling:
    """Test error handling in orchestrated flow."""

    def test_validation_error_stops_execution(self, tmp_path):
        """Test that validation error prevents URL generation and download."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        with pytest.raises(InvalidDocName):
            use_case.execute(
                destination_path=str(tmp_path),
                doc_types=["INVALID"],
                start_year=2020,
                end_year=2023,
            )

        # Repository should NOT be called
        assert not mock_repo.download_docs_called

    def test_invalid_year_error_stops_execution(self, tmp_path):
        """Test that invalid year prevents download."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        with pytest.raises(InvalidFirstYear):
            use_case.execute(
                destination_path=str(tmp_path),
                doc_types=["DFP"],
                start_year=1990,
                end_year=2020,
            )

        # Repository should NOT be called
        assert not mock_repo.download_docs_called

    def test_invalid_path_error_stops_execution(self):
        """Test that invalid path prevents download."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        with pytest.raises(InvalidDestinationPathError):
            use_case.execute(
                destination_path="",  # Invalid
                doc_types=["DFP"],
                start_year=2020,
                end_year=2023,
            )

        # Repository should NOT be called
        assert not mock_repo.download_docs_called

    def test_repository_error_is_propagated(self, tmp_path):
        """Test that repository errors are propagated."""

        class ErrorRepository(DownloadDocsCVMRepository):
            def download_docs(self, path, dict_zip):
                raise RuntimeError("Download failed")

        error_repo = ErrorRepository()
        use_case = DownloadDocumentsUseCase(error_repo)

        with pytest.raises(RuntimeError, match="Download failed"):
            use_case.execute(
                destination_path=str(tmp_path),
                doc_types=["DFP"],
                start_year=2020,
                end_year=2020,
            )


class TestDownloadDocumentsUseCaseInitialization:
    """Test use case initialization."""

    def test_init_with_valid_repository(self):
        """Test initialization with valid repository."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        assert use_case is not None
        assert use_case._repository is mock_repo

    def test_init_with_invalid_repository_raises_error(self):
        """Test that non-repository raises InvalidRepositoryTypeError."""
        with pytest.raises(InvalidRepositoryTypeError, match="must be an instance"):
            DownloadDocumentsUseCase("not a repository")

    def test_init_with_none_repository_raises_error(self):
        """Test that None repository raises InvalidRepositoryTypeError."""
        with pytest.raises(InvalidRepositoryTypeError):
            DownloadDocumentsUseCase(None)

    def test_init_creates_sub_use_cases(self):
        """Test that initialization creates validator and URL generator."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        assert hasattr(use_case, "_validator")
        assert hasattr(use_case, "_url_generator")
        assert use_case._validator is not None
        assert use_case._url_generator is not None


class TestDownloadDocumentsUseCaseLogging:
    """Test logging behavior."""

    def test_logs_orchestration_start(self, tmp_path, caplog):
        """Test that orchestration start is logged."""
        import logging

        caplog.set_level(logging.INFO)

        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2020,
            end_year=2020,
        )

        assert any(
            "orchestration" in record.message.lower() for record in caplog.records
        )

    def test_logs_download_completion(self, tmp_path, caplog):
        """Test that completion is logged."""
        import logging

        caplog.set_level(logging.INFO)

        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        use_case.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2020,
            end_year=2020,
        )

        assert any("completed" in record.message.lower() for record in caplog.records)


class TestDownloadDocumentsUseCaseIntegrationWithRealSubUseCases:
    """Integration tests using real sub-use cases (not mocked)."""

    def test_full_integration_with_real_sub_use_cases(self, tmp_path):
        """Test complete flow with real validator and URL generator."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP"],
            start_year=2022,
            end_year=2023,
        )

        # Should complete successfully
        assert isinstance(result, DownloadResult)

        # Repository should receive correct data
        assert mock_repo.last_path == str(tmp_path)
        assert "DFP" in mock_repo.last_dict_zips
        assert len(mock_repo.last_dict_zips["DFP"]) == 2  # 2022, 2023

    def test_integration_with_multiple_docs_and_years(self, tmp_path):
        """Test integration with complex scenario."""
        mock_repo = MockRepository()
        use_case = DownloadDocumentsUseCase(mock_repo)

        result = use_case.execute(
            destination_path=str(tmp_path),
            doc_types=["DFP", "ITR", "FRE"],
            start_year=2020,
            end_year=2022,
        )

        assert isinstance(result, DownloadResult)
        assert len(mock_repo.last_dict_zips) == 3
        assert all(len(urls) == 3 for urls in mock_repo.last_dict_zips.values())
