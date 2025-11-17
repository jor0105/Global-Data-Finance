from datetime import date
from unittest.mock import patch

import pytest

from datafinc.brazil.dados_b3.historical_quotes.domain.exceptions import (
    InvalidFirstYear,
    InvalidLastYear,
)
from datafinc.brazil.dados_b3.historical_quotes.domain.services import (
    YearValidationService,
)
from datafinc.brazil.dados_b3.historical_quotes.domain.value_objects import YearRange


class TestGetCurrentYear:
    def test_returns_current_year(self):
        expected_year = date.today().year
        result = YearValidationService.get_current_year()
        assert result == expected_year

    def test_returns_integer(self):
        result = YearValidationService.get_current_year()
        assert isinstance(result, int)

    def test_returns_reasonable_year(self):
        result = YearValidationService.get_current_year()
        assert result >= 2020
        assert result <= 2100

    def test_is_class_method(self):
        result = YearValidationService.get_current_year()
        assert result is not None


class TestGetMinYear:
    def test_returns_1986(self):
        result = YearValidationService.get_min_year()
        assert result == 1986

    def test_returns_integer(self):
        result = YearValidationService.get_min_year()
        assert isinstance(result, int)

    def test_is_class_method(self):
        result = YearValidationService.get_min_year()
        assert result is not None

    def test_min_year_is_constant(self):
        result1 = YearValidationService.get_min_year()
        result2 = YearValidationService.get_min_year()
        assert result1 == result2


class TestValidateAndCreateYearRange:
    def test_creates_valid_year_range(self):
        initial_year = 2020
        last_year = 2024
        result = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )
        assert isinstance(result, YearRange)
        assert result.initial_year == initial_year
        assert result.last_year == last_year

    def test_creates_range_with_same_year(self):
        year = 2020
        result = YearValidationService.validate_and_create_year_range(year, year)
        assert result.initial_year == year
        assert result.last_year == year

    def test_creates_range_from_min_year_to_current(self):
        initial_year = 1986
        last_year = date.today().year
        result = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )
        assert result.initial_year == 1986
        assert result.last_year == last_year

    def test_creates_range_for_single_recent_year(self):
        year = date.today().year
        result = YearValidationService.validate_and_create_year_range(year, year)
        assert result.initial_year == year
        assert result.last_year == year

    def test_raises_invalid_first_year_for_year_before_1986(self):
        initial_year = 1985
        last_year = 2024
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_first_year_for_future_year(self):
        initial_year = date.today().year + 1
        last_year = date.today().year + 2
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_first_year_for_non_integer(self):
        initial_year = "2020"
        last_year = 2024
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_first_year_for_float(self):
        initial_year = 2020.5
        last_year = 2024
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_first_year_for_none(self):
        initial_year = None
        last_year = 2024
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_last_year_for_year_before_initial(self):
        initial_year = 2024
        last_year = 2020
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_last_year_for_future_year(self):
        initial_year = 2020
        last_year = date.today().year + 1
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_last_year_for_non_integer(self):
        initial_year = 2020
        last_year = "2024"
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_last_year_for_float(self):
        initial_year = 2020
        last_year = 2024.5
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_last_year_for_none(self):
        initial_year = 2020
        last_year = None
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_accepts_min_year_as_initial(self):
        initial_year = 1986
        last_year = 2000
        result = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )
        assert result.initial_year == 1986

    def test_accepts_current_year_as_last(self):
        current_year = date.today().year
        initial_year = 2020
        last_year = current_year
        result = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )
        assert result.last_year == current_year

    def test_validates_with_mocked_current_year(self):
        initial_year = 2020
        last_year = 2023
        with patch(
            "datafinc.brazil.dados_b3.historical_quotes.domain.services.year_validation_service.date"
        ) as mock_date:
            mock_date.today.return_value.year = 2024
            result = YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )
        assert result.initial_year == initial_year
        assert result.last_year == last_year

    def test_validates_long_year_range(self):
        initial_year = 1986
        last_year = date.today().year
        result = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )
        years_in_range = list(result.to_range())
        assert len(years_in_range) == (last_year - initial_year + 1)

    def test_raises_invalid_first_year_for_negative_year(self):
        initial_year = -2020
        last_year = 2024
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_first_year_for_zero(self):
        initial_year = 0
        last_year = 2024
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_is_class_method(self):
        result = YearValidationService.validate_and_create_year_range(2020, 2024)
        assert result is not None

    def test_exception_contains_correct_min_year(self):
        initial_year = 1985
        last_year = 2024
        with pytest.raises(InvalidFirstYear) as exc_info:
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )
        assert "1986" in str(exc_info.value)

    def test_exception_contains_correct_current_year(self):
        initial_year = date.today().year + 1
        last_year = date.today().year + 2
        with pytest.raises(InvalidFirstYear) as exc_info:
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )
        assert str(date.today().year) in str(exc_info.value)
