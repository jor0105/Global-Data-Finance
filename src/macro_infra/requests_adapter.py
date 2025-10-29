"""
RequestsAdapter - Wrapper completo para a biblioteca httpx.

Este adaptador encapsula todas as funcionalidades importantes do httpx,
permitindo o uso de requisições HTTP síncronas e assíncronas sem
necessidade de importar httpx diretamente no código.
"""

from typing import Any, Dict, Optional

import httpx


class RequestsAdapter:
    """
    Adaptador que encapsula a biblioteca httpx para requisições HTTP.

    Fornece métodos síncronos e assíncronos para fazer requisições HTTP,
    com suporte a streaming, timeout, retry, e outras funcionalidades do httpx.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_redirects: int = 20,
        verify: bool = True,
        http2: bool = False,
    ):
        """
        Inicializa o adaptador httpx.

        Args:
            timeout: Timeout padrão para requisições em segundos
            max_redirects: Número máximo de redirecionamentos
            verify: Verificar certificados SSL
            http2: Habilitar HTTP/2
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.verify = verify
        self.http2 = http2

    # ==================== MÉTODOS SÍNCRONOS ====================

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Requisição GET síncrona.

        Args:
            url: URL da requisição
            params: Parâmetros de query string
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
            **kwargs: Argumentos adicionais do httpx

        Returns:
            httpx.Response: Resposta da requisição
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
        Requisição POST síncrona.

        Args:
            url: URL da requisição
            data: Dados para enviar no body
            json: Dados JSON para enviar
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
            **kwargs: Argumentos adicionais do httpx

        Returns:
            httpx.Response: Resposta da requisição
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
        Requisição PUT síncrona.

        Args:
            url: URL da requisição
            data: Dados para enviar no body
            json: Dados JSON para enviar
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
            **kwargs: Argumentos adicionais do httpx

        Returns:
            httpx.Response: Resposta da requisição
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
        Requisição DELETE síncrona.

        Args:
            url: URL da requisição
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
            **kwargs: Argumentos adicionais do httpx

        Returns:
            httpx.Response: Resposta da requisição
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
        Requisição GET com streaming síncrono.

        Args:
            url: URL da requisição
            params: Parâmetros de query string
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
            **kwargs: Argumentos adicionais do httpx

        Returns:
            Context manager com a resposta em streaming
        """
        client = httpx.Client(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        )
        return client.stream("GET", url, params=params, headers=headers, **kwargs)

    # ==================== MÉTODOS ASSÍNCRONOS ====================

    async def async_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Requisição GET assíncrona.

        Args:
            url: URL da requisição
            params: Parâmetros de query string
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
            **kwargs: Argumentos adicionais do httpx

        Returns:
            httpx.Response: Resposta da requisição
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
        Requisição POST assíncrona.

        Args:
            url: URL da requisição
            data: Dados para enviar no body
            json: Dados JSON para enviar
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
            **kwargs: Argumentos adicionais do httpx

        Returns:
            httpx.Response: Resposta da requisição
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
        Requisição PUT assíncrona.

        Args:
            url: URL da requisição
            data: Dados para enviar no body
            json: Dados JSON para enviar
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
            **kwargs: Argumentos adicionais do httpx

        Returns:
            httpx.Response: Resposta da requisição
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
        Requisição DELETE assíncrona.

        Args:
            url: URL da requisição
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
            **kwargs: Argumentos adicionais do httpx

        Returns:
            httpx.Response: Resposta da requisição
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
        Requisição GET com streaming assíncrono.

        Args:
            url: URL da requisição
            params: Parâmetros de query string
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
            **kwargs: Argumentos adicionais do httpx

        Returns:
            Context manager assíncrono com a resposta em streaming
        """
        client = httpx.AsyncClient(
            timeout=timeout or self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=self.verify,
            http2=self.http2,
        )
        return client.stream("GET", url, params=params, headers=headers, **kwargs)

    # ==================== MÉTODOS DE DOWNLOAD ====================

    def download_file(
        self,
        url: str,
        output_path: str,
        chunk_size: int = 8192,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Download síncrono de arquivo com streaming.

        Args:
            url: URL do arquivo
            output_path: Caminho onde salvar o arquivo
            chunk_size: Tamanho dos chunks para streaming
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
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
        Download assíncrono de arquivo com streaming.

        Args:
            url: URL do arquivo
            output_path: Caminho onde salvar o arquivo
            chunk_size: Tamanho dos chunks para streaming
            headers: Headers customizados
            timeout: Timeout específico para esta requisição
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

    # ==================== UTILITÁRIOS ====================

    @staticmethod
    def create_headers(
        content_type: Optional[str] = None,
        authorization: Optional[str] = None,
        **custom_headers,
    ) -> Dict[str, str]:
        """
        Cria um dicionário de headers.

        Args:
            content_type: Tipo de conteúdo (ex: 'application/json')
            authorization: Token de autorização (ex: 'Bearer token')
            **custom_headers: Headers adicionais

        Returns:
            Dict com os headers
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
        Verifica se a resposta indica sucesso (2xx).

        Args:
            response: Resposta HTTP

        Returns:
            True se status code é 2xx
        """
        return 200 <= response.status_code < 300

    @staticmethod
    def raise_for_status(response: httpx.Response) -> None:
        """
        Lança exceção se a resposta indica erro.

        Args:
            response: Resposta HTTP

        Raises:
            httpx.HTTPStatusError: Se status code indica erro
        """
        response.raise_for_status()
