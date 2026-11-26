-- One row per item sold: the grain for product category and seller analysis.
-- The order's status, purchase date, delay flag and review are carried on each item so a
-- category or a seller can be measured on delivery and satisfaction without a second join.
with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select order_id, status, purchase_date, is_delayed, delay_days, review_score
    from {{ ref('fct_orders') }}
)

select
    items.order_id,
    items.order_item_id,
    items.product_id,
    items.seller_id,
    orders.status,
    orders.purchase_date,
    cast(items.price as decimal(12, 2)) as price,
    cast(items.freight_value as decimal(12, 2)) as freight_value,
    orders.is_delayed,
    orders.delay_days,
    orders.review_score
from items
inner join orders on items.order_id = orders.order_id
