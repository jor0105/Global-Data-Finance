"""Adapt asynchronous HTTP requests and streamed filesystem writes."""

import contextlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx

from ..macro_exceptions import (
    DiskFullError,
    FileWriteError,
    PathPermissionError,
)


class RequestsAdapter:
    """Adapt httpx for asynchronous HTTP requests and streamed downloads.

    Provides asynchronous HTTP HEAD requests and streamed file downloads.
    """

    def __init__(
        self,
        timeout: float = 60.0,
        max_redirects: int = 5,
        verify: bool = True,
        http2: bool = False,
        default_headers: Mapping[str, str] | None = None,
    ):
        """Initialize the httpx adapter.

        Args:
            timeout: Default request timeout in seconds
            max_redirects: Maximum number of redirects to follow. Default
                lowered to 5 (from a previous 20) as a hardening measure:
                legitimate CVM/B3 endpoints never chain more than 1-2
                redirects, and a low cap shortens the blast radius of
                redirect-loop attacks. Override for custom transports.
            verify: Verify SSL certificates
            http2: Enable HTTP/2
            default_headers: Optional headers merged into every request.
                Headers explicitly supplied to a request take precedence.
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.verify = verify
        self.http2 = http2
        self.default_headers = (
            dict(default_headers) if default_headers is not None else None
        )

    def _merge_headers(
        self, headers: dict[str, str] | None
    ) -> dict[str, str] | None:
        """Merge request headers over the adapter's default headers."""
        if self.default_headers is None:
            return headers

        merged_headers = dict(self.default_headers)
        if headers is None:
            return merged_headers

        for key, value in headers.items():
            normalized_key = key.casefold()
            for existing_key in tuple(merged_headers):
                if existing_key.casefold() == normalized_key:
                    del merged_headers[existing_key]
            merged_headers[key] = value

        return merged_headers

    async def async_head(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send a HEAD request to inspect headers without downloading a body.

        Useful for checking Content-Length, Content-Type, etc. before download.

        Args:
            url: Request URL
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response: Request response (no body, only headers)
        """
        request_headers = self._merge_headers(headers)
        async with httpx.AsyncClient(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            return await client.head(url, headers=request_headers, **kwargs)

    async def async_download_file(
        self,
        url: str,
        output_path: str,
        chunk_size: int = 8192,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> None:
        """Download a file asynchronously with streaming.

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
        request_headers = self._merge_headers(headers)
        try:
            async with (
                httpx.AsyncClient(
                    timeout=timeout or self.timeout,
                    follow_redirects=True,
                    max_redirects=self.max_redirects,
                    verify=self.verify,
                    http2=self.http2,
                ) as client,
                client.stream('GET', url, headers=request_headers) as response,
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
