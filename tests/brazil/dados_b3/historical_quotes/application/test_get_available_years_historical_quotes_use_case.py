from datetime import date

from datafinc.brazil.dados_b3.historical_quotes.application.use_cases import (
    GetAvailableYearsUseCase,
)


class TestGetAvailableYearsUseCase:
    def test_get_atual_year_returns_current_year(self):
        use_case = GetAvailableYearsUseCase()
        expected_year = date.today().year
        result = use_case.get_atual_year()
        assert result == expected_year

    def test_get_atual_year_returns_integer(self):
        use_case = GetAvailableYearsUseCase()
        result = use_case.get_atual_year()
        assert isinstance(result, int)

    def test_get_atual_year_returns_reasonable_value(self):
        use_case = GetAvailableYearsUseCase()
        result = use_case.get_atual_year()
        assert result >= 2020
        assert result <= 2100

    def test_get_minimal_year_returns_1986(self):
        use_case = GetAvailableYearsUseCase()
        result = use_case.get_minimal_year()
        assert result == 1986

    def test_get_minimal_year_returns_integer(self):
        use_case = GetAvailableYearsUseCase()
        result = use_case.get_minimal_year()
        assert isinstance(result, int)

    def test_get_minimal_year_is_constant(self):
        use_case = GetAvailableYearsUseCase()
        result1 = use_case.get_minimal_year()
        result2 = use_case.get_minimal_year()
        assert result1 == result2

    def test_minimal_year_less_than_atual_year(self):
        use_case = GetAvailableYearsUseCase()
        minimal = use_case.get_minimal_year()
        atual = use_case.get_atual_year()
        assert minimal < atual

    def test_can_instantiate_use_case(self):
        use_case = GetAvailableYearsUseCase()
        assert use_case is not None
        assert isinstance(use_case, GetAvailableYearsUseCase)

    def test_methods_are_callable(self):
        use_case = GetAvailableYearsUseCase()
        assert callable(use_case.get_atual_year)
        assert callable(use_case.get_minimal_year)

    def test_multiple_instances_return_same_values(self):
        use_case1 = GetAvailableYearsUseCase()
        use_case2 = GetAvailableYearsUseCase()
        minimal1 = use_case1.get_minimal_year()
        minimal2 = use_case2.get_minimal_year()
        atual1 = use_case1.get_atual_year()
        atual2 = use_case2.get_atual_year()
        assert minimal1 == minimal2
        assert atual1 == atual2

    def test_year_range_is_valid(self):
        use_case = GetAvailableYearsUseCase()
        minimal = use_case.get_minimal_year()
        atual = use_case.get_atual_year()
        assert atual - minimal >= 0
        assert atual - minimal < 200

    def test_minimal_year_in_past(self):
        use_case = GetAvailableYearsUseCase()
        current_year = date.today().year
        minimal = use_case.get_minimal_year()
        assert minimal < current_year

    def test_get_atual_year_consistent_with_date_module(self):
        use_case = GetAvailableYearsUseCase()
        expected = date.today().year
        result = use_case.get_atual_year()
        assert result == expected

    def test_get_minimal_year_matches_b3_history(self):
        use_case = GetAvailableYearsUseCase()
        result = use_case.get_minimal_year()
        assert result == 1986
