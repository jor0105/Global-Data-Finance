"""Exemplo 02: Início Rápido com B3 (Cotações Históricas de Ações).

Este exemplo demonstra como ler e extrair cotações históricas de Ações
a partir de arquivos COTAHIST locais (ex: COTAHIST_A2023.ZIP ou .TXT)
previamente salvos na pasta 'path_of_docs' e gerar um arquivo Parquet consolidado.
"""

from globaldatafinance import HistoricalQuotesB3


def main() -> None:
    # 1. Inicializar a fachada pública da B3
    b3 = HistoricalQuotesB3()

    # 2. Extrair cotações de ações a partir de arquivos COTAHIST locais
    print('Iniciando extração de cotações de Ações da B3...')
    resultado = b3.extract(
        path_of_docs='./cotahist_b3',  # Pasta contendo os arquivos COTAHIST locais
        assets_list=['ações'],
        initial_year=2023,
        last_year=2023,
        destination_path='./dados_b3',
        output_filename='cotacoes_acoes_2023',
    )

    # 3. Exibir o resultado final
    print('✓ Extração concluída com sucesso!')
    print(f'  Arquivo Parquet gerado em: {resultado["output_path"]}')
    print(
        f'  Total de arquivos processados: {len(resultado["files_processed"])}'
    )


if __name__ == '__main__':
    main()
