-- Grain: one row per team.
select
    team_id,
    team_name,
    country_name
from {{ ref('stg_teams') }}
