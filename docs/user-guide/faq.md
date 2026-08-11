# FAQ - Perguntas Frequentes

Respostas para as perguntas mais comuns sobre o Global-Data-Finance.

______________________________________________________________________

## Instalação e Configuração

### Como instalar o Global-Data-Finance?

```bash
pip install globaldatafinance
```

Veja o [guia completo de instalação](installation.md) para mais detalhes.

### Qual versão do Python é necessária?

Global-Data-Finance requer **Python 3.12 ou superior**. Versões anteriores não são suportadas.

### Posso usar em ambiente virtual?

Sim, e é altamente recomendado! Use `venv` ou `conda`:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install globaldatafinance
```

______________________________________________________________________

## Uso Geral

### Onde os arquivos são salvos?

Os arquivos são salvos no diretório especificado em `destination_path`. Por exemplo:

```python
cvm.download(destination_path="/home/usuario/dados")
# Arquivos salvos em: /home/usuario/dados/
```

### Como verificar quais documentos estão disponíveis?

Use os métodos `get_available_*`:

```python
# Para CVM
cvm = FundamentalStocksDataCVM()
docs = cvm.get_available_docs()
years = cvm.get_available_years()

# Para B3
b3 = HistoricalQuotesB3()
assets = b3.get_available_assets()
years = b3.get_available_years()
```

______________________________________________________________________

## Documentos CVM

### Quais tipos de documentos posso baixar?

- **DFP**: Demonstrações Financeiras Padronizadas
- **ITR**: Informações Trimestrais
- **FRE**: Formulário de Referência
- **FCA**: Formulário Cadastral
- **CGVN**: Código de Governança
- **VLMO**: Valores Mobiliários
- **IPE**: Informações Periódicas e Eventuais

Veja [Documentos CVM](cvm-docs.md) para detalhes.

### Como baixar apenas um tipo de documento?

```python
cvm.download(
    destination_path="/data",
    list_docs=["DFP"],  # Apenas DFP
    initial_year=2022
)
```

### O que é extração automática?

Com `automatic_extractor=True`, os arquivos ZIP são automaticamente extraídos e convertidos para formato Parquet:

```python
cvm.download(
    destination_path="/data",
    list_docs=["DFP"],
    automatic_extractor=True  # Converte para Parquet
)
```

### Como lidar com downloads interrompidos?

A biblioteca possui retry automático. Para maior robustez, implemente sua própria lógica de retry (veja [estratégia de retry](../dev-guide/retry-strategy.md#exemplo-de-uso)).

______________________________________________________________________

## Cotações B3

### Onde obter arquivos COTAHIST?

Baixe do site oficial da B3:
🔗 [https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)

### Qual a diferença entre modo fast e slow?

| Modo     | Performance | CPU   | RAM    | Quando usar                         |
| -------- | ----------- | ----- | ------ | ----------------------------------- |
| **fast** | Alta        | Alto  | ~2GB   | Máquinas com bons recursos (padrão) |
| **slow** | Moderada    | Baixo | ~500MB | Recursos limitados                  |

```python
# Modo fast (padrão)
result = b3.extract(..., processing_mode="fast")

# Modo slow
result = b3.extract(..., processing_mode="slow")
```

### Como extrair apenas ações?

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],  # Apenas ações
    initial_year=2023
)
```

### Posso extrair múltiplas classes de ativos?

Sim! Passe uma lista com as classes desejadas:

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf", "opções"],
    initial_year=2023
)
```

### Como personalizar o nome do arquivo de saída?

Use o parâmetro `output_filename`:

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    output_filename="acoes_2023"  # Gera: acoes_2023.parquet
)
```

______________________________________________________________________

## Performance

### Como acelerar downloads?

O Global-Data-Finance já usa download paralelo por padrão (`AsyncDownloadAdapterCVM`), que é 3-5x mais rápido que download sequencial.

### Como acelerar extração de cotações?

Use o modo `"fast"` (padrão):

```python
result = b3.extract(..., processing_mode="fast")
```

### Posso processar em paralelo?

Sim! Você pode executar múltiplas extrações em paralelo usando `multiprocessing` ou `concurrent.futures`:

```python
from concurrent.futures import ProcessPoolExecutor
from globaldatafinance import HistoricalQuotesB3

def extract_year(year):
    b3 = HistoricalQuotesB3()
    return b3.extract(
        path_of_docs="/data/cotahist",
        assets_list=["ações"],
        initial_year=year,
        last_year=year,
        output_filename=f"acoes_{year}"
    )

# Processar anos em paralelo
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(extract_year, range(2020, 2024)))
```

______________________________________________________________________

## Análise de Dados

### Como ler os arquivos Parquet gerados?

Use Pandas ou Polars:

```python
# Com Pandas
import pandas as pd
df = pd.read_parquet("cotahist_extracted.parquet")

# Com Polars (mais rápido)
import polars as pl
df = pl.read_parquet("cotahist_extracted.parquet")
```

### Qual biblioteca é melhor: Pandas ou Polars?

- **Pandas**: Mais popular, maior ecossistema, boa para datasets pequenos/médios
- **Polars**: Muito mais rápido, menor uso de memória, ideal para grandes volumes

Para análise de dados financeiros (grandes volumes), recomendamos **Polars**.

### Como filtrar dados de um ativo específico?

```python
import polars as pl

df = pl.read_parquet("cotahist_extracted.parquet")

# Filtrar PETR4
petr4 = df.filter(pl.col('codigo_negociacao') == 'PETR4')

# Ou com Pandas
import pandas as pd
df = pd.read_parquet("cotahist_extracted.parquet")
petr4 = df[df['codigo_negociacao'] == 'PETR4']
```

______________________________________________________________________

## Erros Comuns

### "No module named 'globaldatafinance'"

**Causa**: Biblioteca não instalada ou ambiente virtual não ativado.

**Solução**:

```bash
pip install globaldatafinance
```

### "Python version not supported"

**Causa**: Python < 3.12.

**Solução**: Atualize para Python 3.12+.

### "InvalidDocumentName"

**Causa**: Tipo de documento inválido.

**Solução**: Verifique tipos disponíveis:

```python
docs = cvm.get_available_docs()
print(list(docs.keys()))
```

### "EmptyDirectoryError"

**Causa**: Diretório vazio ou sem arquivos COTAHIST.

**Solução**: Verifique se os arquivos `COTAHIST_AXXXX.ZIP` estão no diretório.

### "NetworkError" ou "TimeoutError"

**Causa**: Problemas de conexão.

**Solução**:

1. Verifique sua conexão com a internet
2. Tente novamente mais tarde
3. Implemente retry logic (veja [estratégia de retry](../dev-guide/retry-strategy.md#exemplo-de-uso))

______________________________________________________________________

## Produção e Deploy

### Posso usar em produção?

Sim! O Global-Data-Finance é estável e testado. Recomendações:

- Use logging apropriado
- Implemente tratamento de erros robusto
- Configure retry logic para downloads
- Monitore uso de disco e memória

### Como agendar downloads automáticos?

Use `cron` (Linux/macOS) ou Task Scheduler (Windows):

```bash
# Crontab: executar todo dia às 2h da manhã
0 2 * * * /path/to/venv/bin/python /path/to/script.py
```

### Como integrar com pipelines de dados?

Global-Data-Finance funciona bem com:

- **Apache Airflow**: Crie DAGs para orquestração
- **Prefect**: Use como tasks em flows
- **Luigi**: Integre como tasks
- **Dagster**: Use como ops/assets

Exemplo com Airflow:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from globaldatafinance import FundamentalStocksDataCVM

def download_cvm():
    cvm = FundamentalStocksDataCVM()
    cvm.download(
        destination_path="/data/cvm",
        list_docs=["DFP"],
        initial_year=2023
    )

with DAG('cvm_download', ...) as dag:
    task = PythonOperator(
        task_id='download',
        python_callable=download_cvm
    )
```

______________________________________________________________________

## Contribuição

### Como contribuir com o projeto?

Veja o [guia de contribuição](../dev-guide/contributing.md) para detalhes completos.

### Como reportar bugs?

Abra uma issue no GitHub:
🔗 [https://github.com/jordanestralioto/Global-Data-Finance/issues](https://github.com/jordanestralioto/Global-Data-Finance/issues)

### Como sugerir novas funcionalidades?

Abra uma issue com a tag `enhancement` no GitHub.

______________________________________________________________________

## Licença e Uso

### Qual a licença do Global-Data-Finance?

Apache License 2.0.

### Posso usar em projetos comerciais?

Sim! A licença Apache 2.0 permite uso comercial.

### Os dados baixados têm restrições de uso?

Os dados são públicos e fornecidos pela CVM e B3. Consulte os termos de uso de cada instituição:

- **CVM**: [http://www.cvm.gov.br/](http://www.cvm.gov.br/)
- **B3**: [https://www.b3.com.br/](https://www.b3.com.br/)

______________________________________________________________________

## Suporte

### Onde obter ajuda?

1. **Documentação**: Leia a [documentação completa](../index.md)
2. **GitHub Issues**: [Abra uma issue](https://github.com/jordanestralioto/Global-Data-Finance/issues)
3. **Email**: estraliotojordan@gmail.com

### Como reportar problemas de segurança?

Envie um email para: estraliotojordan@gmail.com

______________________________________________________________________

!!! tip "Não encontrou sua pergunta?"
Abra uma issue no GitHub ou consulte a [documentação completa](../index.md).
