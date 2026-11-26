-- Item prices and freight add up, order by order, to the totals on fct_orders.
select o.order_id
from {{ ref('fct_orders') }} as o
join (
    select order_id, sum(price) as price, sum(freight_value) as freight
    from {{ ref('fct_order_items') }}
    group by order_id
) as i on o.order_id = i.order_id
where o.total_item_price <> i.price or o.total_freight <> i.freight
