with source as (
    select * from {{ source('raw_lake', 'payment_methods') }}
)
select
    cast(id as varchar) as payment_method_id,
    cast(name as varchar) as payment_method_name
from source