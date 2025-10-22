"""Tests for DownloadResult domain model.

This module tests the DownloadResult class which encapsulates the outcome
of download operations.
"""

from src.brasil.dados_cvm.dados_fundamentalistas_ações.domain import DownloadResult


class TestDownloadResultInitialization:
    """Tests for DownloadResult initialization."""

    def test_init_with_defaults(self):
        """Should initialize with empty collections when no args provided."""
        result = DownloadResult()

        assert result.successful_downloads == {}
        assert result.errors == []
        assert result.success_count == 0
        assert result.error_count == 0

    def test_init_with_successful_downloads(self):
        """Should initialize with provided successful downloads."""
        downloads = {"DFP": ["2020", "2021"]}
        result = DownloadResult(successful_downloads=downloads)

        assert result.successful_downloads == downloads
        assert result.success_count == 2

    def test_init_with_errors(self):
        """Should initialize with provided errors."""
        errors = ["Error 1", "Error 2"]
        result = DownloadResult(errors=errors)

        assert result.errors == errors
        assert result.error_count == 2

    def test_init_with_both_parameters(self):
        """Should initialize with both downloads and errors."""
        downloads = {"DFP": ["2020"]}
        errors = ["Error"]
        result = DownloadResult(successful_downloads=downloads, errors=errors)

        assert result.successful_downloads == downloads
        assert result.errors == errors


class TestDownloadResultProperties:
    """Tests for DownloadResult properties."""

    def test_has_errors_when_false(self):
        """Should return False when no errors."""
        result = DownloadResult()
        assert result.has_errors is False

    def test_has_errors_when_true(self):
        """Should return True when errors exist."""
        result = DownloadResult(errors=["Error"])
        assert result.has_errors is True

    def test_success_count_calculation(self):
        """Should correctly calculate total successful downloads."""
        downloads = {
            "DFP": ["2020", "2021"],
            "ITR": ["2020"],
            "FRE": ["2019", "2020", "2021"],
        }
        result = DownloadResult(successful_downloads=downloads)

        assert result.success_count == 6

    def test_error_count(self):
        """Should correctly count errors."""
        errors = ["Error 1", "Error 2", "Error 3"]
        result = DownloadResult(errors=errors)

        assert result.error_count == 3


class TestDownloadResultAddSuccess:
    """Tests for adding successful downloads."""

    def test_add_success_to_empty_result(self):
        """Should add success to empty result."""
        result = DownloadResult()
        result.add_success("DFP", "2020")

        assert "DFP" in result.successful_downloads
        assert "2020" in result.successful_downloads["DFP"]
        assert result.success_count == 1

    def test_add_success_to_existing_document(self):
        """Should add year to existing document."""
        result = DownloadResult(successful_downloads={"DFP": ["2020"]})
        result.add_success("DFP", "2021")

        assert result.successful_downloads["DFP"] == ["2020", "2021"]
        assert result.success_count == 2

    def test_add_success_prevents_duplicates(self):
        """Should not add duplicate years."""
        result = DownloadResult(successful_downloads={"DFP": ["2020"]})
        result.add_success("DFP", "2020")

        assert result.successful_downloads["DFP"].count("2020") == 1
        assert result.success_count == 1

    def test_add_success_multiple_documents(self):
        """Should support multiple documents."""
        result = DownloadResult()
        result.add_success("DFP", "2020")
        result.add_success("ITR", "2020")

        assert "DFP" in result.successful_downloads
        assert "ITR" in result.successful_downloads
        assert result.success_count == 2


class TestDownloadResultAddError:
    """Tests for adding errors."""

    def test_add_error_to_empty_result(self):
        """Should add error to empty result."""
        result = DownloadResult()
        result.add_error("NetworkError: connection failed")

        assert "NetworkError: connection failed" in result.errors
        assert result.error_count == 1

    def test_add_multiple_errors(self):
        """Should accumulate errors."""
        result = DownloadResult()
        result.add_error("Error 1")
        result.add_error("Error 2")
        result.add_error("Error 3")

        assert result.error_count == 3
        assert "Error 1" in result.errors
        assert "Error 2" in result.errors
        assert "Error 3" in result.errors

    def test_add_error_allows_duplicates(self):
        """Should allow duplicate error messages."""
        result = DownloadResult()
        result.add_error("Same error")
        result.add_error("Same error")

        assert result.error_count == 2


class TestDownloadResultClear:
    """Tests for clearing results."""

    def test_clear_successful_downloads(self):
        """Should clear successful downloads."""
        result = DownloadResult(successful_downloads={"DFP": ["2020"]})
        result.clear()

        assert result.successful_downloads == {}
        assert result.success_count == 0

    def test_clear_errors(self):
        """Should clear errors."""
        result = DownloadResult(errors=["Error 1", "Error 2"])
        result.clear()

        assert result.errors == []
        assert result.error_count == 0

    def test_clear_both(self):
        """Should clear both downloads and errors."""
        result = DownloadResult(
            successful_downloads={"DFP": ["2020"]}, errors=["Error"]
        )
        result.clear()

        assert result.successful_downloads == {}
        assert result.errors == []
        assert result.has_errors is False


class TestDownloadResultRepr:
    """Tests for string representation."""

    def test_repr_format(self):
        """Should have correct repr format."""
        result = DownloadResult(
            successful_downloads={"DFP": ["2020", "2021"]}, errors=["Error"]
        )
        repr_str = repr(result)

        assert "DownloadResult" in repr_str
        assert "success_count=2" in repr_str
        assert "error_count=1" in repr_str

    def test_repr_with_empty_result(self):
        """Should have correct repr for empty result."""
        result = DownloadResult()
        repr_str = repr(result)

        assert "DownloadResult" in repr_str
        assert "success_count=0" in repr_str
        assert "error_count=0" in repr_str


class TestDownloadResultIntegration:
    """Integration tests for DownloadResult."""

    def test_mixed_operations(self):
        """Should handle a mix of operations correctly."""
        result = DownloadResult()

        # Add successes
        result.add_success("DFP", "2020")
        result.add_success("DFP", "2021")
        result.add_success("ITR", "2020")

        # Add errors
        result.add_error("Error 1")
        result.add_error("Error 2")

        # Verify state
        assert result.success_count == 3
        assert result.error_count == 2
        assert result.has_errors is True

        # Clear
        result.clear()
        assert result.success_count == 0
        assert result.error_count == 0

    def test_result_as_return_value(self):
        """Should work well as a function return value."""

        def simulate_download(should_succeed: bool) -> DownloadResult:
            result = DownloadResult()

            if should_succeed:
                result.add_success("DFP", "2020")
            else:
                result.add_error("Download failed")

            return result

        success_result = simulate_download(True)
        assert success_result.success_count == 1
        assert success_result.error_count == 0

        failure_result = simulate_download(False)
        assert failure_result.success_count == 0
        assert failure_result.error_count == 1
