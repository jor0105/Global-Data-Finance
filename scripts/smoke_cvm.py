"""Bit-stable behavioral smoke for `FundamentalStocksDataCVM().download(...)`.

The smoke patches `httpx.AsyncClient` to use an `httpx.MockTransport` that
serves a deterministic ZIP for every request, then drives the public CVM
download flow with `automatic_extractor=True` so the download → use-case →
adapter wiring (the path most affected by the refactor) is exercised end to end.

Output captures:

- `artifacts`: basename-only sorted list of files produced under `destination_path`.
- `sha256`: content-hash of Parquet files (canonical record JSON) and raw-bytes
  hash for everything else. Content-hashing the Parquet sidesteps PyArrow's
  non-deterministic stats/dictionary encoding without monkeypatching the writer.
- `schema`: Arrow schema (column name → dtype) for each Parquet artifact.

Determinism rules followed:
- ZIP entries built via `zipfile.ZipInfo(filename, date_time=(1980,1,1,0,0,0))`.
- No `random`, `time`, `datetime.now`, `os.path.getmtime`, or filesystem
  timestamps captured in output.
- All paths normalized to basename before serializing.
- Output JSON has `sort_keys=True`.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import zipfile
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx


def _build_cvm_csv() -> bytes:
    """Build a small CVM-style CSV (semicolon-delimited, latin-1)."""
    lines = [
        'CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA',
        '00.000.000/0001-91;2023-12-31;1;COMPANHIA A',
        '11.111.111/0001-11;2023-12-31;2;COMPANHIA B',
        '22.222.222/0001-22;2023-12-31;3;COMPANHIA C',
    ]
    return ('\r\n'.join(lines) + '\r\n').encode('latin-1')


def _build_cvm_zip_bytes() -> bytes:
    """Build a deterministic CVM-style ZIP with one CSV inside."""
    csv_bytes = _build_cvm_csv()
    buf = io.BytesIO()
    info = zipfile.ZipInfo(
        'dfp_cia_aberta_2023.csv', date_time=(1980, 1, 1, 0, 0, 0)
    )
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(buf, mode='w') as zf:
        zf.writestr(info, csv_bytes)
    return buf.getvalue()


_CVM_ZIP_BYTES = _build_cvm_zip_bytes()


def _mock_handler(request: httpx.Request) -> httpx.Response:
    """Mock transport: return the deterministic ZIP for every URL."""
    if request.method == 'HEAD':
        return httpx.Response(
            200,
            headers={'content-length': str(len(_CVM_ZIP_BYTES))},
        )
    return httpx.Response(
        200,
        headers={'content-length': str(len(_CVM_ZIP_BYTES))},
        content=_CVM_ZIP_BYTES,
    )


@contextlib.contextmanager
def _patched_httpx():
    """Patch httpx.AsyncClient so every instance routes through MockTransport."""
    transport = httpx.MockTransport(_mock_handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs['transport'] = transport
        original_init(self, *args, **kwargs)

    httpx.AsyncClient.__init__ = patched_init  # type: ignore[method-assign]
    try:
        yield
    finally:
        httpx.AsyncClient.__init__ = original_init  # type: ignore[method-assign]


def _canonical_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return f'{value:f}'
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode('latin-1')
    return value


def _canonical_content_hash(parquet_path: Path) -> str:
    import pyarrow.parquet as pq

    table = pq.read_table(str(parquet_path))
    records = table.to_pylist()
    canonical = [
        {k: _canonical_value(v) for k, v in sorted(rec.items())}
        for rec in records
    ]
    canonical.sort(key=lambda r: json.dumps(r, sort_keys=True, default=str))
    payload = json.dumps(
        canonical, sort_keys=True, separators=(',', ':'), default=str
    ).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def _capture_schema(parquet_path: Path) -> dict[str, str]:
    import pyarrow.parquet as pq

    schema = pq.read_schema(str(parquet_path))
    return {field.name: str(field.type) for field in schema}


def run() -> dict[str, Any]:
    from globaldatafinance import FundamentalStocksDataCVM

    tmpdir = Path(tempfile.mkdtemp(prefix='smoke_cvm_'))
    try:
        dest = tmpdir / 'out'
        dest.mkdir()

        with _patched_httpx():
            cvm = FundamentalStocksDataCVM()
            with contextlib.redirect_stdout(io.StringIO()):
                cvm.download(
                    destination_path=str(dest),
                    list_docs=['DFP'],
                    initial_year=2023,
                    last_year=2023,
                    automatic_extractor=True,
                )

        artifacts: list[Path] = sorted(
            p for p in dest.rglob('*') if p.is_file()
        )

        result: dict[str, Any] = {
            'artifacts': [p.name for p in artifacts],
            'sha256': {},
            'schema': {},
        }
        for p in artifacts:
            if p.suffix == '.parquet':
                result['sha256'][p.name] = _canonical_content_hash(p)
                result['schema'][p.name] = _capture_schema(p)
            else:
                result['sha256'][p.name] = hashlib.sha256(
                    p.read_bytes()
                ).hexdigest()
        return result
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main() -> int:
    payload = run()
    json.dump(
        payload, sys.stdout, sort_keys=True, indent=2, separators=(',', ': ')
    )
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
