select
    player_id,
    player_name,
    coalesce(player_nickname, player_name) as display_name,
    country_name
from {{ source('core', 'players') }}
