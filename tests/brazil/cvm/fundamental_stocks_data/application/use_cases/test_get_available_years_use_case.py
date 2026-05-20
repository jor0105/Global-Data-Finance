from unittest.mock import patch

import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data import (
    GetAvailableYearsUseCaseCVM,
)


@pytest.mark.unit
class TestGetAvailableYearsUseCase:
    def test_execute_returns_years_info(self):
        use_case = GetAvailableYearsUseCaseCVM()
        result = use_case.execute()

        assert isinstance(result, dict)
        assert len(result) == 4

    def test_execute_contains_required_keys(self):
        use_case = GetAvailableYearsUseCaseCVM()
        result = use_case.execute()

        required_keys = {
            'General Document Years',
            'ITR Document Years',
            'CGVN and VMLO Document Years',
            'Current Year',
        }
        assert set(result.keys()) == required_keys

    def test_execute_all_values_are_integers(self):
        use_case = GetAvailableYearsUseCaseCVM()
        result = use_case.execute()

        for key, value in result.items():
            assert isinstance(value, int), (
                f'{key} should be int, got {type(value)}'
            )

    def test_minimum_years_are_reasonable(self):
        use_case = GetAvailableYearsUseCaseCVM()
        result = use_case.execute()

        assert result['General Document Years'] < result['Current Year']
        assert result['ITR Document Years'] < result['Current Year']
        assert result['CGVN and VMLO Document Years'] < result['Current Year']

    def test_current_year_is_reasonable(self):
        use_case = GetAvailableYearsUseCaseCVM()
        result = use_case.execute()

        from datetime import datetime

        current_year = datetime.now().year

        assert abs(result['Current Year'] - current_year) <= 1

    def test_initialization_does_not_raise(self):
        try:
            use_case = GetAvailableYearsUseCaseCVM()
            assert use_case is not None
        except Exception as e:
            pytest.fail(f'Initialization raised {type(e).__name__}: {e}')

    def test_execute_propagates_underlying_failure(self, caplog):
        use_case = GetAvailableYearsUseCaseCVM()
        with patch.object(
            use_case,
            '_GetAvailableYearsUseCaseCVM__available_years',
            autospec=True,
        ) as mock_years:
            mock_years.get_minimal_general_year.side_effect = RuntimeError(
                'boom'
            )
            with pytest.raises(RuntimeError, match='boom'):
                use_case.execute()
        assert any(
            'Failed to retrieve available years' in record.message
            for record in caplog.records
        )
