"""
Historical Quotes Extraction Example

This example demonstrates how to extract historical quotes from COTAHIST files
from the Brazilian stock exchange (B3).
"""

from src.brazil.dados_b3.historical_quotes.application import (
    CreateDocsToExtractUseCase,
    ExtractHistoricalQuotesUseCase,
)


def main():
    # Step 1: Configure extraction parameters
    assets_list = ["ações", "etf"]  # Asset classes to extract
    initial_year = 2023
    last_year = 2024
    path_of_docs = (
        "/path/to/cotahist/zip/files"  # Directory containing COTAHIST*.ZIP files
    )
    destination_path = "/path/to/output"  # Where to save the Parquet file

    # Step 2: Create and validate extraction configuration
    print("Validating extraction parameters...")
    docs_extractor = CreateDocsToExtractUseCase(
        assets_list=assets_list,
        initial_year=initial_year,
        last_year=last_year,
        path_of_docs=path_of_docs,
        destination_path=destination_path,
    ).execute()

    print(f"Found {len(docs_extractor.set_documents_to_download)} ZIP files to process")
    print(f"Asset classes: {docs_extractor.set_assets}")
    print(f"Years: {list(docs_extractor.range_years)}")

    # Step 3: Execute extraction
    print("\nStarting extraction...")
    extraction_use_case = ExtractHistoricalQuotesUseCase()

    # Use 'fast' mode for maximum speed (high CPU/RAM usage)
    # Use 'slow' mode for minimal resource consumption
    result = extraction_use_case.execute_sync(
        docs_to_extract=docs_extractor,
        processing_mode="fast",  # or 'slow'
        output_filename="cotahist_stocks_etfs.parquet",
    )

    # Step 4: Display results
    print("\n" + "=" * 60)
    print("EXTRACTION RESULTS")
    print("=" * 60)
    print(f"Status: {'✓ SUCCESS' if result['success'] else '✗ FAILED'}")
    print(f"Message: {result['message']}")
    print(f"\nFiles processed: {result['success_count']}/{result['total_files']}")
    print(f"Records extracted: {result['total_records']:,}")

    if result["error_count"] > 0:
        print(f"\nErrors encountered: {result['error_count']}")
        for file, error in result["errors"].items():
            print(f"  - {file}: {error}")

    if result["success"]:
        print(f"\nOutput saved to: {result['output_file']}")


if __name__ == "__main__":
    main()
