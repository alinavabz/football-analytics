-- Indexes chosen from measured query plans (see docs/query-performance.md).
--
-- Both are composite: an equality filter on the first column, then on event_type. Postgres can
-- use a composite index for any leftmost prefix, so these also serve "all events for a team"
-- and "all events for a player". They do not help a filter on event_type alone.
--
-- core.events(match_id) needs no index of its own: the UNIQUE (match_id, event_index)
-- constraint already created one with match_id as its leading column.

-- Team-level questions: a team's shots, passes, pressures.
CREATE INDEX IF NOT EXISTS events_team_type_idx ON core.events (team_id, event_type);

-- Player-level questions: a player's passes, shots, carries.
-- INCLUDE (event_id) makes it a covering index for joins to shots and passes: the join key is read
-- from the index itself (an index-only scan), without visiting the table.
CREATE INDEX IF NOT EXISTS events_player_type_idx
    ON core.events (player_id, event_type) INCLUDE (event_id);
