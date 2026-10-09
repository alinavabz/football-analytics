-- A team's shots, goals, and expected goals (xG) in each match, excluding the penalty shootout.
SELECT
    m.match_date,
    m.competition_stage,
    opp.team_name                              AS opponent,
    count(*)                                   AS shots,
    count(*) FILTER (WHERE s.outcome = 'Goal') AS goals,
    round(sum(s.xg)::numeric, 2)               AS xg
FROM core.events  e
JOIN core.shots   s   USING (event_id)
JOIN core.teams   t   ON t.team_id = e.team_id
JOIN core.matches m   ON m.match_id = e.match_id
JOIN core.teams   opp ON opp.team_id = CASE WHEN m.home_team_id = e.team_id
                                             THEN m.away_team_id ELSE m.home_team_id END
WHERE t.team_name = 'Argentina'
  AND e.event_type = 'Shot'  -- implied by the join to shots, but stating it lets the planner use
                             -- events_team_type_idx to read ~100 rows instead of ~15,000
  AND e.period < 5
GROUP BY m.match_date, m.competition_stage, opp.team_name
ORDER BY m.match_date;
