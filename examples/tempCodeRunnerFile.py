from src.presentation.cvm_docs import FundamentalStocksData

cvm = FundamentalStocksData()

docs = cvm.get_available_docs()
years = cvm.get_available_years()
