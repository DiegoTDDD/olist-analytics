-- Orders with status 'delivered' need a delivery timestamp, or delay_days silently becomes null
-- and the order drops out of the delivery-vs-satisfaction analysis. A handful of source rows
-- break this (the dataset's own inconsistency), so the test warns above a small tolerance.
{{ config(severity='warn', warn_if='> 10') }}
select order_id
from {{ ref('stg_orders') }}
where status = 'delivered' and delivered_to_customer_at is null
