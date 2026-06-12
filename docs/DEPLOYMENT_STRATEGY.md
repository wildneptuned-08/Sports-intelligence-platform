# DEPLOYMENT STRATEGY
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.0.0  
**Fecha:** 2026-06-12  
**Estado:** Diseño Pre-Implementación

---

## 1. RESUMEN EJECUTIVO

La estrategia de despliegue sigue el mismo ciclo de tres fases que la arquitectura:

| Fase | Ambiente | Complejidad | Costo Estimado |
|------|----------|-------------|---------------|
| Fase 1 | Local (Docker Compose) | Baja | $0 |
| Fase 2 | Cloud Managed (Railway + Neon + Netlify) | Media | $30-100/mes |
| Fase 3 | Cloud Orquestado (Kubernetes o managed) | Alta | $300-1000/mes |

**Principio rector:** Cada ambiente es reproducible con un solo comando. Ningún paso de despliegue requiere acceso manual a servidores.

---

## 2. AMBIENTES DE EJECUCIÓN

### 2.1 Ambientes Definidos

| Ambiente | Propósito | URL |
|----------|-----------|-----|
| `local` | Desarrollo, testing, demo | http://localhost:8000 |
| `staging` | QA previo a producción (Fase 2) | https://staging-api.sip.com |
| `production` | Usuarios reales | https://api.sip.com |

### 2.2 Variación por Ambiente

| Variable | local | staging | production |
|----------|-------|---------|------------|
| DEBUG | True | False | False |
| LOG_LEVEL | DEBUG | INFO | WARNING |
| POSTGRES_URL | localhost:5432 | Neon branch | Neon main |
| JWT_SECRET | dev-secret | staging-secret | Vault/Secrets Manager |
| CORS_ORIGINS | * | staging.sip.com | sip.com, www.sip.com |
| CELERY_WORKERS | 1 | 2 | 4+ |
| SSL | No | Yes | Yes |

---

## 3. FASE 1 — DESPLIEGUE LOCAL CON DOCKER COMPOSE

### 3.1 Arquitectura de Contenedores

```
docker-compose.yml
├── api          → FastAPI + Uvicorn (puerto 8000)
├── worker       → Celery worker (consume tareas ETL y ML)
├── beat         → Celery beat (scheduler de cron jobs)
├── postgres     → PostgreSQL 16 (puerto 5432)
├── redis        → Redis 7 (puerto 6379)
└── flower       → Celery monitoring UI (puerto 5555) [opcional dev]
```

### 3.2 Configuración `docker-compose.yml`

```yaml
version: "3.9"

services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app             # Hot reload en desarrollo
    environment:
      - DATABASE_URL=postgresql+asyncpg://sip_user:sip_pass@postgres:5432/sip_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - ENVIRONMENT=local
      - DEBUG=true
      - SECRET_KEY=${SECRET_KEY}
      - API_FOOTBALL_KEY=${API_FOOTBALL_KEY}
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    restart: unless-stopped

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql+asyncpg://sip_user:sip_pass@postgres:5432/sip_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    command: celery -A app.core.celery worker --loglevel=info --concurrency=2
    restart: unless-stopped

  beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    volumes:
      - ./backend:/app
    env_file:
      - .env
    depends_on:
      - redis
    command: celery -A app.core.celery beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"              # Solo expuesto localmente
    environment:
      POSTGRES_USER: sip_user
      POSTGRES_PASSWORD: sip_pass
      POSTGRES_DB: sip_db
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sip_user -d sip_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"              # Solo expuesto localmente
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  flower:
    image: mher/flower:2.0
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - redis
    profiles:
      - debug                    # Solo se levanta con: docker compose --profile debug up

volumes:
  pgdata:
  redisdata:
```

### 3.3 Dockerfile Multi-Stage

```dockerfile
# backend/Dockerfile

# ─────────────────────────────
# Stage 1: base
# ─────────────────────────────
FROM python:3.12-slim AS base

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────
# Stage 2: development
# ─────────────────────────────
FROM base AS development

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .
# El código se monta como volumen; este COPY es para la imagen de CI

# ─────────────────────────────
# Stage 3: production
# ─────────────────────────────
FROM base AS production

COPY . .

# Usuario sin privilegios
RUN adduser --disabled-password --no-create-home appuser
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

### 3.4 Archivo `.env.example`

```env
# ─── APLICACIÓN ─────────────────────────────
ENVIRONMENT=local
DEBUG=true
SECRET_KEY=cambia-esto-por-una-clave-segura-de-al-menos-64-chars
LOG_LEVEL=DEBUG

# ─── BASE DE DATOS ──────────────────────────
DATABASE_URL=postgresql+asyncpg://sip_user:sip_pass@postgres:5432/sip_db
DATABASE_URL_SYNC=postgresql://sip_user:sip_pass@postgres:5432/sip_db  # Para Alembic

# ─── REDIS ──────────────────────────────────
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# ─── JWT ────────────────────────────────────
JWT_SECRET_KEY=otro-secreto-para-jwt
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# ─── APIS EXTERNAS ──────────────────────────
API_FOOTBALL_KEY=tu-api-key-de-rapidapi
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
FOOTBALL_DATA_API_KEY=tu-api-key-de-football-data-org
THE_ODDS_API_KEY=tu-api-key-de-the-odds-api

# ─── SENTRY (opcional en local) ─────────────
SENTRY_DSN=

# ─── CORS ───────────────────────────────────
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 3.5 Makefile para Operaciones Frecuentes

```makefile
# Makefile en raíz del proyecto

.PHONY: up down logs shell test migrate seed lint

# ─── Docker ──────────────────────────────────────────
up:
	docker compose up -d

up-debug:
	docker compose --profile debug up -d

down:
	docker compose down

down-volumes:
	docker compose down -v    # Borra datos (cuidado en local)

logs:
	docker compose logs -f api worker

logs-all:
	docker compose logs -f

build:
	docker compose build --no-cache

# ─── Base de Datos ────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

migrate-down:
	docker compose exec api alembic downgrade -1

migrate-create:
	docker compose exec api alembic revision --autogenerate -m "$(name)"

seed:
	docker compose exec api python -m app.scripts.seed_data

# ─── Tests ────────────────────────────────────────────
test:
	docker compose exec api pytest tests/ -v

test-unit:
	docker compose exec api pytest tests/unit/ -v

test-integration:
	docker compose exec api pytest tests/integration/ -v

test-coverage:
	docker compose exec api pytest tests/ --cov=app --cov-report=html

# ─── Calidad de Código ────────────────────────────────
lint:
	docker compose exec api ruff check app/ tests/
	docker compose exec api mypy app/

format:
	docker compose exec api ruff format app/ tests/

# ─── ETL Manual ───────────────────────────────────────
sync-fixtures:
	docker compose exec api python -m app.etl.scripts.sync_fixtures --league laliga-esp

sync-results:
	docker compose exec api python -m app.etl.scripts.sync_results --league laliga-esp

generate-predictions:
	docker compose exec api python -m app.ml.scripts.generate_predictions

# ─── Utilidades ───────────────────────────────────────
shell:
	docker compose exec api python

psql:
	docker compose exec postgres psql -U sip_user -d sip_db

redis-cli:
	docker compose exec redis redis-cli
```

### 3.6 Instrucciones de Setup Local (Primeros Pasos)

```bash
# 1. Clonar repositorio
git clone https://github.com/usuario/sports-intelligence-platform.git
cd sports-intelligence-platform

# 2. Copiar variables de entorno
cp .env.example .env
# Editar .env con tus API keys reales

# 3. Levantar servicios
make up
make build   # Solo la primera vez

# 4. Aplicar migraciones de base de datos
make migrate

# 5. Cargar datos iniciales
make seed

# 6. Sincronizar datos de fuentes externas (primera vez)
make sync-fixtures
make sync-results

# 7. Generar predicciones
make generate-predictions

# 8. Acceder al sistema
# Dashboard: http://localhost:8000
# API Docs:  http://localhost:8000/docs
# Admin ETL: http://localhost:8000/admin/etl
```

---

## 4. FASE 2 — DESPLIEGUE CLOUD MANAGED

### 4.1 Stack de Infraestructura Seleccionada

| Componente | Servicio | Plan | Costo Estimado |
|-----------|---------|------|----------------|
| Backend API | Railway | Starter ($5/mes) | $5-20/mes |
| Worker Celery | Railway | Starter adicional | $5-15/mes |
| PostgreSQL | Neon | Free → Launch ($19/mes) | $0-19/mes |
| Redis | Upstash | Pay-per-use | $0-10/mes |
| Frontend | Netlify | Free → Pro ($19/mes) | $0-19/mes |
| Storage media | Cloudflare R2 | Free tier (10GB) | $0-5/mes |
| Email | SendGrid | Free (100/día) | $0-15/mes |
| Monitoring | Sentry | Free | $0 |
| DNS/SSL | Cloudflare | Free | $0 |
| **Total estimado** | | | **$10-103/mes** |

### 4.2 Pipeline CI/CD con GitHub Actions

```yaml
# .github/workflows/deploy.yml

name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ─── Fase 1: Tests ───────────────────────────────────
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: pip install -r backend/requirements-dev.txt

      - name: Run linting
        run: |
          cd backend
          ruff check app/ tests/
          mypy app/

      - name: Run migrations
        env:
          DATABASE_URL_SYNC: postgresql://test_user:test_pass@localhost:5432/test_db
        run: |
          cd backend
          alembic upgrade head

      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-for-ci
          JWT_SECRET_KEY: test-jwt-key-for-ci
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4

  # ─── Fase 2: Build imagen Docker ─────────────────────
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    permissions:
      contents: read
      packages: write

    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}

    steps:
      - uses: actions/checkout@v4

      - name: Log in to container registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=sha-
            type=raw,value=latest

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          target: production
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ─── Fase 3: Deploy a Railway ─────────────────────────
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@v1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: sip-api

      - name: Run migrations in production
        run: |
          # Usar Railway CLI para ejecutar migración
          railway run --service sip-api alembic upgrade head

      - name: Verify deployment
        run: |
          sleep 30
          curl -f https://api.sip.com/health || exit 1
```

### 4.3 Deploy de Frontend (Netlify)

```toml
# netlify.toml (en la raíz de /frontend)

[build]
  command = "npm run build"
  publish = ".next"

[build.environment]
  NEXT_PUBLIC_API_URL = "https://api.sip.com/api/v1"
  NODE_VERSION = "20"

[[redirects]]
  from = "/api/*"
  to = "https://api.sip.com/api/:splat"
  status = 200

[context.staging]
  environment = { NEXT_PUBLIC_API_URL = "https://staging-api.sip.com/api/v1" }
```

**Deploy automático:** Netlify se conecta al repositorio GitHub. Cada push a `main` dispara build y deploy del frontend automáticamente. Las PRs generan deploy previews.

### 4.4 Gestión de Secretos en Producción

```
NO hacer:
  ❌ Hardcodear secretos en código o Dockerfile
  ❌ Commitear .env a git (excluir con .gitignore)
  ❌ Compartir credenciales por Slack o email

SÍ hacer:
  ✅ Railway: usar "Variables" del servicio en el dashboard
  ✅ Neon: la URL de conexión se obtiene del dashboard, se guarda en Railway
  ✅ GitHub Actions: usar "Repository Secrets" para CI/CD
  ✅ Netlify: usar "Environment Variables" del dashboard
  ✅ API Keys de proveedores: una key por ambiente (dev ≠ prod)

Rotación de secretos:
  - JWT_SECRET_KEY: rotar cada 90 días (invalida todos los tokens activos)
  - API keys externas: rotar si hay sospecha de compromiso
  - Database password: rotar en mantenimientos programados
```

---

## 5. ESTRATEGIA DE BASE DE DATOS

### 5.1 Migraciones Sin Downtime

```
Regla: NUNCA bloquear una tabla de producción en horario de alta actividad.

Para agregar columna nullable:
  → Agregar columna nullable con DEFAULT
  → Hacer backfill en batches (no UPDATE masivo)
  → Agregar constraint NOT NULL en migración separada

Para crear índice en tabla grande:
  → CREATE INDEX CONCURRENTLY (no bloquea lectura/escritura)
  → Verificar pg_stat_activity que no hay queries largas bloqueadas

Para renombrar columna:
  → Fase 1: agregar nueva columna, escribir en ambas
  → Fase 2: migrar lectura a nueva columna
  → Fase 3: eliminar columna antigua
```

### 5.2 Política de Backups

```
Local (Fase 1):
  - pg_dump manual antes de migraciones destructivas
  - Volumen Docker persiste datos entre reinicios

Cloud Neon (Fase 2):
  - Backups automáticos cada 24h (incluido en plan)
  - Point-in-Time Recovery disponible
  - Branches de BD para testing (feature de Neon)

Política de retención:
  - Diarios: 7 días
  - Semanales: 1 mes
  - Mensuales: 6 meses
```

### 5.3 Pool de Conexiones

```
Local (Fase 1):
  SQLAlchemy async pool:
    pool_size = 5
    max_overflow = 10
    pool_timeout = 30s

Cloud (Fase 2+):
  PgBouncer (incluido en Neon) en modo transaction pooling
  Beneficio: reducir conexiones físicas a PostgreSQL
  
  SQLAlchemy config para PgBouncer:
    pool_pre_ping = True
    pool_recycle = 300
    # statement-level prepared statements deben desactivarse
```

---

## 6. MONITOREO Y ALERTAS

### 6.1 Stack de Observabilidad por Fase

| Herramienta | Fase 1 | Fase 2 | Fase 3 |
|-----------|--------|--------|--------|
| Logs | stdout Docker | Sentry + Railway logs | DataDog |
| Errores | stdout | Sentry | Sentry + PagerDuty |
| Métricas | - | Grafana Cloud | DataDog |
| Uptime | Manual | UptimeRobot (gratis) | Pingdom |
| APM | - | Sentry Performance | DataDog APM |

### 6.2 Alertas Críticas a Configurar

| Condición | Umbral | Acción |
|-----------|--------|--------|
| API 5xx rate | > 1% en 5 min | Alerta email |
| API latencia p95 | > 1000ms | Alerta email |
| Job ETL fallido | 3 fallas consecutivas | Alerta email + Slack |
| BD conexiones | > 80% del pool | Alerta |
| Disco (local) | > 85% | Alerta |
| Expiración API key externa | < 7 días | Email recordatorio |

### 6.3 Health Check Endpoints

```
GET /health
→ {
    "status": "ok",
    "version": "1.2.3",
    "environment": "production"
  }

GET /health/ready
→ {
    "status": "ok",
    "components": {
      "database": {"status": "ok", "latency_ms": 12},
      "redis": {"status": "ok", "latency_ms": 2},
      "celery": {"status": "ok", "workers": 4},
      "external_apis": {
        "api_football": {"status": "ok", "requests_remaining": 850},
        "football_data": {"status": "ok"}
      }
    }
  }
```

---

## 7. RUNBOOK DE INCIDENTES

### 7.1 API no responde (5xx masivos)

```
1. Revisar Railway logs: railway logs --service sip-api
2. Verificar /health endpoint desde máquina externa
3. Verificar estado PostgreSQL: SELECT 1
4. Verificar Redis: redis-cli PING
5. Revisar Sentry para stack traces
6. Si es problema de código: rollback a imagen anterior
   railway run --service sip-api railway rollback
```

### 7.2 ETL Job fallando repetidamente

```
1. Revisar EtlJobLog: SELECT * FROM etl_job_logs WHERE status = 'FAILED' ORDER BY started_at DESC LIMIT 10
2. Verificar disponibilidad de API externa
3. Revisar rate limits: headers X-RateLimit-Remaining de la API
4. Si es error de datos: revisar transformer y agregar manejo del caso
5. Retrigger manual: POST /admin/etl/trigger
```

### 7.3 Predicciones no generadas para un partido

```
1. Verificar que el partido existe: GET /matches/{id}
2. Verificar que hay suficientes datos históricos del equipo
3. Revisar logs del worker: celery logs
4. Forzar generación: POST /admin/predictions/generate {"match_id": N}
```

---

## 8. ESTRATEGIA DE ROLLBACK

### 8.1 Rollback de Código (Railway)

```bash
# Ver historial de deploys
railway list --service sip-api

# Rollback a deploy anterior
railway rollback --service sip-api --deployment <deploy-id>
```

### 8.2 Rollback de Migración de BD

```bash
# Revertir última migración
alembic downgrade -1

# Revertir a revisión específica
alembic downgrade <revision_id>
```

**IMPORTANTE:** Solo las migraciones aditivas (nueva columna nullable, nuevo índice) son reversibles sin pérdida de datos. Las migraciones destructivas (DROP COLUMN) requieren backup previo obligatorio.

### 8.3 Ventana de Mantenimiento

```
Horario preferido para cambios riesgosos:
  Lunes a miércoles entre 03:00 y 06:00 UTC
  (menor tráfico; lejos de partidos del fin de semana)

Notificación previa:
  - 24h antes: email a usuarios Pro
  - 1h antes: banner en el dashboard
  - Durante: página de mantenimiento personalizada (Cloudflare)
```

---

## 9. SEGURIDAD EN DEPLOYMENT

### 9.1 Checklist Pre-Deploy

```
□ No hay secretos en el código fuente (grep -r "password\|secret\|api_key" --include="*.py")
□ Dependencias actualizadas (pip-audit o safety check)
□ Tests pasan en CI
□ Variables de entorno de producción verificadas en Railway dashboard
□ CORS configurado correctamente (no '*' en producción)
□ Rate limiting activo
□ HTTPS obligatorio (redirect de HTTP a HTTPS)
□ Headers de seguridad configurados en nginx/Cloudflare
```

### 9.2 Headers de Seguridad HTTP

```nginx
# nginx.conf o equivalente en proxy
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self';" always;
```

### 9.3 Puertos Expuestos

```
Local:
  8000 → API (acceso desde navegador)
  5432 → PostgreSQL (solo acceso desde host para herramientas de BD)
  6379 → Redis (solo acceso desde host)
  5555 → Flower (solo con --profile debug)

Producción:
  80  → Redirige a 443
  443 → HTTPS (Cloudflare/Nginx termina SSL)
  Ningún otro puerto expuesto públicamente
  Base de datos y Redis: VPC privada, sin acceso público
```
