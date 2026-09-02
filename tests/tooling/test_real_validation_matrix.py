"""Deterministic tests for the real-validation case matrix."""

from __future__ import annotations

from dataclasses import replace
from os import sep
from pathlib import Path

import pytest

from scripts.real_validation_matrix import (
    _normalized_path,
    _selected_documents,
    build_cases,
    canonical_cvm_case,
    cases_from_manifest,
    manifest_for,
)
from scripts.real_validation_report import ReportFormatError
from scripts.real_validation_types import ValidationCase
from tests.support.builders import build_cotahist_record, write_cotahist_zip

pytestmark = pytest.mark.unit


def test_cotahist_matrix_builds_fast_parity_and_all_modes(
    tmp_path: Path,
) -> None:
    """Each requested B3 mode points at the catalogued annual input."""
    archive = write_cotahist_zip(
        tmp_path,
        year=2024,
        records=[build_cotahist_record(year=2024)],
    )

    fast = build_cases(
        source='cotahist',
        initial_year=2024,
        last_year=2024,
        document=None,
        cotahist_path=str(tmp_path),
        cvm_output=None,
        cotahist_modes='fast',
    )
    parity = build_cases(
        source='cotahist',
        initial_year=2024,
        last_year=2024,
        document=None,
        cotahist_path=str(tmp_path),
        cvm_output=None,
        cotahist_modes='parity',
    )
    all_modes = build_cases(
        source='cotahist',
        initial_year=2024,
        last_year=2024,
        document=None,
        cotahist_path=str(tmp_path),
        cvm_output=None,
        cotahist_modes='all',
    )

    assert [case.case_id for case in fast] == ['cotahist-fast-2024']
    assert [case.case_id for case in parity] == ['cotahist-parity-2024']
    assert {case.case_id for case in all_modes} == {
        'cotahist-fast-2024',
        'cotahist-parity-2024',
    }
    assert all(case.input_path == str(archive) for case in all_modes)
    assert all(
        case.input_size_bytes == archive.stat().st_size for case in fast
    )
    assert all(case.input_sha256 for case in all_modes)


def test_cotahist_matrix_rejects_missing_selected_year(tmp_path: Path) -> None:
    """A selected year must exist even when the catalog has another year."""
    write_cotahist_zip(
        tmp_path,
        year=2024,
        records=[build_cotahist_record(year=2024)],
    )

    with pytest.raises(ValueError, match='missing selected years'):
        build_cases(
            source='cotahist',
            initial_year=2023,
            last_year=2023,
            document=None,
            cotahist_path=str(tmp_path),
            cvm_output=None,
        )


@pytest.mark.parametrize(
    ('initial_year', 'last_year', 'message'),
    [
        (1999, 2024, '2000..2024'),
        (2024, 2025, '2000..2024'),
        (2024, 2023, '2000..2024'),
    ],
)
def test_cotahist_matrix_rejects_invalid_year_ranges(
    tmp_path: Path,
    initial_year: int,
    last_year: int,
    message: str,
) -> None:
    """The B3 matrix rejects ranges outside its supported annual window."""
    with pytest.raises(ValueError, match=message):
        build_cases(
            source='cotahist',
            initial_year=initial_year,
            last_year=last_year,
            document=None,
            cotahist_path=str(tmp_path),
            cvm_output=None,
        )


def test_all_matrix_combines_one_b3_case_with_one_cvm_case(
    tmp_path: Path,
) -> None:
    """The all-source request keeps both owners in one stable matrix."""
    input_directory = tmp_path / 'inputs'
    input_directory.mkdir()
    write_cotahist_zip(
        input_directory,
        year=2024,
        records=[build_cotahist_record(year=2024)],
    )

    cases = build_cases(
        source='all',
        initial_year=2024,
        last_year=2024,
        document='DFP',
        cotahist_path=str(input_directory),
        cvm_output=str(tmp_path / 'cvm-output'),
    )

    assert [case.case_id for case in cases] == [
        'cotahist-fast-2024',
        'cotahist-parity-2024',
        'cvm-DFP-2024',
    ]
    assert cases[-1].output_root == str((tmp_path / 'cvm-output').resolve())


def test_manifest_round_trip_normalizes_campaign_paths(tmp_path: Path) -> None:
    """Manifest serialization preserves case data and canonical paths."""
    case = ValidationCase(
        case_id='cvm-DFP-2024',
        source='cvm',
        year=2024,
        input_path='https://example.test/dfp.zip',
        output_root=str(tmp_path / 'output'),
        document='DFP',
        mode='cvm',
        url='https://example.test/dfp.zip',
    )

    manifest = manifest_for(
        [case],
        source='cvm',
        initial_year=2024,
        last_year=2024,
        document='DFP',
        cotahist_path=None,
        cvm_output=str(tmp_path / 'output'),
        timeout=12.5,
    )
    decoded = cases_from_manifest(manifest)

    assert manifest['campaign']['cotahistPath'] is None
    assert manifest['campaign']['cvmOutput'] == str(
        (tmp_path / 'output').resolve()
    )
    assert decoded == [case]
    assert _normalized_path(None) is None


def test_selected_documents_accepts_case_insensitive_names() -> None:
    """Document selection accepts the public spelling and preserves order."""
    assert _selected_documents(None)[0] == 'CGVN'
    assert _selected_documents('all')[-1] == 'VLMO'
    assert _selected_documents('dfp') == ('DFP',)


def test_selected_documents_rejects_unknown_document() -> None:
    """An unknown document cannot silently produce an empty matrix."""
    with pytest.raises(ValueError, match='unsupported CVM document'):
        _selected_documents('unknown')


def test_cvm_matrix_rejects_missing_output_and_invalid_years() -> None:
    """CVM cases require an output root and supported year bounds."""
    with pytest.raises(ValueError, match='--cvm-output'):
        build_cases(
            source='cvm',
            initial_year=None,
            last_year=None,
            document=None,
            cotahist_path=None,
            cvm_output=None,
        )
    with pytest.raises(ValueError, match=r'2010\.\.2026'):
        build_cases(
            source='cvm',
            initial_year=2009,
            last_year=2026,
            document=None,
            cotahist_path=None,
            cvm_output=str(Path(sep, 'tmp')),
        )


def test_cvm_matrix_can_have_no_cases_before_document_start(
    tmp_path: Path,
) -> None:
    """A valid global request may be empty for a document's later start."""
    cases = build_cases(
        source='cvm',
        initial_year=2010,
        last_year=2017,
        document='CGVN',
        cotahist_path=None,
        cvm_output=str(tmp_path),
    )

    assert cases == []


def test_canonical_cvm_case_rebuilds_and_compares_every_network_identity_field(
    tmp_path: Path,
) -> None:
    """A persisted CVM case cannot override code-owned document/year rules."""
    case = build_cases(
        source='cvm',
        initial_year=2024,
        last_year=2024,
        document='DFP',
        cotahist_path=None,
        cvm_output=str(tmp_path / 'output'),
    )[0]

    assert canonical_cvm_case(case, str(tmp_path / 'output')) == case

    tampered = replace(
        case,
        input_path='http://127.0.0.1/private',
        url='http://127.0.0.1/private',
    )
    with pytest.raises(ValueError, match='inputPath, url'):
        canonical_cvm_case(tampered, str(tmp_path / 'output'))

    with pytest.raises(ValueError, match='outputRoot'):
        canonical_cvm_case(case, str(tmp_path / 'other-output'))


def test_cases_from_manifest_rejects_corrupt_case_order_and_values() -> None:
    """Manifest decoding fails closed on structural matrix corruption."""
    case = ValidationCase(
        case_id='cvm-DFP-2024',
        source='cvm',
        year=2024,
        input_path='https://example.test/dfp.zip',
        output_root=str(Path(sep, 'tmp', 'output')),
        document='DFP',
        mode='cvm',
    )
    raw = case.to_manifest_dict()

    with pytest.raises(ReportFormatError, match='non-empty list'):
        cases_from_manifest({'cases': []})
    with pytest.raises(ReportFormatError, match='must be an object'):
        cases_from_manifest({'cases': [None]})
    with pytest.raises(ReportFormatError, match='unique and sorted'):
        cases_from_manifest({'cases': [raw, raw]})
    with pytest.raises(ReportFormatError, match='source must be one of'):
        cases_from_manifest({'cases': [{**raw, 'source': 'unknown'}]})


def test_cases_from_manifest_rejects_inconsistent_source_and_mode() -> None:
    """A COTAHIST case cannot use the CVM processing mode."""
    case = ValidationCase(
        case_id='cotahist-fast-2024',
        source='cotahist',
        year=2024,
        input_path=str(Path(sep, 'tmp', 'COTAHIST_A2024.ZIP')),
        output_root='',
        mode='fast',
    )

    with pytest.raises(ReportFormatError, match='inconsistent'):
        cases_from_manifest(
            {'cases': [{**case.to_manifest_dict(), 'mode': 'cvm'}]}
        )
