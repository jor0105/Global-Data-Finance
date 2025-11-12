import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.presentation import HistoricalQuotes

print("=" * 80)
print("HISTORICAL QUOTES EXTRACTION - SAFE MODE FOR LOW-END HARDWARE")
print("=" * 80)
print("\nThis example demonstrates memory-safe extraction for systems with")
print("limited RAM and CPU resources. All processing is adaptive and monitored.")
print()

b3 = HistoricalQuotes()

print("Available asset classes:")
assets = b3.get_available_assets()
for asset in assets:
    print(f"  - {asset}")

# Display available year range
print("\nAvailable year range:")
years = b3.get_available_years()
print(f"  From: {years['minimal_year']}")
print(f"  To: {years['current_year']}")

print("\n" + "=" * 80)
print("Example 1: Extract stocks and ETFs (2022-2024)")
print("=" * 80)

result = b3.extract(
    path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
    destination_path="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST/Extracted",
    assets_list=["ações", "etf"],
    initial_year=2022,
    last_year=2024,
    output_filename="stocks_etf_2022_2024",
    processing_mode="fast",
)

print("\n" + "=" * 80)
print("Example 2: Extract with CUSTOM memory limits (2023)")
print("=" * 80)
print()


result = b3.extract(
    path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
    destination_path="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST/Extracted",
    assets_list=["ações"],
    initial_year=2023,
    last_year=2023,
    output_filename="stocks_2023_ultra",
    processing_mode="fast",
)

if result["success"]:
    print(f"\n✓ Ultra-safe extraction completed: {result['total_records']:,} records")
else:
    print(f"\n✗ Extraction failed: {result['message']}")
