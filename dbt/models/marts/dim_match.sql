-- Grain: one row per match.
select
    m.match_id,
    m.date_key,
    m.match_date,
    m.kick_off,
    c.competition_name,
    c.season_name,
    m.competition_stage,
    case m.competition_stage
        when 'Group Stage' then 1
        when 'Round of 16' then 2
        when 'Quarter-finals' then 3
        when 'Semi-finals' then 4
        when '3rd Place Final' then 5
        when 'Final' then 6
    end as stage_order,
    m.home_team_id,
    home.team_name as home_team_name,
    m.away_team_id,
    away.team_name as away_team_name,
    m.home_score,
    m.away_score,
    home.team_name || ' ' || m.home_score || '-' || m.away_score || ' ' || away.team_name as scoreline,
    m.stadium_name,
    m.referee_name
from {{ ref('stg_matches') }} as m
join {{ ref('stg_competitions') }} as c using (competition_id, season_id)
join {{ ref('stg_teams') }} as home on home.team_id = m.home_team_id
join {{ ref('stg_teams') }} as away on away.team_id = m.away_team_id
