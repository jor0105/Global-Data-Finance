from dataclasses import dataclass, field

from src.brasil.dados_cvm.dados_fundamentalistas.domain.exceptions import (
    exceptions_entities,
)


@dataclass
class ListYearsToDownload:
    __ATUAL_YEAR: int = 2025
    __MIN_YEAR_GERAL = 2010
    __MIN_YEAR_ITR = 2011
    __MIN_YEAR_CGVN = 2018

    list_year_cgvn: list[int] = field(default_factory=list)
    list_year_dfp: list[int] = field(default_factory=list)
    list_year_itr: list[int] = field(default_factory=list)
    list_year_fre: list[int] = field(default_factory=list)
    list_year_fca: list[int] = field(default_factory=list)
    list_year_ipe: list[int] = field(default_factory=list)
    list_year_vlmo: list[int] = field(default_factory=list)

    @classmethod
    def update_list_year_cgvn(cls, first_year: int, last_year: int) -> None:
        if (
            not isinstance(first_year, int)
            or first_year < cls.__MIN_YEAR_CGVN
            or first_year > cls.__ATUAL_YEAR
        ):
            raise exceptions_entities.InvalidFirstYearCVGN(
                cls.__MIN_YEAR_CGVN, cls.__ATUAL_YEAR
            )
