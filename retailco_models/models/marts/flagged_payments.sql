with staged as (
    select * from {{ ref('stg_payments') }}
)
select *
from staged
-- We isolate payments that are 0 or negative, UNLESS they are explicitly marked as a refund
where amount_paid <= 0 
  and lower(payment_status) not like '%refund%'