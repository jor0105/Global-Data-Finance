"""Build and decode the deterministic real-validation case matrix."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

from globaldatafinance.brazil.b3_data.historical_quotes.catalog import (
    CotahistCatalogError,
    select_cotahist_file,
    validate_cotahist_catalog,
)

from .real_validation_report import REPORT_SCHEMA_VERSION, ReportFormatError
from .real_validation_types import ValidationCase
from .real_validation_utils import sha256_file

Source = Literal['cotahist', 'cvm', 'all']

COTAHIST_START = 2000
COTAHIST_END = 2024
CVM_START = 2010
CVM_END = 2026
CVM_DOCUMENT_WINDOWS: dict[str, tuple[int, int]] = {
    'CGVN': (2018, 2026),
    'FRE': (2010, 2026),
    'FCA': (2010, 2026),
    'DFP': (2010, 2026),
    'ITR': (2011, 2026),
    'IPE': (2010, 2026),
    'VLMO': (2018, 2026),
}
_CVM_DOCUMENT_ORDER = tuple(CVM_DOCUMENT_WINDOWS)


def build_cases(
    *,
    source: Source,
    initial_year: int | None,
    last_year: int | None,
    document: str | None,
    cotahist_path: str | None,
    cvm_output: str | None,
    cotahist_modes: Literal['fast', 'parity', 'all'] = 'all',
) -> list[ValidationCase]:
    """Build a stable case matrix without reading environment variables."""
    cases: list[ValidationCase] = []
    if source in {'cotahist', 'all'}:
        cases.extend(
            _build_cotahist_cases(
                cotahist_path,
                initial_year,
                last_year,
                cotahist_modes,
            )
        )
    if source in {'cvm', 'all'}:
        cases.extend(
            _build_cvm_cases(
                cvm_output,
                initial_year,
                last_year,
                document,
            )
        )
    return sorted(cases, key=lambda case: case.case_id)


def manifest_for(
    cases: list[ValidationCase],
    *,
    source: Source,
    initial_year: int | None,
    last_year: int | None,
    document: str | None,
    cotahist_path: str | None,
    cvm_output: str | None,
    timeout: float,
) -> dict[str, Any]:
    """Create the deterministic manifest consumed by ``--resume``."""
    return {
        'schemaVersion': REPORT_SCHEMA_VERSION,
        'campaign': {
            'source': source,
            'cotahistPath': _normalized_path(cotahist_path),
            'cvmOutput': _normalized_path(cvm_output),
            'initialYear': initial_year,
            'lastYear': last_year,
            'document': document,
            'timeoutSeconds': timeout,
        },
        'cases': [case.to_manifest_dict() for case in cases],
    }


def cases_from_manifest(manifest: dict[str, Any]) -> list[ValidationCase]:
    """Decode and validate the sorted case list from a prior run."""
    raw_cases = manifest.get('cases')
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ReportFormatError('manifest cases must be a non-empty list')
    cases = [_case_from_dict(item) for item in raw_cases]
    ids = [case.case_id for case in cases]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ReportFormatError('manifest cases must be unique and sorted')
    return cases


def canonical_cvm_case(
    case: ValidationCase, expected_output_root: str
) -> ValidationCase:
    """Rebuild and validate one CVM case from the official matrix.

    A persisted campaign manifest is evidence, not authority for a network
    endpoint.  Resume and worker paths use this helper before any CVM request
    so every identity field and the endpoint are derived from code-owned
    document/year rules.

    Args:
        case: CVM case decoded from a manifest or supplied to a worker.
        expected_output_root: Validated campaign destination that owns the
            CVM output for this case.

    Returns:
        The reconstructed official CVM case.

    Raises:
        ValueError: If ``case`` cannot be represented by the official matrix.
    """
    if case.source != 'cvm':
        raise ValueError('only CVM cases can be reconstructed')
    if case.document is None:
        raise ValueError('CVM case document is required')

    expected_cases = _build_cvm_cases(
        expected_output_root,
        case.year,
        case.year,
        case.document,
    )
    if len(expected_cases) != 1:
        raise ValueError(
            'CVM case is outside the official document/year matrix'
        )

    expected = expected_cases[0]
    mismatches = _cvm_case_mismatches(case, expected)
    if mismatches:
        raise ValueError(
            'CVM case does not match the official matrix: '
            + ', '.join(mismatches)
        )
    return expected


def _build_cotahist_cases(
    raw_path: str | None,
    initial_year: int | None,
    last_year: int | None,
    modes: Literal['fast', 'parity', 'all'],
) -> list[ValidationCase]:
    if not raw_path:
        raise ValueError('--cotahist-path is required for COTAHIST cases')
    start = COTAHIST_START if initial_year is None else initial_year
    end = COTAHIST_END if last_year is None else last_year
    if start < COTAHIST_START or end > COTAHIST_END or start > end:
        raise ValueError('COTAHIST years must be within 2000..2024')
    expected = range(COTAHIST_START, COTAHIST_END + 1)
    exact = start == COTAHIST_START and end == COTAHIST_END
    catalog = validate_cotahist_catalog(
        raw_path, expected_years=expected if exact else None
    )
    missing = set(range(start, end + 1)) - set(catalog)
    if missing:
        raise CotahistCatalogError(
            f'COTAHIST catalog is missing selected years: {sorted(missing)}'
        )
    selected_by_year = {
        year: select_cotahist_file(catalog, year)
        for year in range(start, end + 1)
    }
    cases: list[ValidationCase] = []
    for year, path in selected_by_year.items():
        size_bytes = path.stat().st_size
        file_hash = sha256_file(path)
        if modes in {'fast', 'all'}:
            cases.append(
                ValidationCase(
                    case_id=f'cotahist-fast-{year}',
                    source='cotahist',
                    year=year,
                    input_path=str(path),
                    output_root='',
                    mode='fast',
                    input_size_bytes=size_bytes,
                    input_sha256=file_hash,
                )
            )
        if modes in {'parity', 'all'}:
            cases.append(
                ValidationCase(
                    case_id=f'cotahist-parity-{year}',
                    source='cotahist',
                    year=year,
                    input_path=str(path),
                    output_root='',
                    mode='parity',
                    input_size_bytes=size_bytes,
                    input_sha256=file_hash,
                )
            )
    return cases


def _build_cvm_cases(
    raw_output: str | None,
    initial_year: int | None,
    last_year: int | None,
    document: str | None,
) -> list[ValidationCase]:
    if not raw_output:
        raise ValueError('--cvm-output is required for CVM cases')
    output_root = _normalized_path(raw_output)
    if output_root is None:
        raise ValueError('--cvm-output is required for CVM cases')
    start = CVM_START if initial_year is None else initial_year
    end = CVM_END if last_year is None else last_year
    if start < CVM_START or end > CVM_END or start > end:
        raise ValueError('CVM years must be within 2010..2026')
    cases: list[ValidationCase] = []
    for item in _selected_documents(document):
        first_valid, last_valid = CVM_DOCUMENT_WINDOWS[item]
        for year in range(max(start, first_valid), min(end, last_valid) + 1):
            url = (
                'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/'
                f'{item}/DADOS/{item.lower()}_cia_aberta_{year}.zip'
            )
            cases.append(
                ValidationCase(
                    case_id=f'cvm-{item}-{year}',
                    source='cvm',
                    year=year,
                    input_path=url,
                    output_root=output_root,
                    document=item,
                    mode='cvm',
                    url=url,
                )
            )
    return cases


def _cvm_case_mismatches(
    actual: ValidationCase, expected: ValidationCase
) -> list[str]:
    """Return the persisted CVM fields that differ from the official case."""
    fields = (
        ('caseId', actual.case_id, expected.case_id),
        ('source', actual.source, expected.source),
        ('document', actual.document, expected.document),
        ('year', actual.year, expected.year),
        ('mode', actual.mode, expected.mode),
        ('inputPath', actual.input_path, expected.input_path),
        ('outputRoot', actual.output_root, expected.output_root),
        ('url', actual.url, expected.url),
        ('inputSizeBytes', actual.input_size_bytes, expected.input_size_bytes),
        ('inputSha256', actual.input_sha256, expected.input_sha256),
    )
    return [
        name
        for name, actual_value, expected_value in fields
        if actual_value != expected_value
    ]


def _normalized_path(raw_path: str | None) -> str | None:
    """Return an absolute caller path without creating or inspecting it."""
    if raw_path is None:
        return None
    return str(Path(raw_path).expanduser().resolve())


def _selected_documents(document: str | None) -> tuple[str, ...]:
    if document is None or document.casefold() == 'all':
        return _CVM_DOCUMENT_ORDER
    normalized = document.strip().upper()
    if normalized not in CVM_DOCUMENT_WINDOWS:
        available = ', '.join(_CVM_DOCUMENT_ORDER)
        raise ValueError(
            f'unsupported CVM document {document!r}; available: {available}'
        )
    return (normalized,)


def _case_from_dict(value: object) -> ValidationCase:
    if not isinstance(value, dict):
        raise ReportFormatError('manifest case must be an object')
    source = _manifest_choice(value, 'source', {'cotahist', 'cvm'})
    mode = _manifest_choice(value, 'mode', {'fast', 'parity', 'cvm'})
    if (source == 'cotahist') != (mode != 'cvm'):
        raise ReportFormatError(
            'manifest source and processing mode are inconsistent'
        )
    case_id = _manifest_string(value, 'caseId')
    year = _manifest_integer(value, 'year')
    input_path = _manifest_string(value, 'inputPath')
    output_root = _manifest_string(value, 'outputRoot')
    document = _manifest_optional_string(value, 'document')
    url = _manifest_optional_string(value, 'url')
    size = _manifest_optional_integer(value, 'inputSizeBytes')
    file_hash = _manifest_optional_string(value, 'inputSha256')
    return ValidationCase(
        case_id=case_id,
        source=cast(Literal['cotahist', 'cvm'], source),
        year=year,
        input_path=input_path,
        output_root=output_root,
        document=document,
        mode=cast(Literal['fast', 'parity', 'cvm'], mode),
        url=url,
        input_size_bytes=size,
        input_sha256=file_hash,
    )


def _manifest_choice(
    value: dict[object, object], key: str, choices: set[str]
) -> str:
    candidate = value.get(key)
    if not isinstance(candidate, str) or candidate not in choices:
        options = ', '.join(sorted(choices))
        raise ReportFormatError(f'manifest {key} must be one of: {options}')
    return candidate


def _manifest_string(value: dict[object, object], key: str) -> str:
    candidate = value.get(key)
    if not isinstance(candidate, str):
        raise ReportFormatError(f'manifest {key} must be a string')
    return candidate


def _manifest_optional_string(
    value: dict[object, object], key: str
) -> str | None:
    candidate = value.get(key)
    if candidate is not None and not isinstance(candidate, str):
        raise ReportFormatError(f'manifest {key} must be a string or null')
    return candidate


def _manifest_integer(value: dict[object, object], key: str) -> int:
    candidate = value.get(key)
    if not isinstance(candidate, int) or isinstance(candidate, bool):
        raise ReportFormatError(f'manifest {key} must be an integer')
    return candidate


def _manifest_optional_integer(
    value: dict[object, object], key: str
) -> int | None:
    candidate = value.get(key)
    if candidate is not None and (
        not isinstance(candidate, int) or isinstance(candidate, bool)
    ):
        raise ReportFormatError(f'manifest {key} must be an integer or null')
    return candidate
