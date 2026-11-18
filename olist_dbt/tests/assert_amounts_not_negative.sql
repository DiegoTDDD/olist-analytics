-- Money and counts in the fact table are never negative.
select order_id
from {{ ref('fct_orders') }}
where total_payment_value < 0
   or total_item_price < 0
   or total_freight < 0
   or item_count < 0
   or max_installments < 0
