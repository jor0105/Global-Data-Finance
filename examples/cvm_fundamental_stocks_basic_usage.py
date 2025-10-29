import time

from src.presentation import FundamentalStocksData

# setup_logging(level="INFO")


cvm = FundamentalStocksData()

docs = cvm.get_available_docs()
years = cvm.get_available_years()

# Medir tempo para download
start_time = time.time()
cvm.download(
    destination_path="/home/jordan/Downloads/Docs_Cvm",
    list_docs=["fre"],
    initial_year=2016,
    last_year=2017,
    automatic_extractor=True,
)
download_time_minutes = (time.time() - start_time) / 60

print(f"Tempo de download: {download_time_minutes:.2f} minutos")
