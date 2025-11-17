import logging
from datetime import datetime

import pytest

from datafinc.brazil.cvm.fundamental_stocks_data import (
    GenerateRangeYearsUseCasesCVM,
    InvalidFirstYear,
    InvalidLastYear,
)


@pytest.mark.unit
class TestGenerateRangeYearsUseCasesInitialization:
    def test_initialization_succeeds(self):
        use_case_instance = GenerateRangeYearsUseCasesCVM()
        assert use_case_instance is not None

    def test_initialization_creates_available_years_instance(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        assert hasattr(use_case, "_GenerateRangeYearsUseCases__range_years")
        assert use_case._GenerateRangeYearsUseCases__range_years is not None

    def test_initialization_logs_debug_message(self, caplog):
        with caplog.at_level(logging.DEBUG):
            GenerateRangeYearsUseCasesCVM()

        assert any("initialized" in record.message.lower() for record in caplog.records)


@pytest.mark.unit
class TestGenerateRangeYearsUseCasesExecuteSuccess:
    def test_execute_with_valid_year_range_returns_range(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=2020, last_year=2023)

        assert isinstance(result, range)
        assert list(result) == [2020, 2021, 2022, 2023]

    def test_execute_with_single_year_returns_single_element_range(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=2023, last_year=2023)

        assert isinstance(result, range)
        assert list(result) == [2023]

    def test_execute_with_none_years_uses_defaults(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=None, last_year=None)

        assert isinstance(result, range)
        assert len(list(result)) > 0

    def test_execute_with_none_initial_year_uses_default(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=None, last_year=2023)

        assert isinstance(result, range)
        assert 2023 in list(result)

    def test_execute_with_none_last_year_uses_current_year(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        current_year = datetime.now().year
        result = use_case.execute(initial_year=2020, last_year=None)

        assert isinstance(result, range)
        assert 2020 in list(result)
        result_list = list(result)
        assert current_year in result_list or (current_year - 1) in result_list

    def test_execute_with_large_year_range(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=2010, last_year=2024)

        assert isinstance(result, range)
        assert len(list(result)) == 15

    def test_execute_returns_consecutive_years(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=2020, last_year=2025)

        result_list = list(result)
        for i in range(len(result_list) - 1):
            assert result_list[i + 1] - result_list[i] == 1


@pytest.mark.unit
class TestGenerateRangeYearsUseCasesExecuteErrors:
    def test_execute_with_invalid_initial_year_raises_error(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        with pytest.raises(InvalidFirstYear):
            use_case.execute(initial_year=1990, last_year=2023)

    def test_execute_with_future_last_year_raises_error(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        with pytest.raises(InvalidLastYear):
            use_case.execute(initial_year=2020, last_year=2050)

    def test_execute_with_initial_greater_than_last_raises_error(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        with pytest.raises(InvalidLastYear):
            use_case.execute(initial_year=2023, last_year=2020)

    def test_execute_with_non_integer_initial_year_raises_error(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        with pytest.raises((TypeError, InvalidFirstYear)):
            use_case.execute(initial_year="2020", last_year=2023)

    def test_execute_with_non_integer_last_year_raises_error(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        with pytest.raises((TypeError, InvalidLastYear)):
            use_case.execute(initial_year=2020, last_year="2023")

    def test_execute_with_float_years_raises_error(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        with pytest.raises((TypeError, InvalidFirstYear)):
            use_case.execute(initial_year=2020.5, last_year=2023)


@pytest.mark.unit
class TestGenerateRangeYearsUseCasesLogging:
    def test_execute_logs_debug_message(self, caplog):
        use_case = GenerateRangeYearsUseCasesCVM()

        with caplog.at_level(logging.DEBUG):
            use_case.execute(initial_year=2020, last_year=2023)

        assert any("generating" in record.message.lower() for record in caplog.records)

    def test_execute_logs_info_message_with_range(self, caplog):
        use_case = GenerateRangeYearsUseCasesCVM()

        with caplog.at_level(logging.INFO):
            use_case.execute(initial_year=2020, last_year=2023)

        assert any(
            "generated range" in record.message.lower() for record in caplog.records
        )

    def test_execute_logs_error_on_exception(self, caplog):
        use_case = GenerateRangeYearsUseCasesCVM()

        with pytest.raises(InvalidFirstYear):
            with caplog.at_level(logging.ERROR):
                use_case.execute(initial_year=1990, last_year=2023)

        assert any("failed" in record.message.lower() for record in caplog.records)


@pytest.mark.unit
class TestGenerateRangeYearsUseCasesEdgeCases:
    def test_execute_multiple_calls_consistent(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        result1 = use_case.execute(initial_year=2020, last_year=2023)
        result2 = use_case.execute(initial_year=2020, last_year=2023)

        assert list(result1) == list(result2)

    def test_execute_with_minimum_valid_year(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        result = use_case.execute(initial_year=2010, last_year=2012)

        assert isinstance(result, range)
        assert 2010 in list(result)

    def test_execute_with_current_year(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        current_year = datetime.now().year

        result = use_case.execute(initial_year=current_year, last_year=current_year)

        assert isinstance(result, range)
        assert list(result) == [current_year]

    def test_execute_range_is_iterable(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=2020, last_year=2023)

        count = 0
        for year in result:
            count += 1
            assert isinstance(year, int)

        assert count == 4

    def test_execute_range_supports_len(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=2020, last_year=2025)

        assert len(result) == 6

    def test_execute_range_supports_membership(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=2020, last_year=2025)

        assert 2022 in result
        assert 2019 not in result
        assert 2026 not in result


@pytest.mark.unit
class TestGenerateRangeYearsUseCasesIntegration:
    def test_execute_integrates_with_available_years(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        result = use_case.execute(initial_year=2020, last_year=2023)

        assert isinstance(result, range)
        assert len(list(result)) == 4

    def test_execute_respects_available_years_constraints(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        with pytest.raises(InvalidFirstYear):
            use_case.execute(initial_year=1900, last_year=2023)

    def test_execute_respects_current_year_constraint(self):
        use_case = GenerateRangeYearsUseCasesCVM()

        with pytest.raises(InvalidLastYear):
            use_case.execute(initial_year=2020, last_year=2100)

    def test_execute_can_be_used_in_loops(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=2020, last_year=2023)

        years_collected = [year for year in result]
        assert years_collected == [2020, 2021, 2022, 2023]

    def test_execute_result_can_be_converted_to_list(self):
        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=2020, last_year=2023)

        result_list = list(result)

        assert result_list == [2020, 2021, 2022, 2023]
        assert isinstance(result_list, list)


@pytest.mark.unit
class TestGenerateRangeYearsUseCasesPerformance:
    def test_execute_performance_large_range(self):
        import time

        use_case = GenerateRangeYearsUseCasesCVM()

        start_time = time.time()
        result = use_case.execute(initial_year=2010, last_year=2024)
        elapsed = time.time() - start_time

        assert elapsed < 0.1
        assert len(result) == 15

    def test_execute_memory_efficiency(self):
        import sys

        use_case = GenerateRangeYearsUseCasesCVM()
        result = use_case.execute(initial_year=2010, last_year=2024)

        assert sys.getsizeof(result) < 100
