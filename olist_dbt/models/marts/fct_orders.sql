with orders as (
    select * from {{ ref('stg_orders') }}
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
                order by review_creation_date desc
            ) as rn
        from {{ ref('stg_order_reviews') }}
    )
    where rn = 1
),

payments as (
    select
        order_id,
        sum(payment_value) as total_payment_value,
        max(payment_installments) as max_installments
    from {{ ref('stg_order_payments') }}
    group by order_id
),

items as (
    select
        order_id,
        count(*) as item_count,
        sum(price) as total_item_price,
        sum(freight_value) as total_freight
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

    case
        when orders.delivered_to_customer_at > orders.estimated_delivery_at then true
        else false
    end as is_delayed

from orders
left join reviews   on orders.order_id = reviews.order_id
left join payments  on orders.order_id = payments.order_id
left join items     on orders.order_id = items.order_id