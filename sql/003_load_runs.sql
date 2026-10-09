-- One row per completed `make load`, written in the same transaction as the data it describes.
-- Downstream freshness checks read finished_at.
CREATE TABLE IF NOT EXISTS core.load_runs (
    run_id       bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    finished_at  timestamptz NOT NULL DEFAULT now(),
    row_counts   jsonb       NOT NULL
);
