"""Opt-in real-data campaign CLI for COTAHIST and CVM sources."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from globaldatafinance.macro_exceptions import SecurityError
from scripts.real_validation_matrix import Source, build_cases, manifest_for
from scripts.real_validation_report import (
    REPORT_SCHEMA_VERSION,
    ReportFormatError,
    write_json,
)
from scripts.real_validation_runner import resume_cases, run_campaign
from scripts.real_validation_types import ValidationCase
from scripts.real_validation_utils import validate_external_directory


def main(argv: list[str] | None = None) -> int:
    """Run the requested campaign and return its audit gate exit code."""
    args = _build_parser().parse_args(argv)
    try:
        report_path = _validate_report_path(args.report)
        cvm_output = _validate_optional_external_directory(
            args.cvm_output, '--cvm-output'
        )
        timeout = _positive_timeout(args.timeout)
        if args.resume:
            cases = resume_cases(report_path)
            _validate_case_output_roots(cases)
        else:
            source = _required_source(args.source)
            cases = build_cases(
                source=source,
                initial_year=args.initial_year,
                last_year=args.last_year,
                document=args.document,
                cotahist_path=args.cotahist_path,
                cvm_output=cvm_output,
                cotahist_modes=args.cotahist_mode,
            )
            cases = _filter_cases(cases, args.case)
            _validate_case_output_roots(cases)
            write_json(
                report_path / 'manifest.json',
                manifest_for(
                    cases,
                    source=source,
                    initial_year=args.initial_year,
                    last_year=args.last_year,
                    document=args.document,
                    cotahist_path=args.cotahist_path,
                    cvm_output=cvm_output,
                    timeout=timeout,
                ),
            )
        return run_campaign(report_path, cases, timeout)
    except (OSError, ReportFormatError, SecurityError, ValueError) as error:
        _emit_error('invalid_campaign', str(error))
        return 3


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            'Run one isolated, explicitly configured real-data validation '
            'campaign and write an external evidence report.'
        )
    )
    parser.add_argument(
        '--source', choices=('cotahist', 'cvm', 'all'), help='source matrix'
    )
    parser.add_argument(
        '--cotahist-path',
        help='caller-owned directory containing COTAHIST files',
    )
    parser.add_argument(
        '--cvm-output',
        help='caller-owned directory for CVM extracted artifacts',
    )
    parser.add_argument('--initial-year', type=int)
    parser.add_argument('--last-year', type=int)
    parser.add_argument('--document', help='CVM document code or all')
    parser.add_argument(
        '--cotahist-mode',
        choices=('fast', 'parity', 'all'),
        default='all',
        help='COTAHIST cases to include; parity executes fast and slow',
    )
    parser.add_argument(
        '--case',
        help='run only this case ID after building the requested matrix',
    )
    parser.add_argument(
        '--report',
        required=True,
        help='external directory for campaign evidence',
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=60.0,
        help='per-case process timeout in seconds',
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='resume the case matrix recorded in report/manifest.json',
    )
    return parser


def _required_source(value: str | None) -> Source:
    if value is None:
        raise ValueError('--source is required unless --resume is used')
    return cast(Source, value)


def _positive_timeout(value: float) -> float:
    if value <= 0:
        raise ValueError('--timeout must be greater than zero')
    return value


def _validate_report_path(raw_path: str) -> Path:
    return _validate_external_directory(raw_path, '--report')


def _validate_optional_external_directory(
    raw_path: str | None, label: str
) -> str | None:
    """Validate an optional caller-owned output before building cases."""
    if raw_path is None:
        return None
    return str(_validate_external_directory(raw_path, label))


def _validate_external_directory(raw_input: str, label: str) -> Path:
    """Validate one caller-owned directory before any write."""
    return validate_external_directory(raw_input, label)


def _validate_case_output_roots(cases: list[ValidationCase]) -> None:
    validated: set[str] = set()
    for case in cases:
        if case.source != 'cvm':
            continue
        if not case.output_root:
            raise ValueError(
                f'CVM case has no output directory: {case.case_id}'
            )
        if case.output_root in validated:
            continue
        _validate_external_directory(
            case.output_root, f'CVM output for {case.case_id}'
        )
        validated.add(case.output_root)


def _filter_cases(
    cases: list[ValidationCase], case_id: str | None
) -> list[ValidationCase]:
    if case_id is None:
        return cases
    selected = [case for case in cases if case.case_id == case_id]
    if not selected:
        raise ValueError(f'unknown validation case: {case_id}')
    return selected


def _emit_error(code: str, message: str) -> None:
    payload: dict[str, Any] = {
        'schemaVersion': REPORT_SCHEMA_VERSION,
        'code': code,
        'message': message,
    }
    sys.stderr.write(
        json.dumps(payload, ensure_ascii=True, sort_keys=True) + '\n'
    )


if __name__ == '__main__':
    sys.exit(main())
