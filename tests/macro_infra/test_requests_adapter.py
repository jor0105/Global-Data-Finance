from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.macro_infra import RequestsAdapter


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


class TestRequestsAdapterSyncMethods:
    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_get_request_success(self, mock_client_class):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        response = adapter.get("https://example.com")

        assert response.status_code == 200
        assert response.text == "Success"
        mock_client.get.assert_called_once()

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_get_request_with_params(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        params = {"key": "value", "foo": "bar"}
        adapter.get("https://example.com", params=params)

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[1]["params"] == params

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_get_request_with_headers(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        headers = {"Authorization": "Bearer token"}
        adapter.get("https://example.com", headers=headers)

        call_args = mock_client.get.call_args
        assert call_args[1]["headers"] == headers

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_get_request_with_custom_timeout(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        adapter.get("https://example.com", timeout=10.0)

        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args
        assert call_args[1]["timeout"] == 10.0

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_post_request_with_json(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        json_data = {"name": "test", "value": 123}
        adapter.post("https://example.com/api", json=json_data)

        call_args = mock_client.post.call_args
        assert call_args[1]["json"] == json_data

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_post_request_with_data(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        form_data = {"field1": "value1"}
        adapter.post("https://example.com/api", data=form_data)

        call_args = mock_client.post.call_args
        assert call_args[1]["data"] == form_data

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_put_request_success(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.put.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        adapter.put("https://example.com/api/1", json={"status": "updated"})

        mock_client.put.assert_called_once()

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_delete_request_success(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.delete.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        adapter.delete("https://example.com/api/1")

        mock_client.delete.assert_called_once()


class TestRequestsAdapterAsyncMethods:
    @pytest.mark.asyncio
    @patch("src.macro_infra.requests_adapter.httpx.AsyncClient")
    async def test_async_get_request_success(self, mock_client_class):
        mock_response = Mock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        response = await adapter.async_get("https://example.com")

        assert response.status_code == 200
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.macro_infra.requests_adapter.httpx.AsyncClient")
    async def test_async_get_with_params(self, mock_client_class):
        mock_response = Mock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        params = {"key": "value"}
        await adapter.async_get("https://example.com", params=params)

        call_args = mock_client.get.call_args
        assert call_args[1]["params"] == params

    @pytest.mark.asyncio
    @patch("src.macro_infra.requests_adapter.httpx.AsyncClient")
    async def test_async_post_with_json(self, mock_client_class):
        mock_response = Mock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        json_data = {"data": "test"}
        await adapter.async_post("https://example.com/api", json=json_data)

        call_args = mock_client.post.call_args
        assert call_args[1]["json"] == json_data

    @pytest.mark.asyncio
    @patch("src.macro_infra.requests_adapter.httpx.AsyncClient")
    async def test_async_put_success(self, mock_client_class):
        mock_response = Mock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.put.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        await adapter.async_put("https://example.com/api/1", json={"field": "value"})

        mock_client.put.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.macro_infra.requests_adapter.httpx.AsyncClient")
    async def test_async_delete_success(self, mock_client_class):
        mock_response = Mock()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.delete.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        await adapter.async_delete("https://example.com/api/1")

        mock_client.delete.assert_called_once()


class TestRequestsAdapterStreaming:
    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_stream_get_returns_context_manager(self, mock_client_class):
        mock_stream = MagicMock()
        mock_client = Mock()
        mock_client.stream.return_value = mock_stream
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        result = adapter.stream_get("https://example.com/stream")

        mock_client.stream.assert_called_once()
        assert result is mock_stream

    @pytest.mark.asyncio
    @patch("src.macro_infra.requests_adapter.httpx.AsyncClient")
    async def test_async_stream_get_returns_context_manager(self, mock_client_class):
        mock_stream = AsyncMock()
        mock_client = Mock()
        mock_client.stream.return_value = mock_stream
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        result = await adapter.async_stream_get("https://example.com/stream")

        mock_client.stream.assert_called_once()
        assert result is mock_stream


class TestRequestsAdapterDownload:
    @patch("src.macro_infra.requests_adapter.httpx.Client")
    @patch("builtins.open", new_callable=MagicMock)
    def test_download_file_success(self, mock_open, mock_client_class):
        mock_response = MagicMock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes.return_value = [b"chunk1", b"chunk2"]
        mock_response.__enter__.return_value = mock_response

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.stream.return_value = mock_response
        mock_client_class.return_value = mock_client

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        adapter = RequestsAdapter()
        adapter.download_file("https://example.com/file.zip", "/tmp/file.zip")

        assert mock_file.write.call_count == 2
        mock_file.write.assert_any_call(b"chunk1")
        mock_file.write.assert_any_call(b"chunk2")

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    @patch("builtins.open", new_callable=MagicMock)
    def test_download_file_with_custom_chunk_size(self, mock_open, mock_client_class):
        mock_response = MagicMock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes.return_value = []
        mock_response.__enter__.return_value = mock_response

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.stream.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        adapter.download_file(
            "https://example.com/file.zip", "/tmp/file.zip", chunk_size=16384
        )

        mock_response.iter_bytes.assert_called_once_with(chunk_size=16384)

    @pytest.mark.asyncio
    @patch("src.macro_infra.requests_adapter.httpx.AsyncClient")
    @patch("builtins.open", new_callable=MagicMock)
    async def test_async_download_file_success(self, mock_open, mock_client_class):
        pytest.skip("Complex async context manager mocking")


class TestRequestsAdapterUtilities:
    def test_create_headers_with_content_type(self):
        headers = RequestsAdapter.create_headers(content_type="application/json")
        assert headers["Content-Type"] == "application/json"

    def test_create_headers_with_authorization(self):
        headers = RequestsAdapter.create_headers(authorization="Bearer token123")
        assert headers["Authorization"] == "Bearer token123"

    def test_create_headers_with_custom_headers(self):
        headers = RequestsAdapter.create_headers(
            content_type="application/json",
            authorization="Bearer token",
            custom_header="custom_value",
        )
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer token"
        assert headers["custom_header"] == "custom_value"

    def test_create_headers_empty(self):
        headers = RequestsAdapter.create_headers()
        assert headers == {}

    def test_is_success_with_200(self):
        mock_response = Mock()
        mock_response.status_code = 200
        assert RequestsAdapter.is_success(mock_response) is True

    def test_is_success_with_201(self):
        mock_response = Mock()
        mock_response.status_code = 201
        assert RequestsAdapter.is_success(mock_response) is True

    def test_is_success_with_299(self):
        mock_response = Mock()
        mock_response.status_code = 299
        assert RequestsAdapter.is_success(mock_response) is True

    def test_is_success_with_404(self):
        mock_response = Mock()
        mock_response.status_code = 404
        assert RequestsAdapter.is_success(mock_response) is False

    def test_is_success_with_500(self):
        mock_response = Mock()
        mock_response.status_code = 500
        assert RequestsAdapter.is_success(mock_response) is False

    def test_is_success_with_199(self):
        mock_response = Mock()
        mock_response.status_code = 199
        assert RequestsAdapter.is_success(mock_response) is False

    def test_is_success_with_300(self):
        mock_response = Mock()
        mock_response.status_code = 300
        assert RequestsAdapter.is_success(mock_response) is False

    def test_raise_for_status_success(self):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        RequestsAdapter.raise_for_status(mock_response)
        mock_response.raise_for_status.assert_called_once()

    def test_raise_for_status_propagates_exception(self):
        mock_response = Mock()
        mock_response.raise_for_status = Mock(side_effect=Exception("HTTP Error"))
        with pytest.raises(Exception):
            RequestsAdapter.raise_for_status(mock_response)


class TestRequestsAdapterEdgeCases:
    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_get_request_uses_default_timeout_when_not_specified(
        self, mock_client_class
    ):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter(timeout=45.0)
        adapter.get("https://example.com")

        call_args = mock_client_class.call_args
        assert call_args[1]["timeout"] == 45.0

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_post_request_with_both_data_and_json(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter()
        adapter.post("https://example.com/api", data="form_data", json={"key": "value"})

        call_args = mock_client.post.call_args
        assert call_args[1]["data"] == "form_data"
        assert call_args[1]["json"] == {"key": "value"}

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_adapter_respects_verify_setting(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter(verify=False)
        adapter.get("https://example.com")

        call_args = mock_client_class.call_args
        assert call_args[1]["verify"] is False

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_adapter_respects_http2_setting(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter(http2=True)
        adapter.get("https://example.com")

        call_args = mock_client_class.call_args
        assert call_args[1]["http2"] is True

    @patch("src.macro_infra.requests_adapter.httpx.Client")
    def test_adapter_respects_max_redirects(self, mock_client_class):
        mock_response = Mock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = RequestsAdapter(max_redirects=5)
        adapter.get("https://example.com")

        call_args = mock_client_class.call_args
        assert call_args[1]["max_redirects"] == 5

    def test_create_headers_overwrites_with_custom(self):
        headers = RequestsAdapter.create_headers(
            content_type="text/plain", **{"Content-Type": "application/json"}
        )
        assert headers["Content-Type"] == "application/json"
