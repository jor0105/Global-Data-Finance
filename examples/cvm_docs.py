from globaldatafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()
path = '/home/jordan/Downloads'
cvm.download(
    destination_path=path,
    list_docs=["ipe"],
    initial_year=2010,
    last_year=2011,
    automatic_extractor=True
)