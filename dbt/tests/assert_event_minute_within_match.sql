-- No event can happen before kick-off or after the longest possible match
-- (120 minutes of extra time plus stoppage). Returns offending events.
{{ config(severity = 'warn') }}
select event_id, match_id, period, minute
from {{ ref('fact_events') }}
where minute < 0 or minute > 135
