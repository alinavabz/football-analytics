select
    match_id,
    player_id,
    team_id,
    jersey_number,
    started,
    played
from {{ source('core', 'match_players') }}
