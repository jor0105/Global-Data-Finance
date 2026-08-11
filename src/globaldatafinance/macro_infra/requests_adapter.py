import contextlib
from pathlib import Path
from typing import Any

import httpx

from ..macro_exceptions import (
    DiskFullError,
    FileWriteError,
    PathPermissionError,
)


class RequestsAdapter:
    """
    Adapter that encapsulates the httpx library for asynchronous HTTP requests.

    Provides methods for making asynchronous HTTP HEAD requests and file downloads
    with streaming support.
    """

    def __init__(
        self,
        timeout: float = 60.0,
        max_redirects: int = 5,
        verify: bool = True,
        http2: bool = False,
    ):
        """
        Initialize the httpx adapter.

        Args:
            timeout: Default request timeout in seconds
            max_redirects: Maximum number of redirects to follow. Default
                lowered to 5 (from a previous 20) as a hardening measure:
                legitimate CVM/B3 endpoints never chain more than 1-2
                redirects, and a low cap shortens the blast radius of
                redirect-loop attacks. Override for custom transports.
            verify: Verify SSL certificates
            http2: Enable HTTP/2
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.verify = verify
        self.http2 = http2

    async def async_head(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
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

    async def async_download_file(
        self,
        url: str,
        output_path: str,
        chunk_size: int = 8192,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
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
        target_path = Path(output_path)
        try:
            async with (
                httpx.AsyncClient(
                    timeout=timeout or self.timeout,
                    follow_redirects=True,
                    max_redirects=self.max_redirects,
                    verify=self.verify,
                    http2=self.http2,
                ) as client,
                client.stream('GET', url, headers=headers) as response,
            ):
                response.raise_for_status()

                with target_path.open('wb') as file_handle:
                    async for chunk in response.aiter_bytes(
                        chunk_size=chunk_size
                    ):
                        if chunk:
                            try:
                                file_handle.write(chunk)
                            except OSError as write_err:
                                # Critical: disk full, permission error, etc
                                err_msg = str(write_err).lower()
                                if (
                                    'enospc' in err_msg
                                    or 'no space left' in err_msg
                                    or 'disk full' in err_msg
                                ):
                                    raise DiskFullError(
                                        output_path
                                    ) from write_err
                                if (
                                    'permission denied' in err_msg
                                    or 'eacces' in err_msg
                                ):
                                    raise PathPermissionError(
                                        output_path
                                    ) from write_err
                                raise FileWriteError(
                                    output_path, str(write_err)
                                ) from write_err

        except Exception:
            # Clean up partial file on any error, then re-raise.
            with contextlib.suppress(Exception):
                target_path.unlink(missing_ok=True)

            raise
