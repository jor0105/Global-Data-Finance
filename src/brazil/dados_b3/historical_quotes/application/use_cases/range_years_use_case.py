from ...domain.value_objects.available_years import AvailableYears


class CreateRangeYearsUseCase:
    @staticmethod
    def execute(initial_year: int, last_year: int) -> range:
        return AvailableYears().return_range_years(initial_year, last_year)
