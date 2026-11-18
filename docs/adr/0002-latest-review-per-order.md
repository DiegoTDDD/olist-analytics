# 0002. One review per order: the most recent

**Status:** Accepted

## Context
Some orders have several reviews. Averaging them produced fractional scores such as 3.5, which the `accepted_values` test on 1 to 5 caught.

## Decision
Keep the most recent review per order (`row_number()` over `review_creation_date` descending).

## Alternatives considered
- **Average.** Not a score a customer gave.
- **First review.** The customer's later review reflects their final opinion of the order.

## Consequences
- `review_score` is always an integer from 1 to 5, and the test enforces it.
