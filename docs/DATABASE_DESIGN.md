# DATABASE DESIGN
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.1.0 _(revisado por comité de arquitectura 2026-06-12)_
**Fecha:** 2026-06-12
**Estado:** Diseño Pre-Implementación — Aprobado

---

## 1. EXTENSIONES REQUERIDAS

```sql
-- Solo pg_trgm es necesaria en MVP
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- búsqueda de texto por similitud (equipos, jugadores)
```

> **Eliminadas vs v1.0:** `uuid-ossp` (no se usa UUID como PK — se usa BIGSERIAL) y `btree_gist` (no se usa en ningún índice del schema actual).

---

## 2. CONVENCIONES DE DISEÑO

| Convención | Decisión |
|-----------|---------|
| PKs | `BIGSERIAL` (autoincremental) — simple, eficiente, compatible con todos los ORMs |
| Timestamps | `TIMESTAMPTZ` — siempre con timezone |
| Texto corto | `VARCHAR(n)` con límite explícito |
| Texto largo | `TEXT` sin límite |
| Slugs | `VARCHAR(200) UNIQUE NOT NULL` — identificadores legibles para URLs |
| Soft delete | `is_active BOOLEAN DEFAULT TRUE` — nunca borrar datos de catálogo |
| Audit trail | `created_at`, `updated_at` en todas las tablas |
| Nombres | `snake_case` para tablas y columnas |

---

## 3. DIAGRAMA ENTIDAD-RELACIÓN (ERD)

```
countries ──< leagues ──< league_seasons >── seasons
                │                │
                │           team_league_seasons >── teams ──< venues (home_venue_id)
                │                │                    │
                │            standings           player_team_contracts
                │                                     │
                                                    players
                                                       │
                                               player_season_stats
                                               match_player_stats ──┐
                                                                     │
matches ──< match_team_stats                                         │
   │    ──< match_events                                             │
   │    ──< match_player_stats ──────────────────────────────────────┘
   │    ──< lineups
   └──< predictions
   └──< odds

users ──< refresh_tokens
      ──< user_favorite_teams
      ──< user_favorite_leagues

etl_job_logs  (standalone — audit de jobs ETL)
```

---

## 4. TABLAS — CATÁLOGO GEOGRÁFICO Y COMPETICIONES

```sql
CREATE TABLE countries (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    code        VARCHAR(10) UNIQUE NOT NULL,   -- 'ES', 'GB', 'CO'
    flag_url    VARCHAR(500),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE leagues (
    id              BIGSERIAL PRIMARY KEY,
    external_id     VARCHAR(50),                           -- ID en API-Football
    name            VARCHAR(200) NOT NULL,
    slug            VARCHAR(200) UNIQUE NOT NULL,          -- 'la-liga', 'premier-league'
    country_id      BIGINT REFERENCES countries(id),      -- NULL permite Champions League / UEFA
    league_type     VARCHAR(50) NOT NULL DEFAULT 'league', -- 'league', 'cup', 'international'
    logo_url        VARCHAR(500),
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,        -- activa = incluida en ETL
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE seasons (
    id          BIGSERIAL PRIMARY KEY,
    year        INTEGER NOT NULL,              -- 2024 = temporada 2024/25
    label       VARCHAR(20) NOT NULL,          -- '2024/25'
    is_current  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE league_seasons (
    id              BIGSERIAL PRIMARY KEY,
    league_id       BIGINT NOT NULL REFERENCES leagues(id),
    season_id       BIGINT NOT NULL REFERENCES seasons(id),
    start_date      DATE,
    end_date        DATE,
    is_current      BOOLEAN NOT NULL DEFAULT FALSE,
    total_rounds    INTEGER,
    current_round   INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (league_id, season_id)
);
```

---

## 5. TABLAS — EQUIPOS Y VENUES

```sql
CREATE TABLE venues (
    id              BIGSERIAL PRIMARY KEY,
    external_id     VARCHAR(50),
    name            VARCHAR(200) NOT NULL,
    city            VARCHAR(100),
    country_id      BIGINT REFERENCES countries(id),
    capacity        INTEGER,
    surface         VARCHAR(50),               -- 'grass', 'artificial'
    image_url       VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE teams (
    id              BIGSERIAL PRIMARY KEY,
    external_id     VARCHAR(50),               -- ID en API-Football
    name            VARCHAR(200) NOT NULL,
    short_name      VARCHAR(50),
    slug            VARCHAR(200) UNIQUE NOT NULL,
    country_id      BIGINT REFERENCES countries(id),
    home_venue_id   BIGINT REFERENCES venues(id),  -- FK a venues (sin duplicar datos)
    logo_url        VARCHAR(500),
    founded_year    INTEGER,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Nombres alternativos de equipos (para normalización ETL entre fuentes)
CREATE TABLE team_aliases (
    id          BIGSERIAL PRIMARY KEY,
    team_id     BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    alias       VARCHAR(200) NOT NULL,
    source      VARCHAR(50),                   -- 'api_football', 'football_data', 'manual'
    UNIQUE (alias, source)
);

CREATE TABLE team_league_seasons (
    id                  BIGSERIAL PRIMARY KEY,
    team_id             BIGINT NOT NULL REFERENCES teams(id),
    league_season_id    BIGINT NOT NULL REFERENCES league_seasons(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (team_id, league_season_id)
);

CREATE TABLE standings (
    id                  BIGSERIAL PRIMARY KEY,
    league_season_id    BIGINT NOT NULL REFERENCES league_seasons(id),
    team_id             BIGINT NOT NULL REFERENCES teams(id),
    rank                INTEGER NOT NULL,
    points              INTEGER NOT NULL DEFAULT 0,
    played              INTEGER NOT NULL DEFAULT 0,
    won                 INTEGER NOT NULL DEFAULT 0,
    drawn               INTEGER NOT NULL DEFAULT 0,
    lost                INTEGER NOT NULL DEFAULT 0,
    goals_for           INTEGER NOT NULL DEFAULT 0,
    goals_against       INTEGER NOT NULL DEFAULT 0,
    goal_diff           INTEGER GENERATED ALWAYS AS (goals_for - goals_against) STORED,
    form                VARCHAR(20),           -- 'WDWLW' — últimos 5 resultados
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (league_season_id, team_id)
);
```

---

## 6. TABLAS — JUGADORES

```sql
CREATE TABLE players (
    id              BIGSERIAL PRIMARY KEY,
    external_id     VARCHAR(50),
    name            VARCHAR(200) NOT NULL,
    slug            VARCHAR(200) UNIQUE NOT NULL,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    date_of_birth   DATE,
    nationality_id  BIGINT REFERENCES countries(id),
    position        VARCHAR(50),               -- 'Goalkeeper', 'Defender', 'Midfielder', 'Attacker'
    height_cm       INTEGER,
    weight_kg       INTEGER,
    photo_url       VARCHAR(500),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE player_team_contracts (
    id              BIGSERIAL PRIMARY KEY,
    player_id       BIGINT NOT NULL REFERENCES players(id),
    team_id         BIGINT NOT NULL REFERENCES teams(id),
    start_date      DATE,
    end_date        DATE,
    jersey_number   INTEGER,
    is_current      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Garantiza que cada jugador tenga máximo un contrato activo
CREATE UNIQUE INDEX uq_player_current_contract
    ON player_team_contracts (player_id)
    WHERE is_current = TRUE;

CREATE TABLE player_season_stats (
    id                  BIGSERIAL PRIMARY KEY,
    player_id           BIGINT NOT NULL REFERENCES players(id),
    league_season_id    BIGINT NOT NULL REFERENCES league_seasons(id),
    team_id             BIGINT NOT NULL REFERENCES teams(id),
    appearances         INTEGER NOT NULL DEFAULT 0,
    minutes_played      INTEGER NOT NULL DEFAULT 0,
    goals               INTEGER NOT NULL DEFAULT 0,
    assists             INTEGER NOT NULL DEFAULT 0,
    yellow_cards        INTEGER NOT NULL DEFAULT 0,
    red_cards           INTEGER NOT NULL DEFAULT 0,
    rating_avg          NUMERIC(4,2),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (player_id, league_season_id, team_id)
);
```

> **Nota sobre particionado:** La tabla `player_season_stats` NO está particionada en MVP. El particionado se evaluará en Fase 2 cuando el profiling identifique queries lentas. El particionado por rango de año es la estrategia correcta cuando sea necesario; la sintaxis `FOR VALUES IN (SELECT ...)` de la versión anterior era inválida en PostgreSQL.

---

## 7. TABLAS — PARTIDOS

```sql
CREATE TABLE matches (
    id                  BIGSERIAL PRIMARY KEY,
    external_id         VARCHAR(50) UNIQUE,
    league_season_id    BIGINT NOT NULL REFERENCES league_seasons(id),
    home_team_id        BIGINT NOT NULL REFERENCES teams(id),
    away_team_id        BIGINT NOT NULL REFERENCES teams(id),
    kickoff_utc         TIMESTAMPTZ NOT NULL,
    round               VARCHAR(50),
    venue_id            BIGINT REFERENCES venues(id),
    referee_name        VARCHAR(200),               -- sin tabla separada en MVP
    status              VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED',
    -- SCHEDULED, LIVE, FINISHED, POSTPONED, CANCELLED, SUSPENDED
    home_score          INTEGER,
    away_score          INTEGER,
    home_score_ht       INTEGER,                    -- marcador al descanso
    away_score_ht       INTEGER,
    minutes_played      INTEGER,                    -- null si no está en juego
    slug                VARCHAR(200) UNIQUE NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (home_team_id <> away_team_id)
);

CREATE TABLE match_team_stats (
    id              BIGSERIAL PRIMARY KEY,
    match_id        BIGINT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    team_id         BIGINT NOT NULL REFERENCES teams(id),
    is_home         BOOLEAN NOT NULL,
    shots_total     INTEGER,
    shots_on_goal   INTEGER,
    possession_pct  NUMERIC(5,2),
    passes_total    INTEGER,
    passes_accuracy NUMERIC(5,2),
    fouls           INTEGER,
    corners         INTEGER,
    offsides        INTEGER,
    yellow_cards    INTEGER,
    red_cards       INTEGER,
    UNIQUE (match_id, team_id)
);

CREATE TABLE match_events (
    id              BIGSERIAL PRIMARY KEY,
    match_id        BIGINT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    team_id         BIGINT NOT NULL REFERENCES teams(id),
    player_id       BIGINT REFERENCES players(id),
    assist_player_id BIGINT REFERENCES players(id),
    event_type      VARCHAR(50) NOT NULL,  -- 'GOAL', 'YELLOW_CARD', 'RED_CARD', 'SUBSTITUTION', 'VAR'
    minute          INTEGER NOT NULL,
    extra_minute    INTEGER,               -- minuto de descuento (90+3 → minute=90, extra=3)
    detail          VARCHAR(200),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE match_player_stats (
    id              BIGSERIAL PRIMARY KEY,
    match_id        BIGINT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id       BIGINT NOT NULL REFERENCES players(id),
    team_id         BIGINT NOT NULL REFERENCES teams(id),
    minutes_played  INTEGER,
    rating          NUMERIC(4,2),
    goals           INTEGER NOT NULL DEFAULT 0,
    assists         INTEGER NOT NULL DEFAULT 0,
    shots_total     INTEGER,
    shots_on_goal   INTEGER,
    passes_total    INTEGER,
    key_passes      INTEGER,
    yellow_cards    INTEGER NOT NULL DEFAULT 0,
    red_cards       INTEGER NOT NULL DEFAULT 0,
    UNIQUE (match_id, player_id)
);

CREATE TABLE lineups (
    id              BIGSERIAL PRIMARY KEY,
    match_id        BIGINT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    team_id         BIGINT NOT NULL REFERENCES teams(id),
    player_id       BIGINT NOT NULL REFERENCES players(id),
    lineup_type     VARCHAR(20) NOT NULL,  -- 'STARTING', 'SUBSTITUTE'
    jersey_number   INTEGER,
    position_abbr   VARCHAR(10),
    grid_position   VARCHAR(10),           -- '3:2' (fila:columna para formación visual)
    UNIQUE (match_id, team_id, player_id)
);
```

---

## 8. TABLAS — PREDICCIONES Y ODDS

```sql
CREATE TABLE predictions (
    id                  BIGSERIAL PRIMARY KEY,
    match_id            BIGINT NOT NULL REFERENCES matches(id),
    model_version       VARCHAR(50) NOT NULL DEFAULT 'poisson_v1',
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Probabilidades 1X2
    prob_home_win       NUMERIC(8,6) NOT NULL,
    prob_draw           NUMERIC(8,6) NOT NULL,
    prob_away_win       NUMERIC(8,6) NOT NULL,

    -- Over/Under 2.5
    prob_over_2_5       NUMERIC(8,6),
    prob_under_2_5      NUMERIC(8,6),

    -- BTTS (Both Teams To Score)
    prob_btts_yes       NUMERIC(8,6),
    prob_btts_no        NUMERIC(8,6),

    -- Goles esperados (outputs del modelo Poisson)
    expected_goals_home NUMERIC(5,2),
    expected_goals_away NUMERIC(5,2),

    -- Marcador más probable
    most_likely_score   VARCHAR(10),   -- '2-1'

    -- Features utilizados (JSON para auditoría y explicabilidad)
    features_snapshot   JSONB,

    -- Resultado real (se completa al finalizar el partido)
    actual_outcome      VARCHAR(10),   -- 'HOME', 'DRAW', 'AWAY'
    brier_score         NUMERIC(8,6),  -- calculado al resolverse

    -- Garantiza solo una predicción activa por modelo y partido
    UNIQUE (match_id, model_version),

    -- Validación de calibración: las 3 probabilidades deben sumar ~1.0
    CONSTRAINT probs_1x2_sum_check
        CHECK (ABS(prob_home_win + prob_draw + prob_away_win - 1.0) < 0.0001)
);

CREATE TABLE odds (
    id              BIGSERIAL PRIMARY KEY,
    match_id        BIGINT NOT NULL REFERENCES matches(id),
    bookmaker       VARCHAR(100) NOT NULL,
    market          VARCHAR(50) NOT NULL,   -- '1X2', 'OVER_UNDER_2_5', 'BTTS'
    outcome         VARCHAR(50) NOT NULL,   -- 'HOME', 'DRAW', 'AWAY', 'OVER', 'UNDER'
    odd_value       NUMERIC(8,3) NOT NULL,
    captured_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (match_id, bookmaker, market, outcome, captured_at)
);
```

---

## 9. TABLAS — USUARIOS Y AUTENTICACIÓN

```sql
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    username        VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(200),
    avatar_url      VARCHAR(500),
    role            VARCHAR(20) NOT NULL DEFAULT 'free',  -- 'free', 'pro', 'admin'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Campos de OAuth y Stripe se agregan en Fase 2 via Alembic migration:
-- ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50);
-- ALTER TABLE users ADD COLUMN oauth_sub VARCHAR(200);
-- ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(100);
-- ALTER TABLE users ADD COLUMN subscription_status VARCHAR(50) DEFAULT 'free';
-- ALTER TABLE users ADD COLUMN subscription_ends_at TIMESTAMPTZ;

CREATE TABLE refresh_tokens (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      VARCHAR(255) UNIQUE NOT NULL,  -- hash SHA-256 del token raw
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,                   -- NULL = activo, NOT NULL = revocado
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Favoritos con integridad referencial completa (sin polimorfismo sin FK)
CREATE TABLE user_favorite_teams (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id     BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, team_id)
);

CREATE TABLE user_favorite_leagues (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    league_id   BIGINT NOT NULL REFERENCES leagues(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, league_id)
);
```

> **Eliminados vs v1.0:** `api_keys` (Fase 2), `oauth_provider`/`stripe_customer_id` en `users` (Fase 2 via migration), tabla `user_favorites` polimórfica reemplazada por tablas tipadas con FK reales.

---

## 10. TABLA — AUDITORÍA ETL

```sql
CREATE TABLE etl_job_logs (
    id                  BIGSERIAL PRIMARY KEY,
    job_name            VARCHAR(100) NOT NULL,  -- 'sync_fixtures', 'sync_results', etc.
    source              VARCHAR(50),            -- 'api_football', 'football_data'
    league_id           BIGINT REFERENCES leagues(id),
    season_id           BIGINT REFERENCES seasons(id),
    status              VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    -- RUNNING, SUCCESS, FAILED, PARTIAL
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at         TIMESTAMPTZ,
    duration_ms         NUMERIC(12,3),          -- NUMERIC para EXTRACT result (DOUBLE PRECISION)
    records_processed   INTEGER NOT NULL DEFAULT 0,
    records_failed      INTEGER NOT NULL DEFAULT 0,
    error_message       TEXT,
    error_traceback     TEXT
);
```

---

## 11. ÍNDICES

```sql
-- Matches: queries más frecuentes
CREATE INDEX idx_matches_kickoff_utc       ON matches (kickoff_utc);
CREATE INDEX idx_matches_status            ON matches (status);
CREATE INDEX idx_matches_home_team         ON matches (home_team_id);
CREATE INDEX idx_matches_away_team         ON matches (away_team_id);
CREATE INDEX idx_matches_league_season     ON matches (league_season_id, kickoff_utc);

-- Teams: búsqueda por texto
CREATE INDEX idx_teams_name_trgm           ON teams USING gin (name gin_trgm_ops);
CREATE INDEX idx_teams_slug                ON teams (slug);

-- Players: búsqueda por texto
CREATE INDEX idx_players_name_trgm         ON players USING gin (name gin_trgm_ops);
CREATE INDEX idx_players_slug              ON players (slug);

-- Predictions: lookup por partido
CREATE INDEX idx_predictions_match_id      ON predictions (match_id);
CREATE INDEX idx_predictions_generated_at  ON predictions (generated_at DESC);

-- Users: autenticación
CREATE INDEX idx_users_email               ON users (email);
CREATE INDEX idx_refresh_tokens_user_id    ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens (token_hash);

-- Standings: tabla de posiciones
CREATE INDEX idx_standings_league_season   ON standings (league_season_id, rank);

-- ETL logs: monitoreo
CREATE INDEX idx_etl_job_logs_job_name     ON etl_job_logs (job_name, started_at DESC);
CREATE INDEX idx_etl_job_logs_status       ON etl_job_logs (status);
```

---

## 12. VISTAS

```sql
-- Forma reciente de equipos (últimos 5 partidos)
CREATE OR REPLACE VIEW v_team_recent_form AS
WITH recent_matches AS (
    SELECT
        team_id,
        match_id,
        is_home,
        ROW_NUMBER() OVER (
            PARTITION BY team_id
            ORDER BY m.kickoff_utc DESC   -- rn=1 es el más reciente
        ) AS rn
    FROM match_team_stats mts
    JOIN matches m ON m.id = mts.match_id
    WHERE m.status = 'FINISHED'
),
results AS (
    SELECT
        rm.team_id,
        rm.rn,
        CASE
            WHEN rm.is_home AND m.home_score > m.away_score THEN 'W'
            WHEN rm.is_home AND m.home_score = m.away_score THEN 'D'
            WHEN rm.is_home AND m.home_score < m.away_score THEN 'L'
            WHEN NOT rm.is_home AND m.away_score > m.home_score THEN 'W'
            WHEN NOT rm.is_home AND m.away_score = m.home_score THEN 'D'
            ELSE 'L'
        END AS result
    FROM recent_matches rm
    JOIN matches m ON m.id = rm.match_id
    WHERE rm.rn <= 5
)
SELECT
    team_id,
    -- ORDER BY rn ASC: rn=5 (más antiguo) primero, rn=1 (más reciente) al final
    -- Resultado: 'WDWLW' → el último carácter es el partido más reciente
    STRING_AGG(result, '' ORDER BY rn ASC) AS form_string,
    COUNT(*) FILTER (WHERE result = 'W') AS wins,
    COUNT(*) FILTER (WHERE result = 'D') AS draws,
    COUNT(*) FILTER (WHERE result = 'L') AS losses
FROM results
GROUP BY team_id;

-- Próximos partidos con predicciones
CREATE OR REPLACE VIEW v_upcoming_matches_with_predictions AS
SELECT
    m.id,
    m.slug,
    m.kickoff_utc,
    m.round,
    m.status,
    ht.id   AS home_team_id,
    ht.name AS home_team_name,
    ht.slug AS home_team_slug,
    ht.logo_url AS home_team_logo,
    at.id   AS away_team_id,
    at.name AS away_team_name,
    at.slug AS away_team_slug,
    at.logo_url AS away_team_logo,
    l.name  AS league_name,
    l.slug  AS league_slug,
    p.prob_home_win,
    p.prob_draw,
    p.prob_away_win,
    p.expected_goals_home,
    p.expected_goals_away,
    p.generated_at AS prediction_generated_at
FROM matches m
JOIN teams ht ON ht.id = m.home_team_id
JOIN teams at ON at.id = m.away_team_id
JOIN league_seasons ls ON ls.id = m.league_season_id
JOIN leagues l ON l.id = ls.league_id
LEFT JOIN predictions p ON p.match_id = m.id AND p.model_version = 'poisson_v1'
WHERE m.status = 'SCHEDULED'
  AND m.kickoff_utc > NOW()
ORDER BY m.kickoff_utc;
```

---

## 13. ESTRATEGIA DE MIGRACIONES (ALEMBIC)

### Convención de nombres

```
alembic/versions/
  001_initial_schema.py
  002_add_search_indexes.py
  003_seed_leagues_and_countries.py
```

### Reglas de migración

1. Nunca modificar una migración ya aplicada en producción
2. Cada migración debe ser reversible (implementar `downgrade()`)
3. Las migraciones de Fase 2 (OAuth, Stripe, api_keys) se generan en su momento con `alembic revision --autogenerate`
4. Seeds de datos de catálogo (países, ligas activas) van en migraciones separadas

### Ejemplo de migración Fase 2 (OAuth)

```python
# Generado automáticamente cuando se agregue el feature
def upgrade():
    op.add_column('users', sa.Column('oauth_provider', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('oauth_sub', sa.String(200), nullable=True))
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('subscription_status', sa.String(50),
                                     server_default='free', nullable=False))
    op.add_column('users', sa.Column('subscription_ends_at', sa.TIMESTAMPTZ(), nullable=True))

def downgrade():
    op.drop_column('users', 'subscription_ends_at')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'stripe_customer_id')
    op.drop_column('users', 'oauth_sub')
    op.drop_column('users', 'oauth_provider')
```

---

## 14. INTEGRIDAD Y CONSISTENCIA

### Constraints de negocio

```sql
-- Un partido no puede enfrentarse a sí mismo
CHECK (home_team_id <> away_team_id)

-- Probabilidades 1X2 calibradas: deben sumar 1.0 con tolerancia < 0.0001
CONSTRAINT probs_1x2_sum_check
    CHECK (ABS(prob_home_win + prob_draw + prob_away_win - 1.0) < 0.0001)

-- Máximo un contrato activo por jugador (índice parcial único)
CREATE UNIQUE INDEX uq_player_current_contract
    ON player_team_contracts (player_id) WHERE is_current = TRUE

-- Un solo alias por nombre y fuente
UNIQUE (alias, source)  -- en team_aliases

-- Una predicción por modelo y partido
UNIQUE (match_id, model_version)  -- en predictions
```

### Notas de integridad referencial

- `user_favorite_teams` y `user_favorite_leagues` usan FK reales (sin polimorfismo sin FK)
- `refresh_tokens.token_hash` almacena el hash SHA-256 del token — nunca el token crudo
- `leagues.country_id` es `NULLABLE` para permitir competiciones internacionales (Champions League, UEFA Nations League)
- `teams.home_venue_id` es FK a `venues` — sin duplicar `stadium_name`/`stadium_capacity` en `teams`
