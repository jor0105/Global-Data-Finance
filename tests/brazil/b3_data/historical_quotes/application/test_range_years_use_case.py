from datetime import date

import pytest

from datafinance.brazil.b3_data.historical_quotes.application.use_cases import (
    CreateRangeYearsUseCaseB3,
)
from datafinance.brazil.b3_data.historical_quotes.exceptions import (
    InvalidFirstYear,
    InvalidLastYear,
)


class TestCreateRangeYearsUseCaseB3:
    def test_execute_returns_range(self):
        result = CreateRangeYearsUseCaseB3.execute(2020, 2024)
        assert isinstance(result, range)

    def test_execute_with_valid_years(self):
        result = CreateRangeYearsUseCaseB3.execute(2020, 2024)
        assert list(result) == [2020, 2021, 2022, 2023, 2024]

    def test_execute_with_single_year(self):
        result = CreateRangeYearsUseCaseB3.execute(2020, 2020)
        assert list(result) == [2020]

    def test_execute_with_consecutive_years(self):
        result = CreateRangeYearsUseCaseB3.execute(2020, 2021)
        assert list(result) == [2020, 2021]

    def test_execute_from_min_year(self):
        result = CreateRangeYearsUseCaseB3.execute(1986, 1990)
        assert list(result)[0] == 1986
        assert len(list(result)) == 5

    def test_execute_to_current_year(self):
        current_year = date.today().year
        result = CreateRangeYearsUseCaseB3.execute(2020, current_year)
        assert list(result)[-1] == current_year

    def test_execute_long_range(self):
        result = CreateRangeYearsUseCaseB3.execute(1986, 2024)
        years = list(result)
        assert len(years) == 39
        assert years[0] == 1986
        assert years[-1] == 2024

    def test_execute_raises_invalid_first_year_for_year_before_1986(self):
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCaseB3.execute(1985, 2024)

    def test_execute_raises_invalid_first_year_for_future_year(self):
        future_year = date.today().year + 1
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCaseB3.execute(future_year, future_year + 1)

    def test_execute_raises_invalid_first_year_for_non_integer(self):
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCaseB3.execute("2020", 2024)

    def test_execute_raises_invalid_first_year_for_float(self):
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCaseB3.execute(2020.5, 2024)

    def test_execute_raises_invalid_first_year_for_none(self):
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCaseB3.execute(None, 2024)

    def test_execute_raises_invalid_last_year_for_year_before_initial(self):
        with pytest.raises(InvalidLastYear):
            CreateRangeYearsUseCaseB3.execute(2024, 2020)

    def test_execute_raises_invalid_last_year_for_future_year(self):
        future_year = date.today().year + 1
        with pytest.raises(InvalidLastYear):
            CreateRangeYearsUseCaseB3.execute(2020, future_year)

    def test_execute_raises_invalid_last_year_for_non_integer(self):
        with pytest.raises(InvalidLastYear):
            CreateRangeYearsUseCaseB3.execute(2020, "2024")

    def test_execute_raises_invalid_last_year_for_float(self):
        with pytest.raises(InvalidLastYear):
            CreateRangeYearsUseCaseB3.execute(2020, 2024.5)

    def test_execute_raises_invalid_last_year_for_none(self):
        with pytest.raises(InvalidLastYear):
            CreateRangeYearsUseCaseB3.execute(2020, None)

    def test_execute_is_static_method(self):
        result = CreateRangeYearsUseCaseB3.execute(2020, 2024)
        assert result is not None

    def test_execute_range_is_inclusive(self):
        result = CreateRangeYearsUseCaseB3.execute(2020, 2024)
        years = list(result)
        assert 2020 in years
        assert 2024 in years

    def test_execute_range_can_be_iterated(self):
        result = CreateRangeYearsUseCaseB3.execute(2020, 2022)
        years = []
        for year in result:
            years.append(year)
        assert years == [2020, 2021, 2022]

    def test_execute_range_supports_membership(self):
        result = CreateRangeYearsUseCaseB3.execute(2020, 2024)
        assert 2020 in result
        assert 2022 in result
        assert 2024 in result
        assert 2019 not in result
        assert 2025 not in result

    def test_execute_with_minimum_and_current_year(self):
        current_year = date.today().year
        result = CreateRangeYearsUseCaseB3.execute(1986, current_year)
        years = list(result)
        assert years[0] == 1986
        assert years[-1] == current_year
        assert len(years) == (current_year - 1986 + 1)

    def test_execute_raises_invalid_first_year_for_negative_year(self):
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCaseB3.execute(-2020, 2024)

    def test_execute_raises_invalid_first_year_for_zero(self):
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCaseB3.execute(0, 2024)
