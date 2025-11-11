"""
Test script to extract historical quotes for stocks (ações) from 2024
and save to /home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST
"""

from src.brazil.dados_b3.historical_quotes.application import (
    CreateDocsToExtractUseCase,
    ExtractHistoricalQuotesUseCase,
)


def main():
    # Configuration
    assets_list = ["ações"]  # Only stocks
    initial_year = 2024
    last_year = 2024
    path_of_docs = "/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST"
    destination_path = "/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST"

    print("=" * 60)
    print("HISTORICAL QUOTES EXTRACTION TEST - 2024 STOCKS")
    print("=" * 60)
    print(f"Asset classes: {assets_list}")
    print(f"Year: {initial_year}")
    print(f"Source path: {path_of_docs}")
    print(f"Destination: {destination_path}")
    print()

    # Step 1: Create and validate extraction configuration
    print("Step 1: Validating extraction parameters...")
    try:
        docs_extractor = CreateDocsToExtractUseCase(
            assets_list=assets_list,
            initial_year=initial_year,
            last_year=last_year,
            path_of_docs=path_of_docs,
            destination_path=destination_path,
        ).execute()

        print(
            f"✓ Found {len(docs_extractor.set_documents_to_download)} ZIP file(s) to process"
        )
        print(f"✓ Asset classes: {docs_extractor.set_assets}")
        print(f"✓ Years: {list(docs_extractor.range_years)}")
        print(f"✓ Files to process: {docs_extractor.set_documents_to_download}")
    except Exception as e:
        print(f"✗ Error validating parameters: {e}")
        return

    # Step 2: Execute extraction
    print("\nStep 2: Starting extraction...")
    extraction_use_case = ExtractHistoricalQuotesUseCase()

    try:
        result = extraction_use_case.execute_sync(
            docs_to_extract=docs_extractor,
            processing_mode="fast",  # Use fast mode for testing
            output_filename="cotahist_acoes_2024.parquet",
        )

        # Step 3: Display results
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
            print(f"\n✓ Output saved to: {result['output_file']}")
            print("\nTest completed successfully! ✓")
        else:
            print("\n✗ Test failed!")

    except Exception as e:
        print(f"\n✗ Error during extraction: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
