"""Export the star schema to the Parquet files the Power BI report reads.

The report (powerbi/) imports these six files from one folder, set in its DataFolder
parameter. They are committed, so the report opens without building anything.

Usage (after `dbt build`):
    python export_powerbi.py
"""

import logging
import os
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("OLIST_DUCKDB", ROOT / "olist.duckdb"))
TARGET = ROOT / "data" / "powerbi"

# table -> sort key, so every rebuild writes the same file
TABLES = {
    "fct_orders": "order_id",
    "fct_order_items": "order_id, order_item_id",
    "dim_customers": "customer_id",
    "dim_products": "product_id",
    "dim_sellers": "seller_id",
    "dim_dates": "date_day",
}


def select(con: duckdb.DuckDBPyConnection, table: str) -> str:
    """SELECT with money as DOUBLE: Power BI reads Parquet DECIMAL(38, x) as text, and the report
    stores money as a fixed-decimal type anyway."""
    cols = []
    for name, dtype, *_ in con.execute(f"DESCRIBE {table}").fetchall():
        money = dtype.startswith("DECIMAL")
        cols.append(f'CAST("{name}" AS DOUBLE) AS "{name}"' if money else f'"{name}"')
    return f"SELECT {', '.join(cols)} FROM {table}"


def export(database: Path = DATABASE, target: Path = TARGET) -> dict[str, int]:
    target.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(database), read_only=True)
    rows = {}
    for table, key in TABLES.items():
        path = (target / f"{table}.parquet").as_posix()
        query = f"{select(con, table)} ORDER BY {key}"
        con.execute(f"COPY ({query}) TO '{path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        rows[table] = con.execute(f"SELECT COUNT(*) FROM '{path}'").fetchone()[0]
    con.close()
    return rows


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for table, n in export().items():
        log.info("%-16s %9s rows", table, f"{n:,}")


if __name__ == "__main__":
    main()
