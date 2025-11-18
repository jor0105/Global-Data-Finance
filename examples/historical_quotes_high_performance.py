import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time

from datafinance import HistoricalQuotesB3
from src.datafinance.core import setup_logging

setup_logging(level="INFO")


print("=" * 80)
print("HISTORICAL QUOTES EXTRACTION - HIGH PERFORMANCE MODE")
print("=" * 80)
print()

b3 = HistoricalQuotesB3()

print("\n" + "=" * 80)

start_time = time.time()

result = b3.extract(
    path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
    assets_list=["ações", "etf"],
    initial_year=2000,
    last_year=2025,
    destination_path="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST_Extracted",
    output_filename="all_assets",
    processing_mode="fast",
)

elapsed_time = time.time() - start_time

if result["success"]:
    records = result["total_records"]
    records_per_sec = records / elapsed_time if elapsed_time > 0 else 0

    print("\n✓ High-performance extraction completed!")
    print(f"  • Total records: {records:,}")
    print(f"  • Time elapsed: {elapsed_time:.2f} seconds")
    print(f"  • Throughput: {records_per_sec:,.0f} records/second")
    print(f"  • Output: {result['output_file']}")
else:
    print(f"\n✗ Extraction failed: {result['message']}")
