from src.presentation.cvm_docs import FundamentalStocksData

cvm = FundamentalStocksData()

docs = cvm.get_available_docs()

years = cvm.get_available_years()

result = cvm.download(
    destination_path="/home/jordan/Downloads/Docs_Cvm/Docs",
    doc_types=["DFP", "ITR"],
    start_year=2020,
    end_year=2023,
)

# print(f"Downloaded {result.success_count} files successfully")
