import time

from src.presentation import FundamentalStocksData

# OPCIONAL: Descomente a linha abaixo se quiser ver mensagens de log
# from src.core import setup_logging
# setup_logging(level="INFO")


cvm = FundamentalStocksData()

docs = cvm.get_available_docs()
years = cvm.get_available_years()

# Medir tempo para download
start_time = time.time()
cvm.download(
    destination_path="/home/jordan/Downloads/Docs_Cvm",
    list_docs=["DFP", "ITR", "FRE"],
    initial_year=2010,
    last_year=2023,
)
download_time_minutes = (time.time() - start_time) / 60

print(f"Tempo de download: {download_time_minutes:.2f} minutos")
