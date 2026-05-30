-- ============================================================
-- resorts
-- Core resort data. Mostly static — updated manually/seasonally.
-- ============================================================
CREATE TABLE resorts (
    id                      SERIAL PRIMARY KEY,
    name                    TEXT NOT NULL,
    slug                    TEXT UNIQUE NOT NULL,

    -- location
    country                 CHAR(2) NOT NULL,           -- ISO 3166-1 alpha-2 (US, CA, JP, FR, CH, NZ, CL...)
    region                  TEXT,                       -- state / province / canton
    continent               TEXT NOT NULL CHECK (continent IN (
                                'north_america', 'europe', 'asia', 'oceania', 'south_america'
                            )),
    hemisphere              TEXT NOT NULL DEFAULT 'northern' CHECK (hemisphere IN ('northern', 'southern')),
    lat                     DECIMAL(9,6) NOT NULL,
    lon                     DECIMAL(9,6) NOT NULL,

    -- elevation
    elevation_base_m        INT NOT NULL,
    elevation_summit_m      INT NOT NULL,

    -- travel
    nearest_airport         CHAR(3) NOT NULL,           -- IATA code of closest airport with commercial service
    airport_drive_minutes   INT NOT NULL,               -- typical drive from that airport to resort base

    -- season (month numbers, 1=Jan 12=Dec) — fallback when dated values are
    -- absent or stale. For southern hemisphere, season_start > season_end is
    -- expected (e.g. June–September).
    season_start_month      INT NOT NULL CHECK (season_start_month BETWEEN 1 AND 12),
    season_end_month        INT NOT NULL CHECK (season_end_month BETWEEN 1 AND 12),

    -- live season window, refreshed monthly by the season_status worker by
    -- scraping the resort's status page. Used in preference to the month
    -- fallback when present and not stale (see SEASON_FRESHNESS_DAYS).
    status_url               TEXT,
    season_open_date         DATE,
    season_close_date        DATE,
    season_status_updated_at TIMESTAMPTZ,

    -- snow profile
    avg_annual_snowfall_cm  INT,                        -- historical average, used for reliability scoring

    -- terrain
    vertical_drop_m         INT GENERATED ALWAYS AS (elevation_summit_m - elevation_base_m) STORED,
    difficulty_mix          JSONB,                      -- {"beginner": 20, "intermediate": 40, "advanced": 30, "expert": 10}
    terrain_tags            TEXT[] NOT NULL DEFAULT '{}', -- powder, trees, groomers, park, backcountry, glaciers, off-piste

    -- vibe / identity
    vibe_tags               TEXT[] NOT NULL DEFAULT '{}', -- luxury, party, family, cultural, remote, village, resort-town, adventure
    budget_tier             TEXT CHECK (budget_tier IN ('budget', 'mid', 'premium', 'luxury')),
    pass_affiliations       TEXT[] DEFAULT '{}',         -- ikon, epic, indy, other
    snowboard_allowed       BOOLEAN NOT NULL DEFAULT true,

    -- agent context: free-form notes surfaced to the LLM when this resort is in consideration
    agent_notes             TEXT,

    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_resorts_continent ON resorts(continent);
CREATE INDEX idx_resorts_country ON resorts(country);
CREATE INDEX idx_resorts_nearest_airport ON resorts(nearest_airport);


-- ============================================================
-- flight_routes
-- Static lookup: one-way flight time between airport pairs.
-- Covers home airports → ski hub airports only.
-- Round trip = 2x. Add 90 min overhead (security, boarding) per flight.
-- ============================================================
CREATE TABLE flight_routes (
    id                      SERIAL PRIMARY KEY,
    origin                  CHAR(3) NOT NULL,
    destination             CHAR(3) NOT NULL,
    flight_minutes          INT NOT NULL,               -- wheels-up to wheels-down
    UNIQUE (origin, destination)
);

CREATE INDEX idx_flight_routes_origin ON flight_routes(origin);


-- ============================================================
-- user_profiles
-- Persisted preferences per session. Updated conversationally.
-- ============================================================
CREATE TABLE user_profiles (
    id                      SERIAL PRIMARY KEY,
    session_id              TEXT UNIQUE NOT NULL,

    -- home
    home_airport            CHAR(3) NOT NULL DEFAULT 'SNA',
    home_lat                DECIMAL(9,6),
    home_lon                DECIMAL(9,6),

    -- skill
    skill_level             TEXT CHECK (skill_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    preferred_terrain       TEXT[] DEFAULT '{}',        -- subset of terrain_tags

    -- trip preferences
    budget_level            TEXT CHECK (budget_level IN ('budget', 'mid', 'premium', 'luxury')),
    max_drive_hours         DECIMAL(4,1) DEFAULT 5.0,
    passport_countries      TEXT[] DEFAULT '{}',        -- ISO 3166-1 alpha-2 list of passports held

    -- history
    visited_resort_ids      INT[] DEFAULT '{}',
    favorite_resort_ids     INT[] DEFAULT '{}',

    -- session context: last ranked resort prompt, reused for follow-up messages
    last_resort_context     TEXT,

    -- current trip for this session. Persisted so follow-up messages that arrive
    -- without explicit dates re-rank against the same trip instead of guessing.
    trip_start_date         DATE,
    trip_end_date           DATE,
    trip_origin_airport     CHAR(3),

    updated_at              TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================
-- snow_forecasts
-- Cached from Open-Meteo. Refreshed every 6 hours per resort.
-- ============================================================
CREATE TABLE snow_forecasts (
    id                      SERIAL PRIMARY KEY,
    resort_id               INT NOT NULL REFERENCES resorts(id) ON DELETE CASCADE,
    fetched_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    forecast_date           DATE NOT NULL,

    new_snow_cm             DECIMAL(6,1),               -- snowfall expected on this specific date
    cumulative_7d_cm        DECIMAL(6,1),               -- total forecast snowfall over the next 7 days from this date
    base_depth_cm           INT,                        -- current snowpack at base
    temperature_c           DECIMAL(4,1),
    wind_kph                DECIMAL(5,1),

    UNIQUE (resort_id, forecast_date)
);

CREATE INDEX idx_snow_forecasts_resort_date ON snow_forecasts(resort_id, forecast_date);
CREATE INDEX idx_snow_forecasts_fetched ON snow_forecasts(fetched_at);


-- ============================================================
-- conversations
-- Multi-turn chat history per session.
-- ============================================================
CREATE TABLE conversations (
    id                      SERIAL PRIMARY KEY,
    session_id              TEXT NOT NULL,
    role                    TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content                 TEXT NOT NULL,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_session ON conversations(session_id, created_at);


-- ============================================================
-- trips  (optional — saved recommendations)
-- ============================================================
CREATE TABLE trips (
    id                      SERIAL PRIMARY KEY,
    session_id              TEXT NOT NULL,
    start_date              DATE NOT NULL,
    end_date                DATE NOT NULL,
    duration_days           INT GENERATED ALWAYS AS (end_date - start_date + 1) STORED,
    origin_airport          CHAR(3) NOT NULL,
    resort_id               INT REFERENCES resorts(id),
    recommendation_text     TEXT,                       -- full agent response stored for reference
    created_at              TIMESTAMPTZ DEFAULT NOW()
);
