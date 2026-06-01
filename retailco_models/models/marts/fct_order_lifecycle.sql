with orders as (
    select * from {{ ref('stg_orders') }}
)

select 
    md5(order_id) as order_lifecycle_sk,
    md5(order_id) as sales_sk,
    
    order_id,
    order_status,
    
    order_created_at as order_placed_at,
    
    -- As the status updates over time in the API, these timestamps will "fill in"
    case when order_status in ('paid', 'shipped', 'delivered') then order_updated_at else null end as paid_at,
    case when order_status in ('shipped', 'delivered') then order_updated_at else null end as shipped_at,
    case when order_status = 'delivered' then order_updated_at else null end as delivered_at
    
from orders