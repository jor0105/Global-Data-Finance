"""Example 03: Advanced B3 Extraction Options (Multiple Assets and Fast Mode).

This example demonstrates how to filter multiple asset types (Stocks, ETFs,
and Options) from local COTAHIST files, select a range of years, and use
high-performance 'fast' mode.
"""

import sys
from pathlib import Path

# Ensure examples import repository code rather than the installed package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from globaldatafinance import HistoricalQuotesB3


def main() -> None:
    """Run the advanced B3 options example."""
    # 1. Initialize the B3 public facade
    b3 = HistoricalQuotesB3()

    # 2. Combined extraction with filters and 'fast' mode over local files
    print('Starting advanced B3 extraction (Stocks, ETFs, Options)...')
    resultado = b3.extract(
        path_of_docs='./cotahist_b3',  # Folder with local COTAHIST files
        assets_list=['ações', 'etf', 'opções'],
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
