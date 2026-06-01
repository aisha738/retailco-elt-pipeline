{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'orders') }}
),

renamed as (
    select
        id as order_id,
        payload->>'customerId' as customer_id,
        payload->>'storeId' as store_id,
        payload->>'employeeId' as employee_id,
        payload->>'status' as order_status,
        cast(payload->>'totalAmount' as numeric) as total_amount,
        cast(payload->>'createdAt' as timestamp) as order_created_at,
        cast(payload->>'updatedAt' as timestamp) as updated_at,
        cast(payload->>'updatedAt' as timestamp) as order_updated_at
    from source
)

select * from renamed