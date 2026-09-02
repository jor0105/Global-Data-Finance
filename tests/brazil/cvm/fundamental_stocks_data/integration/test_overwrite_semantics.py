import zipfile
from pathlib import Path

import pandas as pd
import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data.extract import (
    ParquetExtractorAdapterCVM,
)

pytestmark = pytest.mark.integration


def _write_archive(
    archive_path: Path, members: list[tuple[str, pd.DataFrame]]
) -> None:
    with zipfile.ZipFile(archive_path, 'w') as archive:
        for filename, dataframe in members:
            archive.writestr(
                filename,
                dataframe.to_csv(sep=';', index=False).encode('latin-1'),
            )


class TestEstablishedOverwriteSemantics:
    def test_same_csv_basename_replaces_existing_parquet(self, tmp_path):
        original_data = pd.DataFrame(
            {'id': [1, 2], 'value': [100, 200], 'state': ['old', 'old']}
        )
        replacement_data = pd.DataFrame(
            {
                'id': [10, 20, 30],
                'value': [900, 800, 700],
                'state': ['new'] * 3,
            }
        )
        output_path = tmp_path / 'data.parquet'
        original_data.to_parquet(output_path)

        archive_path = tmp_path / 'replacement.zip'
        _write_archive(archive_path, [('data.csv', replacement_data)])

        ParquetExtractorAdapterCVM().extract(
            source_path=str(archive_path), destination_path=str(tmp_path)
        )

        pd.testing.assert_frame_equal(
            pd.read_parquet(output_path), replacement_data
        )
        assert sorted(path.name for path in tmp_path.glob('*.parquet')) == [
            'data.parquet'
        ]

    def test_multiple_sequential_replacements_keep_latest_data(self, tmp_path):
        output_path = tmp_path / 'data.parquet'
        first_data = pd.DataFrame({'version': [1], 'value': ['first']})
        second_data = pd.DataFrame({'version': [2, 2], 'value': ['last'] * 2})

        for index, dataframe in enumerate((first_data, second_data), start=1):
            archive_path = tmp_path / f'replacement_{index}.zip'
            _write_archive(archive_path, [('data.csv', dataframe)])
            ParquetExtractorAdapterCVM().extract(
                source_path=str(archive_path), destination_path=str(tmp_path)
            )

        pd.testing.assert_frame_equal(
            pd.read_parquet(output_path), second_data
        )

    def test_different_csv_basenames_create_independent_outputs(
        self, tmp_path
    ):
        first_data = pd.DataFrame({'asset': ['A'], 'value': [1]})
        second_data = pd.DataFrame({'asset': ['B', 'C'], 'value': [2, 3]})
        archive_path = tmp_path / 'independent_outputs.zip'
        _write_archive(
            archive_path,
            [('first.csv', first_data), ('second.csv', second_data)],
        )

        ParquetExtractorAdapterCVM().extract(
            source_path=str(archive_path), destination_path=str(tmp_path)
        )

        pd.testing.assert_frame_equal(
            pd.read_parquet(tmp_path / 'first.parquet'), first_data
        )
        pd.testing.assert_frame_equal(
            pd.read_parquet(tmp_path / 'second.parquet'), second_data
        )
        assert sorted(path.name for path in tmp_path.glob('*.parquet')) == [
            'first.parquet',
            'second.parquet',
        ]
