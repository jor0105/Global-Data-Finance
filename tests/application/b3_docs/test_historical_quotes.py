from unittest.mock import AsyncMock, Mock, patch

import pytest

from globaldatafinance.application.b3_docs import HistoricalQuotesB3


class TestHistoricalQuotes:
    def test_initialization(self):
        b3 = HistoricalQuotesB3()
        assert b3 is not None
        assert repr(b3) == 'HistoricalQuotesB3()'

    def test_get_available_assets(self):
        b3 = HistoricalQuotesB3()
        assets = b3.get_available_assets()

        assert isinstance(assets, list)
        assert len(assets) > 0
        assert 'ações' in assets
        assert 'etf' in assets
        assert 'opções' in assets

    def test_get_available_years(self):
        b3 = HistoricalQuotesB3()
        years = b3.get_available_years()

        assert isinstance(years, dict)
        assert 'minimal_year' in years
        assert 'current_year' in years
        assert years['minimal_year'] == 1986
        assert years['current_year'] >= 2025

    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.CreateDocsToExtractUseCaseB3'
    )
    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.ExtractHistoricalQuotesUseCaseB3'
    )
    def test_extract_with_all_parameters(
        self, mock_extract_use_case, mock_create_docs_use_case
    ):
        mock_docs = Mock()
        mock_docs.documents_to_download = {'file1.zip', 'file2.zip'}
        mock_create_docs_use_case.return_value.execute.return_value = mock_docs

        mock_result = {
            'success': True,
            'message': 'Success',
            'total_files': 2,
            'success_count': 2,
            'error_count': 0,
            'total_records': 1000,
            'output_file': '/output/test.parquet',
        }
        mock_extract_instance = Mock()
        mock_extract_instance.execute = AsyncMock(return_value=mock_result)
        mock_extract_use_case.return_value = mock_extract_instance

        b3 = HistoricalQuotesB3()
        result = b3.extract(
            path_of_docs='/data/cotahist',
            destination_path='/output',
            assets_list=['ações', 'etf'],
            initial_year=2020,
            last_year=2023,
            output_filename='test.parquet',
            processing_mode='fast',
        )

        assert result == mock_result
        assert result['success'] is True
        assert result['total_records'] == 1000

    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.CreateDocsToExtractUseCaseB3'
    )
    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.ExtractHistoricalQuotesUseCaseB3'
    )
    def test_extract_with_minimal_parameters(
        self, mock_extract_use_case, mock_create_docs_use_case
    ):
        mock_docs = Mock()
        mock_docs.documents_to_download = {'file1.zip'}
        mock_create_docs_use_case.return_value.execute.return_value = mock_docs

        mock_result = {
            'success': True,
            'message': 'Success',
            'total_files': 1,
            'success_count': 1,
            'error_count': 0,
            'total_records': 500,
            'output_file': '/data/cotahist/cotahist_extracted.parquet',
        }
        mock_extract_instance = Mock()
        mock_extract_instance.execute = AsyncMock(return_value=mock_result)
        mock_extract_use_case.return_value = mock_extract_instance

        b3 = HistoricalQuotesB3()
        result = b3.extract(
            path_of_docs='/data/cotahist',
            assets_list=['ações'],
            initial_year=2023,
        )

        assert result['success'] is True
        mock_create_docs_use_case.assert_called_once()

    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.CreateDocsToExtractUseCaseB3'
    )
    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.ExtractHistoricalQuotesUseCaseB3'
    )
    def test_extract_with_errors(
        self, mock_extract_use_case, mock_create_docs_use_case
    ):
        mock_docs = Mock()
        mock_docs.documents_to_download = {'file1.zip', 'file2.zip'}
        mock_create_docs_use_case.return_value.execute.return_value = mock_docs

        mock_result = {
            'success': False,
            'message': 'Some errors occurred',
            'total_files': 2,
            'success_count': 1,
            'error_count': 1,
            'total_records': 500,
            'output_file': '/output/test.parquet',
            'errors': ['Error processing file2.zip'],
        }
        mock_extract_instance = Mock()
        mock_extract_instance.execute = AsyncMock(return_value=mock_result)
        mock_extract_use_case.return_value = mock_extract_instance

        b3 = HistoricalQuotesB3()
        result = b3.extract(
            path_of_docs='/data/cotahist',
            assets_list=['ações'],
            initial_year=2023,
        )

        assert result['success'] is False
        assert result['error_count'] == 1
        assert 'errors' in result

    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.CreateDocsToExtractUseCaseB3'
    )
    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.ExtractHistoricalQuotesUseCaseB3'
    )
    def test_extract_verbose_false_suppresses_print(
        self, mock_extract_use_case, mock_create_docs_use_case
    ):
        mock_docs = Mock()
        mock_docs.documents_to_download = {'file1.zip'}
        mock_create_docs_use_case.return_value.execute.return_value = mock_docs

        mock_result = {
            'total_files': 1,
            'success_count': 1,
            'error_count': 0,
            'total_records': 500,
            'output_file': '/output/test.parquet',
        }
        mock_extract_instance = Mock()
        mock_extract_instance.execute = AsyncMock(return_value=mock_result)
        mock_extract_use_case.return_value = mock_extract_instance

        b3 = HistoricalQuotesB3()
        b3._result_formatter = Mock()

        result = b3.extract(
            path_of_docs='/data/cotahist',
            assets_list=['ações'],
            initial_year=2023,
            verbose=False,
        )

        assert result['success'] is True
        b3._result_formatter.print_result.assert_not_called()

    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.CreateDocsToExtractUseCaseB3'
    )
    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.ExtractHistoricalQuotesUseCaseB3'
    )
    def test_extract_verbose_true_prints_by_default(
        self, mock_extract_use_case, mock_create_docs_use_case
    ):
        mock_docs = Mock()
        mock_docs.documents_to_download = {'file1.zip'}
        mock_create_docs_use_case.return_value.execute.return_value = mock_docs

        mock_result = {
            'total_files': 1,
            'success_count': 1,
            'error_count': 0,
            'total_records': 500,
            'output_file': '/output/test.parquet',
        }
        mock_extract_instance = Mock()
        mock_extract_instance.execute = AsyncMock(return_value=mock_result)
        mock_extract_use_case.return_value = mock_extract_instance

        b3 = HistoricalQuotesB3()
        b3._result_formatter = Mock()

        b3.extract(
            path_of_docs='/data/cotahist',
            assets_list=['ações'],
            initial_year=2023,
        )

        b3._result_formatter.print_result.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.CreateDocsToExtractUseCaseB3'
    )
    @patch(
        'globaldatafinance.application.b3_docs.historical_quotes.ExtractHistoricalQuotesUseCaseB3'
    )
    async def test_extract_async_returns_result(
        self, mock_extract_use_case, mock_create_docs_use_case
    ):
        mock_docs = Mock()
        mock_docs.documents_to_download = {'file1.zip', 'file2.zip'}
        mock_create_docs_use_case.return_value.execute.return_value = mock_docs

        mock_result = {
            'total_files': 2,
            'success_count': 2,
            'error_count': 0,
            'total_records': 1000,
            'output_file': '/output/test.parquet',
        }
        mock_extract_instance = Mock()
        mock_extract_instance.execute = AsyncMock(return_value=mock_result)
        mock_extract_use_case.return_value = mock_extract_instance

        b3 = HistoricalQuotesB3()

        result = await b3.extract_async(
            path_of_docs='/data/cotahist',
            destination_path='/output',
            assets_list=['ações', 'etf'],
            initial_year=2020,
            last_year=2023,
            verbose=False,
        )

        assert result['success'] is True
        assert result['total_records'] == 1000
        assert result['assets'] == ['ações', 'etf']
        assert 'elapsed_time' in result
        mock_extract_instance.execute.assert_awaited_once()
