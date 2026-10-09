-- Grain: one row per calendar day, covering every match date.
with bounds as (
    select min(match_date) as first_day, max(match_date) as last_day
    from {{ ref('stg_matches') }}
),

days as (
    select generate_series(first_day, last_day, interval '1 day')::date as date_day
    from bounds
)

select
    to_char(date_day, 'YYYYMMDD')::int as date_key,
    date_day,
    extract(year from date_day)::int as year,
    extract(month from date_day)::int as month,
    to_char(date_day, 'FMMonth') as month_name,
    extract(isodow from date_day)::int as day_of_week,
    to_char(date_day, 'FMDay') as day_name,
    extract(isodow from date_day) in (6, 7) as is_weekend
from days
