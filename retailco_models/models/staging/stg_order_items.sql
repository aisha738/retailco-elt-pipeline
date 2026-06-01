{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'order_items') }}
),

renamed as (
    select
        id as order_item_id,
        payload->>'orderId' as order_id,
        payload->>'productId' as product_id,
        cast(payload->>'quantity' as integer) as quantity,
        cast(payload->>'unitPrice' as numeric) as unit_price,
        cast(payload->>'discountPct' as numeric) as discount_pct,
        cast(payload->>'lineTotal' as numeric) as line_total,
        cast(payload->>'updatedAt' as timestamp) as updated_at
    from source
)

select * from renamed