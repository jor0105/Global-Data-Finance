import sys
from pathlib import Path

# Add parent directory to path to import src module
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
    output_filename="stocks_etf_2022_2024_safe",
    processing_mode="fast",
)

# # Check results
# if result["success"]:
#     print(f"\n✓ Success! Extracted {result['total_records']:,} records")
#     print(f"  Output file: {result['output_file']}")
#     if result.get("batches_written"):
#         print(f"  Written in {result['batches_written']} memory-safe batches")
# else:
#     print("\n✗ Extraction failed or completed with errors")
#     print(f"  Message: {result['message']}")

# Example 2: Extract with custom resource limits
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
    output_filename="stocks_2023_ultra_safe",
    processing_mode="fast",
)

if result["success"]:
    print(f"\n✓ Ultra-safe extraction completed: {result['total_records']:,} records")
else:
    print(f"\n✗ Extraction failed: {result['message']}")

# # Example 3: Fast mode for powerful machines
# print("\n" + "=" * 80)
# print("Example 3: FAST mode (only for systems with 8GB+ RAM)")
# print("=" * 80)

# Uncomment to test FAST mode (not recommended for low-end hardware)
# result = b3.extract(
#     path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
#     destination_path="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST/Extracted",
#     assets_list=["ações", "etf"],
#     initial_year=2024,
#     output_filename="stocks_etf_2024_fast.parquet",
#     processing_mode="fast",  # ⚡ High performance mode
# )

# print("\n" + "=" * 80)
# print("TIPS FOR LOW-END HARDWARE:")
# print("=" * 80)
# print(
#     """
# 1. Always use processing_mode="slow" for systems with <4GB RAM
# 2. Extract data year by year instead of all at once
# 3. Process one asset class at a time (e.g., only stocks, then ETFs)
# 4. Close other applications while processing
# 5. Monitor your system with 'htop' or Task Manager
# 6. If extraction fails, try smaller date ranges

# The system will automatically:
# - Reduce batch sizes when memory is low
# - Pause processing if RAM usage is critical
# - Force garbage collection to free memory
# - Skip corrupted or malformed data lines
# - Use streaming I/O to minimize memory footprint
# """
# )

# print("\nExamples completed safely!")
# print("All resource usage was monitored and adapted in real-time.")
# print("=" * 80)
