"""Exemplo 03: Opções Avançadas de Extração da B3 (Múltiplos Ativos e Modo Fast).

Este exemplo demonstra como filtrar múltiplos tipos de ativos (Ações, ETFs e FIIs)
a partir de arquivos COTAHIST locais, selecionar um intervalo de anos e utilizar o
modo de alto desempenho ('fast').
"""

from globaldatafinance import HistoricalQuotesB3


def main() -> None:
    # 1. Inicializar a fachada pública da B3
    b3 = HistoricalQuotesB3()

    # 2. Extração combinada com filtros e modo 'fast' sobre arquivos locais
    print('Iniciando extração avançada B3 (Ações, ETFs, FIIs)...')
    resultado = b3.extract(
        path_of_docs='./cotahist_b3',  # Pasta com arquivos COTAHIST (ex: COTAHIST_A2022.ZIP, COTAHIST_A2023.ZIP)
        assets_list=['ações', 'etf', 'fii'],
        initial_year=2022,
        last_year=2023,
        destination_path='./dados_b3',
        output_filename='carteira_completa_2022_2023',
        processing_mode='fast',
    )

    # 3. Exibir o resultado final
    print('✓ Extração avançada concluída com sucesso!')
    print(f'  Arquivo Parquet gerado em: {resultado["output_path"]}')


if __name__ == '__main__':
    main()
