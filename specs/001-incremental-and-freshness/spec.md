# Spec 001: incremental fact tables and source freshness

## Problem
The Olist files are a fixed 2016-2018 extract, so the project rebuilt everything on every run
and had no freshness check (ADR 0004). A warehouse fed daily needs both: facts that update only
the orders that changed, and an alarm when the feed stops. Neither can be shown on a static
file unless the data arrives over time.

## Requirements
- R1. `load_data.py --as-of DATE` loads the data as it was known at the end of DATE: orders
  purchased by then, with the delivery events and status of that day; items and payments of
  those orders; reviews answered by then. Reference tables load in full. Without `--as-of`, the
  load is the full extract (unchanged results).
- R2. Every raw table carries `_loaded_at`, the time of the load (`--loaded-at` overrides it).
- R3. `fct_orders` and `fct_order_items` are incremental: a run reprocesses only orders whose
  latest event (purchase, approval, hand-over to the carrier, delivery, review answer) is newer
  than the table's watermark minus a 3-day lookback, replacing those orders' rows.
- R4. At every step of a replay (several as-of dates, then the full extract), the incremental
  tables equal a full rebuild of the same data, row for row. CI checks this.
- R5. Sources have freshness on `_loaded_at`: warn after 26 hours, error after 50 (a daily
  feed may miss one run). CI runs it on a fresh load (passes) and on a load stamped three days
  old (must fail).
- R6. Exports, the dashboard and the Power BI files are unchanged: the watermark column is not
  exported.

## Clarifications
- Status as of a date: an order finally `delivered` shows `shipped` / `approved` / `created`
  before its delivery, hand-over or approval time. Other final statuses (canceled, unavailable,
  invoiced, processing) carry no event time in the data, so they keep their final status from
  purchase; documented as a limit of the replay.
- Reviews become visible at `review_answer_timestamp`.
