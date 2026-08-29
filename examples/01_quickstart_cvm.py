"""Example 01: Quickstart with CVM (DFP Financial Statements).

This example demonstrates how to download and extract standardized financial
statements (DFP) for Brazilian public companies directly into Parquet format.
"""

import sys
from pathlib import Path

# Ensure examples import repository code rather than the installed package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from globaldatafinance import FundamentalStocksDataCVM


def main() -> None:
    """Run the CVM quickstart example."""
    # 1. Initialize the CVM public facade
    cvm = FundamentalStocksDataCVM()

    output_dir = './dados_cvm'

    # 2. Execute download with automatic conversion to Parquet
    print('Starting CVM DFP data download and extraction...')
    resultado = cvm.download(
        destination_path=output_dir,
        list_docs=['DFP'],
        initial_year=2023,
        last_year=2023,
        automatic_extractor=True,
    )

    # 3. Display final result
    print('✓ Download completed successfully!')
    print(f'  Parquet files directory: {output_dir}')
    print(f'  Downloaded files count: {resultado.success_count_downloads}')


if __name__ == '__main__':
    main()
