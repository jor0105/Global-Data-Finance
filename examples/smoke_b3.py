"""Bit-stable behavioral smoke for `HistoricalQuotesB3().extract(...)`.

The smoke generates a deterministic COTAHIST ZIP fixture in a TMPDIR, runs the
public B3 extraction path, and emits canonical JSON capturing:

- `artifacts`: basename-only sorted list of Parquet files produced.
- `sha256`: hash of canonical content (records sorted + serialized as JSON) per
  artifact. We hash content rather than raw bytes because the production writer
  uses ZSTD + per-column statistics, which is not bit-stable across runs in
  subtle ways (statistics encoding, dictionary order). Content-hash preserves
  the design intent — catching regressions in parser/writer output — without
  brittle monkeypatching of the Polars/PyArrow writer.
- `schema`: column names + Arrow dtypes via `pyarrow.parquet.read_schema`.

Determinism rules followed:
- ZIP entries built via `zipfile.ZipInfo(filename, date_time=(1980,1,1,0,0,0))`.
- No `random`, `time`, `datetime.now`, `os.path.getmtime`, or filesystem
  timestamps captured in output.
- All paths normalized to `os.path.basename(...)`.
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


def _build_cotahist_line(
    data_pregao: str, ticker: str, tpmerc: str, isin: str
) -> str:
    """Build a single 245-byte COTAHIST type-01 record."""
    parts: list[str] = []

    def w(text: str, length: int) -> None:
        s = text.ljust(length)[:length]
        parts.append(s)

    w('01', 2)  # TIPREG
    w(data_pregao, 8)  # DATPREGAO (YYYYMMDD)
    w('02', 2)  # CODBDI
    w(ticker, 12)  # CODNEG
    w(tpmerc, 3)  # TPMERC
    w('PETROBRAS', 12)  # NOMRES
    w('PN     EJ', 10)  # ESPECI
    w('', 3)  # PRAZOT
    w('R$', 4)  # MODREF
    w('0000000050000', 13)  # PREABE
    w('0000000050000', 13)  # PREMAX
    w('0000000049000', 13)  # PREMIN
    w('0000000049500', 13)  # PREMED
    w('0000000049000', 13)  # PREULT
    w('0000000048900', 13)  # PREOFC
    w('0000000049100', 13)  # PREOFV
    w('00100', 5)  # TOTNEG
    w('000000000000010000', 18)  # QUATOT
    w('000000000050000000', 18)  # VOLTOT
    w('0000000000000', 13)  # PREEXE
    w(' ', 1)  # INDOPC
    w('00000000', 8)  # DATVEN (blank for cash)
    w('0000001', 7)  # FATCOT
    w('', 13)  # PTOEXE + reserved
    w(isin, 12)  # CODISI
    w('001', 3)  # DISMES

    line = ''.join(parts)
    if len(line) != 245:
        raise RuntimeError(f'COTAHIST line length {len(line)} != 245')
    return line


def _build_cotahist_txt() -> bytes:
    """Build the inner TXT contents of a COTAHIST ZIP — deterministic bytes."""
    header = '00COTAHIST.2023BOVESPA 20230102'.ljust(245)
    records = [
        _build_cotahist_line('20230102', 'PETR4', '010', 'BRPETRACNPR6'),
        _build_cotahist_line('20230103', 'PETR4', '010', 'BRPETRACNPR6'),
        _build_cotahist_line('20230102', 'VALE3', '010', 'BRVALEACNOR0'),
    ]
    trailer = '99COTAHIST.2023BOVESPA 20230102'.ljust(245)
    text = '\r\n'.join([header, *records, trailer]) + '\r\n'
    return text.encode('latin-1')


def _build_cotahist_zip(zip_path: Path) -> None:
    """Build a deterministic COTAHIST ZIP using ZipInfo with fixed mtime."""
    txt_bytes = _build_cotahist_txt()
    info = zipfile.ZipInfo(
        'COTAHIST_A2023.TXT', date_time=(1980, 1, 1, 0, 0, 0)
    )
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(zip_path, mode='w') as zf:
        zf.writestr(info, txt_bytes)


def _canonical_value(value: Any) -> Any:
    """Convert a parsed value to a canonical JSON-serializable form."""
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
    """Hash canonical content of a Parquet file (records sorted by key)."""
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
    """Capture column name → Arrow dtype mapping."""
    import pyarrow.parquet as pq

    schema = pq.read_schema(str(parquet_path))
    return {field.name: str(field.type) for field in schema}


def run() -> dict[str, Any]:
    from globaldatafinance import HistoricalQuotesB3

    tmpdir = Path(tempfile.mkdtemp(prefix='smoke_b3_'))
    try:
        docs_dir = tmpdir / 'docs'
        out_dir = tmpdir / 'out'
        docs_dir.mkdir()
        out_dir.mkdir()

        _build_cotahist_zip(docs_dir / 'COTAHIST_A2023.ZIP')

        b3 = HistoricalQuotesB3()
        # Silence the formatter's stdout chatter so JSON is the only output.
        with contextlib.redirect_stdout(io.StringIO()):
            b3.extract(
                path_of_docs=str(docs_dir),
                destination_path=str(out_dir),
                assets_list=['ações'],
                initial_year=2023,
                last_year=2023,
                output_filename='smoke',
                processing_mode='slow',
            )

        artifacts = sorted(
            p for p in out_dir.iterdir() if p.suffix == '.parquet'
        )
        return {
            'artifacts': [p.name for p in artifacts],
            'sha256': {p.name: _canonical_content_hash(p) for p in artifacts},
            'schema': {p.name: _capture_schema(p) for p in artifacts},
        }
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
