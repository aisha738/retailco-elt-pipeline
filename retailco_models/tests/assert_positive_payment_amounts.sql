-- This test checks if any rows in fct_payments have an amount_paid of 0 or less.
-- If this returns any rows, the test fails, meaning our anomaly filtering broke.

select
    payment_id,
    amount_paid
from {{ ref('fct_payments') }}
where amount_paid <= 0