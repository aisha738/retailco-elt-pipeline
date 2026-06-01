with source as (
    select * from {{ source('raw_lake', 'stores') }}
)
select
    cast(id as varchar) as store_id,
    cast(name as varchar) as store_name,
    cast(city as varchar) as city
from source