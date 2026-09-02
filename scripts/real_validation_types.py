"""Typed values shared by the opt-in real-validation campaign."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

CaseStatus = Literal[
    'passed',
    'failed',
    'skipped',
    'external_failure',
    'not_published',
]


class ExternalFailure(RuntimeError):
    """Indicate that a case could not be evaluated at its external boundary."""


class NotPublished(RuntimeError):
    """Indicate that the official CVM endpoint has no published archive."""


@dataclass(frozen=True)
class ValidationCase:
    """One isolated source/year or source/document/year execution."""

    case_id: str
    source: Literal['cotahist', 'cvm']
    year: int
    input_path: str
    output_root: str
    document: str | None = None
    mode: Literal['fast', 'parity', 'cvm'] = 'cvm'
    url: str | None = None
    input_size_bytes: int | None = None
    input_sha256: str | None = None

    def to_manifest_dict(self) -> dict[str, object]:
        """Serialize the case with stable keys and no runtime state."""
        return {
            'caseId': self.case_id,
            'source': self.source,
            'document': self.document,
            'year': self.year,
            'inputPath': self.input_path,
            'outputRoot': self.output_root,
            'mode': self.mode,
            'url': self.url,
            'inputSizeBytes': self.input_size_bytes,
            'inputSha256': self.input_sha256,
        }

    def command(self) -> list[str]:
        """Return the public operation represented by this case."""
        if self.source == 'cotahist':
            processing_mode = (
                'fast+slow' if self.mode == 'parity' else self.mode
            )
            return [
                'HistoricalQuotesB3.extract_async',
                f'path_of_docs={Path(self.input_path).parent}',
                'assets_list=[ações]',
                f'initial_year={self.year}',
                f'last_year={self.year}',
                f'processing_mode={processing_mode}',
                'automatic_network_access=False',
            ]
        return [
            'FundamentalStocksDataCVM.download',
            f'destination_path={self.output_root}',
            f'list_docs=[{self.document}]',
            f'initial_year={self.year}',
            f'last_year={self.year}',
            'automatic_extractor=True',
        ]
