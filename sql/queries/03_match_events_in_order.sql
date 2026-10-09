-- Every event in the final, in order, as needed to replay the match.
SELECT
    e.event_index,
    e.period,
    e.minute,
    e.second,
    e.event_type,
    p.player_name
FROM core.events e
LEFT JOIN core.players p ON p.player_id = e.player_id
WHERE e.match_id = 3869685
ORDER BY e.event_index;
