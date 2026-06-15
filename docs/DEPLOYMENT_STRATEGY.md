# DEPLOYMENT STRATEGY
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.1.0 _(revisado por comité de arquitectura 2026-06-12)_
**Fecha:** 2026-06-12
**Estado:** Diseño Pre-Implementación — Aprobado

---

## 1. ENTORNOS

| Entorno | Descripción | Infraestructura |
|---------|-------------|-----------------|
| `local` | Desarrollo en máquina del desarrollador | Docker Compose (2 contenedores) |
| `staging` | Validación antes de producción (Fase 2) | Railway — rama `staging` |
| `production` | Usuarios reales (Fase 2) | Railway + Neon + Upstash |

---

## 2. DOCKER COMPOSE — FASE 1 (MVP LOCAL)

**2 servicios. Sin Redis, sin worker, sin beat, sin Flower.**

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build:
      context: .
      target: development
    ports:
      - "8000:8000"
    volumes:
      - .:/app                         # hot-reload en desarrollo
    environment:
      - DATABASE_URL=postgresql+asyncpg://sip:sip_password@postgres:5432/sip_db
      - SECRET_KEY=${SECRET_KEY}
      - API_FOOTBALL_KEY=${API_FOOTBALL_KEY}
      - FOOTBALL_DATA_KEY=${FOOTBALL_DATA_KEY}
      - ENVIRONMENT=development
      - LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: sip
      POSTGRES_PASSWORD: sip_password
      POSTGRES_DB: sip_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sip -d sip_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

> **Nota Fase 2:** Al migrar a cloud, se agregan servicios `worker` (Celery) y `beat` (Celery Beat) y se introduce Upstash Redis como broker. Esto es un sprint de trabajo cuando el cloud lo requiera.

---

## 3. DOCKERFILE

```dockerfile
# Dockerfile
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# ─── development ──────────────────────────────────────────────
FROM base AS development

RUN uv sync --frozen      # incluye dev dependencies

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ─── production ───────────────────────────────────────────────
FROM base AS production

COPY . .

# Ejecutar migraciones y arrancar la app
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
```

---

## 4. VARIABLES DE ENTORNO

```bash
# .env.example

# ── Aplicación ──────────────────────────────────────────────────
ENVIRONMENT=development                      # development | production
SECRET_KEY=change_me_to_a_random_64_char_string
LOG_LEVEL=INFO

# ── Base de datos ───────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://sip:sip_password@postgres:5432/sip_db

# ── JWT ─────────────────────────────────────────────────────────
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── APIs externas ───────────────────────────────────────────────
API_FOOTBALL_KEY=your_rapidapi_key_here
FOOTBALL_DATA_KEY=your_footballdata_key_here
THE_ODDS_API_KEY=your_odds_api_key_here

# ── ETL Scheduler ───────────────────────────────────────────────
ETL_SYNC_FIXTURES_INTERVAL_HOURS=6
ETL_SYNC_RESULTS_INTERVAL_HOURS=1
ETL_ENABLED_LEAGUES=la-liga,premier-league    # slugs separados por coma

# ── Observabilidad ──────────────────────────────────────────────
SENTRY_DSN=                                   # vacío en desarrollo

# ── CORS (Fase 2) ───────────────────────────────────────────────
# ALLOWED_ORIGINS=https://tu-app.netlify.app,https://sip.com
```

---

## 5. MAKEFILE

```makefile
# Makefile

.PHONY: up down restart logs shell test migrate lint

# ── Docker ──────────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart api

logs:
	docker compose logs -f api

shell:
	docker compose exec api python

# ── Base de datos ───────────────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

migration:
	docker compose exec api alembic revision --autogenerate -m "$(name)"

rollback:
	docker compose exec api alembic downgrade -1

# ── Tests ────────────────────────────────────────────────────────
test:
	docker compose exec api pytest -v

test-cov:
	docker compose exec api pytest --cov=app --cov-report=term-missing

# ── Calidad ──────────────────────────────────────────────────────
lint:
	docker compose exec api ruff check app tests
	docker compose exec api ruff format --check app tests

format:
	docker compose exec api ruff format app tests

# ── ETL Manual ───────────────────────────────────────────────────
sync-fixtures:
	docker compose exec api python -c "import asyncio; from app.etl.jobs.sync_fixtures import sync_fixtures; asyncio.run(sync_fixtures())"

sync-results:
	docker compose exec api python -c "import asyncio; from app.etl.jobs.sync_results import sync_results; asyncio.run(sync_results())"
```

---

## 6. CI/CD — GITHUB ACTIONS (FASE 1: CI + BUILD)

En Fase 1, CI corre en cada PR y push a `main`. El deploy es manual o via `make up` en el servidor local.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: sip
          POSTGRES_PASSWORD: sip_password
          POSTGRES_DB: sip_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Install dependencies
        run: uv sync --frozen

      - name: Lint
        run: |
          uv run ruff check app tests
          uv run ruff format --check app tests

      - name: Run migrations
        env:
          DATABASE_URL: postgresql+asyncpg://sip:sip_password@localhost:5432/sip_test
        run: uv run alembic upgrade head

      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://sip:sip_password@localhost:5432/sip_test
          SECRET_KEY: test_secret_key_for_ci_only
          ENVIRONMENT: testing
        run: uv run pytest --cov=app --cov-report=xml -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build --target production -t sip-api:${{ github.sha }} .

      - name: Smoke test image
        run: |
          docker run --rm -e DATABASE_URL=postgresql+asyncpg://x:x@localhost/x \
            -e SECRET_KEY=smoke_test sip-api:${{ github.sha }} python -c "from app.main import app; print('OK')"
```

---

## 7. CI/CD — GITHUB ACTIONS FASE 2 (CON DEPLOY A RAILWAY)

```yaml
# .github/workflows/deploy.yml (Fase 2)
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: [test]          # reutiliza el job de test del ci.yml

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: sip-api
```

---

## 8. CONFIGURACIÓN NETLIFY (FASE 2 — NEXT.JS)

```toml
# netlify.toml
[build]
  base    = "frontend/"
  command = "npm run build"
  publish = ".next"

[build.environment]
  NEXT_PUBLIC_API_URL = "https://api.sip.com"
  NODE_VERSION        = "20"

[[redirects]]
  from   = "/api/*"
  to     = "https://api.sip.com/api/:splat"
  status = 200

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options        = "DENY"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy        = "strict-origin-when-cross-origin"
```

---

## 9. RUNBOOK DE OPERACIONES

### 9.1 Arranque inicial del proyecto

```bash
# 1. Clonar repositorio
git clone https://github.com/org/sports-intelligence-platform
cd sports-intelligence-platform

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con las API keys reales

# 3. Levantar contenedores y crear schema
make up
make migrate

# 4. Verificar health
curl http://localhost:8000/health
# → {"status": "ok", "db": "ok", "scheduler": "running"}

# 5. Ejecutar primer sync manual
make sync-fixtures

# 6. Verificar datos en BD
make shell
# >>> from app.database import SessionLocal
# >>> # consultar tablas...
```

### 9.2 Diagnóstico de jobs ETL fallidos

```bash
# Ver últimas 10 ejecuciones
curl http://localhost:8000/api/v1/admin/etl/jobs?per_page=10 \
  -H "Authorization: Bearer <admin_token>"

# Forzar re-ejecución de un job específico
curl -X POST http://localhost:8000/api/v1/admin/etl/jobs/trigger \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"job_name": "sync_fixtures", "league_slug": "la-liga"}'
```

### 9.3 Rollback de migración de base de datos

```bash
# Ver historial de migraciones
docker compose exec api alembic history

# Retroceder una migración
make rollback

# O a una revisión específica
docker compose exec api alembic downgrade 001_initial_schema
```

### 9.4 Logs en tiempo real

```bash
# Todos los servicios
make logs

# Solo errores
docker compose logs -f api | grep -E '"level":"ERROR|CRITICAL"'
```

---

## 10. CHECKLIST DE PRODUCCIÓN (FASE 2)

Antes de hacer go-live en cloud, verificar:

**Seguridad:**
- [ ] `SECRET_KEY` es un string aleatorio de 64+ caracteres (no el de `.env.example`)
- [ ] `ENVIRONMENT=production` en variables del provider
- [ ] HTTPS forzado (Railway y Netlify lo hacen automáticamente)
- [ ] CORS configurado solo para dominios propios
- [ ] `SENTRY_DSN` configurado con DSN de producción

**Base de datos:**
- [ ] Backup automático configurado en Neon/Supabase
- [ ] `alembic upgrade head` ejecutado en la BD de producción
- [ ] Índices de búsqueda (`pg_trgm`) creados

**Funcionalidad:**
- [ ] `GET /health` devuelve 200 con scheduler running
- [ ] Login, refresh y logout funcionan end-to-end en prod
- [ ] Al menos un job ETL ejecutado manualmente y registrado en `etl_job_logs`
- [ ] Predicciones generadas para próximos partidos

**Monitoreo:**
- [ ] Sentry recibe eventos de error de producción
- [ ] Alertas configuradas en el provider de cloud (CPU, memoria, errores)
- [ ] Rate limiting activo (verificar respuesta 429)
