"""Validate persisted inputs before resuming a real-validation campaign."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from globaldatafinance.macro_exceptions import SecurityError

from .real_validation_matrix import canonical_cvm_case, cases_from_manifest
from .real_validation_report import (
    REPORT_SCHEMA_VERSION,
    ReportFormatError,
    read_json,
)
from .real_validation_types import ValidationCase
from .real_validation_utils import validate_external_directory


def resume_cases(
    report_path: Path, *, hash_file: Callable[[Path], str]
) -> list[ValidationCase]:
    """Read a manifest and fail before execution if inputs drifted."""
    manifest = read_json(report_path / 'manifest.json')
    if manifest.get('schemaVersion') != REPORT_SCHEMA_VERSION:
        raise ReportFormatError('unsupported real-validation manifest version')
    decoded_cases = cases_from_manifest(manifest)
    cvm_output = _resume_cvm_output(manifest, decoded_cases)
    cases = _rebuild_resume_cvm_cases(decoded_cases, cvm_output)
    cotahist_cases = [case for case in cases if case.source == 'cotahist']
    if cotahist_cases:
        _validate_resume_cotahist_inputs(cotahist_cases, hash_file)
    return cases


def _rebuild_resume_cvm_cases(
    cases: list[ValidationCase], expected_output_root: str | None
) -> list[ValidationCase]:
    """Replace persisted CVM cases with code-owned canonical cases."""
    rebuilt: list[ValidationCase] = []
    for case in cases:
        if case.source != 'cvm':
            rebuilt.append(case)
            continue
        if expected_output_root is None:
            raise ReportFormatError(
                'manifest campaign must contain cvmOutput for CVM resume'
            )
        try:
            rebuilt.append(canonical_cvm_case(case, expected_output_root))
        except ValueError as error:
            raise ReportFormatError(
                f'resume CVM case is not in the official matrix for '
                f'caseId={case.case_id}: {error}'
            ) from error
    return rebuilt


def _resume_cvm_output(
    manifest: dict[str, Any], cases: list[ValidationCase]
) -> str | None:
    """Validate the persisted CVM destination before reconstruction."""
    if not any(case.source == 'cvm' for case in cases):
        return None
    campaign = manifest.get('campaign')
    if not isinstance(campaign, dict):
        raise ReportFormatError(
            'manifest campaign must contain cvmOutput for CVM resume'
        )
    raw_output = campaign.get('cvmOutput')
    if not isinstance(raw_output, str) or not raw_output.strip():
        raise ReportFormatError(
            'manifest campaign cvmOutput must be a non-empty directory'
        )
    try:
        return str(validate_external_directory(raw_output, '--cvm-output'))
    except (OSError, SecurityError, ValueError) as error:
        raise ReportFormatError(
            f'invalid manifest campaign cvmOutput: {error}'
        ) from error


def _validate_resume_cotahist_inputs(
    cases: list[ValidationCase], hash_file: Callable[[Path], str]
) -> None:
    normalized_paths = {
        case.case_id: Path(case.input_path).expanduser().resolve()
        for case in cases
    }
    for case in cases:
        path = normalized_paths[case.case_id]
        if not path.is_file():
            raise ReportFormatError(
                _resume_input_error(case, 'missing', str(path))
            )
    parent = _resume_input_parent(normalized_paths)
    catalog = _resume_catalog(cases[0], parent)
    available = {
        path.resolve() for paths in catalog.values() for path in paths
    }
    _validate_resume_input_paths(cases, normalized_paths, available)
    _validate_resume_cotahist_identity(cases, normalized_paths, catalog)
    snapshots = _resume_input_snapshots(cases, normalized_paths, hash_file)
    _validate_resume_snapshots(cases, normalized_paths, snapshots)


def _resume_input_parent(normalized_paths: dict[str, Path]) -> Path:
    """Require every COTAHIST case to use one input directory."""
    parents = {path.parent for path in normalized_paths.values()}
    if len(parents) != 1:
        raise ReportFormatError(
            'resume manifest contains COTAHIST inputs from multiple '
            'directories'
        )
    return parents.pop()


def _resume_catalog(
    case: ValidationCase, parent: Path
) -> dict[int, list[Path]]:
    """Load the current catalog and preserve its diagnostic cause."""
    from globaldatafinance.brazil.b3_data.historical_quotes.catalog import (
        CotahistCatalogError,
        validate_cotahist_catalog,
    )

    try:
        return validate_cotahist_catalog(parent)
    except CotahistCatalogError as error:
        raise ReportFormatError(
            _resume_input_error(
                case,
                'catalog_validation',
                str(error),
            )
        ) from error


def _validate_resume_input_paths(
    cases: list[ValidationCase],
    normalized_paths: dict[str, Path],
    available: set[Path],
) -> None:
    """Reject manifest inputs no longer present in the current catalog."""
    for case in cases:
        path = normalized_paths[case.case_id]
        if path not in available:
            raise ReportFormatError(
                _resume_input_error(case, 'missing', str(path))
            )


def _validate_resume_cotahist_identity(
    cases: list[ValidationCase],
    normalized_paths: dict[str, Path],
    catalog: dict[int, list[Path]],
) -> None:
    """Bind each persisted COTAHIST case to its current catalogued year."""
    year_by_path = {
        path.resolve(): year
        for year, paths in catalog.items()
        for path in paths
    }
    for case in cases:
        actual_year = year_by_path.get(normalized_paths[case.case_id])
        expected_id = f'cotahist-{case.mode}-{case.year}'
        if (
            actual_year != case.year
            or case.case_id != expected_id
            or case.output_root != ''
            or case.document is not None
            or case.url is not None
        ):
            raise ReportFormatError(
                _resume_input_error(
                    case,
                    'identity',
                    'caseId, year, source fields, outputRoot, or catalogued '
                    'input year does not match the COTAHIST matrix',
                )
            )


def _resume_input_snapshots(
    cases: list[ValidationCase],
    normalized_paths: dict[str, Path],
    hash_file: Callable[[Path], str],
) -> dict[Path, tuple[int, str]]:
    """Read size and SHA-256 once for every unique manifest input."""
    case_by_path: dict[Path, ValidationCase] = {}
    for case in cases:
        case_by_path.setdefault(normalized_paths[case.case_id], case)
    snapshots: dict[Path, tuple[int, str]] = {}
    for path in sorted(set(normalized_paths.values()), key=str):
        case = case_by_path[path]
        try:
            snapshots[path] = (path.stat().st_size, hash_file(path))
        except OSError as error:
            raise ReportFormatError(
                _resume_input_error(case, 'unreadable', f'{path}: {error}')
            ) from error
    return snapshots


def _validate_resume_snapshots(
    cases: list[ValidationCase],
    normalized_paths: dict[str, Path],
    snapshots: dict[Path, tuple[int, str]],
) -> None:
    """Compare recorded input size and hash with current content."""
    for case in cases:
        path = normalized_paths[case.case_id]
        current_size, current_hash = snapshots[path]
        if case.input_size_bytes is None or case.input_sha256 is None:
            raise ReportFormatError(
                _resume_input_error(
                    case,
                    'manifest_metadata',
                    'input_size_bytes and input_sha256 are required',
                )
            )
        drift = _resume_snapshot_drift(case, current_size, current_hash)
        if drift:
            raise ReportFormatError(
                _resume_input_error(case, 'changed', '; '.join(drift))
            )


def _resume_snapshot_drift(
    case: ValidationCase, current_size: int, current_hash: str
) -> list[str]:
    """Return stable field-level differences for one input snapshot."""
    if case.input_size_bytes is None or case.input_sha256 is None:
        return []
    drift: list[str] = []
    if current_size != case.input_size_bytes:
        drift.append(
            'input_size_bytes '
            f'expected={case.input_size_bytes} actual={current_size}'
        )
    if current_hash.casefold() != case.input_sha256.casefold():
        drift.append(
            f'input_sha256 expected={case.input_sha256} actual={current_hash}'
        )
    return drift


def _resume_input_error(
    case: ValidationCase, drift_type: str, detail: str
) -> str:
    """Build stable resume guidance without modifying existing results."""
    return (
        f'resume input drift for caseId={case.case_id}: '
        f'{drift_type} ({detail}). Start a new campaign; '
        'existing results were not modified.'
    )
