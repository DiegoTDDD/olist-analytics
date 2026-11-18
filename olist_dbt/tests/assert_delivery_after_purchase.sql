-- A delivered order cannot arrive before it was bought.
select order_id, delivery_days
from {{ ref('fct_orders') }}
where delivery_days < 0
