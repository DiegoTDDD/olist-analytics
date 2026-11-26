with products as (
    select * from {{ ref('stg_products') }}
),

categories as (
    select * from {{ ref('stg_product_category') }}
),

names_pt as (
    select * from {{ ref('category_names_pt') }}
)

select
    products.product_id,
    products.product_category_name,
    categories.category_name_english,
    coalesce(
        names_pt.category_name_pt,
        case when products.product_category_name is null then 'Sem categoria' end
    ) as category_name_pt,
    products.product_weight_g,
    products.product_length_cm,
    products.product_height_cm,
    products.product_width_cm,
    products.product_photos_qty
from products
left join categories
    on products.product_category_name = categories.product_category_name
left join names_pt
    on products.product_category_name = names_pt.product_category_name