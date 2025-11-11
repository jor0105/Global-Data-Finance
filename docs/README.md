# 📚 Documentação do Projeto DataFinance

Bem-vindo à documentação do projeto DataFinance!

## 🗂️ Índice de Documentos

### 📖 Documentação Geral

- **[TODO.MD](TODO.MD)** - Lista de tarefas e planejamento geral do projeto

### 🏗️ Historical Quotes (COTAHIST B3)

#### Contexto e Especificações

- **[HistoricalQuoteB3.md](context/HistoricalQuoteB3.md)** - Layout oficial do arquivo COTAHIST (245 bytes/linha)
- **[Proj_Historical_Quote.md](context/Proj_Historical_Quote.md)** - Especificação do projeto de extração

#### Implementação

- **[SUMMARY.md](SUMMARY.md)** - 📊 Sumário executivo completo do projeto
- **[CHECKLIST.md](CHECKLIST.md)** - ✅ Checklist detalhado de implementação (100% completo)
- **[CODE_REVIEW.md](CODE_REVIEW.md)** - 🔍 Análise de código e princípios SOLID/Clean Architecture
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - 🔄 Guia de migração e uso do código novo

## 🚀 Quick Start - Historical Quotes

### 1. Leia a Documentação

Comece por estes documentos na ordem:

1. **[SUMMARY.md](SUMMARY.md)** - Visão geral do que foi implementado
2. **[CODE_REVIEW.md](CODE_REVIEW.md)** - Entenda a arquitetura e princípios
3. **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Como usar na prática

### 2. Veja o Código

```bash
cd src/brazil/dados_b3/historical_quotes/
cat README.md
```

### 3. Execute os Exemplos

```bash
# Exemplo básico (síncrono)
python examples/historical_quotes_extraction.py

# Exemplo avançado (assíncrono)
python examples/historical_quotes_async.py
```

### 4. Execute os Testes

```bash
pytest tests/brazil/dados_b3/historical_quotes/ -v
```

## 📋 Status dos Módulos

| Módulo                 | Status       | Documentação | Testes      |
| ---------------------- | ------------ | ------------ | ----------- |
| **Historical Quotes**  | ✅ Completo  | ✅ Completa  | ✅ Completa |
| CVM Fundamental Stocks | 🟢 Existente | 🟡 Parcial   | 🟡 Parcial  |
| B3 Capital Social      | 🟢 Existente | 🟡 Parcial   | ⚪ Pendente |
| B3 Dados Ações         | 🟢 Existente | 🟡 Parcial   | ⚪ Pendente |
| B3 Opções              | 🟢 Existente | 🟡 Parcial   | ⚪ Pendente |

## 🎯 Arquitetura do Projeto

O projeto segue **Clean Architecture** com três camadas principais:

```
src/
├── domain/              # Entidades e Value Objects
│   ├── entities/
│   └── value_objects/
├── application/         # Casos de Uso e Interfaces
│   ├── interfaces/
│   └── use_cases/
└── infra/              # Implementações Concretas
    ├── parsers/
    ├── repositories/
    └── services/
```

### Princípios Aplicados

- ✅ **SOLID**: Todos os 5 princípios
- ✅ **DRY**: Don't Repeat Yourself
- ✅ **KISS**: Keep It Simple, Stupid
- ✅ **YAGNI**: You Aren't Gonna Need It
- ✅ **Separation of Concerns**: Separação clara de responsabilidades

## 📦 Dependências

```toml
[dependencies]
pandas = ">=2.3.3"
polars = ">=1.0.0"
pyarrow = ">=22.0.0"
httpx = ">=0.28.1"
pydantic-settings = ">=2.11.0"

[dev-dependencies]
pytest = ">=8.4.2"
pytest-asyncio = "^1.2.0"
pre-commit = ">=4.3.0"
```

## 🧪 Testando o Projeto

### Testes Unitários

```bash
pytest tests/ -v
```

### Testes de Integração

```bash
pytest tests/ -v -m integration
```

### Cobertura de Código

```bash
pytest tests/ --cov=src --cov-report=html
```

## 📚 Recursos Adicionais

### Historical Quotes

- [B3 - Histórico de Cotações](http://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)
- [Layout COTAHIST](context/HistoricalQuoteB3.md)

### Clean Architecture

- [The Clean Architecture - Uncle Bob](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Guidelines

- Siga os princípios SOLID e Clean Architecture
- Escreva testes para novas features
- Documente suas mudanças
- Use type hints
- Mantenha o código limpo e legível

## 📝 Changelog

### v1.0.0 (2024-11-11) - Historical Quotes

- ✅ Implementação completa do módulo Historical Quotes
- ✅ Parser COTAHIST com todos os campos
- ✅ Processamento assíncrono com controle de recursos
- ✅ Mapeamento de asset classes para TPMERC
- ✅ Salvamento em Parquet
- ✅ Testes unitários e de integração
- ✅ Documentação completa

## 📞 Suporte

Para questões, sugestões ou problemas:

1. Abra uma issue no GitHub
2. Consulte a documentação em `docs/`
3. Veja os exemplos em `examples/`

## 📄 Licença

Ver arquivo `LICENSE` na raiz do projeto.

---

**Última atualização**: 11 de novembro de 2024
**Versão**: 1.0.0
**Autor**: Jordan Estralioto
