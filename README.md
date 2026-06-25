# Sports Intelligence Platform

Plataforma de inteligencia deportiva predictiva para fútbol — análisis estadístico, predicciones con modelo Poisson y analytics de equipos y jugadores.

**Stack MVP:** FastAPI · PostgreSQL 16 · SQLAlchemy 2.0 · Alembic · APScheduler · Docker Compose

---

## Quickstart

### Prerrequisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Git

### 1. Clonar y configurar variables de entorno

```bash
git clone https://github.com/tu-usuario/sports-intelligence-platform.git
cd sports-intelligence-platform

cp .env.example .env
```

Edita `.env` y al menos genera una `SECRET_KEY`:

```bash
# Genera una clave segura (Python requerido localmente)
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Levantar los contenedores

```bash
make up
```

Esto:
1. Construye la imagen Docker
2. Arranca PostgreSQL 16
3. Espera a que PostgreSQL esté saludable
4. Arranca FastAPI con hot-reload

### 3. Ejecutar migraciones

```bash
make migrate
```

Crea todas las tablas definidas en `docs/DATABASE_DESIGN.md`.

### 4. Verificar que todo funciona

```
http://localhost:8000          → Responde 404 (no hay ruta en /)
http://localhost:8000/health   → {"status":"ok","db":"ok","scheduler":"running"}
http://localhost:8000/docs     → Swagger UI interactivo
http://localhost:8000/redoc    → Documentación ReDoc
```

---

## Comandos disponibles

```bash
make help          # Ver todos los comandos

# Docker
make up            # Levantar contenedores
make down          # Detener y eliminar contenedores
make restart       # Reiniciar solo el API
make logs          # Ver logs en tiempo real
make build         # Reconstruir imágenes

# Base de datos
make migrate       # Aplicar migraciones pendientes
make migration name="descripcion"  # Crear nueva migración (autogenerate)
make rollback      # Revertir última migración
make psql          # Abrir consola PostgreSQL interactiva

# Tests
make test          # Ejecutar todos los tests
make test-cov      # Tests con reporte de cobertura

# Calidad de código
make lint          # Verificar con ruff
make format        # Formatear con ruff

# Shell
make shell         # Abrir Python shell dentro del contenedor
```

---

## Estructura del proyecto

```
sports-intelligence-platform/
├── app/
│   ├── main.py              # FastAPI app factory + APScheduler lifespan
│   ├── config.py            # Settings con pydantic-settings
│   ├── database.py          # Engine async, SessionLocal, get_db
│   ├── api/
│   │   ├── dependencies.py  # get_current_user, require_pro, require_admin
│   │   └── v1/
│   │       ├── router.py    # Agrega sub-routers (Sprint 4+)
│   │       └── health.py    # GET /health y GET /health/ready
│   ├── core/
│   │   ├── logging.py       # Logging JSON estructurado
│   │   ├── exceptions.py    # SIPException + handlers
│   │   ├── security.py      # JWT, bcrypt, refresh tokens
│   │   └── slug.py          # slugify()
│   ├── models/              # SQLAlchemy ORM (describe la BD)
│   ├── schemas/             # Pydantic v2 (validación + DTOs)
│   ├── services/            # Lógica de negocio (Sprint 4+)
│   ├── repositories/        # Queries SQL (Sprint 2+)
│   ├── etl/                 # Pipeline ETL + APScheduler (Sprint 2+)
│   ├── ml/                  # Motor predictivo Poisson (Sprint 3+)
│   └── web/                 # Jinja2 templates (Sprint 5+)
├── alembic/
│   ├── env.py               # Configuración async de Alembic
│   └── versions/
│       └── 001_initial_schema.py
├── tests/
│   ├── conftest.py          # Fixtures: test_engine, db_session, client
│   └── test_health.py       # Tests del health endpoint y OpenAPI
├── docker-compose.yml       # 2 servicios: api + postgres
├── Dockerfile               # Multi-stage: base → development → production
├── pyproject.toml           # Dependencias con uv
├── requirements.txt         # Dependencias flat (alternativa a uv)
├── alembic.ini
├── Makefile
└── .env.example
```

---

## Tests

Los tests requieren que PostgreSQL esté corriendo (usa el contenedor de Docker):

```bash
# Primera vez: crear la BD de test
make create-test-db

# Ejecutar todos los tests
make test

# Con reporte de cobertura
make test-cov
```

El conftest usa `sip_test` (base de datos separada) para evitar contaminar datos de desarrollo. El schema se crea automáticamente al inicio de la sesión de tests y se elimina al final.

Para CI/CD (GitHub Actions), ver [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development` o `production` |
| `SECRET_KEY` | *(requerida)* | Clave para firmar JWT — cambiar en producción |
| `DATABASE_URL` | `postgresql+asyncpg://sip:sip_password@postgres:5432/sip_db` | URL de la base de datos |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `JWT_ALGORITHM` | `HS256` | Algoritmo JWT (HS256 MVP → RS256 Fase 2) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Expiración del access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Expiración del refresh token |
| `API_FOOTBALL_KEY` | *(vacío)* | API key de API-Football (Sprint 2+) |
| `FOOTBALL_DATA_KEY` | *(vacío)* | API key de Football-Data.org (Sprint 2+) |
| `SENTRY_DSN` | *(vacío)* | DSN de Sentry (Sprint 6+) |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8000` | Orígenes CORS permitidos |

---

## Arquitectura

Ver `docs/ARCHITECTURE.md` para la arquitectura completa.

**Principios clave:**
- API REST diseñada como contrato independiente — tanto Jinja2 (Fase 1) como Next.js (Fase 2) la consumen sin cambios en backend
- APScheduler in-process en Fase 1 → Celery + Redis en Fase 2 (migración de 1 sprint)
- Separación estricta: SQLAlchemy models ≠ Pydantic schemas ≠ API DTOs

---

## Fases del proyecto

| Fase | Stack | Estado |
|------|-------|--------|
| **Fase 1: MVP Local** | FastAPI + Jinja2 + PostgreSQL + APScheduler + Docker | ✅ Bootstrap |
| **Fase 2: Cloud** | + Next.js + Netlify + Neon + Celery + Redis | 🔜 Sprint 7+ |
| **Fase 3: Scale** | + Microservices + Kafka + MLflow + Kubernetes | 🔜 Semana 25+ |

---

## Desarrollo

```bash
# Crear una nueva migración después de modificar modelos
make migration name="add_player_nationality"

# Verificar tipos con mypy (opcional)
docker compose exec api mypy app

# Abrir psql para inspeccionar el schema
make psql
\dt        -- listar tablas
\d matches -- describir tabla matches
```
