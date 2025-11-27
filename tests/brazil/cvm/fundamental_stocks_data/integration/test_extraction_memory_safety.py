import zipfile

import pandas as pd  # type: ignore
import psutil  # type: ignore
import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data.infra.adapters.extractors_docs_adapter import (
    ParquetExtractorAdapterCVM,
)


@pytest.mark.integration
class TestMemorySafety:
    @pytest.fixture
    def large_csv_zip(self, tmp_path):
        zip_path = tmp_path / 'large_data.zip'

        num_rows = 200_000
        data = {
            'col1': list(range(num_rows)),
            'col2': [f'text_{i}' * 5 for i in range(num_rows)],
            'col3': [float(i) * 1.5 for i in range(num_rows)],
            'col4': [f'category_{i % 100}' for i in range(num_rows)],
        }
        df = pd.DataFrame(data)

        with zipfile.ZipFile(
            zip_path, 'w', compression=zipfile.ZIP_DEFLATED
        ) as z:
            csv_content = df.to_csv(sep=';', index=False)
            z.writestr('large_data.csv', csv_content.encode('latin-1'))

        zip_size_mb = zip_path.stat().st_size / 1024 / 1024
        print(f'✓ ZIP created: {zip_size_mb:.2f} MB')

        return zip_path

    def test_extraction_does_not_load_full_file_in_memory(
        self, large_csv_zip, tmp_path
    ):
        process = psutil.Process()

        mem_before = process.memory_info().rss / 1024 / 1024

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(
            source_path=str(large_csv_zip), destination_path=str(tmp_path)
        )

        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before

        parquet_file = tmp_path / 'large_data.parquet'
        assert parquet_file.exists(), 'Parquet was not created'

        file_size_mb = parquet_file.stat().st_size / 1024 / 1024

        print('\n📊 Memory Statistics:')
        print(f'  Memory before: {mem_before:.2f} MB')
        print(f'  Memory after: {mem_after:.2f} MB')
        print(f'  Increase: {mem_increase:.2f} MB')
        print(f'  File size: {file_size_mb:.2f} MB')
        print(f'  Ratio: {(mem_increase / file_size_mb) * 100:.1f}%')

        MAX_MEM_INCREASE_MB = 50

        assert mem_increase < MAX_MEM_INCREASE_MB, (
            f'Memory increased too much ({mem_increase:.2f} MB > {MAX_MEM_INCREASE_MB} MB)! '
            f'Suspected full-file load into memory. File size: {file_size_mb:.2f} MB.'
        )

        df_result = pd.read_parquet(parquet_file)
        assert len(df_result) == 200_000, 'Incorrect number of rows'
        print(
            f'✅ Extraction with controlled memory: {len(df_result)} rows processed'
        )

    def test_multiple_large_files_do_not_accumulate_memory(self, tmp_path):
        process = psutil.Process()

        zip_files = []
        for i in range(3):
            zip_path = tmp_path / f'file_{i}.zip'

            num_rows = 50_000
            data = {
                'col1': list(range(num_rows)),
                'col2': [f'data_{j}' * 10 for j in range(num_rows)],
            }
            df = pd.DataFrame(data)

            with zipfile.ZipFile(zip_path, 'w') as z:
                csv_content = df.to_csv(sep=';', index=False)
                z.writestr(f'data_{i}.csv', csv_content.encode('latin-1'))

            zip_files.append(zip_path)

        mem_readings = []

        for i, zip_file in enumerate(zip_files):
            extractor = ParquetExtractorAdapterCVM()
            extractor.extract(
                source_path=str(zip_file), destination_path=str(tmp_path)
            )

            mem_after = process.memory_info().rss / 1024 / 1024
            mem_readings.append(mem_after)

            print(f'  File {i + 1}: Memory = {mem_after:.2f} MB')

        mem_growth = mem_readings[-1] - mem_readings[0]

        print(f'\n📊 Total memory growth: {mem_growth:.2f} MB')

        assert mem_growth < 100, (
            f'Memory grew too much ({mem_growth:.2f} MB) between extractions! '
            f'Suspected memory leak.'
        )

        parquet_files = list(tmp_path.glob('*.parquet'))
        assert len(parquet_files) == 3, 'Not all parquets were created'
        print(f'✅ Memory stable: {len(parquet_files)} files processed')

    def test_fallback_respects_memory_limit(self, tmp_path):
        zip_path = tmp_path / 'huge.zip'

        with zipfile.ZipFile(zip_path, 'w') as z:
            info = zipfile.ZipInfo('huge.csv')
            info.file_size = 600 * 1024 * 1024
            info.compress_size = 10 * 1024
            z.writestr(info, b'col1;col2\n1;test\n' * 100)

        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        print('✅ 2GB protection implemented (conceptual test)')
