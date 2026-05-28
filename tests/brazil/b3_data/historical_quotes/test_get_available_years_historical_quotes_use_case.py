"""Unit tests for GetAvailableYearsUseCaseB3."""

from datetime import date

import pytest

from globaldatafinance.brazil.b3_data.historical_quotes.client import (
    GetAvailableYearsUseCaseB3,
)

pytestmark = pytest.mark.unit


class TestGetAvailableYearsUseCaseB3:
    @pytest.fixture
    def use_case(self):
        return GetAvailableYearsUseCaseB3()

    def test_get_current_year_returns_current_year(self, use_case):
        assert use_case.get_current_year() == date.today().year

    def test_get_current_year_returns_integer(self, use_case):
        assert isinstance(use_case.get_current_year(), int)

    def test_get_minimal_year_returns_1986(self, use_case):
        assert use_case.get_minimal_year() == 1986

    def test_minimal_year_less_than_current_year(self, use_case):
        assert use_case.get_minimal_year() < use_case.get_current_year()

    def test_year_range_span_is_reasonable(self, use_case):
        span = use_case.get_current_year() - use_case.get_minimal_year()
        assert 0 <= span < 200
