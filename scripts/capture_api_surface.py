"""Capture the public API surface of `globaldatafinance` as deterministic JSON.

The surface captured is intentionally narrow:

- `top_level_exports`: `sorted(globaldatafinance.__all__)` — the names the package
  officially re-exports at the root.
- `signatures`: `str(inspect.signature(...))` for each public method of the two
  public classes (`FundamentalStocksDataCVM`, `HistoricalQuotesB3`).
- `repr`: `repr(...)` of a default-constructed instance of each public class.

Items deliberately NOT captured: `__doc__`, inferred exception names, or `dir()`
of instances. Behavioral guarantees for exceptions stay in delta specs + tests;
incidental collaborator attributes must not become contract by accident.

Output: JSON to stdout with `sort_keys=True` and stable separators. Idempotent.
"""

from __future__ import annotations

import inspect
import json
import re
import sys
from typing import Any

# Strip internal module prefixes from annotation strings so the signature is
# stable across internal module moves. The public class name (e.g.
# `DownloadResultCVM`) is preserved; only the path prefix (e.g.
# `globaldatafinance.brazil.cvm.fundamental_stocks_data.domain.download_result.`)
# is removed. This keeps the API surface diff focused on observable shape, not
# internal package layout — which is exactly the scope of this refactor.
_MODULE_PREFIX = re.compile(r'\bglobaldatafinance\.[\w.]+?\.(?=[A-Z])')


def _normalize_signature(text: str) -> str:
    return _MODULE_PREFIX.sub('', text)


def _capture_signatures(cls: type, method_names: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in method_names:
        method = getattr(cls, name)
        out[name] = _normalize_signature(str(inspect.signature(method)))
    return out


def capture() -> dict[str, Any]:
    import globaldatafinance as gdf
    from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3

    cvm_methods = [
        '__init__',
        'download',
        'get_available_docs',
        'get_available_years',
    ]
    b3_methods = [
        '__init__',
        'extract',
        'get_available_assets',
        'get_available_years',
    ]

    return {
        'top_level_exports': sorted(gdf.__all__),
        'signatures': {
            'FundamentalStocksDataCVM': _capture_signatures(
                FundamentalStocksDataCVM, cvm_methods
            ),
            'HistoricalQuotesB3': _capture_signatures(
                HistoricalQuotesB3, b3_methods
            ),
        },
        'repr': {
            'FundamentalStocksDataCVM': repr(FundamentalStocksDataCVM()),
            'HistoricalQuotesB3': repr(HistoricalQuotesB3()),
        },
    }


def main() -> int:
    payload = capture()
    json.dump(
        payload, sys.stdout, sort_keys=True, indent=2, separators=(',', ': ')
    )
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
