# 0004. Source tests instead of freshness checks for a static snapshot

**Status:** Superseded by [0006](0006-incremental-facts-and-freshness-on-a-replayed-feed.md): the feed is now replayed day by day, and the sources have freshness checks. The source tests below remain.

## Context
dbt's source freshness compares the newest timestamp in a source with the current time. The Olist dataset is a fixed historical extract (2016 to 2018) and will never be refreshed, so any threshold would either always fail or be set so high that it checks nothing.

## Decision
No freshness block. Instead, test the sources directly: unique and not-null primary keys, order items pointing at real orders, review scores between 1 and 5, and category translations that are unique. Integrity of the files themselves comes from pinned SHA-256 hashes (`scripts/olist_csv.sha256`).

## Consequences
- A broken or changed input fails `dbt build` before any model is built on it.
- If the project ever moved to a live feed, freshness on `orders.order_purchase_timestamp` would be the first check to add.
