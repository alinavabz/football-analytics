-- Grain: one row per shot, including penalty shootout kicks (is_shootout).
select
    s.shot_id,
    e.match_id,
    m.date_key,
    e.team_id,
    case when m.home_team_id = e.team_id then m.away_team_id else m.home_team_id end
        as opponent_team_id,
    e.player_id,
    e.period,
    e.is_shootout,
    e.minute,
    e.second,
    e.play_pattern,
    e.location_x,
    e.location_y,
    e.under_pressure,
    s.xg,
    s.is_goal,
    s.outcome,
    s.body_part,
    s.technique,
    s.shot_type,
    s.shot_type = 'Penalty' as is_penalty,
    s.first_time,
    s.key_pass_id
from {{ ref('stg_shots') }} as s
join {{ ref('stg_events') }} as e on e.event_id = s.shot_id
join {{ ref('stg_matches') }} as m on m.match_id = e.match_id
