"""The replay load: what was known at the end of a day, and the full extract unchanged."""

import datetime as dt
from pathlib import Path

import duckdb
import pytest

import load_data

ORDERS = """order_id,customer_id,order_status,order_purchase_timestamp,order_approved_at,order_delivered_carrier_date,order_delivered_customer_date,order_estimated_delivery_date
o1,c1,delivered,2017-01-01 10:00:00,2017-01-01 11:00:00,2017-01-03 09:00:00,2017-01-06 15:00:00,2017-01-10 00:00:00
o2,c2,canceled,2017-01-02 10:00:00,,,,2017-01-12 00:00:00
o3,c3,delivered,2017-01-08 10:00:00,2017-01-08 12:00:00,2017-01-09 09:00:00,2017-01-15 15:00:00,2017-01-20 00:00:00
"""
ITEMS = """order_id,order_item_id,product_id,seller_id,shipping_limit_date,price,freight_value
o1,1,p1,s1,2017-01-05 00:00:00,10.00,1.00
o3,1,p1,s1,2017-01-12 00:00:00,20.00,2.00
"""
REVIEWS = """review_id,order_id,review_score,review_comment_title,review_comment_message,review_creation_date,review_answer_timestamp
r1,o1,5,,,2017-01-07 00:00:00,2017-01-08 10:00:00
"""
CUSTOMERS = """customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,customer_state
c1,u1,1000,sao paulo,SP
c2,u2,1000,sao paulo,SP
c3,u3,1000,sao paulo,SP
"""


@pytest.fixture
def raw(tmp_path: Path) -> Path:
    d = tmp_path / "raw"
    d.mkdir()
    (d / "olist_orders_dataset.csv").write_text(ORDERS)
    (d / "olist_order_items_dataset.csv").write_text(ITEMS)
    (d / "olist_order_reviews_dataset.csv").write_text(REVIEWS)
    (d / "olist_customers_dataset.csv").write_text(CUSTOMERS)
    return d


def run(raw: Path, tmp_path: Path, **kw) -> duckdb.DuckDBPyConnection:
    db = tmp_path / "t.duckdb"
    load_data.load(raw, db, **kw)
    return duckdb.connect(str(db))


def test_full_extract_is_loaded_as_is(raw, tmp_path):
    con = run(raw, tmp_path)
    assert con.execute("select order_id, order_status from orders order by 1").fetchall() == [
        ("o1", "delivered"), ("o2", "canceled"), ("o3", "delivered")]  # fmt: skip
    assert con.execute("select count(*) from order_reviews").fetchone()[0] == 1
    assert con.execute("select count(*) from customers").fetchone()[0] == 3


def test_as_of_walks_a_delivery_back_and_hides_future_events(raw, tmp_path):
    con = run(raw, tmp_path, as_of=dt.date(2017, 1, 4))
    rows = con.execute(
        "select order_id, order_status, order_delivered_carrier_date, order_delivered_customer_date "
        "from orders order by 1"
    ).fetchall()
    assert rows == [
        ("o1", "shipped", dt.datetime(2017, 1, 3, 9), None),
        ("o2", "canceled", None, None),  # no event time: keeps its final status
    ]
    assert con.execute("select order_id from order_items").fetchall() == [("o1",)]
    assert con.execute("select count(*) from order_reviews").fetchone()[0] == 0  # answered on the 8th
    assert con.execute("select count(*) from customers").fetchone()[0] == 3  # reference data in full


def test_as_of_the_day_of_an_event_includes_it(raw, tmp_path):
    con = run(raw, tmp_path, as_of=dt.date(2017, 1, 8))
    assert con.execute("select order_status from orders where order_id = 'o1'").fetchone()[0] == "delivered"
    assert con.execute("select order_status from orders where order_id = 'o3'").fetchone()[0] == "approved"
    assert con.execute("select count(*) from order_reviews").fetchone()[0] == 1


def test_every_table_is_stamped_with_the_load_time(raw, tmp_path):
    con = run(raw, tmp_path, loaded_at=dt.datetime(2026, 1, 2, 3, 4, 5))
    for table in ["orders", "order_items", "order_reviews", "customers"]:
        assert con.execute(f"select distinct _loaded_at from {table}").fetchall() == [(dt.datetime(2026, 1, 2, 3, 4, 5),)]
