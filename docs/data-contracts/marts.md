# Data contract: `marts` schema (PostgreSQL)

Star schema for reporting, built by dbt from `core`. Power BI reads from here.

| | |
|---|---|
| Owner | dbt project in `dbt/` |
| Source | `core` schema (see [core-postgres.md](core-postgres.md)) |
| Delivery | `make dbt`, after `make load`. Tables are rebuilt in full on each run |
| Guarantees | Every build runs the tests in `dbt/models/marts/_marts.yml` and `dbt/tests/`; a failing test fails the build |
| Freshness | Warn if the last load is older than 30 days, error after 90 (`dbt source freshness`) |

| Table | Grain | Key |
|---|---|---|
| `fact_shots` | one shot (shootout kicks flagged `is_shootout`) | `shot_id` |
| `fact_events` | one event | `event_id` |
| `dim_match` | one match | `match_id` |
| `dim_team` | one team | `team_id` |
| `dim_player` | one player | `player_id` |
| `dim_date` | one calendar day | `date_key` (YYYYMMDD) |

Column descriptions: `make docs`, then `cd dbt && uv run dbt docs serve --profiles-dir .`.
