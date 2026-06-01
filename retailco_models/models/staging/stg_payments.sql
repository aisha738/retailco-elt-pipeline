with source as (
    select * from {{ source('raw_lake', 'payments') }}
)
select
    cast(id as varchar) as payment_id,
    cast(order_id as varchar) as order_id,
    cast(payment_method_id as varchar) as payment_method_id,
    
    -- The brief specifically mentions checking 'amount_paid'
    cast(amount_paid as numeric) as amount_paid,
    cast(status as varchar) as payment_status,
    cast(created_at as timestamp) as payment_date
from source