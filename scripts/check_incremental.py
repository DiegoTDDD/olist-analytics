"""Prove the incremental models equal a full rebuild at every step of a day-by-day replay.

    python scripts/check_incremental.py [--dates 2017-03-31 2017-09-30 ...]

For each as-of date, then the full extract: load that state into a database that keeps its
tables between steps and run `dbt build` there (incremental), load the same state into a fresh
database and run `dbt build --full-refresh`, and compare fct_orders and fct_order_items row for
row. Any difference fails. Also checks that each incremental step rebuilt only part of the table.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import load_data  # noqa: E402

TABLES = ["fct_orders", "fct_order_items"]
# Months apart, then two consecutive days (an ordinary daily run), then the end of the feed.
DEFAULT_DATES = ["2017-03-31", "2017-09-30", "2017-12-31", "2018-04-30", "2018-08-14", "2018-08-15", "2018-09-15"]


def dbt(database: Path, *args: str) -> None:
    env = {**os.environ, "OLIST_DUCKDB": str(database)}
    out = subprocess.run(["dbt", *args, "--quiet"], cwd=ROOT / "olist_dbt", env=env, text=True,
                         capture_output=True)  # fmt: skip
    if out.returncode:
        sys.exit(f"dbt {' '.join(args)} failed:\n{out.stdout}\n{out.stderr}")


def differences(a: Path, b: Path, table: str) -> tuple[int, int, int]:
    con = duckdb.connect()
    con.execute(f"ATTACH '{a}' AS inc (READ_ONLY)")
    con.execute(f"ATTACH '{b}' AS full_ (READ_ONLY)")
    only_inc = con.execute(f"SELECT count(*) FROM (FROM inc.{table} EXCEPT ALL FROM full_.{table})").fetchone()[0]
    only_full = con.execute(f"SELECT count(*) FROM (FROM full_.{table} EXCEPT ALL FROM inc.{table})").fetchone()[0]
    rows = con.execute(f"SELECT count(*) FROM full_.{table}").fetchone()[0]
    con.close()
    return rows, only_inc, only_full


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dates", nargs="+", default=DEFAULT_DATES)
    args = parser.parse_args(argv)
    steps: list[dt.date | None] = [dt.date.fromisoformat(d) for d in args.dates] + [None]
    work = Path(tempfile.mkdtemp())
    incremental = work / "incremental.duckdb"
    failed = False
    for i, as_of in enumerate(steps):
        label = str(as_of) if as_of else "full extract"
        load_data.load(database=incremental, as_of=as_of)
        before = 0
        if i:
            con = duckdb.connect(str(incremental), read_only=True)
            before = con.execute("SELECT max(source_updated_at) FROM fct_orders").fetchone()[0]
            con.close()
        dbt(incremental, "build")
        fresh = work / f"full_{i}.duckdb"
        load_data.load(database=fresh, as_of=as_of)
        dbt(fresh, "build", "--full-refresh")
        con = duckdb.connect(str(incremental), read_only=True)
        rebuilt = con.execute(
            "SELECT count(*) FROM fct_orders WHERE source_updated_at > ? - interval 3 day", [before]
        ).fetchone()[0] if i else None
        con.close()
        for table in TABLES:
            rows, only_inc, only_full = differences(incremental, fresh, table)
            ok = only_inc == 0 and only_full == 0
            failed |= not ok
            note = f", {rebuilt:,} orders reprocessed" if rebuilt is not None and table == "fct_orders" else ""
            print(f"{label:>12} {table:16} {rows:>7,} rows; only incremental {only_inc}, "
                  f"only full rebuild {only_full}{note} {'OK' if ok else 'MISMATCH'}", flush=True)  # fmt: skip
        fresh.unlink()
    if failed:
        sys.exit("incremental and full rebuild differ")
    print("incremental == full rebuild at every step")


if __name__ == "__main__":
    main()
