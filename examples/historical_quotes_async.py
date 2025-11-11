"""
Advanced async usage example for Historical Quotes extraction.

This example demonstrates:
- Asynchronous extraction
- Custom configuration
- Error handling
- Progress monitoring
"""

import asyncio
import time
from pathlib import Path

from src.brazil.dados_b3.historical_quotes.application import (
    CreateDocsToExtractUseCase,
    ExtractHistoricalQuotesUseCase,
)


async def extract_with_monitoring():
    """Extract historical quotes with progress monitoring."""
    # Configuration
    config = {
        "assets_list": ["ações", "etf", "opções"],
        "initial_year": 2023,
        "last_year": 2024,
        "path_of_docs": "/path/to/cotahist/files",
        "destination_path": "/path/to/output",
    }

    print("=" * 70)
    print("HISTORICAL QUOTES EXTRACTION - ASYNC MODE")
    print("=" * 70)

    # Step 1: Validate and prepare
    print("\n[1/3] Validating extraction parameters...")
    start_validation = time.time()

    try:
        docs = CreateDocsToExtractUseCase(
            assets_list=config["assets_list"],
            initial_year=config["initial_year"],
            last_year=config["last_year"],
            path_of_docs=config["path_of_docs"],
            destination_path=config["destination_path"],
        ).execute()

        validation_time = time.time() - start_validation
        print(f"   ✓ Validation completed in {validation_time:.2f}s")
        print(f"   ✓ Found {len(docs.set_documents_to_download)} files")
        print(f"   ✓ Asset classes: {', '.join(sorted(docs.set_assets))}")
        print(f"   ✓ Years: {list(docs.range_years)}")

    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
        return

    # Step 2: Extract with async
    print("\n[2/3] Starting asynchronous extraction...")
    start_extraction = time.time()

    extractor = ExtractHistoricalQuotesUseCase()

    try:
        # Use await instead of execute_sync for true async
        result = await extractor.execute(
            docs_to_extract=docs,
            processing_mode="fast",
            output_filename="cotahist_full.parquet",
        )

        extraction_time = time.time() - start_extraction

        print(f"   ✓ Extraction completed in {extraction_time:.2f}s")
        print(
            f"   ✓ Files processed: {result['success_count']}/{result['total_files']}"
        )
        print(f"   ✓ Records extracted: {result['total_records']:,}")

        if result["error_count"] > 0:
            print(f"   ⚠ Errors encountered: {result['error_count']}")
            for file, error in result["errors"].items():
                print(f"      - {Path(file).name}: {error}")

    except Exception as e:
        print(f"   ✗ Extraction failed: {e}")
        return

    # Step 3: Display results
    print("\n[3/3] Extraction Results")
    print("-" * 70)
    print(f"Status: {'✓ SUCCESS' if result['success'] else '✗ FAILED'}")
    print(f"Total records: {result['total_records']:,}")
    print(f"Output file: {result['output_file']}")

    total_time = time.time() - start_validation
    if result["total_records"] > 0:
        throughput = result["total_records"] / extraction_time
        print("\nPerformance:")
        print(f"  - Total time: {total_time:.2f}s")
        print(f"  - Extraction time: {extraction_time:.2f}s")
        print(f"  - Throughput: {throughput:,.0f} records/second")

    print("=" * 70)


async def extract_multiple_outputs():
    """Extract different asset classes to separate files."""
    print("Extracting multiple asset classes to separate files...\n")

    base_config = {
        "initial_year": 2023,
        "last_year": 2024,
        "path_of_docs": "/path/to/cotahist/files",
        "destination_path": "/path/to/output",
    }

    # Define extraction tasks
    tasks = [
        ("ações", "stocks.parquet"),
        ("etf", "etfs.parquet"),
        ("opções", "options.parquet"),
    ]

    # Create async tasks
    async def extract_asset_class(asset_class, output_filename):
        docs = CreateDocsToExtractUseCase(
            assets_list=[asset_class], **base_config
        ).execute()

        extractor = ExtractHistoricalQuotesUseCase()
        result = await extractor.execute(
            docs_to_extract=docs,
            processing_mode="slow",  # Use slow mode to avoid resource exhaustion
            output_filename=output_filename,
        )

        return asset_class, result

    # Run all extractions concurrently
    start = time.time()
    results = await asyncio.gather(
        *[extract_asset_class(ac, of) for ac, of in tasks], return_exceptions=True
    )
    elapsed = time.time() - start

    # Display results
    print("Extraction Summary:")
    print("-" * 70)
    total_records = 0

    for (asset_class, _), result in zip(tasks, results):
        if isinstance(result, Exception):
            print(f"{asset_class:15s}: ✗ FAILED - {result}")
        else:
            _, res = result
            total_records += res["total_records"]
            print(f"{asset_class:15s}: ✓ {res['total_records']:,} records")

    print("-" * 70)
    print(f"Total records: {total_records:,}")
    print(f"Total time: {elapsed:.2f}s")


async def main():
    """Main async entry point."""
    # Choose example to run
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--multiple":
        await extract_multiple_outputs()
    else:
        await extract_with_monitoring()


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())

    # Usage:
    # python examples/historical_quotes_async.py              # Single extraction
    # python examples/historical_quotes_async.py --multiple   # Multiple extractions
