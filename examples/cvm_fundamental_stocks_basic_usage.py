import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time

from src.core import setup_logging
from src.presentation import FundamentalStocksData

setup_logging(level="ERROR")


cvm = FundamentalStocksData()

docs = cvm.get_available_docs()
years = cvm.get_available_years()

# Medir tempo para download
start_time = time.time()
cvm.download(
    destination_path="/home/jordan/Downloads/Docs_Cvm",
    list_docs=[],
    initial_year=2024,
    last_year=2025,
    automatic_extractor=True,
)
download_time_minutes = (time.time() - start_time) / 60

print(f"Tempo de download: {download_time_minutes:.2f} minutos")
