"""Aria2c download adapter for high-performance parallel downloads.

Aria2 is a lightweight, multi-protocol, multi-source command-line download utility.
This adapter leverages aria2c for maximum throughput with built-in support for:
- Multiple connections per file
- File segmentation and parallel downloads
- Metalink and torrent support
- Resume capability
- Advanced connection management

Installation:
    Ubuntu/Debian: sudo apt-get install aria2
    macOS: brew install aria2
    Windows: https://github.com/aria2/aria2/releases
    Docker: docker run -it aria2/aria2

See: https://aria2.github.io/
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.brazil.dados_cvm.fundamental_stocks_data.application.interfaces import (
    DownloadDocsCVMRepository,
)
from src.brazil.dados_cvm.fundamental_stocks_data.domain.download_result import (
    DownloadResult,
)

logger = logging.getLogger(__name__)

# Default aria2c options
DEFAULT_MAX_CONCURRENT_DOWNLOADS = 8
DEFAULT_CONNECTIONS_PER_SERVER = 4
DEFAULT_MIN_SPLIT_SIZE = "1M"  # Minimum 1MB per split for parallelization
DEFAULT_TIMEOUT = 300  # 5 minutes
DEFAULT_MAX_TRIES = 5
DEFAULT_RETRY_WAIT = 3  # seconds


class Aria2cAdapter(DownloadDocsCVMRepository):
    """High-performance download adapter using aria2c CLI tool.

    Aria2 excels at:
    - Large files (splits into segments, downloads in parallel)
    - Many concurrent downloads (efficient connection pooling)
    - Resume/partial downloads (checks local file before download)
    - Rate limiting and connection management

    Requires aria2 to be installed and in PATH.

    Example:
        >>> adapter = Aria2cAdapter(max_concurrent_downloads=8)
        >>> result = adapter.download_docs(
        ...     "/path/to/dest",
        ...     {"DFP": ["url1", "url2"], "ITR": ["url3"]}
        ... )
        >>> print(f"Downloaded {result.success_count} files")
    """

    def __init__(
        self,
        max_concurrent_downloads: int = DEFAULT_MAX_CONCURRENT_DOWNLOADS,
        connections_per_server: int = DEFAULT_CONNECTIONS_PER_SERVER,
        min_split_size: str = DEFAULT_MIN_SPLIT_SIZE,
        timeout: int = DEFAULT_TIMEOUT,
        max_tries: int = DEFAULT_MAX_TRIES,
        retry_wait: int = DEFAULT_RETRY_WAIT,
        aria2c_path: Optional[str] = None,
    ):
        """Initialize Aria2c adapter.

        Args:
            max_concurrent_downloads: Max number of parallel downloads. Default: 8.
            connections_per_server: Connections per server/file. Default: 4.
            min_split_size: Minimum bytes per segment for splitting. Default: "1M".
            timeout: Connection timeout in seconds. Default: 300.
            max_tries: Max download attempts. Default: 5.
            retry_wait: Wait seconds between retries. Default: 3.
            aria2c_path: Full path to aria2c binary. Auto-detected if None.

        Raises:
            RuntimeError: If aria2c is not found in PATH or specified path.
        """
        self.max_concurrent_downloads = max_concurrent_downloads
        self.connections_per_server = connections_per_server
        self.min_split_size = min_split_size
        self.timeout = timeout
        self.max_tries = max_tries
        self.retry_wait = retry_wait
        self.aria2c_path = aria2c_path or self._find_aria2c()

        if not self.aria2c_path:
            raise RuntimeError(
                "aria2c not found. Install with:\n"
                "  Ubuntu/Debian: sudo apt-get install aria2\n"
                "  macOS: brew install aria2\n"
                "  Windows: https://github.com/aria2/aria2/releases"
            )

        logger.info(f"Aria2cAdapter initialized: {self.aria2c_path}")

    def _find_aria2c(self) -> Optional[str]:
        """Locate aria2c in system PATH."""
        try:
            result = subprocess.run(
                ["which", "aria2c"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                logger.debug(f"Found aria2c at {path}")
                return path
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Try direct execution
        try:
            subprocess.run(
                ["aria2c", "--version"],
                capture_output=True,
                timeout=5
            )
            return "aria2c"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def _build_aria2c_command(
        self,
        input_file: str,
        destination_path: str
    ) -> List[str]:
        """Build aria2c command line."""
        assert self.aria2c_path is not None, "aria2c_path must be set"
        return [
            self.aria2c_path,
            "-i", input_file,  # Read URLs from file
            "-d", destination_path,  # Output directory
            f"--max-concurrent-downloads={self.max_concurrent_downloads}",
            f"--max-connection-per-server={self.connections_per_server}",
            f"--split={self.connections_per_server}",  # Split downloads
            f"--min-split-size={self.min_split_size}",
            f"--connect-timeout={self.timeout}",
            f"--max-tries={self.max_tries}",
            f"--retry-wait={self.retry_wait}",
            "--allow-overwrite=false",  # Don't overwrite existing files
            "--auto-file-renaming=true",  # Rename if exists
            "--continue=true",  # Resume partial downloads
            "--quiet=false",
            "--console-log-level=notice",
        ]

    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        try:
            return url.split("/")[-1].split("?")[0] or "download"
        except Exception:
            return "download"

    def download_docs(
        self,
        your_path: str,
        dict_zip_to_download: Dict[str, List[str]]
    ) -> DownloadResult:
        """Download documents using aria2c.

        Args:
            your_path: Destination directory path
            dict_zip_to_download: Dict mapping doc types to URL lists

        Returns:
            DownloadResult with success/error counts
        """
        result = DownloadResult()
        total_files = sum(len(urls) for urls in dict_zip_to_download.values())

        logger.info(
            f"Starting aria2c download of {total_files} files to {your_path}"
        )

        # Create destination if doesn't exist
        os.makedirs(your_path, exist_ok=True)

        # Create a temporary file with all URLs
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8"
        ) as f:
            input_file = f.name
            for doc_name, url_list in dict_zip_to_download.items():
                for url in url_list:
                    # Extract year for logging
                    try:
                        year = url.split("_")[-1].split(".")[0]
                    except Exception:
                        year = "unknown"

                    # Write URL with comment (doc_type and year)
                    f.write(f"{url}\n")
                    logger.debug(f"Queued {doc_name}_{year}: {url}")

        try:
            # Build and run aria2c command
            cmd = self._build_aria2c_command(input_file, your_path)
            logger.debug(f"Running: {' '.join(cmd[:5])}...")

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=None  # No timeout; aria2 handles its own timeouts
            )

            logger.debug(f"aria2c exit code: {process.returncode}")

            # Parse results
            if process.returncode == 0:
                # Success: count files in destination
                downloaded_files = [
                    f for f in os.listdir(your_path)
                    if os.path.isfile(os.path.join(your_path, f))
                ]
                for doc_name, url_list in dict_zip_to_download.items():
                    for url in url_list:
                        try:
                            year = url.split("_")[-1].split(".")[0]
                        except Exception:
                            year = "unknown"
                        filename = self._extract_filename_from_url(url)
                        if filename in downloaded_files or any(
                            filename in f for f in downloaded_files
                        ):
                            result.add_success(doc_name, year)
                        else:
                            result.add_error(
                                f"File not found after download: {filename}"
                            )
            else:
                # aria2c failed; parse stderr for errors
                logger.error(f"aria2c stderr: {process.stderr}")
                for doc_name, url_list in dict_zip_to_download.items():
                    for url in url_list:
                        try:
                            year = url.split("_")[-1].split(".")[0]
                        except Exception:
                            year = "unknown"
                        result.add_error(
                            f"aria2c error ({process.returncode}): {doc_name}_{year}"
                        )

            logger.info(
                f"aria2c download completed: {result.success_count} successful, "
                f"{result.error_count} errors"
            )

        except subprocess.TimeoutExpired:
            logger.error("aria2c subprocess timed out")
            for doc_name, url_list in dict_zip_to_download.items():
                for url in url_list:
                    try:
                        year = url.split("_")[-1].split(".")[0]
                    except Exception:
                        year = "unknown"
                    result.add_error(f"Timeout: {doc_name}_{year}")

        except Exception as e:
            logger.error(f"aria2c adapter error: {e}", exc_info=True)
            for doc_name, url_list in dict_zip_to_download.items():
                for url in url_list:
                    try:
                        year = url.split("_")[-1].split(".")[0]
                    except Exception:
                        year = "unknown"
                    result.add_error(f"Exception: {doc_name}_{year} - {e}")

        finally:
            # Clean up temporary file
            try:
                os.unlink(input_file)
            except Exception:
                pass

        return result
