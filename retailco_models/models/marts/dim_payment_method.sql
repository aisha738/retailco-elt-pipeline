with staged as (
    select * from {{ ref('stg_payment_methods') }}
)
select
    md5(payment_method_id) as payment_method_sk,
    payment_method_id,
    payment_method_name
from staged