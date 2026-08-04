"""Exemplo 01: Início Rápido com CVM (Demonstrações Financeiras DFP).

Este exemplo demonstra como baixar e extrair demonstrações financeiras
padronizadas (DFP) de empresas abertas brasileiras diretamente para Parquet.
"""

from globaldatafinance import FundamentalStocksDataCVM


def main() -> None:
    # 1. Inicializar a fachada pública da CVM
    cvm = FundamentalStocksDataCVM()

    # 2. Executar o download com conversão automática para Parquet
    print('Iniciando download e extração de dados DFP da CVM...')
    resultado = cvm.download(
        destination_path='./dados_cvm',
        list_docs=['DFP'],
        initial_year=2023,
        last_year=2023,
        automatic_extractor=True,
    )

    # 3. Exibir o resultado final
    print('✓ Download concluído com sucesso!')
    print(f'  Diretório dos arquivos Parquet: {resultado.destination_path}')
    print(f'  Arquivos baixados: {len(resultado.success_downloads)}')


if __name__ == '__main__':
    main()
