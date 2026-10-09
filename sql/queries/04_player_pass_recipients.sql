-- Who Lionel Messi passed to most, and how often those passes were completed.
SELECT
    r.player_name                                                   AS recipient,
    count(*)                                                        AS passes,
    round(avg((pa.outcome = 'Complete')::int) * 100, 1)             AS completion_pct
FROM core.events  e
JOIN core.passes  pa USING (event_id)
JOIN core.players r  ON r.player_id = pa.recipient_player_id
WHERE e.player_id = 5503
  AND e.event_type = 'Pass'
GROUP BY r.player_name
ORDER BY passes DESC
LIMIT 10;
