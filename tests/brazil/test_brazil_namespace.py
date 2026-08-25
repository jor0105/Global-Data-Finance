import pytest

import globaldatafinance.brazil as brazil_ns
from globaldatafinance.application.b3_docs import HistoricalQuotesB3
from globaldatafinance.application.cvm_docs import FundamentalStocksDataCVM

pytestmark = pytest.mark.unit


def test_brazil_namespace_lazy_exports() -> None:
    assert brazil_ns.FundamentalStocksDataCVM is FundamentalStocksDataCVM
    assert brazil_ns.HistoricalQuotesB3 is HistoricalQuotesB3


def test_brazil_namespace_raises_attribute_error_for_unknown_attribute() -> (
    None
):
    with pytest.raises(AttributeError) as exc_info:
        _ = brazil_ns.NonExistentService

    assert (
        "module 'globaldatafinance.brazil' has no attribute 'NonExistentService'"
        in str(exc_info.value)
    )
