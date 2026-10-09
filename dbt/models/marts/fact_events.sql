-- Grain: one row per event (pass, carry, pressure, shot, ...).
select
    e.event_id,
    e.match_id,
    m.date_key,
    e.team_id,
    case when m.home_team_id = e.team_id then m.away_team_id else m.home_team_id end
        as opponent_team_id,
    e.player_id,
    e.event_index,
    e.period,
    e.is_shootout,
    e.minute,
    e.second,
    e.event_type,
    e.play_pattern,
    e.position_name,
    e.possession,
    e.location_x,
    e.location_y,
    e.under_pressure,
    p.is_complete as is_pass_complete
from {{ ref('stg_events') }} as e
join {{ ref('stg_matches') }} as m on m.match_id = e.match_id
left join {{ ref('stg_passes') }} as p on p.pass_id = e.event_id
