import time

from src.presentation.cvm_docs import FundamentalStocksData

cvm = FundamentalStocksData()

docs = cvm.get_available_docs()
years = cvm.get_available_years()

# Medir tempo para download
start_time = time.time()
result = cvm.download(
    destination_path="/home/jordan/Downloads/Docs_Cvm",
    doc_types=["DFP", "ITR", "FRE"],
    start_year=2010,
    end_year=2023,
)
download_time_minutes = (time.time() - start_time) / 60

print(f"Tempo de download: {download_time_minutes:.2f} minutos")
print(f"Downloaded {result.success_count} files successfully")
