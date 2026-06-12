# ARCHITECTURE DESIGN
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.0.0  
**Fecha:** 2026-06-12  
**Estado:** Diseño Pre-Implementación

---

## 1. VISIÓN ARQUITECTÓNICA

La plataforma evoluciona en tres fases distintas con arquitecturas adaptadas al tamaño y complejidad del problema en cada momento:

```
FASE 1 (MVP Local)       →  FASE 2 (Cloud Managed)    →  FASE 3 (Scale)
─────────────────────────   ─────────────────────────   ─────────────────────
Monolito FastAPI             Monolito + Servicios ext.   Microservicios
Jinja2 Server-Side           React/Next.js (Netlify)     Event-driven
PostgreSQL Local             PostgreSQL Managed           CQRS + Event Store
Docker Compose               Docker + CI/CD              Kubernetes
```

El principio central: **diseñar las interfaces correctamente desde el inicio** para que la migración entre fases sea una decisión de configuración, no una reescritura.

---

## 2. ARQUITECTURA FASE 1 — MVP LOCAL

### 2.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Compose Network                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    CONTENEDOR: api                            │   │
│  │                                                               │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │                  FastAPI Application                  │    │   │
│  │  │                                                       │    │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │    │   │
│  │  │  │  Routers │  │ Services │  │    Schedulers     │  │    │   │
│  │  │  │ (HTTP)   │  │(Business │  │  (APScheduler /  │  │    │   │
│  │  │  │          │  │  Logic)  │  │   Celery Beat)   │  │    │   │
│  │  │  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │    │   │
│  │  │       │             │                  │             │    │   │
│  │  │  ┌────▼─────────────▼──────────────────▼─────────┐  │    │   │
│  │  │  │           Repositories (Data Access)           │  │    │   │
│  │  │  │           SQLAlchemy ORM + Alembic             │  │    │   │
│  │  │  └────────────────────┬──────────────────────────┘  │    │   │
│  │  │                       │                              │    │   │
│  │  │  ┌────────────────────▼──────────────────────────┐  │    │   │
│  │  │  │              Jinja2 Templates                  │  │    │   │
│  │  │  │         (Server-Side Rendering)                │  │    │   │
│  │  │  └───────────────────────────────────────────────┘  │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                               │                                      │
│  ┌────────────────────┐  ┌────▼────────────────┐                    │
│  │ CONTENEDOR: worker │  │ CONTENEDOR: postgres │                    │
│  │                    │  │                      │                    │
│  │  Celery Worker     │  │  PostgreSQL 16       │                    │
│  │  (ETL Jobs,        │  │  Port: 5432          │                    │
│  │   ML Predictions)  │  │  Volume: pgdata      │                    │
│  └────────┬───────────┘  └─────────────────────┘                    │
│           │                                                          │
│  ┌────────▼───────────┐                                              │
│  │ CONTENEDOR: redis  │                                              │
│  │                    │                                              │
│  │  Redis 7           │                                              │
│  │  (Celery Broker,   │                                              │
│  │   Cache L2)        │                                              │
│  └────────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   APIs EXTERNAS      │
                    │  - API-Football      │
                    │  - Football-Data.org │
                    │  - The Odds API      │
                    └─────────────────────┘
```

### 2.2 Estructura de Carpetas del Proyecto

```
sports-intelligence-platform/
├── backend/
│   ├── app/
│   │   ├── api/                    # Capa de presentación HTTP
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── matches.py
│   │   │   │   │   ├── teams.py
│   │   │   │   │   ├── players.py
│   │   │   │   │   ├── predictions.py
│   │   │   │   │   ├── leagues.py
│   │   │   │   │   └── auth.py
│   │   │   │   └── router.py
│   │   │   └── deps.py             # Inyección de dependencias
│   │   ├── core/                   # Configuración central
│   │   │   ├── config.py           # Settings con Pydantic BaseSettings
│   │   │   ├── security.py         # JWT, hashing
│   │   │   └── database.py         # Engine, SessionLocal
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── base.py
│   │   │   ├── league.py
│   │   │   ├── team.py
│   │   │   ├── player.py
│   │   │   ├── match.py
│   │   │   ├── prediction.py
│   │   │   └── user.py
│   │   ├── schemas/                # Pydantic schemas (I/O validation)
│   │   │   ├── match.py
│   │   │   ├── team.py
│   │   │   ├── player.py
│   │   │   ├── prediction.py
│   │   │   └── user.py
│   │   ├── services/               # Lógica de negocio
│   │   │   ├── match_service.py
│   │   │   ├── team_service.py
│   │   │   ├── player_service.py
│   │   │   ├── prediction_service.py
│   │   │   └── user_service.py
│   │   ├── repositories/           # Acceso a datos (patrón Repository)
│   │   │   ├── match_repo.py
│   │   │   ├── team_repo.py
│   │   │   └── prediction_repo.py
│   │   ├── etl/                    # Módulo ETL (ingesta de datos)
│   │   │   ├── clients/            # Clientes para APIs externas
│   │   │   │   ├── base_client.py
│   │   │   │   ├── api_football.py
│   │   │   │   └── football_data.py
│   │   │   ├── transformers/       # Normalización y mapeo
│   │   │   │   ├── match_transformer.py
│   │   │   │   └── team_transformer.py
│   │   │   └── jobs/               # Tareas Celery
│   │   │       ├── sync_fixtures.py
│   │   │       ├── sync_results.py
│   │   │       └── sync_odds.py
│   │   ├── ml/                     # Motor de predicciones
│   │   │   ├── models/
│   │   │   │   ├── base_model.py
│   │   │   │   └── poisson_model.py
│   │   │   ├── features/           # Feature engineering
│   │   │   │   └── team_features.py
│   │   │   └── jobs/
│   │   │       └── generate_predictions.py
│   │   ├── templates/              # Jinja2 (MVP)
│   │   │   ├── base.html
│   │   │   ├── dashboard/
│   │   │   ├── matches/
│   │   │   ├── teams/
│   │   │   └── players/
│   │   └── main.py                 # FastAPI app factory
│   ├── migrations/                 # Alembic migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
├── database/
│   └── init.sql                    # Extensiones y datos iniciales
├── frontend/                       # Vacío en MVP (reservado para Fase 2)
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── nginx/
│       └── nginx.conf
├── ml_engine/                      # En MVP: parte de backend; en Fase 3: servicio independiente
├── docs/
└── tests/
```

### 2.3 Flujo de Datos — Ingesta ETL

```
API Externa
    │
    ▼
ETL Client (HTTP con retry)
    │
    ▼ datos crudos (JSON)
Transformer (normalización, mapeo de entidades)
    │
    ▼ objetos Python tipados
Repository (upsert idempotente)
    │
    ▼
PostgreSQL (tabla de staging → tablas definitivas)
    │
    ▼
Evento: trigger recálculo de predicciones (Celery task)
    │
    ▼
ML Engine (calcula probabilidades)
    │
    ▼
PostgreSQL (tabla predictions actualizada)
    │
    ▼
Cache invalidada (Redis)
```

### 2.4 Flujo de Datos — Request de Usuario

```
Browser / Cliente
    │
    ▼ HTTP Request
Nginx (reverse proxy, SSL termination en prod)
    │
    ▼
FastAPI Router
    │
    ▼
Auth Middleware (validar JWT)
    │
    ▼
Rate Limiter
    │
    ▼
Endpoint Handler
    │
    ├── Cache hit? → Redis → Response
    │
    └── Cache miss?
            │
            ▼
        Service Layer (lógica de negocio)
            │
            ▼
        Repository Layer (SQLAlchemy queries)
            │
            ▼
        PostgreSQL
            │
            ▼
        Response Schema (Pydantic serialización)
            │
            ▼
        Cache Store (Redis, TTL según tipo de dato)
            │
            ▼
        HTTP Response (JSON o HTML con Jinja2)
```

---

## 3. ARQUITECTURA FASE 2 — CLOUD MANAGED

### 3.1 Cambios Arquitectónicos vs Fase 1

| Componente | Fase 1 | Fase 2 | Motivación |
|-----------|--------|--------|------------|
| Frontend | Jinja2 (SSR in FastAPI) | Next.js en Netlify | SEO, DX, separación de concerns |
| Backend | FastAPI local | FastAPI en Railway/Render/Fly.io | Disponibilidad, auto-scaling |
| Base de datos | PostgreSQL Docker | Neon / Supabase / RDS | Backups automáticos, réplicas |
| Cache | Redis Docker | Redis Cloud / Upstash | Managed, sin mantenimiento |
| Media storage | Disco local | Cloudflare R2 / AWS S3 | Durabilidad, CDN |
| Emails | SMTP local | SendGrid | Deliverability |
| Autenticación | JWT custom | Auth0 / Supabase Auth | OAuth social, MFA |

### 3.2 Diagrama Fase 2

```
┌────────────────────────────────────────────────────────────┐
│                         INTERNET                            │
└─────────────┬──────────────────────────────────────────────┘
              │
   ┌──────────▼──────────┐          ┌────────────────────┐
   │   Netlify CDN        │          │   Cloudflare DNS   │
   │   Next.js Frontend   │◄────────►│   + WAF            │
   │   (SSG + ISR)        │          └────────────────────┘
   └──────────┬───────────┘
              │ API calls (HTTPS)
   ┌──────────▼───────────┐
   │   FastAPI Backend     │          ┌────────────────────┐
   │   (Railway / Fly.io)  │◄────────►│   Redis Cloud      │
   │   Workers: 4          │          │   (Upstash)        │
   └──────────┬────────────┘          └────────────────────┘
              │
   ┌──────────▼───────────┐          ┌────────────────────┐
   │   PostgreSQL Managed  │          │   Celery Workers   │
   │   (Neon / Supabase)   │          │   (mismo servicio  │
   │   Primary + Read      │          │    o Railway job)  │
   │   Replica             │          └────────────────────┘
   └───────────────────────┘
```

### 3.3 Estrategia de Migración Fase 1 → Fase 2

**Principio:** La API REST diseñada desde MVP es la misma que consumirá Next.js. La migración es solo de capa de presentación.

```
Semana 1-2: 
  - Scaffolding Next.js
  - Configurar CORS en FastAPI
  - Migrar autenticación a cookies httpOnly + refresh tokens

Semana 3-4:
  - Migrar página a página de Jinja2 → React components
  - Feature flag: /new/* rutas en Next.js, /* en FastAPI legacy

Semana 5-6:
  - Migrar base de datos a managed provider
  - Validar conexiones con pg_bouncer
  - Go-live y redirigir tráfico

Semana 7:
  - Deprecar templates Jinja2
  - Limpiar código de server-side rendering en FastAPI
```

---

## 4. ARQUITECTURA FASE 3 — ESCALA Y MICROSERVICIOS

### 4.1 Extracción de Servicios

```
MONOLITO (Fase 2)                    MICROSERVICIOS (Fase 3)
─────────────────                    ───────────────────────
FastAPI App                  →       api-gateway (Kong / Traefik)
  └─ ETL Module              →       etl-service (Python + Airflow)
  └─ ML Module               →       ml-service (Python + MLflow)
  └─ Notifications Module    →       notification-service (Go / Node)
  └─ Auth Module             →       auth-service (o Auth0)
  └─ Core API                →       core-api (FastAPI, reducido)
```

### 4.2 Event-Driven Communication

```
Evento: match_result_updated
  │
  ├── ml-service → recalcular predicciones
  ├── notification-service → alertar usuarios suscritos
  └── analytics-service → actualizar métricas de accuracy

Message broker: Apache Kafka o AWS EventBridge
```

---

## 5. STACK TECNOLÓGICO COMPLETO

### 5.1 Fase 1 — MVP

| Capa | Tecnología | Versión | Justificación |
|------|-----------|---------|---------------|
| Backend Framework | FastAPI | 0.115+ | Async nativo, tipado, OpenAPI automático |
| ORM | SQLAlchemy | 2.0+ | Async support, type hints en modelos |
| Migraciones | Alembic | 1.13+ | Integración perfecta con SQLAlchemy |
| Validación | Pydantic | 2.0+ | Performance, type safety |
| Template Engine | Jinja2 | 3.1+ | Solo en MVP, SSR |
| Base de Datos | PostgreSQL | 16 | JSONB, CTEs, window functions, particiones |
| Cache/Broker | Redis | 7.2 | Streams, pub/sub, Celery broker |
| Task Queue | Celery | 5.3+ | Distributed workers, beat scheduler |
| HTTP Client | httpx | 0.27+ | Async, HTTP/2, retry policies |
| Contenedores | Docker + Compose | 26+ | Reproducibilidad del entorno |
| Servidor | Uvicorn + Gunicorn | latest | ASGI workers |
| Auth | python-jose / PyJWT | latest | JWT generation/validation |
| Password | passlib + bcrypt | latest | Hash seguro |
| Estadísticas | scipy + numpy | latest | Distribución de Poisson, cálculos |
| Testing | pytest + pytest-asyncio | latest | |
| Linting | ruff + mypy | latest | Fast linting, type checking |

### 5.2 Fase 2 — Adiciones

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Frontend Framework | Next.js 15 (App Router) | SSG, ISR, Server Components |
| UI Components | Shadcn/UI + Tailwind | Design system consistente |
| Estado cliente | TanStack Query | Caching, sincronización servidor |
| Gráficos | Recharts | Ligero, customizable |
| Hosting frontend | Netlify | CI/CD integrado, edge functions |
| Hosting backend | Railway o Fly.io | Simple, PostgreSQL managed opcional |
| DB Managed | Neon PostgreSQL | Serverless, branching, free tier |
| Cache Managed | Upstash Redis | Serverless, pay-per-use |
| Storage | Cloudflare R2 | S3-compatible, sin egress fees |
| Emails | SendGrid | Deliverability, templates |
| Monitoring | Sentry + Grafana Cloud | Error tracking + métricas |
| CI/CD | GitHub Actions | |

### 5.3 Fase 3 — Adiciones ML

| Tecnología | Propósito |
|-----------|-----------|
| MLflow | Experiment tracking, model registry |
| Scikit-learn / LightGBM | Modelos ML supervisados |
| Pandas / Polars | Feature engineering en datasets grandes |
| Apache Airflow | Orchestración de pipelines complejos |
| dbt | Transformaciones SQL versionadas |

---

## 6. PATRONES ARQUITECTÓNICOS APLICADOS

### 6.1 Repository Pattern
- Separa la lógica de acceso a datos de la lógica de negocio
- Permite testear servicios con mocks de repositorios
- Facilita cambiar el motor de base de datos sin tocar servicios

### 6.2 Service Layer Pattern
- Contiene toda la lógica de negocio
- Los endpoints solo validan input, llaman servicios y formatean respuestas
- Los servicios no conocen nada de HTTP (sin Request/Response objects)

### 6.3 Unit of Work (implícito vía SQLAlchemy Session)
- Cada request HTTP opera en una única sesión de base de datos
- Las transacciones se abren al inicio y se cierran (commit/rollback) al final

### 6.4 Strategy Pattern — Motor de Predicciones
- `BasePredictionModel` define la interfaz
- `PoissonModel`, `LogisticModel`, `XGBoostModel` implementan la estrategia
- El servicio de predicciones delega sin saber qué modelo usa

### 6.5 Transformer Pattern — ETL
- Cada fuente externa tiene su propio Transformer
- El Transformer convierte de JSON externo a objetos del dominio interno
- Nuevo proveedor = nuevo Transformer sin tocar el repositorio

---

## 7. CONSIDERACIONES DE SEGURIDAD ARQUITECTÓNICA

### 7.1 Defensa en Profundidad

```
Capa 1: Red     → Firewall, HTTPS obligatorio, Cloudflare WAF
Capa 2: App     → Autenticación JWT, Rate Limiting, CORS configurado
Capa 3: Datos   → ORM (no raw SQL), parámetros bound, permisos DB mínimos
Capa 4: Infra   → Secretos en env vars / Vault, contenedores sin root
```

### 7.2 Política de Secretos

```
# MVP (Docker)
Variables de entorno en .env (excluido de git con .gitignore)
docker-compose.yml referencia ${VAR} sin hardcodear valores

# Fase 2 (Cloud)
Railway / Fly.io: secrets management nativo
GitHub Actions: GitHub Secrets
Frontend (Netlify): Environment variables en dashboard
```

### 7.3 Usuario de Base de Datos con Mínimos Privilegios

```sql
-- Usuario de aplicación: solo DML sobre schema app
CREATE ROLE app_user LOGIN PASSWORD '...';
GRANT CONNECT ON DATABASE sip_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;

-- Usuario de migraciones: DDL completo
CREATE ROLE migration_user LOGIN PASSWORD '...';
GRANT ALL ON DATABASE sip_db TO migration_user;
```

---

## 8. OBSERVABILIDAD

### 8.1 Logging (Estructura JSON)

```json
{
  "timestamp": "2026-06-12T10:00:00Z",
  "level": "INFO",
  "service": "api",
  "module": "etl.jobs.sync_fixtures",
  "trace_id": "abc123",
  "user_id": null,
  "message": "Fixtures sync completed",
  "context": {
    "league_id": 5,
    "records_processed": 12,
    "duration_ms": 345
  }
}
```

### 8.2 Métricas Clave a Exponer

- `api_request_duration_seconds` (histograma por endpoint)
- `etl_job_duration_seconds` (por job y estado)
- `prediction_generated_total` (contador por liga)
- `db_query_duration_seconds` (histograma por query)
- `cache_hit_ratio` (por tipo de recurso)

### 8.3 Health Checks

```
GET /health          → {status: "ok", version: "1.0.0"}
GET /health/ready    → {db: "ok", redis: "ok", external_apis: {api_football: "ok"}}
GET /health/live     → {status: "ok"}
```
