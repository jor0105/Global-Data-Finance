# Historical Quotes Extraction (COTAHIST)

Sistema de extração de dados históricos de cotações da B3 (Brasil, Bolsa, Balcão) a partir dos arquivos COTAHIST.

## 📋 Características

- **Arquitetura Limpa**: Separação clara entre Domain, Application, Infrastructure
- **SOLID**: Princípios de design bem aplicados
- **Assíncrono**: Processamento paralelo com `asyncio` para alta performance
- **Controle de Recursos**: Modos `fast` e `slow` para gerenciar CPU/RAM
- **Type-Safe**: Uso de Type Hints e protocolos
- **Parsing Preciso**: Conversão correta de decimais usando `Decimal`
- **Formato Parquet**: Saída otimizada usando Polars

## 🏗️ Arquitetura

```
historical_quotes/
├── domain/
│   ├── entities/          # Entidades de domínio
│   ├── value_objects/     # Objetos de valor com validação
│   └── exceptions/        # Exceções de domínio
├── application/
│   ├── interfaces/        # Protocolos (DIP)
│   └── use_cases/         # Casos de uso
└── infra/
    ├── file_system_service.py  # I/O de arquivos
    ├── zip_reader.py           # Leitura de ZIPs em memória
    ├── cotahist_parser.py      # Parser do formato B3
    ├── parquet_writer.py       # Escrita em Parquet
    └── extraction_service.py   # Orquestração assíncrona
```

## 🚀 Como Usar

### Instalação

```bash
pip install polars pyarrow
```

### Uso Básico

```python
from src.brazil.dados_b3.historical_quotes.application import (
    CreateDocsToExtractUseCase,
    ExtractHistoricalQuotesUseCase,
)

# 1. Configurar parâmetros
docs_extractor = CreateDocsToExtractUseCase(
    assets_list=['ações', 'etf'],
    initial_year=2023,
    last_year=2024,
    path_of_docs='/caminho/para/zips',
    destination_path='/caminho/saida'
).execute()

# 2. Executar extração
extraction = ExtractHistoricalQuotesUseCase()
result = extraction.execute_sync(
    docs_to_extract=docs_extractor,
    processing_mode='fast',  # ou 'slow'
    output_filename='cotahist.parquet'
)

print(f"Registros extraídos: {result['total_records']}")
```

## 📊 Classes de Ativos Suportadas

| Classe             | Códigos TPMERC | Descrição                         |
| ------------------ | -------------- | --------------------------------- |
| `ações`            | 010, 020       | Ações (lote padrão e fracionário) |
| `etf`              | 010, 020       | ETFs                              |
| `opções`           | 070, 080       | Opções de compra e venda          |
| `termo`            | 030            | Mercado a termo                   |
| `exercicio_opcoes` | 012, 013       | Exercício de opções               |
| `forward`          | 050, 060       | Mercado a termo com retorno       |
| `leilao`           | 017            | Leilão                            |

## ⚙️ Modos de Processamento

### Fast Mode (Rápido)

- **Concorrência**: Até 10 arquivos simultâneos
- **Uso**: Alto consumo de CPU e RAM
- **Indicado para**: Máquinas potentes, extração única

### Slow Mode (Lento)

- **Concorrência**: Até 2 arquivos simultâneos
- **Uso**: Baixo consumo de recursos
- **Indicado para**: Máquinas limitadas, processos em background

## 📝 Formato dos Dados

Os arquivos COTAHIST seguem um layout de **largura fixa** com 245 bytes por linha.

### Principais Campos Extraídos

- `data_pregao`: Data da sessão de negociação
- `codneg`: Código de negociação (ticker)
- `tpmerc`: Tipo de mercado
- `nomres`: Nome resumido da empresa
- `preabe`, `premax`, `premin`, `preult`: Preços (abertura, máximo, mínimo, fechamento)
- `totneg`: Número de negócios
- `quatot`: Quantidade negociada
- `voltot`: Volume financeiro
- `codisi`: Código ISIN

## 🧪 Testes

```bash
pytest tests/brazil/dados_b3/historical_quotes/
```

## 🔍 Análise de Código (Clean Architecture & SOLID)

### ✅ Princípios Aplicados

1. **Single Responsibility Principle (SRP)**

   - Cada classe tem uma única responsabilidade
   - `CotahistParser`: apenas parsing
   - `ZipFileReader`: apenas leitura de ZIPs
   - `FileSystemService`: apenas operações de sistema de arquivos

2. **Open/Closed Principle (OCP)**

   - Classes abertas para extensão via interfaces
   - Fechadas para modificação via dependency injection

3. **Liskov Substitution Principle (LSP)**

   - Uso de Protocolos permite substituição de implementações
   - Qualquer classe que implemente `IZipReader` pode ser usada

4. **Interface Segregation Principle (ISP)**

   - Interfaces pequenas e focadas
   - Cada protocolo define apenas os métodos necessários

5. **Dependency Inversion Principle (DIP)**
   - Use Cases dependem de abstrações (Protocolos)
   - Implementações concretas são injetadas

## 📦 Dependências

- `polars`: DataFrame e escrita Parquet
- `pyarrow`: Backend para Parquet
- Python 3.10+

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Veja o arquivo `LICENSE` para mais detalhes.

## 📚 Referências

- [Documentação B3 - Histórico de Cotações](http://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)
- [Layout COTAHIST](docs/context/HistoricalQuoteB3.md)
