with staged as (
    select * from {{ ref('stg_stores') }}
)
select
    md5(store_id) as store_sk,
    store_id,
    store_name,
    city
from staged