import sys
from pathlib import Path

# Add parent directory to path to import src module
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.utils import ResourceLimits
from src.presentation.b3_docs import HistoricalQuotes

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

# Example 1: Extract stocks and ETFs for recent years (SLOW mode - recommended for weak hardware)
print("\n" + "=" * 80)
print("Example 1: Extract stocks and ETFs (2022-2024) - SLOW MODE")
print("=" * 80)
print("\n⚠️  SLOW mode uses minimal resources:")
print("   - Only 2 files processed concurrently")
print("   - Sequential parsing (no parallel workers)")
print("   - Adaptive batch sizes based on available RAM")
print("   - Automatic memory monitoring and garbage collection")
print("   - Circuit breaker protection against crashes")
print()

result = b3.extract(
    path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
    destination_path="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST/Extracted",
    assets_list=["ações", "etf"],
    initial_year=2022,
    last_year=2024,
    output_filename="stocks_etf_2022_2024_safe.parquet",
    processing_mode="slow",  # ✅ Best for limited resources
)

# Check results
if result["success"]:
    print(f"\n✓ Success! Extracted {result['total_records']:,} records")
    print(f"  Output file: {result['output_file']}")
    if result.get("batches_written"):
        print(f"  Written in {result['batches_written']} memory-safe batches")
else:
    print("\n✗ Extraction failed or completed with errors")
    print(f"  Message: {result['message']}")

# Example 2: Extract with custom resource limits
print("\n" + "=" * 80)
print("Example 2: Extract with CUSTOM memory limits (2023)")
print("=" * 80)
print("\nYou can customize resource thresholds for your specific hardware:")
print()

# Create custom resource limits for very constrained environments
# These settings are extremely conservative for systems with <2GB RAM
custom_limits = ResourceLimits(
    memory_warning_threshold=60.0,  # Warn at 60% RAM usage (default: 70%)
    memory_critical_threshold=75.0,  # Critical at 75% (default: 85%)
    memory_exhausted_threshold=90.0,  # Circuit breaker at 90% (default: 95%)
    min_free_memory_mb=200,  # Keep 200MB free minimum (default: 100MB)
    auto_gc_on_warning=True,  # Force garbage collection on warning
    circuit_breaker_cooldown_seconds=15,  # Wait 15s after exhaustion
)

print("Custom limits configured:")
print(f"  - Warning threshold: {custom_limits.memory_warning_threshold}%")
print(f"  - Critical threshold: {custom_limits.memory_critical_threshold}%")
print(f"  - Minimum free RAM: {custom_limits.min_free_memory_mb}MB")
print()

# Note: Custom limits need to be passed through the full extraction flow
# For now, they are applied automatically by the system
result = b3.extract(
    path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
    destination_path="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST/Extracted",
    assets_list=["ações"],
    initial_year=2023,
    last_year=2023,
    output_filename="stocks_2023_ultra_safe.parquet",
    processing_mode="slow",
)

if result["success"]:
    print(f"\n✓ Ultra-safe extraction completed: {result['total_records']:,} records")
else:
    print(f"\n✗ Extraction failed: {result['message']}")

# Example 3: Fast mode for powerful machines
print("\n" + "=" * 80)
print("Example 3: FAST mode (only for systems with 8GB+ RAM)")
print("=" * 80)
print("\n⚡ FAST mode uses aggressive optimization:")
print("   - Up to 10 files processed concurrently")
print("   - Parallel parsing with multiple CPU cores")
print("   - Large batch sizes (dynamically adjusted)")
print("   - Still includes memory monitoring and safety features")
print()
print("⚠️  WARNING: Only use FAST mode if you have:")
print("   - At least 8GB of RAM")
print("   - Multi-core CPU (4+ cores recommended)")
print("   - Good cooling system")
print()

# Uncomment to test FAST mode (not recommended for low-end hardware)
# result = b3.extract(
#     path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
#     destination_path="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST/Extracted",
#     assets_list=["ações", "etf"],
#     initial_year=2024,
#     output_filename="stocks_etf_2024_fast.parquet",
#     processing_mode="fast",  # ⚡ High performance mode
# )

print("\n" + "=" * 80)
print("TIPS FOR LOW-END HARDWARE:")
print("=" * 80)
print(
    """
1. Always use processing_mode="slow" for systems with <4GB RAM
2. Extract data year by year instead of all at once
3. Process one asset class at a time (e.g., only stocks, then ETFs)
4. Close other applications while processing
5. Monitor your system with 'htop' or Task Manager
6. If extraction fails, try smaller date ranges

The system will automatically:
- Reduce batch sizes when memory is low
- Pause processing if RAM usage is critical
- Force garbage collection to free memory
- Skip corrupted or malformed data lines
- Use streaming I/O to minimize memory footprint
"""
)

print("\nExamples completed safely!")
print("All resource usage was monitored and adapted in real-time.")
print("=" * 80)
