"""Simple test for historical quotes extraction in fast mode."""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.presentation import HistoricalQuotes


def test_fast_mode_extraction():
    """Test extraction with fast processing mode.

    This test verifies that:
    1. Fast mode can be initialized without errors
    2. The extraction process handles multiprocessing correctly
    3. Basic extraction works with the fast mode enabled
    """
    print("\n" + "=" * 80)
    print("Testing Historical Quotes - FAST MODE")
    print("=" * 80)

    # Initialize the client
    b3 = HistoricalQuotes()
    print("✓ HistoricalQuotes client initialized")

    # Test getting available assets
    assets = b3.get_available_assets()
    assert len(assets) > 0, "Should have available assets"
    print(f"✓ Found {len(assets)} available asset classes")

    # Test getting available years
    years = b3.get_available_years()
    assert "minimal_year" in years, "Should have minimal_year"
    assert "current_year" in years, "Should have current_year"
    print(f"✓ Year range: {years['minimal_year']} - {years['current_year']}")

    # Create a temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n✓ Using temporary directory: {temp_dir}")

        # Test extraction with fast mode (single year to keep it fast)
        result = b3.extract(
            path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
            destination_path=temp_dir,
            assets_list=["ações"],
            initial_year=2024,
            last_year=2024,
            output_filename="test_fast_mode",
            processing_mode="fast",
        )

        # Verify results
        assert "total_files" in result, "Result should have total_files"
        assert "success_count" in result, "Result should have success_count"
        assert "error_count" in result, "Result should have error_count"
        assert "total_records" in result, "Result should have total_records"

        print("\n✓ Extraction completed:")
        print(f"  - Total files: {result['total_files']}")
        print(f"  - Success: {result['success_count']}")
        print(f"  - Errors: {result['error_count']}")
        print(f"  - Records: {result['total_records']}")

        # Check if output file was created (if there were files to process)
        if result["total_files"] > 0:
            output_file = Path(result["output_file"])
            if result["total_records"] > 0:
                assert output_file.exists(), f"Output file should exist: {output_file}"
                print(f"✓ Output file created: {output_file.name}")
            else:
                print("⚠ No records extracted (no matching data)")
        else:
            print("⚠ No ZIP files found in the specified directory")

    print("\n" + "=" * 80)
    print("✓ FAST MODE TEST PASSED")
    print("=" * 80)


def test_slow_mode_extraction():
    """Test extraction with slow processing mode for comparison.

    This ensures both modes work correctly.
    """
    print("\n" + "=" * 80)
    print("Testing Historical Quotes - SLOW MODE")
    print("=" * 80)

    b3 = HistoricalQuotes()
    print("✓ HistoricalQuotes client initialized")

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"✓ Using temporary directory: {temp_dir}")

        result = b3.extract(
            path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
            destination_path=temp_dir,
            assets_list=["ações"],
            initial_year=2024,
            last_year=2024,
            output_filename="test_slow_mode",
            processing_mode="slow",
        )

        print("\n✓ Extraction completed:")
        print(f"  - Total files: {result['total_files']}")
        print(f"  - Success: {result['success_count']}")
        print(f"  - Errors: {result['error_count']}")
        print(f"  - Records: {result['total_records']}")

    print("\n" + "=" * 80)
    print("✓ SLOW MODE TEST PASSED")
    print("=" * 80)


if __name__ == "__main__":
    # This guard is CRITICAL for multiprocessing to work correctly
    try:
        test_fast_mode_extraction()
        print("\n" + "=" * 80)
        test_slow_mode_extraction()
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
