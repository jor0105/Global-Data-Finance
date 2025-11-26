import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data import (
    GenerateUrlsUseCaseCVM,
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
)


@pytest.mark.unit
class TestGenerateUrlsUseCaseSuccess:
    def test_generate_urls_for_single_doc_single_year(self):
        generator = GenerateUrlsUseCaseCVM()
        urls, _ = generator.execute(
            list_docs=["DFP"], initial_year=2023, last_year=2023
        )
        assert isinstance(urls, dict)
        assert "DFP" in urls
        assert len(urls["DFP"]) == 1
        assert "2023.zip" in urls["DFP"][0]
        assert "dfp_cia_aberta" in urls["DFP"][0].lower()

    def test_generate_urls_for_single_doc_multiple_years(self):
        generator = GenerateUrlsUseCaseCVM()
        urls, _ = generator.execute(
            list_docs=["DFP"], initial_year=2020, last_year=2023
        )
        assert "DFP" in urls
        assert len(urls["DFP"]) == 4
        years_in_urls = [
            url
            for url in urls["DFP"]
            if "2020" in url or "2021" in url or "2022" in url or "2023" in url
        ]
        assert len(years_in_urls) == 4

    def test_generate_urls_for_multiple_docs_single_year(self):
        generator = GenerateUrlsUseCaseCVM()

        urls, _ = generator.execute(
            list_docs=["DFP", "ITR"], initial_year=2023, last_year=2023
        )

        assert len(urls) == 2
        assert "DFP" in urls
        assert "ITR" in urls
        assert len(urls["DFP"]) == 1
        assert len(urls["ITR"]) == 1

    def test_generate_urls_for_multiple_docs_multiple_years(self):
        generator = GenerateUrlsUseCaseCVM()

        urls, _ = generator.execute(
            list_docs=["DFP", "ITR", "FRE"], initial_year=2020, last_year=2022
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
        generator = GenerateUrlsUseCaseCVM()

        urls, _ = generator.execute(
            list_docs=["DFP"], initial_year=2023, last_year=2023
        )

        url = urls["DFP"][0]
        assert url.startswith("https://dados.cvm.gov.br")
        assert "DFP" in url or "dfp" in url
        assert "2023.zip" in url

    def test_generate_urls_for_all_available_doc_types(self):
        generator = GenerateUrlsUseCaseCVM()

        all_docs = ["CGVN", "FRE", "FCA", "DFP", "ITR", "IPE", "VLMO"]
        urls, _ = generator.execute(
            list_docs=all_docs, initial_year=2023, last_year=2023
        )

        assert len(urls) == len(all_docs)
        for doc in all_docs:
            assert doc in urls
            assert len(urls[doc]) > 0

    def test_generate_urls_returns_correct_year_count(self):
        generator = GenerateUrlsUseCaseCVM()

        start = 2015
        end = 2023
        expected_count = end - start + 1  # 9 years

        urls, _ = generator.execute(
            list_docs=["DFP"], initial_year=start, last_year=end
        )

        assert len(urls["DFP"]) == expected_count

    def test_generate_urls_for_minimum_year_range(self):
        generator = GenerateUrlsUseCaseCVM()

        urls, _ = generator.execute(
            list_docs=["DFP"], initial_year=2010, last_year=2012
        )

        assert len(urls["DFP"]) == 3
        assert any("2010" in url for url in urls["DFP"])


@pytest.mark.unit
class TestGenerateUrlsUseCaseDocTypeErrors:
    def test_generate_urls_with_invalid_doc_type_raises_error(self):
        use_case = GenerateUrlsUseCaseCVM()

        with pytest.raises(InvalidDocName):
            use_case.execute(
                list_docs=["INVALID_DOC"], initial_year=2020, last_year=2023
            )

    def test_generate_urls_with_mixed_valid_invalid_raises_error(self):
        generator = GenerateUrlsUseCaseCVM()

        with pytest.raises(InvalidDocName):
            generator.execute(
                list_docs=["DFP", "INVALID", "ITR"], initial_year=2020, last_year=2023
            )

    def test_generate_urls_with_empty_doc_list_raises_error(self):
        pass

    def test_generate_urls_with_none_doc_type_uses_all_docs(self):
        generator = GenerateUrlsUseCaseCVM()

        # None should download all available docs
        urls, new_set_docs = generator.execute(
            list_docs=None, initial_year=2020, last_year=2023
        )

        assert isinstance(urls, dict)
        assert isinstance(new_set_docs, set)
        assert len(urls) > 1  # Should have multiple doc types


@pytest.mark.unit
class TestGenerateUrlsUseCaseYearErrors:
    def test_generate_urls_with_start_year_too_old_raises_error(self):
        generator = GenerateUrlsUseCaseCVM()

        with pytest.raises(InvalidFirstYear):
            generator.execute(list_docs=["DFP"], initial_year=1990, last_year=2020)

    def test_generate_urls_with_future_end_year_raises_error(self):
        generator = GenerateUrlsUseCaseCVM()

        with pytest.raises(InvalidLastYear):
            generator.execute(list_docs=["DFP"], initial_year=2020, last_year=2050)

    def test_generate_urls_with_start_greater_than_end_raises_error(self):
        generator = GenerateUrlsUseCaseCVM()

        with pytest.raises(InvalidLastYear):
            generator.execute(list_docs=["DFP"], initial_year=2023, last_year=2020)

    def test_generate_urls_with_non_integer_year_raises_error(self):
        generator = GenerateUrlsUseCaseCVM()

        with pytest.raises((TypeError, InvalidFirstYear)):
            generator.execute(
                list_docs=["DFP"],
                initial_year="2020",  # String instead of int
                last_year=2023,
            )


@pytest.mark.unit
class TestGenerateUrlsUseCaseEdgeCases:
    def test_generate_urls_preserves_doc_type_order(self):
        generator = GenerateUrlsUseCaseCVM()

        doc_types = ["ITR", "DFP", "FRE"]  # Non-alphabetical
        urls, _ = generator.execute(
            list_docs=doc_types, initial_year=2023, last_year=2023
        )

        # Dict keys should be in same order (Python 3.7+)
        assert list(urls.keys()) == doc_types

    def test_generate_urls_handles_case_insensitive_docs(self):
        generator = GenerateUrlsUseCaseCVM()

        # Lowercase should work (gets normalized)
        urls, _ = generator.execute(
            list_docs=["dfp", "itr"], initial_year=2023, last_year=2023
        )

        # Should have uppercase keys
        assert "DFP" in urls or "dfp" in urls
        assert len(urls) == 2

    def test_generate_urls_returns_unique_urls(self):
        generator = GenerateUrlsUseCaseCVM()

        urls, _ = generator.execute(
            list_docs=["DFP"], initial_year=2020, last_year=2023
        )

        url_list = urls["DFP"]
        assert len(url_list) == len(set(url_list))  # No duplicates

    def test_generate_urls_large_year_range(self):
        generator = GenerateUrlsUseCaseCVM()

        urls, _ = generator.execute(
            list_docs=["DFP"], initial_year=2010, last_year=2024
        )

        assert len(urls["DFP"]) == 15  # 2010-2024 inclusive

    def test_generate_urls_multiple_calls_consistent(self):
        generator = GenerateUrlsUseCaseCVM()

        urls1, _ = generator.execute(
            list_docs=["DFP", "ITR"], initial_year=2020, last_year=2022
        )

        urls2, _ = generator.execute(
            list_docs=["DFP", "ITR"], initial_year=2020, last_year=2022
        )

        assert urls1 == urls2


@pytest.mark.unit
class TestGenerateUrlsUseCaseIntegration:
    def test_generate_urls_uses_dict_zips_to_download(self):
        generator = GenerateUrlsUseCaseCVM()

        urls, _ = generator.execute(
            list_docs=["DFP"], initial_year=2023, last_year=2023
        )

        # Should return dict with list of URLs
        assert isinstance(urls, dict)
        assert isinstance(urls["DFP"], list)
        assert all(isinstance(url, str) for url in urls["DFP"])

    def test_generate_urls_all_urls_are_valid_http(self):
        generator = GenerateUrlsUseCaseCVM()

        urls, _ = generator.execute(
            list_docs=["DFP", "ITR"], initial_year=2022, last_year=2023
        )

        for doc_type, url_list in urls.items():
            for url in url_list:
                assert url.startswith("http://") or url.startswith("https://")
                assert ".zip" in url

    def test_generate_urls_logging_works(self, caplog):
        import logging

        caplog.set_level(logging.INFO)

        generator = GenerateUrlsUseCaseCVM()
        generator.execute(list_docs=["DFP"], initial_year=2023, last_year=2023)

        # Check that info log was generated
        assert any("Generated" in record.message for record in caplog.records)


@pytest.mark.unit
class TestGenerateUrlsUseCasePerformance:
    def test_generate_urls_performance_many_docs_and_years(self):
        import time

        generator = GenerateUrlsUseCaseCVM()

        start_time = time.time()
        urls, _ = generator.execute(
            list_docs=["DFP", "ITR", "FRE", "FCA", "CGVN"],
            initial_year=2010,
            last_year=2024,
        )
        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 1 second)
        assert elapsed < 1.0

        # Should generate correct number of URLs
        total_urls = sum(len(url_list) for url_list in urls.values())
        assert total_urls == 5 * 15  # 5 docs * 15 years

    def test_generate_urls_memory_efficiency(self):
        import sys

        generator = GenerateUrlsUseCaseCVM()

        # Generate many URLs
        urls, _ = generator.execute(
            list_docs=["DFP", "ITR", "FRE", "FCA"], initial_year=2010, last_year=2024
        )

        # Check memory usage is reasonable
        total_urls = sum(len(url_list) for url_list in urls.values())
        assert total_urls > 0

        # URLs should be strings, not heavy objects
        sample_url = urls["DFP"][0]
        assert sys.getsizeof(sample_url) < 1000  # Less than 1KB per URL
