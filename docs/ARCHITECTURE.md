# ARCHITECTURE DESIGN
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.1.0 _(revisado por comité de arquitectura 2026-06-12)_
**Fecha:** 2026-06-12
**Estado:** Diseño Pre-Implementación — Aprobado

---

## 1. VISIÓN ARQUITECTÓNICA

### 1.1 Principios Fundamentales

1. **Simplicidad primero:** No agregar componentes hasta que el problema que resuelven sea real y medible.
2. **API como contrato:** La API REST es el contrato entre backend y frontend. Jinja2 y Next.js son consumidores intercambiables; el backend no sabe cuál de los dos está respondiendo.
3. **Separación de capas:** Modelos SQLAlchemy ≠ Schemas Pydantic ≠ DTOs de respuesta. Esta separación es el enabler central para la migración a React.
4. **Stateless API:** El servidor FastAPI no guarda estado en memoria. Todo el estado vive en la BD y en cookies httpOnly. Permite escala horizontal sin cambios de código.
5. **Evolución justificada:** Cada componente de Fase 2/3 se agrega cuando las métricas reales lo justifiquen, no por anticipación.

### 1.2 Evolución Arquitectónica

```
FASE 1 (MVP Local)          FASE 2 (Cloud)               FASE 3 (Scale)
──────────────────          ──────────────               ──────────────
FastAPI                     FastAPI                      FastAPI
+ Jinja2 (SSR)    ──────►  + Next.js / Netlify ──────►  + microservicios
+ PostgreSQL                + Neon PostgreSQL             + Aurora PostgreSQL
+ APScheduler       [swap]  + Celery + Redis              + Kafka + Airflow
+ Docker Compose            + Railway / Fly.io            + Kubernetes

Complejidad: BAJA           Complejidad: MEDIA            Complejidad: ALTA
Costo:  ~$0/mes             Costo: ~$50-100/mes           Costo: ~$200-500/mes
Contenedores: 2             Contenedores: cloud-managed   Contenedores: orquestados
```

---

## 2. ARQUITECTURA FASE 1 — MVP LOCAL

### 2.1 Diagrama de Contenedores

```
┌─────────────────────────────────────────────────────────────────┐
│  Docker Compose (2 servicios)                                   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  api  (puerto 8000)                                      │  │
│  │                                                          │  │
│  │  FastAPI application                                     │  │
│  │  ├── REST API routers (/api/v1/*)                        │  │
│  │  ├── Jinja2 template engine (SSR para MVP)               │  │
│  │  ├── APScheduler (BackgroundScheduler, in-process)       │  │
│  │  │    ├── sync_fixtures       → cada 6 h                 │  │
│  │  │    ├── sync_results        → cada 1 h (días partido)  │  │
│  │  │    ├── sync_standings      → diario 04:00             │  │
│  │  │    ├── generate_predictions→ diario 08:00             │  │
│  │  │    └── cleanup_tokens      → diario 03:00             │  │
│  │  └── SQLAlchemy 2.0 async + asyncpg                      │  │
│  │                                                          │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │ asyncpg (TCP)                       │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  postgres  (puerto 5432)                                 │  │
│  │  PostgreSQL 16                                           │  │
│  │  Volumen persistente: ./data/postgres                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ✅ Sin Redis   ✅ Sin worker   ✅ Sin beat   ✅ Sin Flower     │
└─────────────────────────────────────────────────────────────────┘

                  Browser / Cliente HTTP
                         │
                         ▼ :8000
                    FastAPI
                    ├── GET /            → Jinja2 render (HTML)
                    ├── GET /api/v1/*    → JSON response
                    └── POST /api/v1/auth/login → JSON
```

### 2.2 Arquitectura de Capas de la Aplicación

```
┌─────────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                                 │
│  ┌───────────────────────┐   ┌──────────────────────────────────┐  │
│  │  app/web/             │   │  app/api/v1/                     │  │
│  │  Jinja2 Templates     │   │  FastAPI Routers (REST)          │  │
│  │  (SSR — solo MVP)     │   │  /api/v1/matches, /teams, ...    │  │
│  └──────────┬────────────┘   └─────────────────┬────────────────┘  │
├─────────────┼───────────────────────────────────┼───────────────────┤
│  SERVICE LAYER               │                  │                   │
│  ┌───────────────────────────▼──────────────────▼────────────────┐ │
│  │  app/services/                                                │ │
│  │  Lógica de negocio pura — sin dependencias de HTTP ni SQL     │ │
│  │  MatchService, PredictionService, TeamService, AuthService    │ │
│  └──────────────────────────────────┬─────────────────────────── ┘ │
├──────────────────────────────────────┼────────────────────────────┤
│  DATA ACCESS LAYER                   │                             │
│  ┌───────────────────────────────────▼──────────────────────────┐ │
│  │  app/repositories/                                           │ │
│  │  Encapsulan todas las queries SQL                            │ │
│  │  MatchRepository, TeamRepository, PredictionRepository       │ │
│  └──────────────────────────────────┬────────────────────────── ┘ │
├──────────────────────────────────────┼────────────────────────────┤
│  DATA LAYER                          │                             │
│  ┌───────────────────────────────────▼──────────────────────────┐ │
│  │  app/models/   (SQLAlchemy ORM — describe la BD, nada más)   │ │
│  │  ┌───────────────────────────────────────────────────────┐   │ │
│  │  │  PostgreSQL 16                                        │   │ │
│  │  └───────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘

ETL Layer — corre dentro del proceso api via APScheduler
  app/etl/
  ├── fetchers/    → httpx async contra APIs externas
  ├── transformers/→ normalización a formato canónico
  └── jobs/        → funciones async registradas en APScheduler
```

### 2.3 Flujo de Datos ETL

```
APIs Externas                    Proceso FastAPI (api container)
─────────────                    ───────────────────────────────
API-Football  ────┐
Football-Data ────┼──► Fetcher ──► Transformer ──► Loader ──► PostgreSQL
OpenLigaDB   ────┘       │              │              │
                     httpx async   Normaliza        Repository
                     + retry exp.  entidades        async upsert
                     + timeout     + slug gen.
                     + circuit     + dedup
                     breaker
                          │
                    etl_job_logs
                    (INSERT al inicio y fin de cada job)
```

**Ciclo de vida del APScheduler:**
```
@app.on_event("startup")
async def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(sync_fixtures,        "interval", hours=6)
    scheduler.add_job(sync_results,         "interval", hours=1)
    scheduler.add_job(sync_standings,       "cron",     hour=4)
    scheduler.add_job(generate_predictions, "cron",     hour=8)
    scheduler.add_job(cleanup_old_tokens,   "cron",     hour=3)
    scheduler.start()

@app.on_event("shutdown")
async def stop_scheduler():
    scheduler.shutdown(wait=False)
```

### 2.4 Flujo de Request API

```
Cliente (Browser con Jinja2 o Next.js en Fase 2)
  │
  │  HTTP con JWT en Authorization header
  ▼
FastAPI Router
  ├── Middleware: CORS (configurado para localhost en MVP)
  ├── Middleware: Rate Limiter (slowapi — por IP y por usuario)
  └── Dependency: get_current_user (JWT decode → User object)
        │
        ▼
  Service Layer
  │  └── lógica de negocio
  │       └── llama a Repository
  │             └── SQLAlchemy genera query parametrizada
  │                   └── asyncpg ejecuta contra PostgreSQL
  │
  └── Response: Pydantic schema → JSON (serializado con orjson)
```

---

## 3. ARQUITECTURA FASE 2 — CLOUD MANAGED

### 3.1 Diagrama de Componentes

```
Netlify (CDN Edge Global)         Railway / Fly.io
──────────────────────────        ─────────────────
Next.js 15                        FastAPI
├── App Router (SSG + ISR)        ├── API Routers (/api/v1/*)
├── Server Components             ├── Celery Worker (ETL jobs)
└── Client Components             ├── Celery Beat  (scheduler)
        │                         ├── Sentry SDK
        │ fetch / HTTPS           └── CORS habilitado
        └──────────────────────────────────────────┐
                                                   │
                               Neon PostgreSQL      │  Upstash Redis
                               (serverless)   ◄────┘  (serverless broker)

Cambios clave Fase 1 → Fase 2:
  ✅ APScheduler  ──►  Celery + Celery Beat (workers distribuidos en cloud)
  ✅ Jinja2        ──►  Next.js 15 (React, SSG/ISR, Netlify CDN)
  ✅ Docker local  ──►  Railway managed containers
  ✅ PG local      ──►  Neon PostgreSQL (serverless, branching)
  ✅ Sin Redis     ──►  Upstash Redis (serverless, Celery broker + cache L2)
  ✅ JWT HS256     ──►  JWT RS256
  ✅ Sin Sentry    ──►  Sentry (error tracking en producción)
```

### 3.2 Estrategia de Migración Jinja2 → Next.js

La API REST del MVP ya es el contrato que hace posible esta migración sin cambios en backend:

```
FASE 1:
  Browser ──── GET /dashboard ──── FastAPI render Jinja2 ──── PostgreSQL
           └── GET /api/v1/*       (JS interactivo minimal)

FASE 2:
  Browser ──── Netlify CDN (Next.js SSG/ISR)
           └── fetch /api/v1/* ──── FastAPI en Railway ──── Neon PostgreSQL

Cambios requeridos en FastAPI para esta migración:
  1. app.add_middleware(CORSMiddleware, allow_origins=["https://tu-app.netlify.app"])
  2. Revisar que ningún response JSON tenga lógica de presentación embebida
  3. Nada más — la API ya estaba diseñada como contrato independiente
```

---

## 4. ARQUITECTURA FASE 3 — ESCALA

```
┌──────────────────────────────────────────────────────────────┐
│  CDN Cloudflare  →  Next.js en Netlify (frontend)            │
├──────────────────────────────────────────────────────────────┤
│  API Gateway / Load Balancer                                 │
│  ├── FastAPI Service       (API pública)                     │
│  ├── Prediction Service    (microservicio separado)          │
│  └── ETL Service           (microservicio separado)          │
├──────────────────────────────────────────────────────────────┤
│  Message Broker: Kafka                                       │
│  ├── match-results topic                                     │
│  ├── prediction-requests topic                               │
│  └── notification-events topic                               │
├──────────────────────────────────────────────────────────────┤
│  Data Layer                                                  │
│  ├── Aurora PostgreSQL (primary + read replica)              │
│  ├── Redis Cluster (cache L2 + Celery broker)                │
│  └── Elasticsearch (búsqueda full-text)                      │
├──────────────────────────────────────────────────────────────┤
│  ML Platform                                                 │
│  ├── Airflow  (orquestación de pipelines)                    │
│  ├── MLflow   (tracking de experimentos)                     │
│  └── Feature Store (features pre-calculados en Redis)        │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. ESTRUCTURA DEL PROYECTO

```
sports-intelligence-platform/
│
├── app/
│   ├── main.py                    # FastAPI factory + APScheduler startup/shutdown
│   ├── config.py                  # Settings via pydantic-settings (.env)
│   ├── database.py                # Engine async, SessionLocal, get_db dependency
│   │
│   ├── api/                       # Presentación REST
│   │   ├── dependencies.py        # get_current_user, require_pro, require_admin
│   │   └── v1/
│   │       ├── router.py          # include_router de todos los módulos
│   │       ├── auth.py
│   │       ├── matches.py
│   │       ├── teams.py
│   │       ├── players.py
│   │       ├── predictions.py
│   │       ├── leagues.py
│   │       └── users.py
│   │
│   ├── web/                       # Presentación Jinja2 (solo Fase 1)
│   │   ├── router.py              # Rutas HTML: /, /matches, /teams…
│   │   └── dependencies.py        # get_current_user_from_cookie
│   │
│   ├── services/                  # Lógica de negocio (sin HTTP, sin SQL)
│   │   ├── match_service.py
│   │   ├── team_service.py
│   │   ├── player_service.py
│   │   ├── prediction_service.py
│   │   ├── auth_service.py
│   │   └── user_service.py
│   │
│   ├── repositories/              # Queries SQL (solo capa que toca ORM)
│   │   ├── base.py                # BaseRepository con upsert genérico
│   │   ├── match_repository.py
│   │   ├── team_repository.py
│   │   ├── player_repository.py
│   │   ├── prediction_repository.py
│   │   └── user_repository.py
│   │
│   ├── models/                    # SQLAlchemy ORM (solo describe tablas)
│   │   ├── base.py
│   │   ├── competition.py         # Country, League, Season, LeagueSeason
│   │   ├── team.py                # Team, Venue, TeamLeagueSeason, Standing
│   │   ├── player.py              # Player, PlayerTeamContract, PlayerSeasonStats
│   │   ├── match.py               # Match, MatchTeamStats, MatchEvent, Lineup
│   │   ├── prediction.py          # Prediction, Odds
│   │   ├── user.py                # User, RefreshToken, UserFavoriteTeam, UserFavoriteLeague
│   │   └── etl.py                 # ETLJobLog
│   │
│   ├── schemas/                   # Pydantic v2 (validación + DTOs)
│   │   ├── auth.py
│   │   ├── match.py
│   │   ├── team.py
│   │   ├── player.py
│   │   ├── prediction.py
│   │   ├── league.py
│   │   └── user.py
│   │
│   ├── etl/
│   │   ├── scheduler.py           # APScheduler setup + registro de jobs
│   │   ├── fetchers/
│   │   │   ├── base.py            # BaseFetcher: retry exponencial, timeout, circuit breaker
│   │   │   ├── api_football.py
│   │   │   └── football_data.py
│   │   ├── transformers/
│   │   │   ├── match_transformer.py
│   │   │   ├── team_transformer.py
│   │   │   └── player_transformer.py
│   │   └── jobs/                  # Funciones async registradas en APScheduler
│   │       ├── sync_fixtures.py
│   │       ├── sync_results.py
│   │       ├── sync_standings.py
│   │       └── cleanup.py
│   │
│   ├── ml/
│   │   ├── poisson_model.py       # Poisson Bivariado (scipy.stats.poisson)
│   │   ├── features.py            # Extracción y cálculo de features
│   │   └── evaluation.py         # Brier score, log loss, accuracy 1X2
│   │
│   └── core/
│       ├── security.py            # JWT encode/decode, bcrypt hash/verify
│       ├── exceptions.py          # HTTPExceptions con códigos de error internos
│       ├── logging.py             # Logging estructurado JSON
│       └── slug.py                # Generación y validación de slugs
│
├── templates/                     # Jinja2 (Fase 1, se elimina en Fase 2)
│   ├── base.html
│   ├── components/
│   └── pages/
│       ├── home.html
│       ├── matches.html
│       ├── teams/
│       ├── leagues/
│       └── auth/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
│
├── tests/
│   ├── conftest.py                # test_db (PostgreSQL real), test_client, factories
│   ├── unit/
│   │   ├── test_poisson_model.py
│   │   ├── test_transformers.py
│   │   └── test_services.py
│   └── integration/
│       ├── test_auth_endpoints.py
│       ├── test_match_endpoints.py
│       └── test_prediction_endpoints.py
│
├── docs/
├── docker-compose.yml             # 2 servicios: api + postgres
├── Dockerfile
├── pyproject.toml                 # Dependencias con uv
├── alembic.ini
├── .env.example
├── Makefile
└── README.md
```

---

## 6. PATRONES ARQUITECTÓNICOS

### 6.1 Repository Pattern

Encapsula toda la lógica de acceso a datos. Los servicios no importan SQLAlchemy.

```python
class MatchRepository:
    async def find_by_slug(self, slug: str) -> Match | None: ...
    async def find_upcoming(self, league_id: int, days: int = 7) -> list[Match]: ...
    async def upsert_from_external(self, data: MatchTransformed) -> Match: ...
```

En Fase 2, si se agrega read replica de PostgreSQL, el cambio está contenido aquí. Los servicios no cambian.

### 6.2 Service Layer Pattern

Lógica de negocio sin dependencias de HTTP ni de SQL. Testeable con mocks de repositorio.

```python
class PredictionService:
    def __init__(self, prediction_repo: PredictionRepository, match_repo: MatchRepository): ...

    async def generate_for_match(self, match_id: int) -> PredictionSchema:
        match = await self.match_repo.find_by_id(match_id)
        result = self._poisson_model.calculate(match.home_attack, match.away_attack, ...)
        return await self.prediction_repo.create(result)
```

### 6.3 Transformer Pattern

Normaliza datos de múltiples fuentes a un formato canónico interno.

```python
class MatchTransformer:
    def from_api_football(self, raw: dict) -> MatchTransformed: ...
    def from_football_data(self, raw: dict) -> MatchTransformed: ...
```

Agregar una nueva fuente de datos = agregar un nuevo método `from_*`. Sin tocar el resto del sistema.

### 6.4 Separación SQLAlchemy / Pydantic / DTO (ADR-005)

La separación más importante del MVP. Habilita la migración React sin cambios en backend.

```
SQLAlchemy Model     Pydantic Schema (internal)    API Response DTO
────────────────     ──────────────────────────    ────────────────
Match (ORM)    ───►  MatchDB              ───►     MatchResponse
 .id                  .id                           .id
 .home_team_id        .slug                         .slug
 .away_team_id        .home_team (obj)              .home_team (obj)
 .kickoff_utc         .away_team (obj)              .away_team (obj)
 .status              .kickoff_utc                  .kickoff_utc
                      .status                       .status
                                                    .prediction (null para Free)
```

**Regla invariante:** Ningún modelo SQLAlchemy sale del Repository. Ningún schema Pydantic contiene lógica de negocio.

---

## 7. SEGURIDAD

```
Internet
   │
   ├── HTTPS / TLS 1.3 — obligatorio en producción
   ├── Rate Limiting (slowapi) — por IP + por usuario autenticado
   │
   ▼
FastAPI Application
   │
   ├── JWT Authentication
   │    ├── Access token:  15 min, HS256 (MVP) → RS256 (Fase 2)
   │    ├── Refresh token: 7 días, rotación en cada uso
   │    └── Refresh token en cookie httpOnly + Secure (no accesible desde JS)
   │
   ├── RBAC: Free / Pro / Admin (Dependency Injection por endpoint)
   │
   ├── Input Validation: Pydantic v2 en toda entrada externa
   │
   ├── SQL Injection: imposible — todo via SQLAlchemy ORM parametrizado
   │
   └── Passwords: bcrypt cost=12
```

**Manejo de secretos:**
- Desarrollo local: `.env` (en `.gitignore`)
- Producción: Variables de entorno del provider (Railway / Fly.io Secrets)
- Nunca en código ni en `docker-compose.yml`

---

## 8. OBSERVABILIDAD

### Logging estructurado (JSON)

Campos en cada log: `timestamp`, `level`, `logger`, `message`, `request_id`, `user_id`.

| Nivel | Cuándo usarlo |
|-------|--------------|
| INFO | Operación normal completada (job OK, request procesado) |
| WARNING | Condición inesperada no fatal (API externa lenta, dato faltante) |
| ERROR | Operación fallida que requiere atención (job ETL fallido, 5xx) |
| CRITICAL | Sistema en estado inoperable |

### Health checks

```
GET /health        → {"status": "ok", "db": "ok", "scheduler": "running"}
GET /health/ready  → 200 si listo para tráfico, 503 si no
```

### Monitoreo de jobs ETL

Cada job registra en `etl_job_logs`: `started_at`, `finished_at`, `status`, `records_processed`, `records_failed`, `duration_ms`, `error_message`.

`GET /api/v1/admin/etl/jobs` expone el estado al administrador.

---

## 9. STACK TÉCNICO COMPLETO

### Fase 1 — MVP Local

| Categoría | Tecnología | Versión | Justificación |
|-----------|-----------|---------|---------------|
| Runtime | Python | 3.12+ | Async nativo, type hints maduros |
| Framework | FastAPI | 0.115+ | Auto-OpenAPI, async-first, alta DX |
| Templates | Jinja2 | 3.x | SSR sin build step para MVP |
| ORM | SQLAlchemy | 2.0 async | Async nativo, Alembic integrado |
| Validación | Pydantic | v2 | 5-10x más rápido que v1, type safety |
| BD Driver | asyncpg | latest | Driver async más rápido para PostgreSQL |
| Migrations | Alembic | latest | Versionado con rollback |
| Base de datos | PostgreSQL | 16 | pg_trgm, JSON, arrays, robustez |
| Scheduler | APScheduler | 3.x | In-process, sin contenedores extra |
| HTTP Client | httpx | latest | Async-first, timeout explícito, retry |
| Auth | python-jose | 3.x | JWT encode/decode |
| Passwords | passlib[bcrypt] | 1.7+ | bcrypt cost configurable |
| Rate limiting | slowapi | latest | Integración nativa FastAPI |
| Serialización | orjson | 3.x | 2-3x más rápido que stdlib json |
| Error tracking | sentry-sdk | latest | Agregado en Sprint 6 |
| Contenedores | Docker + Compose | 24+ | Entorno reproducible |
| Package manager | uv | latest | 10-100x más rápido que pip |

### Fase 2 — Adiciones Cloud

| Categoría | Tecnología | Justificación |
|-----------|-----------|---------------|
| Frontend | Next.js 15 (App Router) | SSG/ISR, SEO, ecosistema React maduro |
| Deploy FE | Netlify | CI/CD integrado, CDN edge global |
| Deploy BE | Railway o Fly.io | Deploy simple desde Dockerfile |
| BD | Neon PostgreSQL | Serverless, branching para dev/staging |
| Cache + Broker | Upstash Redis | Serverless, pay-per-use, compatible Celery |
| Task Queue | Celery + Celery Beat | Workers distribuidos, reintentos durables |
| Error tracking | Sentry (producción) | Alertas en tiempo real |
| Auth social | Google OAuth | Reducir fricción de registro |
| Pagos | Stripe | Suscripciones y webhooks |
| Email | SendGrid | Transaccional y marketing |

### Fase 3 — Adiciones Scale

| Categoría | Tecnología | Justificación |
|-----------|-----------|---------------|
| Message broker | Kafka | Eventos de alta frecuencia (live scores) |
| Pipeline ML | Apache Airflow | Orquestación de workflows complejos |
| Experimentos ML | MLflow | Tracking y comparación de modelos |
| Búsqueda | Elasticsearch | Full-text escalable con facets |
| BD | Aurora PostgreSQL | HA, read replicas automáticas |
| Infra | Kubernetes (EKS/GKE) | Escala horizontal automática |
