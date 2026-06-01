with movements as (
    select * from {{ ref('stg_inventory_movements') }}
),

products as (
    select * from {{ ref('dim_product') }}
),

stores as (
    select * from {{ ref('dim_store') }}
)

select
    -- A composite surrogate key for the daily snapshot
    md5(m.store_id || m.product_id || cast(cast(m.movement_date as date) as varchar)) as inventory_snapshot_sk,
    
    p.product_sk,
    s.store_sk,
    cast(to_char(m.movement_date, 'YYYYMMDD') as integer) as date_sk,
    
    m.store_id,
    m.product_id,
    
    -- The actual aggregation requested by the brief
    sum(m.quantity_changed) as daily_quantity_change
    
from movements m

-- Point-in-time join to ensure we capture what the product was ON that specific day
left join products p 
    on m.product_id = p.product_id
    and m.movement_date >= p.valid_from
    and (m.movement_date < p.valid_to or p.valid_to is null)

left join stores s
    on m.store_id = s.store_id

-- Group by all the dimensions to create the daily snapshot
group by 1, 2, 3, 4, 5, 6