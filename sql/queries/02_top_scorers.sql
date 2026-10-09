-- Top scorers of the tournament, excluding the penalty shootout.
SELECT
    p.player_name,
    t.team_name,
    count(*)                      AS goals,
    round(sum(s.xg)::numeric, 2)  AS xg_of_goals
FROM core.shots   s
JOIN core.events  e USING (event_id)
JOIN core.players p ON p.player_id = e.player_id
JOIN core.teams   t ON t.team_id = e.team_id
WHERE s.outcome = 'Goal'
  AND e.period < 5
GROUP BY p.player_name, t.team_name
ORDER BY goals DESC, xg_of_goals
LIMIT 10;
