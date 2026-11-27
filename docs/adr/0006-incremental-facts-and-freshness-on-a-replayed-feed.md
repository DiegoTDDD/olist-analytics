# 0006. Incremental fact tables and source freshness, proven on a replayed feed

**Status:** Accepted. Supersedes [0004](0004-source-tests-instead-of-freshness.md).

## Context
The Olist files are a fixed 2016-2018 extract, so every run rebuilt everything and there was
nothing for a freshness check to watch (ADR 0004). A warehouse fed every day needs both: fact
tables that touch only the orders that changed, and an alarm when the feed stops. Neither can be
shown, let alone tested, on a file that never changes.

The data does say when things happened: each order has its purchase, approval, hand-over to the
carrier and delivery times, and each review its answer time. That is enough to rebuild what the
marketplace knew at the end of any day.

## Decision
- **Replay.** `load_data.py --as-of DATE` loads the state at the end of DATE: orders purchased
  by then, with later events blanked and a final `delivered` walked back to `shipped`,
  `approved` or `created`; their items and payments; reviews answered by then. Reference tables
  (customers, products, sellers, geolocation, categories) load in full. Without `--as-of`, the
  load is the full extract, and every published number is unchanged.
- **Incremental facts.** `fct_orders` and `fct_order_items` are incremental (`delete+insert` on
  `order_id`). Each order carries `source_updated_at`, the latest of its events and review
  answers; a run rebuilds the orders newer than the table's maximum minus a 3-day lookback for
  rows that arrive late, and replaces all of their rows. The column is the watermark only and is
  not exported, so the dashboard and Power BI files are unchanged. Dimensions and staging stay
  views: they are cheap and have no history to keep.
- **Proof.** `scripts/check_incremental.py` replays the feed (months apart, two consecutive days,
  the end of the feed, then the full extract). At every step it runs the incremental build on a
  database that keeps its tables, a full rebuild on a fresh one, and compares both tables row for
  row; CI fails on any difference. Removing the review answer from the watermark, on purpose,
  makes it fail with 197 differing orders after one month.
- **Freshness.** Every raw table carries `_loaded_at`, the load time. The sources warn after 26
  hours and fail after 50 (a daily feed may miss one run). CI runs the check on its own load,
  which must pass, and on a load stamped three days old, which must fail.

## Consequences
- A daily run reprocesses the orders that changed that day plus the lookback, not the 99,441
  orders; the replay prints how many each step touched.
- Status replay is approximate where the data has no time: canceled, unavailable, invoiced and
  processing orders keep their final status from purchase.
- `--full-refresh` rebuilds everything, and CI shows it gives the same tables.
- Freshness measures the pipeline (when data last arrived), not how recent the orders are; on
  this extract, the newest order is from 2018 by design.
