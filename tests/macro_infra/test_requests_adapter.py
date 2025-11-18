from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from datafinance.macro_infra import RequestsAdapter


class TestRequestsAdapterInitialization:
    def test_initialization_with_defaults(self):
        adapter = RequestsAdapter()
        assert adapter.timeout == 30.0
        assert adapter.max_redirects == 20
        assert adapter.verify is True
        assert adapter.http2 is False

    def test_initialization_with_custom_params(self):
        adapter = RequestsAdapter(
            timeout=60.0, max_redirects=10, verify=False, http2=True
        )
        assert adapter.timeout == 60.0
        assert adapter.max_redirects == 10
        assert adapter.verify is False
        assert adapter.http2 is True


class TestRequestsAdapterAsyncMethods:
    @pytest.mark.asyncio
    @patch("datafinance.macro_infra.requests_adapter.httpx.AsyncClient")
    async def test_async_head_request_success(self, mock_client_class):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "1024"}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.head.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        response = await adapter.async_head("https://example.com")

        assert response.status_code == 200
        assert response.headers["content-length"] == "1024"
        mock_client.head.assert_called_once()

    @pytest.mark.asyncio
    @patch("datafinance.macro_infra.requests_adapter.httpx.AsyncClient")
    async def test_async_head_with_custom_headers(self, mock_client_class):
        mock_response = Mock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.head.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        headers = {"Authorization": "Bearer token"}
        await adapter.async_head("https://example.com", headers=headers)

        call_args = mock_client.head.call_args
        assert call_args[1]["headers"] == headers

    @pytest.mark.asyncio
    @patch("datafinance.macro_infra.requests_adapter.httpx.AsyncClient")
    async def test_async_head_with_custom_timeout(self, mock_client_class):
        mock_response = Mock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.head.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        await adapter.async_head("https://example.com", timeout=10.0)

        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args
        assert call_args[1]["timeout"] == 10.0


class TestRequestsAdapterDownload:
    @pytest.mark.asyncio
    @patch("datafinance.macro_infra.requests_adapter.httpx.AsyncClient")
    @patch("builtins.open", new_callable=MagicMock)
    async def test_async_download_file_success(self, mock_open, mock_client_class):
        async def chunk_generator():
            yield b"chunk1"
            yield b"chunk2"

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.aiter_bytes = MagicMock(return_value=chunk_generator())

        mock_stream = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream.__aexit__ = AsyncMock(return_value=None)

        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_stream)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        mock_file = MagicMock()
        mock_open.return_value = mock_file

        adapter = RequestsAdapter()
        await adapter.async_download_file(
            "https://example.com/file.zip", "/tmp/file.zip"
        )

        assert mock_file.write.call_count == 2
        mock_file.write.assert_any_call(b"chunk1")
        mock_file.write.assert_any_call(b"chunk2")
        mock_file.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("datafinance.macro_infra.requests_adapter.httpx.AsyncClient")
    @patch("builtins.open", new_callable=MagicMock)
    async def test_async_download_file_with_custom_chunk_size(
        self, mock_open, mock_client_class
    ):
        async def chunk_generator():
            if False:
                yield b""

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.aiter_bytes = MagicMock(return_value=chunk_generator())

        mock_stream = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream.__aexit__ = AsyncMock(return_value=None)

        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_stream)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        mock_file = MagicMock()
        mock_open.return_value = mock_file

        adapter = RequestsAdapter()
        await adapter.async_download_file(
            "https://example.com/file.zip", "/tmp/file.zip", chunk_size=16384
        )

        mock_response.aiter_bytes.assert_called_once_with(chunk_size=16384)

    @pytest.mark.asyncio
    @patch("datafinance.macro_infra.requests_adapter.httpx.AsyncClient")
    @patch("datafinance.macro_infra.requests_adapter.open", new_callable=MagicMock)
    @patch("os.path.exists")
    @patch("os.remove")
    async def test_async_download_file_handles_http_error(
        self, mock_remove, mock_exists, mock_open, mock_client_class
    ):
        async def chunk_generator():
            if False:
                yield b""

        def raise_http_error():
            raise Exception("HTTP Error")

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock(side_effect=raise_http_error)
        mock_response.aiter_bytes = MagicMock(return_value=chunk_generator())

        mock_stream = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream.__aexit__ = AsyncMock(return_value=None)

        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_stream)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        mock_exists.return_value = True

        adapter = RequestsAdapter()
        with pytest.raises(Exception, match="HTTP Error"):
            await adapter.async_download_file(
                "https://example.com/file.zip", "/tmp/file.zip"
            )

        mock_remove.assert_called_once_with("/tmp/file.zip")

    @pytest.mark.asyncio
    @patch("datafinance.macro_infra.requests_adapter.httpx.AsyncClient")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.path.exists")
    @patch("os.remove")
    async def test_async_download_file_handles_disk_write_error(
        self, mock_remove, mock_exists, mock_open, mock_client_class
    ):
        async def chunk_generator():
            yield b"chunk1"

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.aiter_bytes = MagicMock(return_value=chunk_generator())

        mock_stream = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream.__aexit__ = AsyncMock(return_value=None)

        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_stream)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        mock_file = MagicMock()
        mock_file.write.side_effect = OSError("Disk full")
        mock_open.return_value = mock_file

        mock_exists.return_value = True

        adapter = RequestsAdapter()
        with pytest.raises(OSError, match="Failed to write chunk"):
            await adapter.async_download_file(
                "https://example.com/file.zip", "/tmp/file.zip"
            )

        mock_remove.assert_called_once_with("/tmp/file.zip")
