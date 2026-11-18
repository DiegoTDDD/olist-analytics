# 0001. A star schema built with dbt on DuckDB

**Status:** Accepted

## Context
Nine raw tables (orders, items, payments, reviews, customers, sellers, products, categories, geolocation) with different grains. The business question needs one row per order that carries the delivery dates, the payment, the items and the review together.

## Decision
- **Staging:** one view per source with consistent names and fixed typos, and no logic.
- **Marts:** `fct_orders` (one row per order) and `dim_customers`, `dim_products`, `dim_sellers` and `dim_dates`.
- dbt manages the SQL, the lineage and the tests. DuckDB runs it in process.

## Alternatives considered
- **One wide denormalised table.** Fine for one chart, but it repeats customer and product attributes and makes every new question a rewrite.
- **A warehouse (Postgres, BigQuery).** A service or a bill, for 100,000 orders.

## Consequences
- The whole build runs in seconds on a laptop or a CI runner.
- Aggregating payments, items and reviews to the order grain is where bugs hide, so tests guard it (one fact row per order, at most one review per order).
