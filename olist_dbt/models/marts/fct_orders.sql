{{
    config(
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key='order_id',
        on_schema_change='fail'
    )
}}

-- Incremental: a run rebuilds only the orders with an event newer than this table's watermark
-- (minus a lookback for late-arriving rows), replacing their rows. scripts/check_incremental.py
-- proves in CI that the result equals a full rebuild at every step of a day-by-day replay
-- (docs/adr/0006).
{% set lookback_days = 3 %}

with latest_answer as (
    select order_id, max(review_answer_timestamp) as answered_at
    from {{ ref('stg_order_reviews') }}
    group by order_id
),

order_events as (
    -- When each order last changed: its own timestamps and its latest review answer.
    select
        orders.order_id,
        greatest(
            orders.purchased_at,
            orders.approved_at,
            orders.delivered_to_carrier_at,
            orders.delivered_to_customer_at,
            latest_answer.answered_at
        ) as source_updated_at
    from {{ ref('stg_orders') }} as orders
    left join latest_answer on orders.order_id = latest_answer.order_id
),

orders as (
    select orders.*, order_events.source_updated_at
    from {{ ref('stg_orders') }} as orders
    inner join order_events on orders.order_id = order_events.order_id
    {% if is_incremental() %}
    where order_events.source_updated_at > (
        select max(source_updated_at) - interval {{ lookback_days }} day from {{ this }}
    )
    {% endif %}
),

reviews as (
    select
        order_id,
        review_score
    from (
        select
            order_id,
            review_score,
            row_number() over (
                partition by order_id
                -- review_creation_date ties for 31 orders whose reviews differ; the extra
                -- keys make the choice deterministic, so every rebuild gives the same table.
                order by review_creation_date desc, review_answer_timestamp desc, review_id
            ) as rn
        from {{ ref('stg_order_reviews') }}
    )
    where rn = 1
),

payments as (
    select
        order_id,
        -- Money is summed as DECIMAL: exact, so the result does not depend on the order in
        -- which parallel threads add the rows (float sums differed between machines).
        sum(cast(payment_value as decimal(12, 2))) as total_payment_value,
        max(payment_installments) as max_installments
    from {{ ref('stg_order_payments') }}
    group by order_id
),

items as (
    select
        order_id,
        count(*) as item_count,
        sum(cast(price as decimal(12, 2))) as total_item_price,
        sum(cast(freight_value as decimal(12, 2))) as total_freight
    from {{ ref('stg_order_items') }}
    group by order_id
)

select
    orders.order_id,
    orders.customer_id,
    orders.status,
    cast(orders.purchased_at as date) as purchase_date,

    payments.total_payment_value,
    payments.max_installments,
    items.item_count,
    items.total_item_price,
    items.total_freight,
    reviews.review_score,

    date_diff('day', orders.purchased_at, orders.delivered_to_customer_at) as delivery_days,
    date_diff('day', orders.estimated_delivery_at, orders.delivered_to_customer_at) as delay_days,

    -- Late = delivered on a later calendar day than promised. The promise is a date (stored as
    -- midnight), so comparing timestamps would flag every delivery made on the promised day.
    coalesce(
        cast(orders.delivered_to_customer_at as date) > cast(orders.estimated_delivery_at as date),
        false
    ) as is_delayed,

    -- The watermark for incremental runs; not exported (export_marts.py, export_powerbi.py).
    orders.source_updated_at

from orders
left join reviews   on orders.order_id = reviews.order_id
left join payments  on orders.order_id = payments.order_id
left join items     on orders.order_id = items.order_id