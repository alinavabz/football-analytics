-- Goals counted from events must equal the official score of every match.
-- Goals = scored shots outside the shootout + own goals credited to the team.
-- Returns the matches that disagree; the test passes when it returns no rows.
with goals as (
    select match_id, team_id, count(*) as goals
    from {{ ref('fact_shots') }}
    where is_goal and not is_shootout
    group by match_id, team_id

    union all

    select match_id, team_id, count(*) as goals
    from {{ ref('fact_events') }}
    where event_type = 'Own Goal For' and not is_shootout
    group by match_id, team_id
),

per_team as (
    select match_id, team_id, sum(goals) as goals
    from goals
    group by match_id, team_id
)

select
    m.match_id,
    m.scoreline,
    coalesce(h.goals, 0) as home_goals_from_events,
    coalesce(a.goals, 0) as away_goals_from_events
from {{ ref('dim_match') }} as m
left join per_team as h on h.match_id = m.match_id and h.team_id = m.home_team_id
left join per_team as a on a.match_id = m.match_id and a.team_id = m.away_team_id
where m.home_score <> coalesce(h.goals, 0)
   or m.away_score <> coalesce(a.goals, 0)
