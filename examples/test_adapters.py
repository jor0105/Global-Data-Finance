import time

from src.brazil.dados_cvm.fundamental_stocks_data.application.use_cases import (
    DownloadDocumentsUseCase,
)
from src.brazil.dados_cvm.fundamental_stocks_data.infra.adapters import (
    ThreadPoolDownloadAdapter,
)

# Mais workers = mais rápido (mas mais carga no servidor)
adapter1 = ThreadPoolDownloadAdapter(max_workers=16)

start_time = time.time()
use_case = DownloadDocumentsUseCase(adapter1)
result = use_case.execute(
    destination_path="/home/jordan/Downloads/Docs_Cvm",
    doc_types=["DFP", "ITR", "FRE"],
    start_year=2010,
    end_year=2023,
)
download_time_minutes = (time.time() - start_time) / 60

print(f"Tempo de download: {download_time_minutes:.2f} minutos")
print(f"Downloaded {result.success_count} files successfully")
