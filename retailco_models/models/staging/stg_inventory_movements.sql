with source as (
    select * from {{ source('raw_lake', 'inventory_movements') }}
)
select
    cast(id as varchar) as movement_id,
    cast(product_id as varchar) as product_id,
    cast(store_id as varchar) as store_id,
    cast(quantity as integer) as quantity_changed, 
    -- Using the standard creation timestamp as the date the inventory moved
    cast(created_at as timestamp) as movement_date
from source