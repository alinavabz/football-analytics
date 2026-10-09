select
    match_id,
    competition_id,
    season_id,
    match_date,
    to_char(match_date, 'YYYYMMDD')::int as date_key,
    kick_off,
    competition_stage,
    home_team_id,
    away_team_id,
    home_score,
    away_score,
    stadium_name,
    referee_name
from {{ source('core', 'matches') }}
