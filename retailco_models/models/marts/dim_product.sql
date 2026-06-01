with staged as (
    select * from {{ ref('stg_products') }}
)
select
    -- Surrogate Key hashed with valid_from to capture historical price/category changes
    md5(product_id || coalesce(cast(valid_from as varchar), '')) as product_sk,
    product_id,
    product_name,
    category,
    price,
    valid_from,
    valid_to,
    is_current
from staged