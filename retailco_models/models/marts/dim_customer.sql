with staged_customers as (
    select * from {{ ref('stg_customers') }}
)

select
    -- Generate a unique Surrogate Key using a hash of the ID and the valid_from date
    -- This ensures every historical version of a customer gets its own unique key
    md5(customer_id || coalesce(cast(valid_from as varchar), '')) as customer_sk,
    
    -- Natural key from the API
    customer_id,
    
    first_name,
    last_name,
    email,
    customer_segment,
    address,
    
    -- SCD2 columns
    valid_from,
    valid_to,
    is_current
    
from staged_customers