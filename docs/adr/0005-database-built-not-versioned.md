# 0005. The database is built, not versioned; the dashboard reads a Parquet export

**Status:** Accepted. Replaces the 46 MB `olist.duckdb` committed to the repository.

## Context
The repository shipped the finished DuckDB file (raw tables plus every model) so the deployed dashboard had something to read. Every rebuild added a new 46 MB binary to Git history, and the file could drift from the code that is supposed to produce it.

## Decision
- `olist.duckdb` is gitignored. It is built with `scripts/download_data.sh`, `load_data.py` and `dbt build`.
- `export_marts.py` writes `fct_orders`, the only table the dashboard uses, to `data/marts/fct_orders.parquet` (4.6 MB), sorted so that rebuilds are identical. The dashboard reads that file.
- CI rebuilds everything from the raw CSV files on every change and fails if the rebuilt export differs from the committed one.

## Alternatives considered
- **Git LFS for the database.** Keeps the binary, and its bandwidth quota, without solving drift.
- **Build the database on Streamlit Cloud at start-up.** Slow, and it needs dbt on the host.

## Consequences
- The repository stops growing by 46 MB per rebuild. Past versions remain in the history; rewriting history would break existing clones, so it was not done.
- The rebuild must give the same table on any machine. Two sources of variation were found by this check and removed: tied reviews (ADR 0002), and money summed as floating point, whose last digits depended on how many CPU threads added the rows. Money is now summed as `DECIMAL`, which is exact.
