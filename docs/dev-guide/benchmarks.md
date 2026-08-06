# Benchmarks de Performance

Este documento registra as linhas de base de extração e processamento para os
módulos da B3 e da CVM. Os números são evidência de um cenário de referência e
servem como métrica para regressão de performance, não uma promessa de tempo
fixo para qualquer hardware.

## 1. Linha de Base em Escala Real — B3 (2026-08-06)

**Ambiente:** Python 3.13.7 · Linux x86_64 (kernel 6.8) · 8 CPUs · 7,55 GB de
memória total. Sem chamadas de rede; apenas extração local dos ZIPs oficiais.

- **Dataset:** 17 arquivos ZIP oficiais (2008–2024), 503,77 MB comprimido.
- **Assets selecionados:** ações, etf, opções, termo, exercicio_opcoes, forward, leilao.
- **Erros:** 0 (todos os 17 arquivos processados com sucesso).
- **Saída Parquet consolidada:** 311,55 MB por modo.

| Modo    | Linhas gravadas | Tempo da API  | Tempo ponta a ponta | Pico RSS    | Throughput     |
| ------- | --------------: | ------------: | ------------------: | ----------: | -------------: |
| `fast`  |      15.059.876 |    1.222,61 s |          1.224,64 s | 4.259,35 MB | 12.317 reg/s   |
| `slow`  |      15.059.876 |    1.759,90 s |          1.761,91 s | 1.570,54 MB |  8.557 reg/s   |

> **Gargalo identificado:** Parser e merge Parquet da B3; o modo `fast` consome
> ~4,2 GiB de pico RSS. O modo `slow` usa menos de 1,6 GiB com throughput ~28%
> menor.

---

## 2. Linha de Base Sintética Reproduzível — B3

Para CI/CD e regressões rápidas, mantemos um dataset sintético menor. Medição
realizada em **2026-08-06**, revisão `7ee1843`, com três execuções independentes
por modo:

| Modo   | Registros | Entrada ZIP | Saída Parquet | Tempo da API (mediana) | Tempo ponta a ponta (mediana) |    Pico RSS | Registros/s (mediana) |
| ------ | --------: | ----------: | ------------: | ---------------------: | ----------------------------: | ----------: | --------------------: |
| `fast` |   250.000 |     8,46 MB |       4,05 MB |                11,15 s |                       12,27 s | 1.111,72 MB |                22.427 |
| `slow` |   250.000 |     8,46 MB |       4,05 MB |                18,05 s |                       19,04 s | 1.103,01 MB |                13.847 |

O cenário processou um arquivo sintético COTAHIST de 61,5 MB descompactado, com
250.000 registros filtrados para `ações`. Todas as execuções terminaram sem
erros. O pico RSS inclui interpretador, dependências, parser e escritor Parquet.

> **Observação:** Em datasets sintéticos pequenos, `fast` e `slow` apresentam
> picos RSS próximos (~1,1 GB). A diferença significativa de memória (~4,2 GB
> vs ~1,6 GB) só fica evidente em escala real, conforme métricas da Seção 1.

### Como reproduzir

```bash
# Dataset sintético (CI/regressão rápida)
uv run python scripts/benchmark_b3.py \
  --records 250000 \
  --mode both \
  --repetitions 3 \
  --output /tmp/globaldatafinance-b3-benchmark.json

# Arquivos oficiais locais
uv run python scripts/benchmark_b3.py \
  --data-dir /caminho/para/cotahist \
  --initial-year 2008 \
  --last-year 2024 \
  --assets ações etf opções termo exercicio_opcoes forward leilao \
  --mode both \
  --repetitions 1 \
  --timeout-seconds 7200
```

O arquivo sintético da linha de base tem SHA-256
`4ba04707468088975125a536b07f5a9cd361676e8ac68866554241ceb58b7e86`.

---

## 3. Linha de Base CVM — Download + Extração (2026-08-06)

Medição do fluxo completo de `FundamentalStocksDataCVM` com
`automatic_extractor=True`: download dos ZIPs brutos da CVM, extração CSV e
geração dos Parquets primários. Executado na mesma máquina dos benchmarks B3.

- **Docs:** DFP, ITR, FRE, FCA, CGVN, VLMO, IPE (todos os tipos disponíveis)
- **Período:** 2010–2024

| ZIPs baixados | Parquets gerados | Linhas extraídas | Saída total | Tempo total | Pico RSS   | Erros |
| ------------: | ---------------: | ---------------: | ----------: | ----------: | ---------: | ----: |
|            88 |            1.392 |       63.300.208 |  337,93 MB  |  505,04 s   | 459,18 MB  |     0 |

- Inclui: conexão com servidores CVM, download de todos os ZIPs, validação,
  extração CSV e conversão para Parquet.
- O tempo de rede varia com condições externas; o tempo de extração
  CSV→Parquet é a parcela estável e reprodutível da medida.

---

## 4. Limitações e Contratos

- O fixture sintético B3 valida o caminho completo de parsing, filtragem e
  escrita Parquet, mas não representa a cardinalidade, compressão ou distribuição
  de ativos de um ano real da B3.
- Ao atualizar os números reprodutíveis, preserve: dataset, checksum, hardware,
  versão do Python, revisão do código, número de repetições e definição de cada
  métrica.
