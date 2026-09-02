import zipfile

import pandas as pd  # type: ignore
import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data.extract import (
    ParquetExtractorAdapterCVM,
)

pytestmark = pytest.mark.integration
# allow-assertion-reduction: Resource checks replace print-heavy stress cases.


class TestMemorySafety:
    def test_small_csv_is_processed_in_multiple_chunks(self, tmp_path):
        source_data = pd.DataFrame(
            {
                'row_id': range(7),
                'label': [f'row-{index}' for index in range(7)],
                'value': [index * 1.5 for index in range(7)],
            }
        )
        archive_path = tmp_path / 'multi_chunk.zip'
        with zipfile.ZipFile(archive_path, 'w') as archive:
            archive.writestr(
                'multi_chunk.csv',
                source_data.to_csv(sep=';', index=False).encode('latin-1'),
            )

        extractor = ParquetExtractorAdapterCVM()
        extractor.extractor_adapter.CHUNK_SIZE_PARQUET = 2
        extractor.extract(
            source_path=str(archive_path), destination_path=str(tmp_path)
        )

        output_path = tmp_path / 'multi_chunk.parquet'
        assert output_path.exists()
        result = pd.read_parquet(output_path)
        pd.testing.assert_frame_equal(result, source_data)
        assert len(result) == 7
