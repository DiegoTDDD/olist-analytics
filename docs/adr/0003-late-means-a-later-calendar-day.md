# 0003. "Late" means delivered on a later calendar day than promised

**Status:** Accepted. Fixes `is_delayed`, which compared timestamps.

## Context
`order_estimated_delivery_date` is a date, stored as midnight. `is_delayed` compared it with the delivery timestamp, so an order delivered on the promised day at 2 pm counted as late. `delay_days`, which the analysis uses, compares calendar days. The two disagreed on 1,292 orders.

## Decision
`is_delayed` = the delivery date is after the promised date, the same rule as `delay_days > 0`. The singular test `assert_is_delayed_matches_delay_days` keeps them in agreement.

## Consequences
- The dashboard's "% delayed" goes from 7.9% to 6.6%. The 1,292 reclassified orders averaged a 4.03 review score, close to the 4.29 of on-time orders and far from late ones, which confirms they were not late for the customer.
- The delay-bucket table in the README was already based on `delay_days` and does not change.
