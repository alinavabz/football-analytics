select
    team_id,
    team_name,
    country_name
from {{ source('core', 'teams') }}
