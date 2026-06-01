with staged as (
    select * from {{ ref('stg_payments') }}
),

flagged as (
    select payment_id from {{ ref('flagged_payments') }}
)

select
    md5(s.payment_id) as payment_sk,
    md5(s.order_id) as sales_sk, 
    md5(s.payment_method_id) as payment_method_sk,
    cast(to_char(s.payment_date, 'YYYYMMDD') as integer) as date_sk,
    
    s.payment_id,
    s.order_id,
    s.amount_paid,
    s.payment_status
    
from staged s
-- Anti-join to completely exclude the anomalous payments from our analytics
left join flagged f on s.payment_id = f.payment_id
where f.payment_id is null