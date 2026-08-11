"""Brazil source namespace.

Intermediate package — intentionally near-empty per the flat per-source
layout (design D6). Public classes are surfaced via
``globaldatafinance.application``. The lazy ``__getattr__`` below is a
fallback resolver kept for safety; callers should import from the
top-level ``globaldatafinance`` package.
"""


def __getattr__(name: str) -> object:
    """Lazy resolver for the public facade classes."""
    if name == 'FundamentalStocksDataCVM':
        from ..application.cvm_docs import FundamentalStocksDataCVM

        return FundamentalStocksDataCVM
    if name == 'HistoricalQuotesB3':
        from ..application.b3_docs import HistoricalQuotesB3

        return HistoricalQuotesB3
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


__all__ = ['FundamentalStocksDataCVM', 'HistoricalQuotesB3']
