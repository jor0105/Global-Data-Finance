import time

from src.brazil.cvm.fundamental_stocks_data import (
    DownloadDocumentsUseCase,
    ThreadPoolDownloadAdapter,
    WgetDownloadAdapter,
)

# OPCIONAL: Descomente a linha abaixo se quiser ver mensagens de log
# from src.core import setup_logging
# setup_logging(level="INFO")


# Mais workers = mais rápido (mas mais carga no servidor)
adapter1 = ThreadPoolDownloadAdapter(max_workers=16)
adapter2 = ThreadPoolDownloadAdapter()
adapter3 = WgetDownloadAdapter()


start_time = time.time()
use_case = DownloadDocumentsUseCase(adapter2)
result = use_case.execute(
    destination_path="/home/jordan/Downloads/Docs_Cvm",
    list_docs=[],
    initial_year=2010,
    last_year=2025,
)
download_time_minutes = (time.time() - start_time) / 60

print(f"Tempo de download: {download_time_minutes:.2f} minutos")
print(f"Downloaded {result.success_count} files successfully")
