# Plan 001
- `load_data.py`: `--as-of`, `--loaded-at`; SQL views over the CSVs, filtered and with the
  derived status; `_loaded_at` on every table.
- `fct_orders`: `materialized='incremental'`, `incremental_strategy='delete+insert'`,
  `unique_key='order_id'`, new column `source_updated_at`; in incremental runs, a `changed`
  CTE selects the orders to rebuild.
- `fct_order_items`: same strategy keyed on `order_id`, driven by `fct_orders.source_updated_at`.
- `_sources.yml`: `loaded_at_field: _loaded_at` and freshness thresholds.
- `export_marts.py` / `export_powerbi.py`: drop `source_updated_at`.
- `scripts/check_incremental.py`: the replay check (R4). Unit tests for the replay load.
- `dbt-check.yml`: replay check, freshness pass and fail.
- ADR 0006 (supersedes 0004); README and counts.
