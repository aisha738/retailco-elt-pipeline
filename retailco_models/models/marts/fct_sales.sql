{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('stg_orders') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
),

final as (
    select
        md5(cast(oi.order_item_id as varchar)) as sales_sk,
        md5(cast(o.customer_id as varchar)) as customer_sk,
        md5(cast(o.store_id as varchar)) as store_sk,
        md5(cast(o.employee_id as varchar)) as employee_sk,
        md5(cast(oi.product_id as varchar)) as product_sk,
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
