# DATABASE DESIGN
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.0.0  
**Fecha:** 2026-06-12  
**Motor:** PostgreSQL 16  
**Estado:** Diseño Pre-Implementación

---

## 1. PRINCIPIOS DE DISEÑO

- **Normalización 3NF** como punto de partida; desnormalización solo cuando el profiling lo justifique
- **Inmutabilidad de históricos:** los datos de partidos pasados no se modifican; nuevas versiones crean nuevos registros
- **Claves naturales como restricciones únicas** (no como PKs); PKs siempre son `BIGINT GENERATED ALWAYS AS IDENTITY`
- **Auditoría universal:** `created_at`, `updated_at` en todas las tablas
- **Soft delete** solo donde sea requerido por compliance (usuarios); hard delete para el resto
- **Particionado:** tablas de estadísticas particionadas por temporada desde el inicio
- **Extensiones requeridas:** `pg_trgm` (búsqueda de texto), `uuid-ossp` (IDs UUID para tokens), `btree_gist` (rangos temporales)

---

## 2. DIAGRAMA ENTIDAD-RELACIÓN (ERD)

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   COUNTRY   │◄────│     LEAGUE      │────►│   SEASON    │
└─────────────┘     └────────┬────────┘     └─────────────┘
                             │
                    ┌────────▼────────┐
                    │  LEAGUE_SEASON  │ (tabla pivote)
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼──┐   ┌───────▼──────┐  ┌───▼──────────┐
    │   TEAM     │   │   STANDING   │  │    MATCH     │
    └─────┬──────┘   └──────────────┘  └──────┬───────┘
          │                                    │
    ┌─────▼──────┐                    ┌────────┼────────┐
    │   PLAYER   │                    │        │        │
    └─────┬──────┘            ┌───────▼──┐ ┌──▼────┐ ┌─▼──────────┐
          │                   │ MATCH_   │ │ MATCH │ │ PREDICTION │
    ┌─────▼──────────┐        │ TEAM_    │ │ EVENT │ └────────────┘
    │ PLAYER_SEASON_ │        │ STATS    │ └───────┘
    │ STATS          │        └──────────┘
    └────────────────┘
          │
    ┌─────▼──────────┐        ┌──────────────┐
    │ PLAYER_MATCH_  │        │   ODD        │
    │ STATS          │        └──────────────┘
    └────────────────┘
                              ┌──────────────┐
    ┌───────────────┐         │   USER       │
    │   ETL_JOB_LOG │         └──────┬───────┘
    └───────────────┘                │
                              ┌──────▼───────┐
                              │ USER_FAVORITE│
                              └──────────────┘
```

---

## 3. DEFINICIÓN DE TABLAS

### 3.1 Dominio Geográfico y Organizacional

#### `countries`
```sql
CREATE TABLE countries (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code        CHAR(2)      NOT NULL UNIQUE,  -- ISO 3166-1 alpha-2: ES, CO, GB
    name        VARCHAR(100) NOT NULL,
    flag_url    VARCHAR(500),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_countries_code ON countries(code);
```

#### `leagues`
```sql
CREATE TABLE leagues (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_id      BIGINT       NOT NULL REFERENCES countries(id),
    external_id     VARCHAR(50),                -- ID en API-Football: "140"
    external_source VARCHAR(50),                -- "api_football", "football_data"
    name            VARCHAR(200) NOT NULL,
    short_name      VARCHAR(50),
    slug            VARCHAR(200) NOT NULL UNIQUE,
    league_type     VARCHAR(20)  NOT NULL CHECK (league_type IN ('league', 'cup', 'friendly', 'international')),
    logo_url        VARCHAR(500),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Ejemplo de slugs: "laliga-esp", "premier-league-eng", "liga-betplay-col"
CREATE INDEX idx_leagues_country ON leagues(country_id);
CREATE INDEX idx_leagues_external ON leagues(external_source, external_id);
CREATE INDEX idx_leagues_active ON leagues(is_active) WHERE is_active = TRUE;
```

#### `seasons`
```sql
CREATE TABLE seasons (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    year_start  SMALLINT     NOT NULL,          -- 2024
    year_end    SMALLINT     NOT NULL,           -- 2025
    label       VARCHAR(20)  NOT NULL,           -- "2024/25" o "2024"
    CONSTRAINT uq_season_years UNIQUE (year_start, year_end)
);
```

#### `league_seasons`
```sql
CREATE TABLE league_seasons (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    league_id   BIGINT      NOT NULL REFERENCES leagues(id),
    season_id   BIGINT      NOT NULL REFERENCES seasons(id),
    is_current  BOOLEAN     NOT NULL DEFAULT FALSE,
    start_date  DATE,
    end_date    DATE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_league_season UNIQUE (league_id, season_id)
);

CREATE INDEX idx_league_seasons_current ON league_seasons(league_id) WHERE is_current = TRUE;
```

---

### 3.2 Dominio de Equipos

#### `teams`
```sql
CREATE TABLE teams (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_id      BIGINT       REFERENCES countries(id),
    external_id     VARCHAR(50),
    external_source VARCHAR(50),
    name            VARCHAR(200) NOT NULL,
    short_name      VARCHAR(50),
    slug            VARCHAR(200) NOT NULL UNIQUE,
    code            VARCHAR(10),                -- "BAR", "REA", "CHE"
    logo_url        VARCHAR(500),
    founded_year    SMALLINT,
    stadium_name    VARCHAR(200),
    stadium_capacity INTEGER,
    city            VARCHAR(100),
    is_national_team BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_teams_external ON teams(external_source, external_id);
CREATE INDEX idx_teams_country ON teams(country_id);
-- Búsqueda por texto
CREATE INDEX idx_teams_name_trgm ON teams USING gin(name gin_trgm_ops);
```

#### `team_aliases`
```sql
-- Resuelve el problema de normalización entre fuentes de datos
CREATE TABLE team_aliases (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    team_id         BIGINT       NOT NULL REFERENCES teams(id),
    alias           VARCHAR(200) NOT NULL,
    source          VARCHAR(50),                -- fuente de donde viene este alias
    CONSTRAINT uq_alias UNIQUE (alias, source)
);

CREATE INDEX idx_team_aliases_team ON team_aliases(team_id);
CREATE INDEX idx_team_aliases_alias ON team_aliases(alias);
```

#### `team_league_seasons`
```sql
-- Membresía de un equipo en una liga en una temporada
CREATE TABLE team_league_seasons (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    team_id         BIGINT      NOT NULL REFERENCES teams(id),
    league_season_id BIGINT     NOT NULL REFERENCES league_seasons(id),
    CONSTRAINT uq_team_in_league_season UNIQUE (team_id, league_season_id)
);
```

#### `standings`
```sql
CREATE TABLE standings (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    league_season_id    BIGINT      NOT NULL REFERENCES league_seasons(id),
    team_id             BIGINT      NOT NULL REFERENCES teams(id),
    position            SMALLINT    NOT NULL,
    points              SMALLINT    NOT NULL DEFAULT 0,
    played              SMALLINT    NOT NULL DEFAULT 0,
    won                 SMALLINT    NOT NULL DEFAULT 0,
    drawn               SMALLINT    NOT NULL DEFAULT 0,
    lost                SMALLINT    NOT NULL DEFAULT 0,
    goals_for           SMALLINT    NOT NULL DEFAULT 0,
    goals_against       SMALLINT    NOT NULL DEFAULT 0,
    goal_difference     SMALLINT    GENERATED ALWAYS AS (goals_for - goals_against) STORED,
    form                VARCHAR(20),            -- "WWDLW" (últimos 5 resultados)
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_standing UNIQUE (league_season_id, team_id)
);

CREATE INDEX idx_standings_league_season ON standings(league_season_id, position);
```

---

### 3.3 Dominio de Jugadores

#### `players`
```sql
CREATE TABLE players (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_id     VARCHAR(50),
    external_source VARCHAR(50),
    name            VARCHAR(200) NOT NULL,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    slug            VARCHAR(200) NOT NULL UNIQUE,
    nationality_id  BIGINT       REFERENCES countries(id),
    date_of_birth   DATE,
    height_cm       SMALLINT,
    weight_kg       SMALLINT,
    photo_url       VARCHAR(500),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_players_external ON players(external_source, external_id);
CREATE INDEX idx_players_name_trgm ON players USING gin(name gin_trgm_ops);
```

#### `player_team_contracts`
```sql
-- Historial de equipos de un jugador
CREATE TABLE player_team_contracts (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    player_id   BIGINT      NOT NULL REFERENCES players(id),
    team_id     BIGINT      NOT NULL REFERENCES teams(id),
    position    VARCHAR(30) NOT NULL CHECK (position IN (
                    'goalkeeper', 'defender', 'midfielder',
                    'winger', 'forward', 'attacking_midfielder'
                )),
    jersey_number SMALLINT,
    start_date  DATE        NOT NULL,
    end_date    DATE,                           -- NULL si contrato activo
    is_current  BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ptc_player ON player_team_contracts(player_id) WHERE is_current = TRUE;
CREATE INDEX idx_ptc_team ON player_team_contracts(team_id) WHERE is_current = TRUE;
```

#### `player_season_stats`
```sql
-- Particionado por temporada para queries eficientes
CREATE TABLE player_season_stats (
    id              BIGINT GENERATED ALWAYS AS IDENTITY,
    player_id       BIGINT      NOT NULL REFERENCES players(id),
    team_id         BIGINT      NOT NULL REFERENCES teams(id),
    league_season_id BIGINT     NOT NULL REFERENCES league_seasons(id),
    -- Estadísticas acumuladas
    appearances     SMALLINT    NOT NULL DEFAULT 0,
    minutes_played  INTEGER     NOT NULL DEFAULT 0,
    goals           SMALLINT    NOT NULL DEFAULT 0,
    assists         SMALLINT    NOT NULL DEFAULT 0,
    yellow_cards    SMALLINT    NOT NULL DEFAULT 0,
    red_cards       SMALLINT    NOT NULL DEFAULT 0,
    shots_total     SMALLINT    NOT NULL DEFAULT 0,
    shots_on_target SMALLINT    NOT NULL DEFAULT 0,
    passes_total    INTEGER     NOT NULL DEFAULT 0,
    passes_accuracy NUMERIC(5,2),               -- 0.00 - 100.00
    dribbles_completed SMALLINT NOT NULL DEFAULT 0,
    tackles_total   SMALLINT    NOT NULL DEFAULT 0,
    -- Métricas avanzadas (cuando disponibles)
    xg              NUMERIC(6,3),               -- Expected Goals
    xa              NUMERIC(6,3),               -- Expected Assists
    npxg            NUMERIC(6,3),               -- Non-Penalty xG
    -- Rating promedio
    avg_rating      NUMERIC(4,2),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, league_season_id),
    CONSTRAINT uq_player_season_stats UNIQUE (player_id, team_id, league_season_id)
) PARTITION BY LIST (league_season_id);

-- Particiones se crean por temporada al activar cada league_season
```

---

### 3.4 Dominio de Partidos

#### `venues`
```sql
CREATE TABLE venues (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    city        VARCHAR(100),
    country_id  BIGINT       REFERENCES countries(id),
    capacity    INTEGER,
    surface     VARCHAR(30) CHECK (surface IN ('grass', 'artificial', 'hybrid')),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

#### `referees`
```sql
CREATE TABLE referees (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_id     VARCHAR(50),
    external_source VARCHAR(50),
    name            VARCHAR(200) NOT NULL,
    nationality_id  BIGINT       REFERENCES countries(id),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

#### `matches`
```sql
CREATE TABLE matches (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    league_season_id BIGINT      NOT NULL REFERENCES league_seasons(id),
    home_team_id    BIGINT       NOT NULL REFERENCES teams(id),
    away_team_id    BIGINT       NOT NULL REFERENCES teams(id),
    venue_id        BIGINT       REFERENCES venues(id),
    referee_id      BIGINT       REFERENCES referees(id),
    external_id     VARCHAR(50),
    external_source VARCHAR(50),
    round           VARCHAR(50),                -- "Regular Season - 10", "Final"
    match_date      TIMESTAMPTZ  NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN (
                        'SCHEDULED', 'LIVE', 'HT', 'FT', 'AET', 'PEN',
                        'POSTPONED', 'CANCELLED', 'ABANDONED'
                    )),
    -- Resultado
    home_goals_ft   SMALLINT,                   -- NULL hasta que el partido termine
    away_goals_ft   SMALLINT,
    home_goals_ht   SMALLINT,
    away_goals_ht   SMALLINT,
    home_goals_et   SMALLINT,                   -- Extra time
    away_goals_et   SMALLINT,
    home_goals_pen  SMALLINT,                   -- Penaltis
    away_goals_pen  SMALLINT,
    winner          VARCHAR(10) CHECK (winner IN ('HOME', 'AWAY', 'DRAW')),
    -- Metadatos
    is_neutral_venue BOOLEAN     NOT NULL DEFAULT FALSE,
    attendance      INTEGER,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_teams_different CHECK (home_team_id <> away_team_id),
    CONSTRAINT uq_match_external UNIQUE (external_source, external_id)
);

CREATE INDEX idx_matches_league_season ON matches(league_season_id);
CREATE INDEX idx_matches_home_team ON matches(home_team_id);
CREATE INDEX idx_matches_away_team ON matches(away_team_id);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_status ON matches(status);
-- Compound para queries del dashboard: partidos de hoy por estado
CREATE INDEX idx_matches_date_status ON matches(match_date, status);
```

#### `match_team_stats`
```sql
-- Estadísticas de equipo por partido (post-partido)
CREATE TABLE match_team_stats (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    match_id        BIGINT      NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    team_id         BIGINT      NOT NULL REFERENCES teams(id),
    is_home         BOOLEAN     NOT NULL,
    -- Estadísticas de juego
    shots_total     SMALLINT,
    shots_on_target SMALLINT,
    shots_off_target SMALLINT,
    shots_blocked   SMALLINT,
    possession_pct  NUMERIC(5,2),
    passes_total    INTEGER,
    passes_accurate INTEGER,
    passes_accuracy NUMERIC(5,2),
    -- Duelos y defensa
    fouls           SMALLINT,
    corners         SMALLINT,
    offsides        SMALLINT,
    yellow_cards    SMALLINT,
    red_cards       SMALLINT,
    saves           SMALLINT,
    -- Métricas avanzadas (de fuentes específicas)
    xg              NUMERIC(6,3),
    xga             NUMERIC(6,3),
    ppda            NUMERIC(6,3),               -- Passes Allowed Per Defensive Action
    ball_recoveries SMALLINT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_match_team_stats UNIQUE (match_id, team_id)
);

CREATE INDEX idx_mts_match ON match_team_stats(match_id);
CREATE INDEX idx_mts_team ON match_team_stats(team_id);
```

#### `match_player_stats`
```sql
-- Estadísticas individuales por jugador por partido
CREATE TABLE match_player_stats (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    match_id        BIGINT      NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id       BIGINT      NOT NULL REFERENCES players(id),
    team_id         BIGINT      NOT NULL REFERENCES teams(id),
    -- Participación
    started         BOOLEAN     NOT NULL DEFAULT FALSE,
    minutes_played  SMALLINT    NOT NULL DEFAULT 0,
    position_played VARCHAR(30),
    -- Contribución ofensiva
    goals           SMALLINT    NOT NULL DEFAULT 0,
    assists         SMALLINT    NOT NULL DEFAULT 0,
    shots_total     SMALLINT,
    shots_on_target SMALLINT,
    key_passes      SMALLINT,
    -- Métricas defensivas
    tackles         SMALLINT,
    interceptions   SMALLINT,
    clearances      SMALLINT,
    -- Disciplina
    yellow_cards    SMALLINT    NOT NULL DEFAULT 0,
    red_cards       SMALLINT    NOT NULL DEFAULT 0,
    -- Pases
    passes_total    SMALLINT,
    passes_accuracy NUMERIC(5,2),
    -- Métricas avanzadas
    xg              NUMERIC(5,3),
    xa              NUMERIC(5,3),
    rating          NUMERIC(4,2),               -- 0.00 - 10.00
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_match_player UNIQUE (match_id, player_id)
);

CREATE INDEX idx_mps_match ON match_player_stats(match_id);
CREATE INDEX idx_mps_player ON match_player_stats(player_id);
```

#### `match_events`
```sql
-- Eventos granulares del partido (goles, tarjetas, sustituciones)
CREATE TABLE match_events (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    match_id    BIGINT      NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    team_id     BIGINT      NOT NULL REFERENCES teams(id),
    player_id   BIGINT      REFERENCES players(id),
    player_assist_id BIGINT REFERENCES players(id),
    event_type  VARCHAR(30) NOT NULL CHECK (event_type IN (
                    'goal', 'own_goal', 'penalty_goal', 'penalty_missed',
                    'yellow_card', 'red_card', 'yellow_red_card',
                    'substitution_in', 'substitution_out',
                    'var_decision'
                )),
    minute      SMALLINT    NOT NULL,
    extra_minute SMALLINT,                      -- minuto adicional en el tiempo de descuento
    detail      VARCHAR(100),                   -- "Normal Goal", "Header", etc.
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_match ON match_events(match_id);
CREATE INDEX idx_events_player ON match_events(player_id);
CREATE INDEX idx_events_type ON match_events(match_id, event_type);
```

#### `lineups`
```sql
-- Alineaciones oficiales (disponibles ~1h antes del partido)
CREATE TABLE lineups (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    match_id    BIGINT      NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    team_id     BIGINT      NOT NULL REFERENCES teams(id),
    player_id   BIGINT      NOT NULL REFERENCES players(id),
    lineup_type VARCHAR(20) NOT NULL CHECK (lineup_type IN ('starting', 'substitute')),
    position    VARCHAR(30),
    jersey_number SMALLINT,
    formation   VARCHAR(20),                    -- "4-3-3"
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_lineup_player UNIQUE (match_id, team_id, player_id)
);

CREATE INDEX idx_lineups_match ON lineups(match_id);
```

---

### 3.5 Dominio de Predicciones y Odds

#### `predictions`
```sql
CREATE TABLE predictions (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    match_id            BIGINT          NOT NULL REFERENCES matches(id),
    model_name          VARCHAR(50)     NOT NULL,   -- "poisson_v1", "xgboost_v2"
    model_version       VARCHAR(20)     NOT NULL,
    -- Predicción 1X2
    prob_home_win       NUMERIC(6,4)    NOT NULL CHECK (prob_home_win BETWEEN 0 AND 1),
    prob_draw           NUMERIC(6,4)    NOT NULL CHECK (prob_draw BETWEEN 0 AND 1),
    prob_away_win       NUMERIC(6,4)    NOT NULL CHECK (prob_away_win BETWEEN 0 AND 1),
    -- Predicción de goles
    expected_goals_home NUMERIC(5,3),
    expected_goals_away NUMERIC(5,3),
    prob_over_25        NUMERIC(6,4),
    prob_btts           NUMERIC(6,4),           -- Both Teams to Score
    -- Marcador exacto (top 5)
    top_scorelines      JSONB,                  -- [{"score": "1-0", "prob": 0.12}, ...]
    -- Otros mercados
    prob_over_35        NUMERIC(6,4),
    prob_home_clean_sheet NUMERIC(6,4),
    prob_away_clean_sheet NUMERIC(6,4),
    -- Metadatos del modelo
    confidence_score    NUMERIC(4,3),           -- confianza interna del modelo 0-1
    features_used       JSONB,                  -- snapshot de features para explicabilidad
    -- Resolución (post-partido)
    is_resolved         BOOLEAN         NOT NULL DEFAULT FALSE,
    actual_outcome      VARCHAR(10) CHECK (actual_outcome IN ('HOME', 'DRAW', 'AWAY')),
    brier_score         NUMERIC(6,4),           -- calculado al resolver
    -- Timestamps
    generated_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,
    CONSTRAINT uq_prediction_match_model UNIQUE (match_id, model_name, model_version),
    CONSTRAINT chk_probs_sum CHECK (
        ABS((prob_home_win + prob_draw + prob_away_win) - 1.0) < 0.01
    )
);

CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_predictions_model ON predictions(model_name, model_version);
CREATE INDEX idx_predictions_resolved ON predictions(is_resolved, resolved_at);
```

#### `odds`
```sql
-- Odds de bookmakers (actualización frecuente)
CREATE TABLE odds (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    match_id        BIGINT          NOT NULL REFERENCES matches(id),
    bookmaker       VARCHAR(100)    NOT NULL,   -- "Bet365", "Betfair", "Bwin"
    market          VARCHAR(50)     NOT NULL,   -- "1x2", "over_under_25", "btts"
    -- Para mercado 1X2
    odd_home        NUMERIC(8,3),
    odd_draw        NUMERIC(8,3),
    odd_away        NUMERIC(8,3),
    -- Para Over/Under
    line            NUMERIC(4,1),               -- 2.5, 3.5
    odd_over        NUMERIC(8,3),
    odd_under       NUMERIC(8,3),
    -- Metadatos
    recorded_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Odds se insertan (no actualizan) para mantener histórico de movimiento
CREATE INDEX idx_odds_match ON odds(match_id, bookmaker, market);
CREATE INDEX idx_odds_recorded ON odds(match_id, recorded_at DESC);
```

#### `model_performance`
```sql
-- Métricas de accuracy del modelo por periodo
CREATE TABLE model_performance (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_name      VARCHAR(50)     NOT NULL,
    model_version   VARCHAR(20)     NOT NULL,
    league_id       BIGINT          REFERENCES leagues(id),  -- NULL = global
    period_start    DATE            NOT NULL,
    period_end      DATE            NOT NULL,
    -- Métricas 1X2
    total_predictions INTEGER        NOT NULL,
    correct_1x2     INTEGER,
    accuracy_1x2    NUMERIC(6,4),
    avg_brier_score NUMERIC(6,4),
    avg_log_loss    NUMERIC(8,6),
    -- Por outcome
    accuracy_home   NUMERIC(6,4),
    accuracy_draw   NUMERIC(6,4),
    accuracy_away   NUMERIC(6,4),
    -- Métricas de valor
    roi_simulation  NUMERIC(8,4),               -- ROI si apostara siempre al favorito
    calculated_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_model_perf UNIQUE (model_name, model_version, league_id, period_start)
);
```

---

### 3.6 Dominio de Usuarios

#### `users`
```sql
CREATE TABLE users (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    hashed_password VARCHAR(255),               -- NULL si solo OAuth
    full_name       VARCHAR(200),
    username        VARCHAR(100)    UNIQUE,
    avatar_url      VARCHAR(500),
    role            VARCHAR(20)     NOT NULL DEFAULT 'free' CHECK (role IN (
                        'free', 'pro', 'enterprise', 'admin'
                    )),
    -- Estado
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN         NOT NULL DEFAULT FALSE,
    -- OAuth
    oauth_provider  VARCHAR(30),                -- "google", "github"
    oauth_sub       VARCHAR(200),               -- Subject ID del provider
    -- Suscripción (Fase 2 con Stripe)
    stripe_customer_id VARCHAR(100),
    subscription_status VARCHAR(30) DEFAULT 'inactive',
    subscription_ends_at TIMESTAMPTZ,
    -- Auditoría
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,               -- Soft delete para GDPR
    CONSTRAINT uq_oauth UNIQUE (oauth_provider, oauth_sub)
);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON users(role) WHERE deleted_at IS NULL;
```

#### `refresh_tokens`
```sql
CREATE TABLE refresh_tokens (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     BIGINT          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(256)    NOT NULL UNIQUE, -- SHA-256 del token
    expires_at  TIMESTAMPTZ     NOT NULL,
    revoked_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    user_agent  VARCHAR(500),
    ip_address  INET
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id) WHERE revoked_at IS NULL;
-- Limpieza automática de tokens expirados
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
```

#### `user_favorites`
```sql
CREATE TABLE user_favorites (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('team', 'league', 'player')),
    entity_id   BIGINT      NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_favorite UNIQUE (user_id, entity_type, entity_id)
);

CREATE INDEX idx_user_favorites_user ON user_favorites(user_id);
```

#### `api_keys`
```sql
CREATE TABLE api_keys (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     BIGINT          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash    VARCHAR(256)    NOT NULL UNIQUE,
    key_prefix  CHAR(8)         NOT NULL,       -- Primeros 8 chars para identificar en logs
    name        VARCHAR(100),                   -- Alias del usuario
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    expires_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
```

---

### 3.7 Operaciones e Infraestructura

#### `etl_job_logs`
```sql
CREATE TABLE etl_job_logs (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_name        VARCHAR(100)    NOT NULL,   -- "sync_fixtures", "sync_results"
    source          VARCHAR(50),                -- "api_football"
    league_id       BIGINT          REFERENCES leagues(id),
    status          VARCHAR(20)     NOT NULL CHECK (status IN (
                        'PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL'
                    )),
    records_fetched INTEGER         NOT NULL DEFAULT 0,
    records_created INTEGER         NOT NULL DEFAULT 0,
    records_updated INTEGER         NOT NULL DEFAULT 0,
    records_failed  INTEGER         NOT NULL DEFAULT 0,
    error_message   TEXT,
    error_detail    JSONB,
    started_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    duration_ms     INTEGER GENERATED ALWAYS AS (
                        EXTRACT(EPOCH FROM (finished_at - started_at)) * 1000
                    ) STORED
);

CREATE INDEX idx_etl_logs_job ON etl_job_logs(job_name, started_at DESC);
CREATE INDEX idx_etl_logs_status ON etl_job_logs(status) WHERE status IN ('PENDING', 'RUNNING', 'FAILED');
```

---

## 4. VISTAS Y QUERIES FRECUENTES

### 4.1 Vista: Próximos Partidos con Predicciones

```sql
CREATE VIEW v_upcoming_matches AS
SELECT
    m.id,
    m.match_date,
    m.status,
    m.round,
    l.name                  AS league_name,
    l.logo_url              AS league_logo,
    ht.name                 AS home_team_name,
    ht.logo_url             AS home_team_logo,
    at.name                 AS away_team_name,
    at.logo_url             AS away_team_logo,
    p.prob_home_win,
    p.prob_draw,
    p.prob_away_win,
    p.expected_goals_home,
    p.expected_goals_away,
    p.confidence_score
FROM matches m
JOIN league_seasons ls ON m.league_season_id = ls.id
JOIN leagues l ON ls.league_id = l.id
JOIN teams ht ON m.home_team_id = ht.id
JOIN teams at ON m.away_team_id = at.id
LEFT JOIN predictions p ON p.match_id = m.id AND p.model_name = 'poisson_v1'
WHERE m.status IN ('SCHEDULED', 'LIVE')
  AND m.match_date >= NOW();
```

### 4.2 Vista: Forma Reciente de Equipos

```sql
CREATE VIEW v_team_recent_form AS
WITH last_5 AS (
    SELECT
        team_id,
        match_id,
        is_home,
        ROW_NUMBER() OVER (PARTITION BY team_id ORDER BY m.match_date DESC) AS rn,
        CASE
            WHEN (is_home AND m.home_goals_ft > m.away_goals_ft) OR
                 (NOT is_home AND m.away_goals_ft > m.home_goals_ft) THEN 'W'
            WHEN m.home_goals_ft = m.away_goals_ft THEN 'D'
            ELSE 'L'
        END AS result
    FROM match_team_stats mts
    JOIN matches m ON mts.match_id = m.id
    WHERE m.status = 'FT'
)
SELECT
    team_id,
    STRING_AGG(result, '' ORDER BY rn DESC) AS form_string,
    COUNT(*) FILTER (WHERE result = 'W') AS wins,
    COUNT(*) FILTER (WHERE result = 'D') AS draws,
    COUNT(*) FILTER (WHERE result = 'L') AS losses
FROM last_5
WHERE rn <= 5
GROUP BY team_id;
```

---

## 5. ÍNDICES DE RENDIMIENTO Y ESTRATEGIA DE PARTICIONADO

### 5.1 Índices Críticos (justificados por queries del dashboard)

```sql
-- Query más frecuente: partidos de hoy/esta semana
CREATE INDEX idx_matches_upcoming 
ON matches(match_date, status, league_season_id)
WHERE status IN ('SCHEDULED', 'LIVE');

-- Query de stats de equipo para features del modelo
CREATE INDEX idx_mts_team_date 
ON match_team_stats(team_id) 
INCLUDE (xg, shots_on_target, possession_pct);

-- Búsqueda de predicciones activas
CREATE INDEX idx_predictions_active 
ON predictions(match_id, model_name) 
WHERE is_resolved = FALSE;
```

### 5.2 Particionado de Tablas de Estadísticas (Fase 2)

```sql
-- Cuando el volumen de player_season_stats crezca, se particiona:
-- Cada partición cubre las ligas de una temporada
-- Queries de una temporada no tocan datos de otras (partition pruning)

-- Ejemplo para temporada 2024/25:
CREATE TABLE player_season_stats_ls_2024 
PARTITION OF player_season_stats
FOR VALUES IN (
    -- IDs de league_seasons correspondientes a 2024/25
    SELECT id FROM league_seasons WHERE season_id IN (
        SELECT id FROM seasons WHERE year_start = 2024
    )
);
```

---

## 6. ESTRATEGIA DE MIGRACIONES

### 6.1 Convención de Nombres de Migraciones Alembic

```
{timestamp}_{número_secuencial}_{descripción_snake_case}.py

Ejemplos:
20260612_001_create_base_tables.py
20260612_002_create_match_tables.py
20260620_003_add_predictions_table.py
20260701_004_add_users_and_auth.py
```

### 6.2 Política de Migraciones

- **Sin DROP TABLE en migraciones automáticas** — requieren revisión manual
- **Columnas nuevas siempre nullable o con DEFAULT** para no bloquear la tabla
- **Índices CONCURRENTLY** para tablas con datos (no bloquea escrituras)
- **Revisión obligatoria** del SQL generado antes de aplicar en producción

```python
# Ejemplo de migración segura para agregar columna
def upgrade():
    op.add_column('matches',
        sa.Column('attendance', sa.Integer(), nullable=True)
    )

def downgrade():
    op.drop_column('matches', 'attendance')
```

---

## 7. DATOS INICIALES (SEED DATA)

```sql
-- Países principales
INSERT INTO countries (code, name) VALUES
    ('ES', 'España'),
    ('GB', 'Inglaterra'),
    ('DE', 'Alemania'),
    ('FR', 'Francia'),
    ('IT', 'Italia'),
    ('CO', 'Colombia'),
    ('AR', 'Argentina'),
    ('BR', 'Brasil');

-- Ligas principales
INSERT INTO leagues (country_id, external_id, external_source, name, slug, league_type) VALUES
    (1, '140', 'api_football', 'La Liga', 'laliga-esp', 'league'),
    (2, '39',  'api_football', 'Premier League', 'premier-league-eng', 'league'),
    (3, '78',  'api_football', 'Bundesliga', 'bundesliga-ger', 'league'),
    (4, '61',  'api_football', 'Ligue 1', 'ligue1-fra', 'league'),
    (5, '135', 'api_football', 'Serie A', 'serie-a-ita', 'league'),
    (6, '239', 'api_football', 'Liga BetPlay Dimayor', 'liga-betplay-col', 'league');

-- Temporada inicial
INSERT INTO seasons (year_start, year_end, label) VALUES
    (2024, 2025, '2024/25'),
    (2025, 2026, '2025/26');
```
