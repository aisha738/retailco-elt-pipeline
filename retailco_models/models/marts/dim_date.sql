with date_spine as (
    -- Generate 3 years of dates starting from Jan 1, 2024
    select cast(d as date) as date_day
    from generate_series(
      '2024-01-01'::date,
      '2026-12-31'::date,
      '1 day'::interval
    ) as d
)

select
    -- Surrogate key for dates is usually an integer like 20240101 for fast joining
    cast(to_char(date_day, 'YYYYMMDD') as integer) as date_sk,
    
    date_day,
    extract(year from date_day) as year,
    extract(quarter from date_day) as quarter,
    extract(month from date_day) as month,
    extract(week from date_day) as week,
    extract(isodow from date_day) as day_of_week,
    
    -- 6 is Saturday, 7 is Sunday
    case when extract(isodow from date_day) in (6, 7) then true else false end as is_weekend,
    
    -- Flagging major Nigerian Public Holidays
    case 
        -- Fixed date holidays
        when extract(month from date_day) = 1 and extract(day from date_day) = 1 then true -- New Year
        when extract(month from date_day) = 5 and extract(day from date_day) = 1 then true -- Workers Day
        when extract(month from date_day) = 6 and extract(day from date_day) = 12 then true -- Democracy Day
        when extract(month from date_day) = 10 and extract(day from date_day) = 1 then true -- Independence Day
        when extract(month from date_day) = 12 and extract(day from date_day) = 25 then true -- Christmas
        when extract(month from date_day) = 12 and extract(day from date_day) = 26 then true -- Boxing Day
        else false
    end as is_public_holiday_nigeria

from date_spine