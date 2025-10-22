"""Examples showing how to use different download adapters with FundamentalStocksData.

This file demonstrates three adapter options:
1. WgetDownloadAdapter (original, simple, single-threaded)
2. ThreadPoolDownloadAdapter (recommended for most users - fast, portable, no external deps)
3. Aria2cAdapter (maximum speed for large volumes, requires aria2 installation)
"""

from src.presentation.cvm_docs import FundamentalStocksData
from src.brazil.dados_cvm.fundamental_stocks_data.application.use_cases import (
    DownloadDocumentsUseCase,
)
from src.brazil.dados_cvm.fundamental_stocks_data.infra.adapters import (
    WgetDownloadAdapter,
    ThreadPoolDownloadAdapter,
    Aria2cAdapter,
)

# ============================================================================
# Example 1: Using the default adapter (currently WgetDownloadAdapter)
# ============================================================================
def example_default_adapter():
    """Simplest usage - uses default single-threaded wget adapter."""
    print("\n=== Example 1: Default Adapter ===")
    
    cvm = FundamentalStocksData()
    
    # List available document types
    docs = cvm.get_available_docs()
    print(f"Available document types: {list(docs.keys())}")
    
    # List available years
    years = cvm.get_available_years()
    print(f"Available years: {years}")
    
    # Download documents
    result = cvm.download(
        destination_path="/tmp/cvm_data_default",
        doc_types=["DFP"],
        start_year=2023,
        end_year=2023
    )
    
    print(f"Downloaded {result.success_count} files")
    if result.has_errors():
        print(f"Errors: {result.error_count}")


# ============================================================================
# Example 2: Using ThreadPoolDownloadAdapter (recommended for most cases)
# ============================================================================
def example_threadpool_adapter():
    """Faster parallel downloads using ThreadPoolExecutor with requests.
    
    Best for:
    - Mixed file sizes
    - Most typical Python environments
    - When you want easy dependency management
    - Good balance between speed and simplicity
    """
    print("\n=== Example 2: ThreadPool Adapter (RECOMMENDED) ===")
    
    # Create a custom adapter with 8 parallel workers
    adapter = ThreadPoolDownloadAdapter(
        max_workers=8,  # Number of concurrent downloads
        chunk_size=8192,  # 8KB chunks for streaming
        timeout=30,  # 30 second timeout per request
        max_retries=3  # Retry up to 3 times on failure
    )
    
    # Use the adapter directly
    use_case = DownloadDocumentsUseCase(adapter)
    result = use_case.execute(
        destination_path="/tmp/cvm_data_threadpool",
        doc_types=["DFP", "ITR"],
        start_year=2022,
        end_year=2023
    )
    
    print(f"Downloaded {result.success_count} files")
    if result.has_errors():
        print(f"Errors encountered: {result.error_count}")
        for error in result.errors[:3]:  # Print first 3 errors
            print(f"  - {error}")


# ============================================================================
# Example 3: Using Aria2cAdapter (maximum speed for large volumes)
# ============================================================================
def example_aria2c_adapter():
    """Ultra-fast parallel downloads using aria2c (external CLI tool).
    
    Best for:
    - Very large volumes of files
    - Large files (aria2 does multipart downloads per file)
    - When you can control the environment and install aria2
    - Maximum throughput scenarios
    
    REQUIREMENTS:
    Install aria2 first:
      Ubuntu/Debian: sudo apt-get install aria2
      macOS: brew install aria2
      Windows: https://github.com/aria2/aria2/releases
      Docker: docker run -it aria2/aria2
    """
    print("\n=== Example 3: Aria2c Adapter (Maximum Speed) ===")
    
    try:
        # Create aria2c adapter with custom settings
        adapter = Aria2cAdapter(
            max_concurrent_downloads=8,  # Download 8 files at once
            connections_per_server=4,  # 4 connections per file
            min_split_size="1M",  # Split files larger than 1MB
            max_tries=5,  # Retry up to 5 times
            retry_wait=3  # Wait 3 seconds between retries
        )
        
        use_case = DownloadDocumentsUseCase(adapter)
        result = use_case.execute(
            destination_path="/tmp/cvm_data_aria2",
            doc_types=["DFP", "ITR"],
            start_year=2022,
            end_year=2023
        )
        
        print(f"Downloaded {result.success_count} files using aria2c")
        if result.has_errors():
            print(f"Errors: {result.error_count}")
    
    except RuntimeError as e:
        print(f"aria2c not available: {e}")
        print("Install aria2 to use this adapter")


# ============================================================================
# Example 4: Comparing different configurations
# ============================================================================
def example_adapter_comparison():
    """Compare performance of different adapter configurations."""
    print("\n=== Example 4: Adapter Comparison ===")
    
    import time
    
    configs = [
        ("Wget (single-threaded)", WgetDownloadAdapter()),
        ("ThreadPool (4 workers)", ThreadPoolDownloadAdapter(max_workers=4)),
        ("ThreadPool (8 workers)", ThreadPoolDownloadAdapter(max_workers=8)),
        ("ThreadPool (16 workers)", ThreadPoolDownloadAdapter(max_workers=16)),
    ]
    
    test_docs = {"DFP": [], "ITR": []}  # Would be populated with actual URLs
    test_path = "/tmp/cvm_bench"
    
    print("\nNote: This is a comparison template.")
    print("To use it, populate test_docs with actual URLs and uncomment the loop below.\n")
    
    # for name, adapter in configs:
    #     print(f"Testing {name}...")
    #     start = time.time()
    #     result = adapter.download_docs(test_path, test_docs)
    #     elapsed = time.time() - start
    #     print(f"  {name}: {elapsed:.1f}s, success: {result.success_count}")


# ============================================================================
# Example 5: Error handling and recovery
# ============================================================================
def example_error_handling():
    """Demonstrate error handling with adapters."""
    print("\n=== Example 5: Error Handling ===")
    
    adapter = ThreadPoolDownloadAdapter(
        max_workers=4,
        max_retries=3,
        timeout=30
    )
    
    use_case = DownloadDocumentsUseCase(adapter)
    result = use_case.execute(
        destination_path="/tmp/cvm_errors",
        doc_types=["DFP"],
        start_year=2020,
        end_year=2021
    )
    
    print(f"Results:")
    print(f"  Successful: {result.success_count}")
    print(f"  Failed: {result.error_count}")
    
    if result.has_errors():
        print(f"\nErrors encountered:")
        for i, error in enumerate(result.errors, 1):
            print(f"  {i}. {error}")
    
    if result.has_successes():
        print(f"\nSuccessfully downloaded:")
        for doc_type, year in result.successful_downloads[:5]:
            print(f"  - {doc_type} {year}")
        if len(result.successful_downloads) > 5:
            print(f"  ... and {len(result.successful_downloads) - 5} more")


# ============================================================================
# Main: Run examples
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("CVM FundamentalStocksData - Adapter Examples")
    print("=" * 70)
    
    # Uncomment examples to run them:
    
    # example_default_adapter()
    example_threadpool_adapter()
    # example_aria2c_adapter()
    # example_adapter_comparison()
    # example_error_handling()
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
