-- fct_orders must have exactly one row per order in the source: the review, payment and
-- item joins must never duplicate or drop an order.
select
    (select count(*) from {{ ref('fct_orders') }}) as fact_rows,
    (select count(*) from {{ ref('stg_orders') }}) as staged_orders
where (select count(*) from {{ ref('fct_orders') }})
   != (select count(*) from {{ ref('stg_orders') }})
