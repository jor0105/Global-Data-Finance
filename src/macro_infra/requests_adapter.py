"""
RequestsAdapter - Full wrapper for the httpx library.

This adapter encapsulates all important httpx functionality,
allowing the use of synchronous and asynchronous HTTP requests
without importing httpx directly in the code.
"""

from typing import Any, Dict, Optional

import httpx


class RequestsAdapter:
    """
    Adapter that encapsulates the httpx library for HTTP requests.

    Provides synchronous and asynchronous methods to make HTTP requests,
    with support for streaming, timeout, retry, and other httpx features.
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

    # ==================== SYNCHRONOUS METHODS ====================

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Synchronous GET request.

        Args:
            url: Request URL
            params: Query string parameters
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response: Request response
        """
        with httpx.Client(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            return client.get(url, params=params, headers=headers, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Synchronous POST request.

        Args:
            url: Request URL
            data: Body data to send
            json: JSON data to send
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response: Request response
        """
        with httpx.Client(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            return client.post(url, data=data, json=json, headers=headers, **kwargs)

    def put(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Synchronous PUT request.

        Args:
            url: Request URL
            data: Body data to send
            json: JSON data to send
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response: Request response
        """
        with httpx.Client(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            return client.put(url, data=data, json=json, headers=headers, **kwargs)

    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Synchronous DELETE request.

        Args:
            url: Request URL
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response: Request response
        """
        with httpx.Client(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            return client.delete(url, headers=headers, **kwargs)

    def stream_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        """
        Synchronous GET request with streaming.

        Args:
            url: Request URL
            params: Query string parameters
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            Context manager with the streaming response
        """
        client = httpx.Client(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        )
        return client.stream("GET", url, params=params, headers=headers, **kwargs)

    # ==================== ASYNCHRONOUS METHODS ====================

    async def async_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Asynchronous GET request.

        Args:
            url: Request URL
            params: Query string parameters
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response: Request response
        """
        async with httpx.AsyncClient(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            return await client.get(url, params=params, headers=headers, **kwargs)

    async def async_post(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Asynchronous POST request.

        Args:
            url: Request URL
            data: Body data to send
            json: JSON data to send
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response: Request response
        """
        async with httpx.AsyncClient(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            return await client.post(
                url, data=data, json=json, headers=headers, **kwargs
            )

    async def async_put(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Asynchronous PUT request.

        Args:
            url: Request URL
            data: Body data to send
            json: JSON data to send
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response: Request response
        """
        async with httpx.AsyncClient(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            return await client.put(
                url, data=data, json=json, headers=headers, **kwargs
            )

    async def async_delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Asynchronous DELETE request.

        Args:
            url: Request URL
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            httpx.Response: Request response
        """
        async with httpx.AsyncClient(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            return await client.delete(url, headers=headers, **kwargs)

    async def async_stream_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        """
        Asynchronous GET request with streaming.

        Args:
            url: Request URL
            params: Query string parameters
            headers: Custom headers
            timeout: Specific timeout for this request
            **kwargs: Additional httpx arguments

        Returns:
            Asynchronous context manager with the streaming response
        """
        client = httpx.AsyncClient(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        )
        return client.stream("GET", url, params=params, headers=headers, **kwargs)

    # ==================== DOWNLOAD HELPERS ====================

    def download_file(
        self,
        url: str,
        output_path: str,
        chunk_size: int = 8192,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Synchronous file download with streaming.

        Args:
            url: File URL
            output_path: Path to save the file
            chunk_size: Chunk size for streaming
            headers: Custom headers
            timeout: Specific timeout for this request
        """
        with self.stream_get(url, headers=headers, timeout=timeout) as response:
            response.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

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
        """
        async with httpx.AsyncClient(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        ) as client:
            async with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()
                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)

    # ==================== UTILITIES ====================

    @staticmethod
    def create_headers(
        content_type: Optional[str] = None,
        authorization: Optional[str] = None,
        **custom_headers,
    ) -> Dict[str, str]:
        """
        Create a headers dictionary.

        Args:
            content_type: Content type (e.g. 'application/json')
            authorization: Authorization token (e.g. 'Bearer token')
            **custom_headers: Additional headers

        Returns:
            Dict with headers
        """
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        if authorization:
            headers["Authorization"] = authorization
        headers.update(custom_headers)
        return headers

    @staticmethod
    def is_success(response: httpx.Response) -> bool:
        """
        Check if the response indicates success (2xx).

        Args:
            response: HTTP response

        Returns:
            True if status code is 2xx
        """
        return 200 <= response.status_code < 300

    @staticmethod
    def raise_for_status(response: httpx.Response) -> None:
        """
        Raise exception if the response indicates an error.

        Args:
            response: HTTP response

        Raises:
            httpx.HTTPStatusError: If status code indicates error
        """
        response.raise_for_status()
