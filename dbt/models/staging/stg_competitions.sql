select
    competition_id,
    season_id,
    competition_name,
    season_name
from {{ source('core', 'competitions') }}
