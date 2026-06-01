with source as (
    select * from {{ ref('product_snapshot') }}
)
select
    cast(id as varchar) as product_id,
    cast(name as varchar) as product_name,
    cast(category as varchar) as category,
    -- Using the column name Postgres found in the raw data
    cast(cost_price as numeric) as price,
    
    dbt_valid_from as valid_from,
    dbt_valid_to as valid_to,
    case when dbt_valid_to is null then true else false end as is_current,
    
    cast(is_deleted as boolean) as is_deleted
from source