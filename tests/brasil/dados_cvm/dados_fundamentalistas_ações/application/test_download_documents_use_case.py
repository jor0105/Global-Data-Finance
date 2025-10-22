import tempfile
from unittest.mock import Mock

import pytest

from src.brasil.dados_cvm.dados_fundamentalistas_ações.application import (
    DownloadDocsCVMRepository,
)
from src.brasil.dados_cvm.dados_fundamentalistas_ações.application.use_cases import (
    DownloadDocumentsUseCase,
)
from src.brasil.dados_cvm.dados_fundamentalistas_ações.domain import DownloadResult


class TestDownloadDocumentsUseCaseInitialization:
    """Tests for use case initialization."""

    def test_init_with_valid_repository(self):
        """Should initialize with valid repository."""
        mock_repo = Mock(spec=DownloadDocsCVMRepository)
        use_case = DownloadDocumentsUseCase(mock_repo)

        assert use_case is not None

    def test_init_with_invalid_repository_raises_error(self):
        """Should raise TypeError for invalid repository."""
        with pytest.raises(TypeError):
            DownloadDocumentsUseCase("not_a_repository")

    def test_init_with_none_repository_raises_error(self):
        """Should raise TypeError for None repository."""
        with pytest.raises(TypeError):
            DownloadDocumentsUseCase(None)


class TestDownloadDocumentsUseCaseExecute:
    """Tests for use case execution."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        mock = Mock(spec=DownloadDocsCVMRepository)
        mock.download_docs.return_value = DownloadResult()
        return mock

    def test_execute_with_all_parameters(self, mock_repository):
        """Should execute with all parameters specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            use_case = DownloadDocumentsUseCase(mock_repository)

            result = use_case.execute(
                destination_path=tmpdir,
                doc_types=["DFP", "ITR"],
                start_year=2020,
                end_year=2023,
            )

            assert isinstance(result, DownloadResult)
            mock_repository.download_docs.assert_called_once()

    def test_execute_with_defaults(self, mock_repository):
        """Should execute with default parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            use_case = DownloadDocumentsUseCase(mock_repository)

            result = use_case.execute(destination_path=tmpdir)

            assert isinstance(result, DownloadResult)
            mock_repository.download_docs.assert_called_once()

    def test_execute_with_empty_destination_raises_error(self, mock_repository):
        """Should raise ValueError for empty destination path."""
        use_case = DownloadDocumentsUseCase(mock_repository)

        with pytest.raises(ValueError):
            use_case.execute(destination_path="")

    def test_execute_with_whitespace_destination_raises_error(self, mock_repository):
        """Should raise ValueError for whitespace-only destination."""
        use_case = DownloadDocumentsUseCase(mock_repository)

        with pytest.raises(ValueError):
            use_case.execute(destination_path="   ")

    def test_execute_with_non_string_destination_raises_error(self, mock_repository):
        """Should raise TypeError for non-string destination."""
        use_case = DownloadDocumentsUseCase(mock_repository)

        with pytest.raises(TypeError):
            use_case.execute(destination_path=12345)

    def test_execute_returns_repository_result(self, mock_repository):
        """Should return the result from repository."""
        expected_result = DownloadResult(
            successful_downloads={"DFP": ["2020"]}, errors=[]
        )
        mock_repository.download_docs.return_value = expected_result

        with tempfile.TemporaryDirectory() as tmpdir:
            use_case = DownloadDocumentsUseCase(mock_repository)
            result = use_case.execute(destination_path=tmpdir)

            assert result is expected_result

    def test_execute_calls_repository_with_generated_urls(self, mock_repository):
        """Should call repository with generated URLs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            use_case = DownloadDocumentsUseCase(mock_repository)

            use_case.execute(
                destination_path=tmpdir,
                doc_types=["DFP"],
                start_year=2020,
                end_year=2020,
            )

            # Verify repository was called
            mock_repository.download_docs.assert_called_once()

            # Get the call arguments
            call_args = mock_repository.download_docs.call_args
            dest_path, dict_zips = call_args[0]

            assert dest_path == tmpdir
            assert isinstance(dict_zips, dict)
            assert "DFP" in dict_zips


class TestDownloadDocumentsUseCaseErrorHandling:
    """Tests for error handling in use case."""

    def test_execute_with_invalid_doc_type_raises_error(self):
        """Should raise error for invalid document type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_repo = Mock(spec=DownloadDocsCVMRepository)
            use_case = DownloadDocumentsUseCase(mock_repo)

            with pytest.raises(Exception):  # InvalidDocName
                use_case.execute(destination_path=tmpdir, doc_types=["INVALID_DOC"])

    def test_execute_with_invalid_year_range_raises_error(self):
        """Should raise error for invalid year range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_repo = Mock(spec=DownloadDocsCVMRepository)
            use_case = DownloadDocumentsUseCase(mock_repo)

            with pytest.raises(Exception):  # InvalidLastYear or similar
                use_case.execute(
                    destination_path=tmpdir,
                    start_year=2025,
                    end_year=2020,  # Reversed years
                )


class TestDownloadDocumentsUseCaseIntegration:
    """Integration tests for use case."""

    def test_complete_workflow(self):
        """Should handle complete download workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_repo = Mock(spec=DownloadDocsCVMRepository)
            mock_repo.download_docs.return_value = DownloadResult(
                successful_downloads={"DFP": ["2020", "2021"], "ITR": ["2020"]},
                errors=[],
            )

            use_case = DownloadDocumentsUseCase(mock_repo)

            result = use_case.execute(
                destination_path=tmpdir,
                doc_types=["DFP", "ITR"],
                start_year=2020,
                end_year=2021,
            )

            assert result.success_count == 3
            assert result.error_count == 0
            assert not result.has_errors

    def test_workflow_with_errors(self):
        """Should handle workflow with download errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_repo = Mock(spec=DownloadDocsCVMRepository)
            mock_repo.download_docs.return_value = DownloadResult(
                successful_downloads={"DFP": ["2020"]},
                errors=[
                    "NetworkError: connection failed",
                    "TimeoutError: timeout occurred",
                ],
            )

            use_case = DownloadDocumentsUseCase(mock_repo)

            result = use_case.execute(destination_path=tmpdir, doc_types=["DFP"])

            assert result.success_count == 1
            assert result.error_count == 2
            assert result.has_errors
