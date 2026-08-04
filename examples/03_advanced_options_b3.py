"""Example 03: Advanced B3 Extraction Options (Multiple Assets and Fast Mode).

This example demonstrates how to filter multiple asset types (Stocks, ETFs, and FIIs)
from local COTAHIST files, select a range of years, and use high-performance 'fast' mode.
"""

from globaldatafinance import HistoricalQuotesB3


def main() -> None:
    # 1. Initialize the B3 public facade
    b3 = HistoricalQuotesB3()

    # 2. Combined extraction with filters and 'fast' mode over local files
    print('Starting advanced B3 extraction (Stocks, ETFs, FIIs)...')
    resultado = b3.extract(
        path_of_docs='./cotahist_b3',  # Folder with COTAHIST files (e.g. COTAHIST_A2022.ZIP, COTAHIST_A2023.ZIP)
        assets_list=['ações', 'etf', 'fii'],
        initial_year=2022,
        last_year=2023,
        destination_path='./dados_b3',
        output_filename='carteira_completa_2022_2023',
        processing_mode='fast',
    )

    # 3. Display final result
    print('✓ Advanced extraction completed successfully!')
    print(f'  Generated Parquet file at: {resultado["output_file"]}')


if __name__ == '__main__':
    main()
