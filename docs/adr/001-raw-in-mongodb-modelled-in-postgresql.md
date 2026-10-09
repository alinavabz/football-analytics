# ADR-001: Raw data in MongoDB, modelled data in PostgreSQL

- Status: accepted
- Date: 2026-10-08

## Context

StatsBomb open data arrives as nested JSON: events contain objects inside objects (`shot.outcome`, `pass.recipient`) and lists (shot freeze frames with every player's position, related events, tactical formations). The fields present depend on the event type. Analysis, on the other hand, asks relational questions: shots per team, passes per player, xG by tournament stage, joined across matches, teams, and players.

We need to keep the original data intact so the model can be changed and rebuilt later, and we need a model analysts can query with SQL.

## Decision

Keep two stores with separate jobs.

- **MongoDB holds the raw data, stored as delivered.** Documents keep their nesting, so nothing has to be designed before the data is saved, and nothing is lost if the model later turns out to be wrong.
- **PostgreSQL holds the organised data:** one row per thing (match, player, event, shot, pass), fixed columns, primary and foreign keys, and constraints. This is the shape SQL analysis, indexing, and reporting tools work with.

The relational model is always rebuilt from MongoDB (`make load`), never edited by hand.

## Alternatives considered

- **PostgreSQL only, with raw JSON in `jsonb` columns.** One database to run, and `jsonb` can be queried. Rejected for this project: the raw store would mix with modelled tables, and the point of the raw layer is that it is never reshaped. Worth reconsidering if running two databases becomes a burden.
- **MongoDB only, querying with the aggregation pipeline.** No modelling step. Rejected: joins across matches, players, and events are awkward, there are no foreign keys to stop orphaned records, and analysis and BI tools expect SQL.
- **Files only (JSON on disk), loaded straight into PostgreSQL.** Simplest. Rejected: no queryable copy of the raw data for checking the model against the source.

## Consequences

- Two databases to run, back up, and secure.
- A load step can drift from its source, so every load reconciles row counts with MongoDB and aborts on a mismatch.
- Fields not modelled in PostgreSQL (freeze frames, tactics, detail for event types other than shots and passes) remain available in MongoDB and can be added to the model later without downloading anything again.
