with staged as (
    select * from {{ ref('stg_employees') }}
)
select
    md5(employee_id) as employee_sk,
    employee_id,
    first_name,
    last_name,
    md5(store_id) as store_sk 
from staged