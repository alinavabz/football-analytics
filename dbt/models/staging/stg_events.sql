select
    event_id,
    match_id,
    event_index,
    period,
    period = 5 as is_shootout,
    minute,
    second,
    event_type,
    team_id,
    player_id,
    position_name,
    play_pattern,
    possession,
    location_x,
    location_y,
    duration,
    under_pressure
from {{ source('core', 'events') }}
