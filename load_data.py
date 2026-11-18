"""Load the nine raw Olist CSV files from data/raw/ into olist.duckdb, one table each, as is.

Usage:
    python load_data.py
Then build the models with dbt (see the README).
"""

import logging
import os
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("OLIST_DUCKDB", ROOT / "olist.duckdb"))
RAW_DIR = ROOT / "data" / "raw"


def table_name(filename: str) -> str:
    """olist_orders_dataset.csv -> orders; product_category_name_translation.csv keeps its name."""
    return filename.removesuffix(".csv").replace("olist_", "").replace("_dataset", "")


def load(raw_dir: Path = RAW_DIR, database: Path = DATABASE) -> list[str]:
    con = duckdb.connect(str(database))
    tables = []
    for path in sorted(raw_dir.glob("*.csv")):
        name = table_name(path.name)
        # quote='"' is explicit on purpose: the automatic detection samples only the start of the
        # file, where no field is quoted, and then fails on the few later rows that are (e.g. a
        # city name containing commas).
        con.execute(
            f"""CREATE OR REPLACE TABLE {name} AS
                SELECT * FROM read_csv_auto('{path.as_posix()}', quote='"')"""
        )
        log.info("table created: %s", name)
        tables.append(name)
    con.close()
    return tables


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    tables = load()
    log.info("%d tables in %s", len(tables), DATABASE)


if __name__ == "__main__":
    main()
