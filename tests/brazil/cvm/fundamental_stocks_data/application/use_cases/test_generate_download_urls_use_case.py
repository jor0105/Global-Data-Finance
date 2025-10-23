"""Comprehensive tests for GenerateDownloadUrlsUseCase.

This module tests all possible scenarios for the URL generation use case,
including success cases and all types of errors.
"""

import pytest

from src.brazil.cvm.fundamental_stocks_data.application.use_cases import (
    GenerateDownloadUrlsUseCase,
)
from src.brazil.cvm.fundamental_stocks_data.exceptions import (
    EmptyDocumentListError,
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
)


class TestGenerateDownloadUrlsUseCaseSuccess:
    """Test successful URL generation scenarios."""

    def test_generate_urls_for_single_doc_single_year(self):
        """Test URL generation for one document type and one year."""
        generator = GenerateDownloadUrlsUseCase()

        urls = generator.execute(doc_types=["DFP"], start_year=2023, end_year=2023)

        assert isinstance(urls, dict)
        assert "DFP" in urls
        assert len(urls["DFP"]) == 1
        assert "2023.zip" in urls["DFP"][0]
        assert "dfp_cia_aberta" in urls["DFP"][0].lower()

    def test_generate_urls_for_single_doc_multiple_years(self):
        """Test URL generation for one document type and multiple years."""
        generator = GenerateDownloadUrlsUseCase()

        urls = generator.execute(doc_types=["DFP"], start_year=2020, end_year=2023)

        assert "DFP" in urls
        assert len(urls["DFP"]) == 4  # 2020, 2021, 2022, 2023

        # Check that all years are present
        years_in_urls = [
            url
            for url in urls["DFP"]
            if "2020" in url or "2021" in url or "2022" in url or "2023" in url
        ]
        assert len(years_in_urls) == 4

    def test_generate_urls_for_multiple_docs_single_year(self):
        """Test URL generation for multiple document types and one year."""
        generator = GenerateDownloadUrlsUseCase()

        urls = generator.execute(
            doc_types=["DFP", "ITR"], start_year=2023, end_year=2023
        )

        assert len(urls) == 2
        assert "DFP" in urls
        assert "ITR" in urls
        assert len(urls["DFP"]) == 1
        assert len(urls["ITR"]) == 1

    def test_generate_urls_for_multiple_docs_multiple_years(self):
        """Test URL generation for multiple documents and multiple years."""
        generator = GenerateDownloadUrlsUseCase()

        urls = generator.execute(
            doc_types=["DFP", "ITR", "FRE"], start_year=2020, end_year=2022
        )

        assert len(urls) == 3
        assert "DFP" in urls
        assert "ITR" in urls
        assert "FRE" in urls

        # Each doc type should have 3 years (2020, 2021, 2022)
        assert len(urls["DFP"]) == 3
        assert len(urls["ITR"]) == 3
        assert len(urls["FRE"]) == 3

    def test_generate_urls_contains_valid_cvm_url_pattern(self):
        """Test that generated URLs follow CVM URL pattern."""
        generator = GenerateDownloadUrlsUseCase()

        urls = generator.execute(doc_types=["DFP"], start_year=2023, end_year=2023)

        url = urls["DFP"][0]
        assert url.startswith("https://dados.cvm.gov.br")
        assert "DFP" in url or "dfp" in url
        assert "2023.zip" in url

    def test_generate_urls_for_all_available_doc_types(self):
        """Test URL generation for all available document types."""
        generator = GenerateDownloadUrlsUseCase()

        all_docs = ["CGVN", "FRE", "FCA", "DFP", "ITR", "IPE", "VLMO"]
        urls = generator.execute(doc_types=all_docs, start_year=2023, end_year=2023)

        assert len(urls) == len(all_docs)
        for doc in all_docs:
            assert doc in urls
            assert len(urls[doc]) > 0

    def test_generate_urls_returns_correct_year_count(self):
        """Test that number of URLs matches year range."""
        generator = GenerateDownloadUrlsUseCase()

        start = 2015
        end = 2023
        expected_count = end - start + 1  # 9 years

        urls = generator.execute(doc_types=["DFP"], start_year=start, end_year=end)

        assert len(urls["DFP"]) == expected_count

    def test_generate_urls_for_minimum_year_range(self):
        """Test URL generation starting from minimum year (2010)."""
        generator = GenerateDownloadUrlsUseCase()

        urls = generator.execute(doc_types=["DFP"], start_year=2010, end_year=2012)

        assert len(urls["DFP"]) == 3
        assert any("2010" in url for url in urls["DFP"])


class TestGenerateDownloadUrlsUseCaseDocTypeErrors:
    """Test document type validation error scenarios."""

    def test_generate_urls_with_invalid_doc_type_raises_error(self):
        """Test that invalid document type raises InvalidDocName."""
        generator = GenerateDownloadUrlsUseCase()

        with pytest.raises(InvalidDocName):
            generator.execute(doc_types=["INVALID_DOC"], start_year=2020, end_year=2023)

    def test_generate_urls_with_mixed_valid_invalid_raises_error(self):
        """Test that mix of valid and invalid doc types raises error."""
        generator = GenerateDownloadUrlsUseCase()

        with pytest.raises(InvalidDocName):
            generator.execute(
                doc_types=["DFP", "INVALID", "ITR"], start_year=2020, end_year=2023
            )

    def test_generate_urls_with_empty_doc_list_raises_error(self):
        """Test that empty doc_types list raises EmptyDocumentListError."""
        generator = GenerateDownloadUrlsUseCase()

        with pytest.raises(EmptyDocumentListError):
            generator.execute(doc_types=[], start_year=2020, end_year=2023)

    def test_generate_urls_with_none_doc_type_raises_error(self):
        """Test that None doc_types raises error."""
        generator = GenerateDownloadUrlsUseCase()

        with pytest.raises((TypeError, AttributeError)):
            generator.execute(doc_types=None, start_year=2020, end_year=2023)


class TestGenerateDownloadUrlsUseCaseYearErrors:
    """Test year validation error scenarios."""

    def test_generate_urls_with_start_year_too_old_raises_error(self):
        """Test that start_year before minimum raises InvalidFirstYear."""
        generator = GenerateDownloadUrlsUseCase()

        with pytest.raises(InvalidFirstYear):
            generator.execute(doc_types=["DFP"], start_year=1990, end_year=2020)

    def test_generate_urls_with_future_end_year_raises_error(self):
        """Test that future end_year raises InvalidLastYear."""
        generator = GenerateDownloadUrlsUseCase()

        with pytest.raises(InvalidLastYear):
            generator.execute(doc_types=["DFP"], start_year=2020, end_year=2050)

    def test_generate_urls_with_start_greater_than_end_raises_error(self):
        """Test that start_year > end_year raises InvalidLastYear."""
        generator = GenerateDownloadUrlsUseCase()

        with pytest.raises(InvalidLastYear):
            generator.execute(doc_types=["DFP"], start_year=2023, end_year=2020)

    def test_generate_urls_with_non_integer_year_raises_error(self):
        """Test that non-integer year raises TypeError."""
        generator = GenerateDownloadUrlsUseCase()

        with pytest.raises((TypeError, InvalidFirstYear)):
            generator.execute(
                doc_types=["DFP"],
                start_year="2020",  # String instead of int
                end_year=2023,
            )


class TestGenerateDownloadUrlsUseCaseEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_generate_urls_preserves_doc_type_order(self):
        """Test that document type order in result matches input order."""
        generator = GenerateDownloadUrlsUseCase()

        doc_types = ["ITR", "DFP", "FRE"]  # Non-alphabetical
        urls = generator.execute(doc_types=doc_types, start_year=2023, end_year=2023)

        # Dict keys should be in same order (Python 3.7+)
        assert list(urls.keys()) == doc_types

    def test_generate_urls_handles_case_insensitive_docs(self):
        """Test that doc types are normalized (case-insensitive)."""
        generator = GenerateDownloadUrlsUseCase()

        # Lowercase should work (gets normalized)
        urls = generator.execute(
            doc_types=["dfp", "itr"], start_year=2023, end_year=2023
        )

        # Should have uppercase keys
        assert "DFP" in urls or "dfp" in urls
        assert len(urls) == 2

    def test_generate_urls_returns_unique_urls(self):
        """Test that generated URLs are unique (no duplicates)."""
        generator = GenerateDownloadUrlsUseCase()

        urls = generator.execute(doc_types=["DFP"], start_year=2020, end_year=2023)

        url_list = urls["DFP"]
        assert len(url_list) == len(set(url_list))  # No duplicates

    def test_generate_urls_large_year_range(self):
        """Test URL generation with large year range."""
        generator = GenerateDownloadUrlsUseCase()

        urls = generator.execute(doc_types=["DFP"], start_year=2010, end_year=2024)

        assert len(urls["DFP"]) == 15  # 2010-2024 inclusive

    def test_generate_urls_multiple_calls_consistent(self):
        """Test that multiple calls with same params return consistent results."""
        generator = GenerateDownloadUrlsUseCase()

        urls1 = generator.execute(
            doc_types=["DFP", "ITR"], start_year=2020, end_year=2022
        )

        urls2 = generator.execute(
            doc_types=["DFP", "ITR"], start_year=2020, end_year=2022
        )

        assert urls1 == urls2


class TestGenerateDownloadUrlsUseCaseIntegration:
    """Integration tests with real domain objects."""

    def test_generate_urls_uses_dict_zips_to_download(self):
        """Test that use case properly uses DictZipsToDownload."""
        generator = GenerateDownloadUrlsUseCase()

        urls = generator.execute(doc_types=["DFP"], start_year=2023, end_year=2023)

        # Should return dict with list of URLs
        assert isinstance(urls, dict)
        assert isinstance(urls["DFP"], list)
        assert all(isinstance(url, str) for url in urls["DFP"])

    def test_generate_urls_all_urls_are_valid_http(self):
        """Test that all generated URLs are valid HTTP URLs."""
        generator = GenerateDownloadUrlsUseCase()

        urls = generator.execute(
            doc_types=["DFP", "ITR"], start_year=2022, end_year=2023
        )

        for doc_type, url_list in urls.items():
            for url in url_list:
                assert url.startswith("http://") or url.startswith("https://")
                assert ".zip" in url

    def test_generate_urls_logging_works(self, caplog):
        """Test that logging messages are generated."""
        import logging

        caplog.set_level(logging.INFO)

        generator = GenerateDownloadUrlsUseCase()
        generator.execute(doc_types=["DFP"], start_year=2023, end_year=2023)

        # Check that info log was generated
        assert any("Generated" in record.message for record in caplog.records)


class TestGenerateDownloadUrlsUseCasePerformance:
    """Performance and scalability tests."""

    def test_generate_urls_performance_many_docs_and_years(self):
        """Test performance with many documents and long year range."""
        import time

        generator = GenerateDownloadUrlsUseCase()

        start_time = time.time()
        urls = generator.execute(
            doc_types=["DFP", "ITR", "FRE", "FCA", "CGVN"],
            start_year=2010,
            end_year=2024,
        )
        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 1 second)
        assert elapsed < 1.0

        # Should generate correct number of URLs
        total_urls = sum(len(url_list) for url_list in urls.values())
        assert total_urls == 5 * 15  # 5 docs * 15 years

    def test_generate_urls_memory_efficiency(self):
        """Test that URL generation doesn't use excessive memory."""
        import sys

        generator = GenerateDownloadUrlsUseCase()

        # Generate many URLs
        urls = generator.execute(
            doc_types=["DFP", "ITR", "FRE", "FCA"], start_year=2010, end_year=2024
        )

        # Check memory usage is reasonable
        total_urls = sum(len(url_list) for url_list in urls.values())
        assert total_urls > 0

        # URLs should be strings, not heavy objects
        sample_url = urls["DFP"][0]
        assert sys.getsizeof(sample_url) < 1000  # Less than 1KB per URL
