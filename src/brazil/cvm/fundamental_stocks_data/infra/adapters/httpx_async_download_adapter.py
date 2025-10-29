import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.brazil.cvm.fundamental_stocks_data.application import (
    DownloadDocsCVMRepository,
    FileExtractor,
)
from src.brazil.cvm.fundamental_stocks_data.application.extractors import (
    ParquetExtractor,
)
from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult
from src.brazil.cvm.fundamental_stocks_data.utils import (
    RetryStrategy,
    SimpleProgressBar,
)
from src.macro_exceptions.macro_exceptions import DiskFullError, ExtractionError
from src.macro_infra.requests_adapter import RequestsAdapter

logger = logging.getLogger(__name__)


class HttpxAsyncDownloadAdapter(DownloadDocsCVMRepository):
    """
    Adaptador de download assíncrono usando httpx.

    Este adaptador realiza downloads de forma assíncrona e paralela,
    oferecendo performance superior ao download síncrono tradicional.
    Utiliza o RequestsAdapter como interface para a biblioteca httpx.
    """

    def __init__(
        self,
        file_extractor: Optional[FileExtractor] = None,
        max_concurrent: int = 10,
        chunk_size: int = 8192,
        timeout: float = 60.0,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_multiplier: float = 2.0,
        http2: bool = True,
    ):
        """
        Inicializa o adaptador de download assíncrono.

        Args:
            file_extractor: Extrator de arquivos para extrair ZIPs baixados
            max_concurrent: Número máximo de downloads simultâneos
            chunk_size: Tamanho dos chunks para streaming
            timeout: Timeout das requisições em segundos
            max_retries: Número máximo de tentativas em caso de falha
            initial_backoff: Backoff inicial em segundos
            max_backoff: Backoff máximo em segundos
            backoff_multiplier: Multiplicador do backoff exponencial
            http2: Habilitar HTTP/2
        """
        self.file_extractor = file_extractor or ParquetExtractor()
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size
        self.max_retries = max_retries

        # Configurar RequestsAdapter
        self.http_client = RequestsAdapter(
            timeout=timeout,
            http2=http2,
            verify=True,
            max_redirects=20,
        )

        # Configurar estratégia de retry
        self.retry_strategy = RetryStrategy(
            initial_backoff=initial_backoff,
            max_backoff=max_backoff,
            multiplier=backoff_multiplier,
        )

        logger.debug(
            f"HttpxAsyncDownloadAdapter initialized with max_concurrent={max_concurrent}, "
            f"http2={http2}, timeout={timeout}"
        )

    def download_docs(
        self,
        dict_zip_to_download: Dict[str, List[str]],
        docs_paths: Dict[str, Dict[int, str]],
    ) -> DownloadResult:
        """
        Baixa documentos de forma assíncrona.

        Args:
            dict_zip_to_download: Dict mapeando tipos de docs para listas de URLs
            docs_paths: Dict com estrutura {doc: {year: path}} contendo
                       o caminho específico de destino para cada documento e ano

        Returns:
            DownloadResult com informações de sucesso/erro agregadas
        """
        result = DownloadResult()
        total_files = sum(len(urls) for urls in dict_zip_to_download.values())

        if total_files == 0:
            logger.warning("No files to download")
            return result

        logger.info(
            f"Starting async download of {total_files} files "
            f"with {self.max_concurrent} concurrent downloads"
        )

        # Preparar tarefas de download
        tasks = self._prepare_download_tasks(dict_zip_to_download, docs_paths)

        # Executar downloads assíncronos
        asyncio.run(self._execute_async_downloads(tasks, result))

        logger.info(
            f"Download completed: {result.success_count} successful, "
            f"{result.error_count} errors"
        )

        return result

    def _prepare_download_tasks(
        self,
        dict_zip_to_download: Dict[str, List[str]],
        docs_paths: Dict[str, Dict[int, str]],
    ) -> List[Tuple[str, str, str, str]]:
        """
        Prepara tarefas de download a partir do dicionário de entrada.

        Returns:
            Lista de tuplas (url, doc_name, year, destination_path)
        """
        tasks = []
        for doc_name, url_list in dict_zip_to_download.items():
            for url in url_list:
                year_str = self._extract_year(url)
                year_int = int(year_str)
                destination_path = docs_paths[doc_name][year_int]
                tasks.append((url, doc_name, year_str, destination_path))
        return tasks

    async def _execute_async_downloads(
        self,
        tasks: List[Tuple[str, str, str, str]],
        result: DownloadResult,
    ) -> None:
        """
        Executa downloads de forma assíncrona com controle de concorrência.

        Args:
            tasks: Lista de tarefas de download
            result: Objeto para acumular resultados
        """
        progress_bar = SimpleProgressBar(total=len(tasks), desc="Downloading (async)")
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def download_with_semaphore(task):
            async with semaphore:
                url, doc_name, year, dest_path = task
                await self._download_and_extract(
                    url, dest_path, doc_name, year, result, progress_bar
                )

        try:
            # Criar todas as tarefas assíncronas
            download_tasks = [download_with_semaphore(task) for task in tasks]

            # Executar todas as tarefas concorrentemente
            await asyncio.gather(*download_tasks)
        finally:
            progress_bar.close()

    async def _download_and_extract(
        self,
        url: str,
        dest_path: str,
        doc_name: str,
        year: str,
        result: DownloadResult,
        progress_bar: SimpleProgressBar,
    ) -> None:
        """
        Baixa um arquivo e extrai seu conteúdo.

        Args:
            url: URL do arquivo
            dest_path: Caminho de destino
            doc_name: Nome do documento
            year: Ano do documento
            result: Objeto para acumular resultados
            progress_bar: Barra de progresso
        """
        filename = self._extract_filename(url)
        filepath = str(Path(dest_path) / filename)

        success, error_msg = await self._download_with_retry(
            url, filepath, doc_name, year
        )

        if success:
            # Extrair arquivo após download bem-sucedido
            try:
                logger.info(f"Starting extraction for {doc_name}_{year}")
                self.file_extractor.extract(filepath, dest_path)
                result.add_success(f"{doc_name}_{year}")
                logger.info(f"Extraction completed for {doc_name}_{year}")
                self._cleanup_zip_file(filepath)

            except DiskFullError as disk_err:
                logger.error(f"Disk full during extraction {filepath}: {disk_err}")
                result.add_error(f"{doc_name}_{year}", f"DiskFull: {disk_err}")
                self._cleanup_zip_file(filepath)

            except ExtractionError as extract_exc:
                logger.error(f"Extraction error for {filepath}: {extract_exc}")
                result.add_error(
                    f"{doc_name}_{year}", f"Extraction failed: {extract_exc}"
                )

            except Exception as extract_exc:
                logger.error(
                    f"Unexpected extraction error for {filepath}: "
                    f"{type(extract_exc).__name__}: {extract_exc}"
                )
                result.add_error(
                    f"{doc_name}_{year}",
                    f"Unexpected extraction error: {extract_exc}",
                )
        else:
            result.add_error(f"{doc_name}_{year}", error_msg or "Unknown error")

        progress_bar.update(1)

    async def _download_with_retry(
        self,
        url: str,
        filepath: str,
        doc_name: str,
        year: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Baixa um arquivo com lógica de retry.

        Returns:
            Tupla (sucesso, mensagem_de_erro)
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    backoff = self.retry_strategy.calculate_backoff(attempt - 1)
                    logger.info(
                        f"Retry {attempt}/{self.max_retries} for {doc_name}_{year} "
                        f"after {backoff:.1f}s"
                    )
                    await asyncio.sleep(backoff)

                logger.debug(f"Downloading {doc_name}_{year} (async)")
                await self._stream_download(url, filepath)
                logger.info(f"Successfully downloaded {doc_name}_{year}")
                return True, None

            except Exception as e:
                last_exception = e

                # Verificar se deve tentar novamente
                if (
                    not self.retry_strategy.is_retryable(e)
                    or attempt >= self.max_retries
                ):
                    logger.error(
                        f"Download failed for {doc_name}_{year}: "
                        f"{type(e).__name__}: {e}"
                    )
                    break

                logger.warning(
                    f"Download error for {doc_name}_{year} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                )

        # Limpar arquivo em caso de falha
        self._cleanup_file(filepath)

        error_msg = (
            f"{type(last_exception).__name__}: {last_exception}"
            if last_exception
            else "Unknown error"
        )
        return False, error_msg

    async def _stream_download(self, url: str, filepath: str) -> None:
        """
        Realiza download com streaming assíncrono.

        Args:
            url: URL do arquivo
            filepath: Caminho onde salvar o arquivo

        Raises:
            Exception: Em caso de erro no download
        """
        try:
            await self.http_client.async_download_file(
                url=url,
                output_path=filepath,
                chunk_size=self.chunk_size,
            )
        except Exception as e:
            # Limpar arquivo parcialmente baixado
            self._cleanup_file(filepath)
            raise e

    @staticmethod
    def _extract_filename(url: str) -> str:
        """Extrai nome do arquivo da URL."""
        try:
            return url.split("/")[-1].split("?")[0] or "download"
        except Exception:
            return "download"

    @staticmethod
    def _extract_year(url: str) -> str:
        """Extrai ano da URL (espera formato: ..._YYYY.zip)."""
        try:
            return url.split("_")[-1].split(".")[0]
        except Exception:
            return "unknown"

    @staticmethod
    def _cleanup_file(filepath: str) -> None:
        """Remove arquivo em caso de falha."""
        try:
            path_obj = Path(filepath)
            if path_obj.exists():
                path_obj.unlink()
        except Exception:
            pass

    @staticmethod
    def _cleanup_zip_file(zip_path: str) -> None:
        """
        Tenta deletar arquivo ZIP após extração.

        Args:
            zip_path: Caminho do arquivo ZIP a deletar
        """
        try:
            Path(zip_path).unlink()
            logger.debug(f"Deleted ZIP file: {zip_path}")
        except Exception as cleanup_err:
            logger.warning(f"Failed to delete ZIP file {zip_path}: {cleanup_err}")
