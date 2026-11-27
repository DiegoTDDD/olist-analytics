"""Load the nine raw Olist CSV files from data/raw/ into olist.duckdb, one table each.

Usage:
    python load_data.py                       # the full extract
    python load_data.py --as-of 2017-06-30    # the data as it was known at the end of that day

Every table gets a `_loaded_at` column (the time of this load, or --loaded-at), which the dbt
source freshness check reads. With --as-of, the orders, their items, payments and reviews are
cut to what had happened by the end of that day (see docs/adr/0006), so a sequence of loads
replays the feed day by day for the incremental models. Then build the models with dbt.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("OLIST_DUCKDB", ROOT / "olist.duckdb"))
RAW_DIR = ROOT / "data" / "raw"

# Tables cut to what was known on the --as-of date; the others are reference data, loaded in full.
OF_ORDERS = {"order_items", "order_payments"}


def table_name(filename: str) -> str:
    """olist_orders_dataset.csv -> orders; product_category_name_translation.csv keeps its name."""
    return filename.removesuffix(".csv").replace("olist_", "").replace("_dataset", "")


def as_of_query(name: str, csv: str, cutoff: str | None) -> str:
    """The SELECT that loads one table: everything, or what was known before `cutoff`."""
    # quote='"' is explicit on purpose: the automatic detection samples only the start of the
    # file, where no field is quoted, and then fails on the few later rows that are (e.g. a
    # city name containing commas).
    source = f"read_csv_auto('{csv}', quote='\"')"
    if cutoff is None:
        return f"SELECT * FROM {source}"
    c = f"TIMESTAMP '{cutoff}'"
    if name == "orders":
        # An event after the cutoff has not happened yet. Only a final 'delivered' can be walked
        # back, because only its steps have times; other final statuses keep their value.
        return f"""
            SELECT * REPLACE (
                CASE
                    WHEN order_status = 'delivered' AND order_delivered_customer_date >= {c} THEN
                        CASE
                            WHEN order_delivered_carrier_date < {c} THEN 'shipped'
                            WHEN order_approved_at < {c} THEN 'approved'
                            ELSE 'created'
                        END
                    ELSE order_status
                END AS order_status,
                CASE WHEN order_approved_at < {c} THEN order_approved_at END AS order_approved_at,
                CASE WHEN order_delivered_carrier_date < {c}
                     THEN order_delivered_carrier_date END AS order_delivered_carrier_date,
                CASE WHEN order_delivered_customer_date < {c}
                     THEN order_delivered_customer_date END AS order_delivered_customer_date
            )
            FROM {source}
            WHERE order_purchase_timestamp < {c}"""
    if name in OF_ORDERS:
        return f"SELECT * FROM {source} WHERE order_id IN (SELECT order_id FROM orders)"
    if name == "order_reviews":
        return (
            f"SELECT * FROM {source} WHERE review_answer_timestamp < {c} "
            "AND order_id IN (SELECT order_id FROM orders)"
        )
    return f"SELECT * FROM {source}"


def load(
    raw_dir: Path = RAW_DIR,
    database: Path = DATABASE,
    as_of: dt.date | None = None,
    loaded_at: dt.datetime | None = None,
) -> list[str]:
    cutoff = None if as_of is None else str(as_of + dt.timedelta(days=1))
    stamp = loaded_at or dt.datetime.now(dt.UTC)
    if stamp.tzinfo is not None:  # stored as naive UTC; a naive --loaded-at is taken as UTC
        stamp = stamp.astimezone(dt.UTC).replace(tzinfo=None)
    paths = {table_name(p.name): p for p in sorted(raw_dir.glob("*.csv"))}
    # orders first: the tables cut to its orders read it.
    order = sorted(paths, key=lambda n: (n != "orders", n))
    con = duckdb.connect(str(database))
    for name in order:
        query = as_of_query(name, paths[name].as_posix(), cutoff)
        con.execute(
            f"CREATE OR REPLACE TABLE {name} AS "
            f"SELECT *, TIMESTAMP '{stamp.isoformat(sep=' ')}' AS _loaded_at FROM ({query})"
        )
        rows = con.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        log.info("table created: %-36s %9d rows", name, rows)
    con.close()
    return order


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--as-of", type=dt.date.fromisoformat, help="load the data known by the end of this day"
    )
    parser.add_argument(
        "--loaded-at",
        type=dt.datetime.fromisoformat,
        help="stamp the load with this time instead of now (the freshness check's failing case)",
    )
    args = parser.parse_args(argv)
    tables = load(as_of=args.as_of, loaded_at=args.loaded_at)
    when = f"as of {args.as_of}" if args.as_of else "full extract"
    log.info("%d tables in %s (%s)", len(tables), DATABASE, when)


if __name__ == "__main__":
    main()
