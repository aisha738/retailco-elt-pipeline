{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('stg_orders') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['oi.order_item_id']) }} as sales_sk,
        {{ dbt_utils.generate_surrogate_key(['o.customer_id']) }} as customer_sk,
        {{ dbt_utils.generate_surrogate_key(['o.store_id']) }} as store_sk,
        {{ dbt_utils.generate_surrogate_key(['o.employee_id']) }} as employee_sk,
        {{ dbt_utils.generate_surrogate_key(['oi.product_id']) }} as product_sk,
        -- Keep your existing fields
        oi.order_item_id,
        o.order_id,
        o.customer_id,
        o.store_id,
        o.employee_id,
        oi.product_id,
        o.updated_at as order_date,
        oi.quantity,
        oi.unit_price,
        oi.discount_pct,
        oi.line_total as revenue_amount
    from order_items oi
    inner join orders o on oi.order_id = o.order_id
)

select * from final
