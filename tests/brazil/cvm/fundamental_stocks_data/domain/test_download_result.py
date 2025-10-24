import pytest

from src.brazil.cvm.fundamental_stocks_data import DownloadResult


@pytest.mark.unit
class TestDownloadResultInitialization:
    def test_init_with_defaults(self):
        result = DownloadResult()

        assert result.successful_downloads == []
        assert result.failed_downloads == {}
        assert result.success_count == 0
        assert result.error_count == 0

    def test_init_with_successful_downloads_list(self):
        downloads = ["DFP_2020", "DFP_2021"]
        result = DownloadResult(successful_downloads=downloads)

        assert result.successful_downloads == downloads
        assert result.success_count == 2

    def test_init_with_failed_downloads(self):
        failures = {"DFP_2020": "Connection timeout", "ITR_2021": "File not found"}
        result = DownloadResult(failed_downloads=failures)

        assert result.failed_downloads == failures
        assert result.error_count == 2

    def test_init_with_both_parameters(self):
        downloads = ["DFP_2020"]
        failures = {"ITR_2020": "Error message"}
        result = DownloadResult(
            successful_downloads=downloads, failed_downloads=failures
        )

        assert result.successful_downloads == downloads
        assert result.failed_downloads == failures


@pytest.mark.unit
class TestDownloadResultProperties:
    def test_success_count_with_empty_result(self):
        result = DownloadResult()
        assert result.success_count == 0

    def test_success_count_calculation(self):
        downloads = ["DFP_2020", "DFP_2021", "ITR_2020"]
        result = DownloadResult(successful_downloads=downloads)

        assert result.success_count == 3

    def test_error_count_with_empty_result(self):
        result = DownloadResult()
        assert result.error_count == 0

    def test_error_count_calculation(self):
        failures = {"DFP_2020": "Error 1", "ITR_2021": "Error 2", "FRE_2020": "Error 3"}
        result = DownloadResult(failed_downloads=failures)

        assert result.error_count == 3

    def test_success_count_is_readonly_property(self):
        result = DownloadResult(successful_downloads=["DFP"])
        assert result.success_count == 1
        # Trying to set would raise AttributeError
        with pytest.raises(AttributeError):
            result.success_count = 5

    def test_error_count_is_readonly_property(self):
        result = DownloadResult(failed_downloads={"DFP": "Error"})
        assert result.error_count == 1
        # Trying to set would raise AttributeError
        with pytest.raises(AttributeError):
            result.error_count = 5


@pytest.mark.unit
class TestDownloadResultAddSuccess:
    def test_add_success_to_empty_result(self):
        result = DownloadResult()
        result.add_success("DFP_2020")

        assert "DFP_2020" in result.successful_downloads
        assert result.success_count == 1

    def test_add_success_to_existing_result(self):
        result = DownloadResult(successful_downloads=["DFP_2020"])
        result.add_success("DFP_2021")

        assert result.successful_downloads == ["DFP_2020", "DFP_2021"]
        assert result.success_count == 2

    def test_add_success_prevents_duplicates(self):
        result = DownloadResult(successful_downloads=["DFP_2020"])
        result.add_success("DFP_2020")

        assert result.successful_downloads.count("DFP_2020") == 1
        assert result.success_count == 1

    def test_add_success_multiple_items(self):
        result = DownloadResult()
        result.add_success("DFP_2020")
        result.add_success("ITR_2020")
        result.add_success("FRE_2020")

        assert result.success_count == 3
        assert "DFP_2020" in result.successful_downloads
        assert "ITR_2020" in result.successful_downloads
        assert "FRE_2020" in result.successful_downloads


@pytest.mark.unit
class TestDownloadResultAddError:
    def test_add_error_to_empty_result(self):
        result = DownloadResult()
        result.add_error("DFP_2020", "Connection timeout")

        assert result.failed_downloads["DFP_2020"] == "Connection timeout"
        assert result.error_count == 1

    def test_add_error_to_existing_result(self):
        result = DownloadResult(failed_downloads={"DFP_2020": "Error 1"})
        result.add_error("ITR_2021", "Error 2")

        assert result.failed_downloads["DFP_2020"] == "Error 1"
        assert result.failed_downloads["ITR_2021"] == "Error 2"
        assert result.error_count == 2

    def test_add_error_overwrites_previous_error(self):
        result = DownloadResult(failed_downloads={"DFP_2020": "Error 1"})
        result.add_error("DFP_2020", "Error 2")

        assert result.failed_downloads["DFP_2020"] == "Error 2"
        assert result.error_count == 1

    def test_add_multiple_errors(self):
        result = DownloadResult()
        result.add_error("DFP_2020", "Error 1")
        result.add_error("ITR_2021", "Error 2")
        result.add_error("FRE_2022", "Error 3")

        assert result.error_count == 3


@pytest.mark.unit
class TestDownloadResultStringRepresentation:
    def test_str_format_with_data(self):
        result = DownloadResult(
            successful_downloads=["DFP_2020", "DFP_2021"],
            failed_downloads={"ITR_2020": "Error"},
        )
        str_repr = str(result)

        assert "success=2" in str_repr
        assert "errors=1" in str_repr

    def test_str_format_with_empty_result(self):
        result = DownloadResult()
        str_repr = str(result)

        assert "success=0" in str_repr
        assert "errors=0" in str_repr

    def test_str_format_only_successes(self):
        result = DownloadResult(
            successful_downloads=["DFP_2020", "DFP_2021", "ITR_2020"]
        )
        str_repr = str(result)

        assert "success=3" in str_repr
        assert "errors=0" in str_repr

    def test_str_format_only_errors(self):
        result = DownloadResult(failed_downloads={"DFP_2020": "E1", "ITR_2020": "E2"})
        str_repr = str(result)

        assert "success=0" in str_repr
        assert "errors=2" in str_repr


@pytest.mark.unit
class TestDownloadResultIntegration:
    def test_mixed_operations(self):
        result = DownloadResult()

        # Add successes
        result.add_success("DFP_2020")
        result.add_success("DFP_2021")
        result.add_success("ITR_2020")

        # Add errors
        result.add_error("FRE_2020", "Connection timeout")
        result.add_error("VLMO_2020", "File not found")

        # Verify state
        assert result.success_count == 3
        assert result.error_count == 2
        assert "DFP_2020" in result.successful_downloads
        assert "FRE_2020" in result.failed_downloads

    def test_result_as_return_value(self):
        def simulate_download(should_succeed: bool, item: str) -> DownloadResult:
            result = DownloadResult()

            if should_succeed:
                result.add_success(item)
            else:
                result.add_error(item, "Download failed")

            return result

        success_result = simulate_download(True, "DFP_2020")
        assert success_result.success_count == 1
        assert success_result.error_count == 0

        failure_result = simulate_download(False, "DFP_2020")
        assert failure_result.success_count == 0
        assert failure_result.error_count == 1

    def test_complete_workflow(self):
        result = DownloadResult()

        # Simulate downloading multiple documents and years
        documents = ["DFP", "ITR", "FRE"]
        years = [2020, 2021, 2022]

        for doc in documents:
            for year in years:
                item = f"{doc}_{year}"
                if year == 2021 and doc == "ITR":
                    # Simulate one failure
                    result.add_error(item, "Network error")
                else:
                    result.add_success(item)

        # Verify counts
        assert result.success_count == 8  # 3 docs * 3 years - 1 failure
        assert result.error_count == 1

        # Verify specific items
        assert "DFP_2020" in result.successful_downloads
        assert "ITR_2021" in result.failed_downloads
        assert "FRE_2022" in result.successful_downloads

    def test_error_messages_are_preserved(self):
        result = DownloadResult()
        error_msg = "Network error: Connection timeout after 30 seconds"
        result.add_error("DFP_2020", error_msg)

        assert result.failed_downloads["DFP_2020"] == error_msg

    def test_large_scale_operations(self):
        result = DownloadResult()

        # Add 100 successes
        for i in range(100):
            result.add_success(f"DOC_{i}")

        assert result.success_count == 100
        assert result.error_count == 0

        # Add 50 errors
        for i in range(50):
            result.add_error(f"ERR_{i}", f"Error message {i}")

        assert result.success_count == 100
        assert result.error_count == 50
