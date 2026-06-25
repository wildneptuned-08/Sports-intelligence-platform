# PHASE 6 — ETL Foundation

**Fecha:** 2026-06-25
**Rama:** `feature/etl-foundation`
**Estado:** Implementado

---

## 1. Arquitectura ETL

```
API-Football (v3)
       │
       ▼
┌──────────────────┐
│  APIFootballClient│  ← httpx async + tenacity retries
│  (Fetcher)        │
└────────┬─────────┘
         │ JSON crudo
         ▼
┌──────────────────┐
│  Transformers     │  ← Convierte JSON → kwargs del modelo
│  - competition    │
│  - team           │
│  - match          │
└────────┬─────────┘
         │ datos limpios
         ▼
┌──────────────────┐
│  Repositories     │  ← SQLAlchemy 2.0 async, upsert por external_id
│  - BaseRepository │
│  - Competition    │
│  - Team           │
│  - Match          │
└────────┬─────────┘
         │ ORM flush
         ▼
┌──────────────────┐
│  PostgreSQL       │  ← Tablas: leagues, teams, matches, etc.
└──────────────────┘
```

## 2. Flujo ETL — Jobs

### sync_competitions
1. Llama `GET /leagues` de API-Football
2. Transforma countries, leagues, seasons
3. Upsert por `code` (countries) y `external_id` (leagues)
4. Crea registros en `league_seasons`
5. Registra métricas en `etl_job_logs`

### sync_teams
1. Obtiene leagues activas (`is_active = true`)
2. Para cada league, llama `GET /teams?league={id}&season={year}`
3. Transforma venues y teams
4. Upsert por `external_id`
5. Registra métricas en `etl_job_logs`

### sync_matches
1. Obtiene leagues activas + season actual
2. Para cada league, llama `GET /fixtures?league={id}&season={year}`
3. Transforma fixtures → matches con mapeo de status
4. Resuelve `home_team_id` y `away_team_id` por `external_id`
5. Upsert por `external_id`
6. Registra métricas en `etl_job_logs`

**Orden de ejecución:** competitions → teams → matches (dependencia de datos)

## 3. Componentes

### Fetcher: `app/etl/fetchers/api_football.py`
- `APIFootballClient` con httpx async
- Retry automático (3 intentos, backoff exponencial) via tenacity
- Timeout: 10s connect, 30s read
- Manejo de rate limit (HTTP 429)
- Logging estructurado por request/response

### Transformers: `app/etl/transformers/`
- `competition_transformer.py` — countries, leagues, seasons
- `team_transformer.py` — teams, venues
- `match_transformer.py` — fixtures con mapeo de status API→interno

### Repositories: `app/repositories/`
- `BaseRepository[T]` — CRUD genérico + upsert por external_id
- `CompetitionRepository` — Country, League, Season, LeagueSeason
- `TeamRepository` — Team, Venue
- `MatchRepository` — Match

### Jobs: `app/etl/jobs/`
- `sync_competitions.py` — idempotente, registra ETLJobLog
- `sync_teams.py` — idempotente, depende de leagues activas
- `sync_matches.py` — idempotente, depende de teams sincronizados

### Scheduler: `app/etl/scheduler.py`
- 3 jobs registrados en APScheduler pero **pausados** (`next_run_time=None`)
- `sync_competitions` — cron 02:00 UTC
- `sync_teams` — cron 03:00 UTC
- `sync_matches` — intervalo configurable (default 6h)

### Endpoints: `app/api/v1/`
- `GET /api/v1/competitions/` — listado paginado de leagues
- `GET /api/v1/teams/` — listado paginado de teams
- `GET /api/v1/matches/` — listado paginado de matches

## 4. Dependencias agregadas

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| tenacity | >=8.2.0 | Retry con backoff para API calls |

## 5. Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `API_FOOTBALL_KEY` | `""` | API key de api-sports.io |
| `API_FOOTBALL_BASE_URL` | `https://v3.football.api-sports.io` | URL base de la API |
| `ETL_SYNC_FIXTURES_INTERVAL_HOURS` | `6` | Intervalo de sync de matches |

## 6. Ejecución local

### Prerequisitos
- Docker y Docker Compose funcionando
- PostgreSQL accesible (via docker-compose)

### Pasos

```bash
# 1. Levantar servicios
docker compose up -d

# 2. Ejecutar migraciones
docker compose exec api alembic upgrade head

# 3. Configurar API key en .env
API_FOOTBALL_KEY=tu_api_key_aqui

# 4. Ejecutar un job manualmente (desde Python)
docker compose exec api python -c "
import asyncio
from app.etl.jobs.sync_competitions import sync_competitions
result = asyncio.run(sync_competitions())
print(result)
"

# 5. Verificar datos via API
curl http://localhost:8000/api/v1/competitions/
curl http://localhost:8000/api/v1/teams/
curl http://localhost:8000/api/v1/matches/
```

### Ejecutar tests

```bash
# Con DB de test corriendo
docker compose exec api pytest tests/ -v --cov=app --cov-report=term-missing
```

## 7. Migración Alembic

- `002_add_external_id_unique_constraints.py`
  - Agrega UNIQUE a `leagues.external_id`, `teams.external_id`, `venues.external_id`, `players.external_id`
  - Agrega UNIQUE a `seasons.year`

## 8. Troubleshooting

### "API-Football error 429: Rate limit exceeded"
La API tiene límite de requests por minuto. Los retries con backoff manejan esto automáticamente. Si persiste, aumentar el intervalo entre syncs.

### "Team not found for match"
Los teams deben sincronizarse antes que los matches. Ejecutar `sync_teams` antes de `sync_matches`.

### "No active leagues found"
Ninguna league tiene `is_active = true`. Después de `sync_competitions`, activar leagues manualmente:
```sql
UPDATE leagues SET is_active = true WHERE slug IN ('la-liga', 'premier-league');
```

### "No current season found"
`sync_competitions` marca seasons con `is_current = true`. Si no hay season actual, verificar que la API devuelve `current: true` en alguna season.

### Jobs no se ejecutan
Los jobs están registrados pero **pausados** (`next_run_time=None`). Para activarlos programáticamente:
```python
scheduler.resume_job("sync_competitions")
scheduler.resume_job("sync_teams")
scheduler.resume_job("sync_matches")
```
