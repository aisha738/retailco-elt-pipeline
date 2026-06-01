with source as (
    select * from {{ source('raw_lake', 'employees') }}
)
select
    cast(id as varchar) as employee_id,
    cast(first_name as varchar) as first_name,
    cast(last_name as varchar) as last_name,
    cast(store_id as varchar) as store_id
from source