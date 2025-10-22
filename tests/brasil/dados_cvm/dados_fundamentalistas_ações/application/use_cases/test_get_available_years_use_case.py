import pytest

from src.brasil.dados_cvm.dados_fundamentalistas_ações.application.use_cases import (
    GetAvailableYearsUseCase,
)


class TestGetAvailableYearsUseCase:
    def test_execute_returns_years_info(self):
        use_case = GetAvailableYearsUseCase()
        result = use_case.execute()

        assert isinstance(result, dict)
        assert len(result) == 4

    def test_execute_contains_required_keys(self):
        use_case = GetAvailableYearsUseCase()
        result = use_case.execute()

        required_keys = {
            "general_minimum",
            "itr_minimum",
            "cgvn_vlmo_minimum",
            "current_year",
        }
        assert set(result.keys()) == required_keys

    def test_execute_all_values_are_integers(self):
        use_case = GetAvailableYearsUseCase()
        result = use_case.execute()

        for key, value in result.items():
            assert isinstance(value, int), f"{key} should be int, got {type(value)}"

    def test_minimum_years_are_reasonable(self):
        use_case = GetAvailableYearsUseCase()
        result = use_case.execute()

        # Minimum years should be before current year
        assert result["general_minimum"] < result["current_year"]
        assert result["itr_minimum"] < result["current_year"]
        assert result["cgvn_vlmo_minimum"] < result["current_year"]

    def test_current_year_is_reasonable(self):
        use_case = GetAvailableYearsUseCase()
        result = use_case.execute()

        from datetime import datetime

        current_year = datetime.now().year

        # Current year should be current or close
        assert abs(result["current_year"] - current_year) <= 1

    def test_initialization_does_not_raise(self):
        try:
            use_case = GetAvailableYearsUseCase()
            assert use_case is not None
        except Exception as e:
            pytest.fail(f"Initialization raised {type(e).__name__}: {e}")
