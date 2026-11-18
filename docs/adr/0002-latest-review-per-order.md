# 0002. One review per order: the most recent

**Status:** Accepted

## Context
Some orders have several reviews. Averaging them produced fractional scores such as 3.5, which the `accepted_values` test on 1 to 5 caught.

## Decision
Keep the most recent review per order: `row_number()` ordered by `review_creation_date` descending, then `review_answer_timestamp` descending, then `review_id`. The extra keys matter because 31 orders have two reviews created at the same instant with different scores. Without them the choice was arbitrary and changed between rebuilds, which CI caught when the rebuilt export differed from the committed one in 77 rows.

## Alternatives considered
- **Average.** Not a score a customer gave.
- **First review.** The customer's later review reflects their final opinion of the order.

## Consequences
- `review_score` is always an integer from 1 to 5, and the test enforces it.
- Rebuilds are deterministic: the CI check compares the rebuilt `fct_orders` with the committed export on every change.
