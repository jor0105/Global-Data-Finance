class InvalidFirstYearGeral(Exception):
    def __init__(self, minimal_first_year, atual_year):
        super().__init__(
            f"Invalid first year. You must provide an integer value greater than or equal to {minimal_first_year} and less than or equal to {atual_year}."
        )


class InvalidFirstYearCVGN(Exception):
    def __init__(self, minimal_first_year, atual_year):
        super().__init__(
            f"Invalid first year for CGVN. You must provide an integer value between {minimal_first_year} and {atual_year} (inclusive)."
        )


class InvalidLastYearGeral(Exception):
    def __init__(self, atual_year):
        super().__init__(
            f"Invalid last year. You must provide an integer value greater than or equal to the first year and less than or equal to {atual_year}."
        )
