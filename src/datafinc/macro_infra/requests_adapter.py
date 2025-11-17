from typing import Dict, Optional

import httpx


class RequestsAdapter:
    """
    Adapter that encapsulates the httpx library for asynchronous HTTP requests.

    Provides methods for making asynchronous HTTP HEAD requests and file downloads
    with streaming support.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_redirects: int = 20,
        verify: bool = True,
        http2: bool = False,
    ):
        """
        Initialize the httpx adapter.

        Args:
            timeout: Default request timeout in seconds
            max_redirects: Maximum number of redirects
            verify: Verify SSL certificates
            http2: Enable HTTP/2
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.verify = verify
        self.http2 = http2

    # ==================== ASYNCHRONOUS METHODS ====================

    async def async_head(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Asynchronous HEAD request to get headers without downloading body.

        Useful for checking Content-Length, Content-Type, etc. before download.

        Args:
            url: Request URL
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response: Request response (no body, only headers)
        """
        async with httpx.AsyncClient(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            return await client.head(url, headers=headers, **kwargs)

    # ==================== DOWNLOAD HELPERS ====================

    async def async_download_file(
        self,
        url: str,
        output_path: str,
        chunk_size: int = 8192,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Asynchronous file download with streaming.

        Args:
            url: File URL
            output_path: Path to save the file
            chunk_size: Chunk size for streaming
            headers: Custom headers
            timeout: Specific timeout for this request

        Raises:
            httpx.HTTPStatusError: If HTTP status indicates error
            httpx.RequestError: If network error occurs
            OSError: If disk write fails
        """
        file_handle = None
        try:
            async with httpx.AsyncClient(
                timeout=timeout or self.timeout,
                follow_redirects=True,
                max_redirects=self.max_redirects,
                verify=self.verify,
                http2=self.http2,
            ) as client:
                async with client.stream("GET", url, headers=headers) as response:
                    response.raise_for_status()

                    # Open file for writing
                    file_handle = open(output_path, "wb")

                    try:
                        async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                            if chunk:
                                try:
                                    file_handle.write(chunk)
                                except OSError as write_err:
                                    # Critical: disk full, permission error, etc
                                    raise OSError(
                                        f"Failed to write chunk to {output_path}: {write_err}"
                                    ) from write_err
                    finally:
                        # Ensure file is closed even on error
                        if file_handle is not None:
                            file_handle.close()
                            file_handle = None

        except Exception:
            # Clean up partial file on any error
            if file_handle is not None:
                try:
                    file_handle.close()
                except Exception:
                    pass

            # Try to remove partial file
            try:
                import os

                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception:
                pass  # File might not exist or be locked

            # Re-raise original error
            raise
