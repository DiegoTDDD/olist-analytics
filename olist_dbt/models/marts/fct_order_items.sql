{{
    config(
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key='order_id',
        on_schema_change='fail'
    )
}}

-- One row per item sold: the grain for product category and seller analysis.
-- The order's status, purchase date, delay flag and review are carried on each item so a
-- category or a seller can be measured on delivery and satisfaction without a second join.
with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select order_id, status, purchase_date, is_delayed, delay_days, review_score, source_updated_at
    from {{ ref('fct_orders') }}
    {% if is_incremental() %}
    -- The orders fct_orders rebuilt in this run (or within the same lookback): their items are
    -- replaced as a whole, keyed on order_id.
    where source_updated_at > (select max(source_updated_at) - interval 3 day from {{ this }})
    {% endif %}
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
    orders.review_score,
    orders.source_updated_at
from items
inner join orders on items.order_id = orders.order_id
