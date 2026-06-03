with products as (
    select * from {{ ref('stg_products') }}
),

categories as (
    select * from {{ ref('stg_product_category') }}
)

select
    products.product_id,
    products.product_category_name,
    categories.category_name_english,
    products.product_weight_g,
    products.product_length_cm,
    products.product_height_cm,
    products.product_width_cm,
    products.product_photos_qty
from products
left join categories
    on products.product_category_name = categories.product_category_name