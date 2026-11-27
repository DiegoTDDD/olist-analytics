# Architecture decision records

| # | Decision | Status |
|---|---|---|
| [0001](0001-star-schema-in-dbt-on-duckdb.md) | A star schema built with dbt on DuckDB | Accepted |
| [0002](0002-latest-review-per-order.md) | One review per order: the most recent | Accepted |
| [0003](0003-late-means-a-later-calendar-day.md) | "Late" means delivered on a later calendar day than promised | Accepted, fixes the timestamp comparison |
| [0004](0004-source-tests-instead-of-freshness.md) | Source tests instead of freshness checks for a static snapshot | Superseded by 0006 |
| [0005](0005-database-built-not-versioned.md) | The database is built, not versioned; the dashboard reads a Parquet export | Accepted, replaces the 46 MB committed database |
| [0006](0006-incremental-facts-and-freshness-on-a-replayed-feed.md) | Incremental fact tables and source freshness, proven on a replayed feed | Accepted, supersedes 0004 |
