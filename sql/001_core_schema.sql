-- Relational model of StatsBomb match data, loaded from the MongoDB raw store.
-- Grain of each table is stated above it. Foreign key columns are deliberately left unindexed
-- here: indexes are added from measured query plans, not guessed up front.

CREATE SCHEMA IF NOT EXISTS core;

-- One row per competition season.
CREATE TABLE IF NOT EXISTS core.competitions (
    competition_id      int  NOT NULL,
    season_id           int  NOT NULL,
    competition_name    text NOT NULL,
    season_name         text NOT NULL,
    country_name        text,
    competition_gender  text,
    PRIMARY KEY (competition_id, season_id)
);

-- One row per team.
CREATE TABLE IF NOT EXISTS core.teams (
    team_id       int  PRIMARY KEY,
    team_name     text NOT NULL,
    country_name  text
);

-- One row per player.
CREATE TABLE IF NOT EXISTS core.players (
    player_id        int  PRIMARY KEY,
    player_name      text NOT NULL,
    player_nickname  text,
    country_name     text
);

-- One row per match.
CREATE TABLE IF NOT EXISTS core.matches (
    match_id           int      PRIMARY KEY,
    competition_id     int      NOT NULL,
    season_id          int      NOT NULL,
    match_date         date     NOT NULL,
    kick_off           time,
    competition_stage  text     NOT NULL,
    match_week         int,
    home_team_id       int      NOT NULL REFERENCES core.teams,
    away_team_id       int      NOT NULL REFERENCES core.teams,
    home_score         smallint NOT NULL CHECK (home_score >= 0),
    away_score         smallint NOT NULL CHECK (away_score >= 0),
    stadium_name       text,
    referee_name       text,
    FOREIGN KEY (competition_id, season_id) REFERENCES core.competitions,
    CHECK (home_team_id <> away_team_id)
);

-- One row per player named in a team's match squad.
CREATE TABLE IF NOT EXISTS core.match_players (
    match_id       int      NOT NULL REFERENCES core.matches,
    player_id      int      NOT NULL REFERENCES core.players,
    team_id        int      NOT NULL REFERENCES core.teams,
    jersey_number  smallint,
    started        boolean  NOT NULL,
    played         boolean  NOT NULL,
    PRIMARY KEY (match_id, player_id),
    CHECK (played OR NOT started)
);

-- One row per event: every pass, carry, shot, pressure, and so on.
-- Pitch coordinates follow StatsBomb: x 0 to 120 (towards the opponent's goal), y 0 to 80.
CREATE TABLE IF NOT EXISTS core.events (
    event_id        uuid     PRIMARY KEY,
    match_id        int      NOT NULL REFERENCES core.matches,
    event_index     int      NOT NULL,
    period          smallint NOT NULL CHECK (period BETWEEN 1 AND 5),
    minute          smallint NOT NULL CHECK (minute >= 0),
    second          smallint NOT NULL CHECK (second BETWEEN 0 AND 59),
    event_type      text     NOT NULL,
    team_id         int      NOT NULL REFERENCES core.teams,
    player_id       int      REFERENCES core.players,
    position_name   text,
    play_pattern    text,
    possession      int,
    location_x      real     CHECK (location_x BETWEEN 0 AND 120),
    location_y      real     CHECK (location_y BETWEEN 0 AND 80),
    duration        real,
    under_pressure  boolean  NOT NULL,
    UNIQUE (match_id, event_index)
);

-- One row per shot. Extends core.events with shot-specific fields.
CREATE TABLE IF NOT EXISTS core.shots (
    event_id     uuid    PRIMARY KEY REFERENCES core.events,
    xg           real    NOT NULL CHECK (xg BETWEEN 0 AND 1),
    outcome      text    NOT NULL,
    body_part    text,
    technique    text,
    shot_type    text,
    end_x        real,
    end_y        real,
    end_z        real,
    first_time   boolean NOT NULL,
    -- Checked at commit: the key pass can be loaded in a later batch than the shot.
    key_pass_id  uuid    REFERENCES core.events DEFERRABLE INITIALLY DEFERRED
);

-- One row per pass. Extends core.events with pass-specific fields.
-- StatsBomb omits the outcome on completed passes; it is stored here as 'Complete'.
CREATE TABLE IF NOT EXISTS core.passes (
    event_id             uuid    PRIMARY KEY REFERENCES core.events,
    recipient_player_id  int     REFERENCES core.players,
    length               real    CHECK (length >= 0),
    angle                real,
    height               text,
    body_part            text,
    pass_type            text,
    end_x                real,
    end_y                real,
    is_cross             boolean NOT NULL,
    outcome              text    NOT NULL
);
