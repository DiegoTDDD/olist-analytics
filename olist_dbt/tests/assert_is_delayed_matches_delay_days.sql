-- An order is late exactly when it arrived on a later day than promised (delay_days > 0).
-- Comparing timestamps instead once flagged 1,292 orders delivered on the promised day.
select order_id, is_delayed, delay_days
from {{ ref('fct_orders') }}
where is_delayed != coalesce(delay_days > 0, false)
