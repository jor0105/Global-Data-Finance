# Performance Benchmarks

This document records reproducible baselines for extraction and processing
across the B3 and CVM modules. The numbers are evidence from a reference
scenario and serve as a regression metric, not a fixed-time promise for every
machine or dataset.

## 1. Real-Scale Baseline — B3 (2026-08-06)

**Environment:** Python 3.13.7 · Linux x86_64 (kernel 6.8) · 8 CPUs · 7.55 GB
total memory. No network calls; local extraction of official ZIPs only.

- **Dataset:** 17 official ZIP files (2008–2024), 503.77 MB compressed.
- **Selected assets:** ações, etf, opções, termo, exercicio_opcoes, forward, leilao.
- **Errors:** 0 (all 17 files processed successfully).
- **Consolidated Parquet output:** 311.55 MB per mode.

| Mode   | Written rows |   API time | End-to-end |    Peak RSS |    Throughput |
| ------ | -----------: | ---------: | ---------: | ----------: | ------------: |
| `fast` |   15,059,876 | 1,222.61 s | 1,224.64 s | 4,259.35 MB | 12,317 rows/s |
| `slow` |   15,059,876 | 1,759.90 s | 1,761.91 s | 1,570.54 MB |  8,557 rows/s |

> **Bottleneck identified:** B3 Parquet parser and merge; `fast` mode peaks at
> ~4.2 GiB RSS. `slow` uses under 1.6 GiB with ~28% lower throughput.

______________________________________________________________________

## 2. Reproducible Synthetic Baseline — B3

For CI/CD and fast regressions, a smaller synthetic dataset is maintained.
Measured on **2026-08-06**, revision `7ee1843`, with three independent runs per
mode:

| Mode   | Records | ZIP input | Parquet output | API time (median) | End-to-end time (median) |    Peak RSS | Records/s (median) |
| ------ | ------: | --------: | -------------: | ----------------: | -----------------------: | ----------: | -----------------: |
| `fast` | 250,000 |   8.46 MB |        4.05 MB |           11.15 s |                  12.27 s | 1,111.72 MB |             22,427 |
| `slow` | 250,000 |   8.46 MB |        4.05 MB |           18.05 s |                  19.04 s | 1,103.01 MB |             13,847 |

The scenario processed a synthetic 61.5 MB uncompressed COTAHIST file with
250,000 records filtered to `ações`. All runs completed without errors. Peak RSS
includes the interpreter, dependencies, parser, and Parquet writer.

> **Note:** At synthetic scale, `fast` and `slow` show similar peak RSS (~1.1 GB).
> The significant memory difference (~4.2 GB vs ~1.6 GB) only becomes apparent at
> real scale, as shown in Section 1.

### Reproduction

```bash
# Synthetic dataset (CI / fast regression)
uv run python scripts/benchmark_b3.py \
  --records 250000 \
  --mode both \
  --repetitions 3 \
  --output /tmp/globaldatafinance-b3-benchmark.json

# Official local files
uv run python scripts/benchmark_b3.py \
  --data-dir /path/to/cotahist \
  --initial-year 2008 \
  --last-year 2024 \
  --assets ações etf opções termo exercicio_opcoes forward leilao \
  --mode both \
  --repetitions 1 \
  --timeout-seconds 7200
```

The synthetic archive used for the baseline has SHA-256
`4ba04707468088975125a536b07f5a9cd361676e8ac68866554241ceb58b7e86`.

______________________________________________________________________

## 3. CVM Baseline — Download + Extraction (2026-08-06)

Full-pipeline measurement of `FundamentalStocksDataCVM` with
`automatic_extractor=True`: raw ZIP downloads from CVM, CSV extraction, and
primary Parquet generation. Run on the same machine as the B3 benchmarks.

- **Docs:** DFP, ITR, FRE, FCA, CGVN, VLMO, IPE (all available types)
- **Period:** 2010–2024

| ZIPs downloaded | Parquets generated | Extracted rows | Total output | Total time |  Peak RSS | Errors |
| --------------: | -----------------: | -------------: | -----------: | ---------: | --------: | -----: |
|              88 |              1,392 |     63,300,208 |    337.93 MB |   505.04 s | 459.18 MB |      0 |

- Includes: CVM server connection, downloading all ZIPs, validation, CSV
  extraction, and Parquet conversion.
- Network time varies with external conditions; the CSV→Parquet extraction
  step is the stable and reproducible portion of the measurement.

______________________________________________________________________

## 4. Limitations and Contracts

- The synthetic B3 fixture validates the complete parsing, filtering, and
  Parquet-writing path, but does not represent the cardinality, compression, or
  asset mix of a real B3 year.
- When updating reproducible numbers, preserve: dataset, checksum, hardware,
  Python version, code revision, repetition count, and metric definitions.
