from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

from src.macro_infra import RequestsAdapter


class TestRequestsAdapterInit:
    def test_default_initialization(self):
        adapter = RequestsAdapter()

        assert adapter.timeout == 30.0
        assert adapter.max_redirects == 20
        assert adapter.verify is True
        assert adapter.http2 is False

    def test_custom_initialization(self):
        adapter = RequestsAdapter(
            timeout=60.0, max_redirects=10, verify=False, http2=True
        )

        assert adapter.timeout == 60.0
        assert adapter.max_redirects == 10
        assert adapter.verify is False
        assert adapter.http2 is True


class TestRequestsAdapterSyncGet:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    def test_get_successful_request(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.text = "Success"

            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            response = adapter.get("https://example.com")

            assert response.status_code == 200
            assert response.text == "Success"
            mock_client.get.assert_called_once_with(
                "https://example.com", params=None, headers=None
            )

    def test_get_with_params_and_headers(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 200

            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            params = {"key": "value", "page": "1"}
            headers = {"User-Agent": "TestAgent"}

            adapter.get("https://api.example.com", params=params, headers=headers)

            mock_client.get.assert_called_once_with(
                "https://api.example.com", params=params, headers=headers
            )

    def test_get_with_custom_timeout(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            adapter.get("https://example.com", timeout=10.0)

            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["timeout"] == 10.0

    def test_get_with_additional_kwargs(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            adapter.get("https://example.com", cookies={"session": "abc123"})

            mock_client.get.assert_called_once()
            call_kwargs = mock_client.get.call_args[1]
            assert "cookies" in call_kwargs

    def test_get_network_error(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.NetworkError("Connection failed")
            mock_client_class.return_value.__enter__.return_value = mock_client

            with pytest.raises(httpx.NetworkError):
                adapter.get("https://example.com")

    def test_get_timeout_error(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value.__enter__.return_value = mock_client

            with pytest.raises(httpx.TimeoutException):
                adapter.get("https://example.com")


class TestRequestsAdapterSyncPost:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    def test_post_with_data(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 201

            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            data = {"username": "test", "password": "secret"}
            response = adapter.post("https://api.example.com/login", data=data)

            assert response.status_code == 201
            mock_client.post.assert_called_once_with(
                "https://api.example.com/login", data=data, json=None, headers=None
            )

    def test_post_with_json(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 200

            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            json_data = {"name": "Test", "value": 123}
            adapter.post("https://api.example.com/data", json=json_data)

            mock_client.post.assert_called_once_with(
                "https://api.example.com/data", data=None, json=json_data, headers=None
            )

    def test_post_with_headers(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            headers = {"Authorization": "Bearer token123"}
            adapter.post("https://api.example.com", headers=headers)

            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["headers"] == headers

    def test_post_with_custom_timeout(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            adapter.post("https://api.example.com", timeout=15.0)

            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["timeout"] == 15.0


class TestRequestsAdapterSyncPut:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    def test_put_with_json(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 200

            mock_client = MagicMock()
            mock_client.put.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            json_data = {"id": 1, "name": "Updated"}
            response = adapter.put("https://api.example.com/items/1", json=json_data)

            assert response.status_code == 200
            mock_client.put.assert_called_once_with(
                "https://api.example.com/items/1",
                data=None,
                json=json_data,
                headers=None,
            )

    def test_put_with_data(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_client = MagicMock()
            mock_client.put.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            data = "raw data"
            adapter.put("https://api.example.com/resource", data=data)

            mock_client.put.assert_called_once()
            call_kwargs = mock_client.put.call_args[1]
            assert call_kwargs["data"] == data


class TestRequestsAdapterSyncDelete:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    def test_delete_successful(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 204

            mock_client = MagicMock()
            mock_client.delete.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            response = adapter.delete("https://api.example.com/items/1")

            assert response.status_code == 204
            mock_client.delete.assert_called_once_with(
                "https://api.example.com/items/1", headers=None
            )

    def test_delete_with_headers(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_client = MagicMock()
            mock_client.delete.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            headers = {"Authorization": "Bearer token"}
            adapter.delete("https://api.example.com/items/1", headers=headers)

            call_kwargs = mock_client.delete.call_args[1]
            assert call_kwargs["headers"] == headers


class TestRequestsAdapterStreamGet:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    def test_stream_get_basic(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = MagicMock()
            mock_response.iter_bytes.return_value = [b"chunk1", b"chunk2"]

            mock_client = MagicMock()
            mock_stream_context = MagicMock()
            mock_stream_context.__enter__.return_value = mock_response
            mock_client.stream.return_value = mock_stream_context
            mock_client_class.return_value = mock_client

            with adapter.stream_get("https://example.com/file") as response:
                chunks = list(response.iter_bytes())
                assert len(chunks) == 2

    def test_stream_get_with_params(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_stream_context = MagicMock()
            mock_client.stream.return_value = mock_stream_context
            mock_client_class.return_value = mock_client

            params = {"version": "1.0"}
            with adapter.stream_get("https://example.com/file", params=params):
                mock_client.stream.assert_called_once()
                call_kwargs = mock_client.stream.call_args[1]
                assert call_kwargs["params"] == params


class TestRequestsAdapterAsyncGet:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    @pytest.mark.asyncio
    async def test_async_get_successful(self, adapter):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.text = "Async Success"

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            response = await adapter.async_get("https://example.com")

            assert response.status_code == 200
            assert response.text == "Async Success"

    @pytest.mark.asyncio
    async def test_async_get_with_params_and_headers(self, adapter):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            params = {"key": "value"}
            headers = {"Custom": "Header"}

            await adapter.async_get(
                "https://api.example.com", params=params, headers=headers
            )

            mock_client.get.assert_called_once_with(
                "https://api.example.com", params=params, headers=headers
            )

    @pytest.mark.asyncio
    async def test_async_get_timeout(self, adapter):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.TimeoutException):
                await adapter.async_get("https://example.com")


class TestRequestsAdapterAsyncPost:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    @pytest.mark.asyncio
    async def test_async_post_with_json(self, adapter):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 201

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            json_data = {"test": "data"}
            response = await adapter.async_post(
                "https://api.example.com", json=json_data
            )

            assert response.status_code == 201
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_post_with_data(self, adapter):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            data = "form data"
            await adapter.async_post("https://api.example.com", data=data)

            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["data"] == data


class TestRequestsAdapterAsyncPut:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    @pytest.mark.asyncio
    async def test_async_put_with_json(self, adapter):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 200

            mock_client = AsyncMock()
            mock_client.put.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            json_data = {"update": "value"}
            response = await adapter.async_put(
                "https://api.example.com/resource", json=json_data
            )

            assert response.status_code == 200


class TestRequestsAdapterAsyncDelete:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    @pytest.mark.asyncio
    async def test_async_delete_successful(self, adapter):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 204

            mock_client = AsyncMock()
            mock_client.delete.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            response = await adapter.async_delete("https://api.example.com/item/1")

            assert response.status_code == 204


class TestRequestsAdapterAsyncStreamGet:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    @pytest.mark.asyncio
    async def test_async_stream_get_basic(self, adapter):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()

            async def mock_aiter_bytes(chunk_size=8192):
                for chunk in [b"chunk1", b"chunk2"]:
                    yield chunk

            mock_response.aiter_bytes = mock_aiter_bytes

            mock_client = MagicMock()
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            mock_stream_context.__aexit__.return_value = AsyncMock(return_value=None)
            mock_client.stream.return_value = mock_stream_context
            mock_client_class.return_value = mock_client

            stream_result = await adapter.async_stream_get("https://example.com/file")
            async with stream_result as response:
                chunks = []
                async for chunk in response.aiter_bytes():
                    chunks.append(chunk)
                assert len(chunks) == 2


class TestRequestsAdapterDownloadFile:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    @pytest.fixture
    def temp_file(self, tmp_path):
        return tmp_path / "downloaded_file.bin"

    def test_download_file_successful(self, adapter, temp_file):
        with patch.object(adapter, "stream_get") as mock_stream_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = Mock()
            mock_response.iter_bytes.return_value = [b"data1", b"data2", b"data3"]
            mock_stream_get.return_value.__enter__.return_value = mock_response

            adapter.download_file("https://example.com/file.bin", str(temp_file))

            assert temp_file.exists()
            content = temp_file.read_bytes()
            assert content == b"data1data2data3"

    def test_download_file_with_custom_chunk_size(self, adapter, temp_file):
        with patch.object(adapter, "stream_get") as mock_stream_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = Mock()
            mock_response.iter_bytes.return_value = [b"chunk"]
            mock_stream_get.return_value.__enter__.return_value = mock_response

            adapter.download_file(
                "https://example.com/file.bin", str(temp_file), chunk_size=4096
            )

            mock_response.iter_bytes.assert_called_once_with(chunk_size=4096)

    def test_download_file_with_headers(self, adapter, temp_file):
        with patch.object(adapter, "stream_get") as mock_stream_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = Mock()
            mock_response.iter_bytes.return_value = []
            mock_stream_get.return_value.__enter__.return_value = mock_response

            headers = {"Authorization": "Bearer token"}
            adapter.download_file(
                "https://example.com/file.bin", str(temp_file), headers=headers
            )

            mock_stream_get.assert_called_once()
            call_kwargs = mock_stream_get.call_args[1]
            assert call_kwargs["headers"] == headers

    def test_download_file_raises_http_error(self, adapter, temp_file):
        with patch.object(adapter, "stream_get") as mock_stream_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=Mock()
            )
            mock_stream_get.return_value.__enter__.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                adapter.download_file(
                    "https://example.com/notfound.bin", str(temp_file)
                )

    def test_download_file_skips_empty_chunks(self, adapter, temp_file):
        with patch.object(adapter, "stream_get") as mock_stream_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = Mock()
            mock_response.iter_bytes.return_value = [
                b"data1",
                b"",
                b"data2",
                None,
                b"data3",
            ]
            mock_stream_get.return_value.__enter__.return_value = mock_response

            adapter.download_file("https://example.com/file.bin", str(temp_file))

            content = temp_file.read_bytes()
            assert content == b"data1data2data3"


class TestRequestsAdapterAsyncDownloadFile:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    @pytest.fixture
    def temp_file(self, tmp_path):
        return tmp_path / "async_downloaded_file.bin"

    @pytest.mark.asyncio
    async def test_async_download_file_successful(self, adapter, temp_file):
        mock_chunks = [b"async1", b"async2"]

        async def mock_aiter_bytes(chunk_size=8192):
            for chunk in mock_chunks:
                yield chunk

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.aiter_bytes = mock_aiter_bytes

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.stream = MagicMock(return_value=mock_context)

            mock_client_context = AsyncMock()
            mock_client_context.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_context

            await adapter.async_download_file(
                "https://example.com/file.bin", str(temp_file)
            )

            assert temp_file.exists()
            content = temp_file.read_bytes()
            assert content == b"async1async2"

    @pytest.mark.asyncio
    async def test_async_download_file_with_custom_chunk(self, adapter, temp_file):
        async def mock_aiter_bytes(chunk_size=8192):
            yield b"test"

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.aiter_bytes = mock_aiter_bytes

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.stream = MagicMock(return_value=mock_context)

            mock_client_context = AsyncMock()
            mock_client_context.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_context

            await adapter.async_download_file(
                "https://example.com/file.bin", str(temp_file), chunk_size=2048
            )

    @pytest.mark.asyncio
    async def test_async_download_file_http_error(self, adapter, temp_file):
        error = httpx.HTTPStatusError(
            "500 Internal Error", request=Mock(), response=Mock()
        )

        mock_response = AsyncMock()

        def raise_error():
            raise error

        mock_response.raise_for_status = raise_error

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.stream = MagicMock(return_value=mock_context)

            mock_client_context = AsyncMock()
            mock_client_context.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_context

            with pytest.raises(httpx.HTTPStatusError):
                await adapter.async_download_file(
                    "https://example.com/error.bin", str(temp_file)
                )


class TestRequestsAdapterCreateHeaders:
    def test_create_headers_empty(self):
        headers = RequestsAdapter.create_headers()
        assert headers == {}

    def test_create_headers_with_content_type(self):
        headers = RequestsAdapter.create_headers(content_type="application/json")
        assert headers == {"Content-Type": "application/json"}

    def test_create_headers_with_authorization(self):
        headers = RequestsAdapter.create_headers(authorization="Bearer token123")
        assert headers == {"Authorization": "Bearer token123"}

    def test_create_headers_with_both(self):
        headers = RequestsAdapter.create_headers(
            content_type="application/xml", authorization="Basic abc123"
        )
        assert headers == {
            "Content-Type": "application/xml",
            "Authorization": "Basic abc123",
        }

    def test_create_headers_with_custom_headers(self):
        headers = RequestsAdapter.create_headers(
            content_type="application/json",
            User_Agent="CustomAgent/1.0",
            X_Custom_Header="value",
        )
        assert headers["Content-Type"] == "application/json"
        assert headers["User_Agent"] == "CustomAgent/1.0"
        assert headers["X_Custom_Header"] == "value"

    def test_create_headers_custom_only(self):
        headers = RequestsAdapter.create_headers(
            Custom_Header="custom_value", Another_Header="another_value"
        )
        assert headers == {
            "Custom_Header": "custom_value",
            "Another_Header": "another_value",
        }


class TestRequestsAdapterIsSuccess:
    def test_is_success_200(self):
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        assert RequestsAdapter.is_success(response) is True

    def test_is_success_201(self):
        response = Mock(spec=httpx.Response)
        response.status_code = 201
        assert RequestsAdapter.is_success(response) is True

    def test_is_success_299(self):
        response = Mock(spec=httpx.Response)
        response.status_code = 299
        assert RequestsAdapter.is_success(response) is True

    def test_is_success_199(self):
        response = Mock(spec=httpx.Response)
        response.status_code = 199
        assert RequestsAdapter.is_success(response) is False

    def test_is_success_300(self):
        response = Mock(spec=httpx.Response)
        response.status_code = 300
        assert RequestsAdapter.is_success(response) is False

    def test_is_success_404(self):
        response = Mock(spec=httpx.Response)
        response.status_code = 404
        assert RequestsAdapter.is_success(response) is False

    def test_is_success_500(self):
        response = Mock(spec=httpx.Response)
        response.status_code = 500
        assert RequestsAdapter.is_success(response) is False


class TestRequestsAdapterRaiseForStatus:
    def test_raise_for_status_success(self):
        response = Mock(spec=httpx.Response)
        response.raise_for_status = Mock()

        RequestsAdapter.raise_for_status(response)

        response.raise_for_status.assert_called_once()

    def test_raise_for_status_error(self):
        response = Mock(spec=httpx.Response)
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=Mock()
        )

        with pytest.raises(httpx.HTTPStatusError):
            RequestsAdapter.raise_for_status(response)


class TestRequestsAdapterConfiguration:
    def test_client_configuration_sync(self):
        adapter = RequestsAdapter(
            timeout=45.0, max_redirects=15, verify=False, http2=True
        )

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.return_value = Mock(spec=httpx.Response)
            mock_client_class.return_value.__enter__.return_value = mock_client

            adapter.get("https://example.com")

            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["timeout"] == 45.0
            assert call_kwargs["max_redirects"] == 15
            assert call_kwargs["verify"] is False
            assert call_kwargs["http2"] is True
            assert call_kwargs["follow_redirects"] is True

    @pytest.mark.asyncio
    async def test_client_configuration_async(self):
        adapter = RequestsAdapter(
            timeout=50.0, max_redirects=5, verify=True, http2=False
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = Mock(spec=httpx.Response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await adapter.async_get("https://example.com")

            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["timeout"] == 50.0
            assert call_kwargs["max_redirects"] == 5
            assert call_kwargs["verify"] is True
            assert call_kwargs["http2"] is False
            assert call_kwargs["follow_redirects"] is True


class TestRequestsAdapterEdgeCases:
    @pytest.fixture
    def adapter(self):
        return RequestsAdapter()

    def test_get_with_none_params(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            adapter.get("https://example.com", params=None, headers=None)

            mock_client.get.assert_called_once_with(
                "https://example.com", params=None, headers=None
            )

    def test_post_with_empty_data(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_response = Mock(spec=httpx.Response)
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            adapter.post("https://example.com", data={})

            mock_client.post.assert_called_once()

    def test_stream_get_context_manager_cleanup(self, adapter):
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            with adapter.stream_get("https://example.com"):
                pass

            mock_client.stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_client_context_manager(self, adapter):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = Mock(spec=httpx.Response)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__ = AsyncMock()

            await adapter.async_get("https://example.com")

            mock_client_class.return_value.__aenter__.assert_called_once()
            mock_client_class.return_value.__aexit__.assert_called_once()

    def test_download_with_timeout(self, adapter, tmp_path):
        temp_file = tmp_path / "test.bin"

        with patch.object(adapter, "stream_get") as mock_stream_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = Mock()
            mock_response.iter_bytes.return_value = [b"data"]
            mock_stream_get.return_value.__enter__.return_value = mock_response

            adapter.download_file(
                "https://example.com/file.bin", str(temp_file), timeout=120.0
            )

            call_kwargs = mock_stream_get.call_args[1]
            assert call_kwargs["timeout"] == 120.0
