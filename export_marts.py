"""Export fct_orders from the built database to the Parquet file the dashboard reads.

olist.duckdb (raw tables + dbt models) is built locally and is not versioned.
The deployed dashboard reads this small, committed export instead.

Usage (after `dbt build`):
    python export_marts.py
"""

import logging
import os
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("OLIST_DUCKDB", ROOT / "olist.duckdb"))
EXPORT = ROOT / "data" / "marts" / "fct_orders.parquet"


def export(database: Path = DATABASE, target: Path = EXPORT) -> int:
    """Write fct_orders, sorted by order_id so the file is the same on every rebuild."""
    target.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(database), read_only=True)
    con.execute(
        # source_updated_at is the incremental models' watermark, not something to report.
        "COPY (SELECT * EXCLUDE (source_updated_at) FROM fct_orders ORDER BY order_id) "
        f"TO '{target.as_posix()}' "
        "(FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    rows = con.execute(f"SELECT COUNT(*) FROM '{target.as_posix()}'").fetchone()[0]
    con.close()
    return rows


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    rows = export()
    log.info("Wrote %s orders to %s (%.1f MB)", f"{rows:,}", EXPORT, EXPORT.stat().st_size / 1e6)


if __name__ == "__main__":
    main()
