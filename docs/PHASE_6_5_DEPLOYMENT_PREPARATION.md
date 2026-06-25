# PHASE 6.5 — Production Readiness & Deployment Preparation

**Fecha:** 2026-06-25
**Rama:** `feature/deployment-preparation`
**Estado:** Implementado

---

## 1. Arquitectura de despliegue

```
┌──────────────────┐     HTTPS      ┌──────────────────┐
│  Vercel           │ ─────────────► │  Render           │
│  (Frontend)       │    API calls   │  (Backend)        │
│  Next.js / React  │                │  FastAPI + Docker  │
└──────────────────┘                └────────┬─────────┘
                                              │ asyncpg (TCP/SSL)
                                    ┌────────▼─────────┐
                                    │  Supabase         │
                                    │  PostgreSQL       │
                                    └──────────────────┘
```

## 2. Configuración Render

### 2.1 Crear Web Service

1. Conectar repositorio GitHub
2. **Build Command:** Docker (automático desde `render.yaml`)
3. **Health Check Path:** `/health/ready`
4. **Docker Target:** `production`

### 2.2 Variables de entorno en Render

| Variable | Requerida | Valor |
|----------|-----------|-------|
| `ENVIRONMENT` | Sí | `production` |
| `SECRET_KEY` | Sí | Auto-generado por Render o `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | Sí | Connection string de Supabase (ver §3) |
| `ALLOWED_ORIGINS` | Sí | `https://tu-app.vercel.app` (comma-separated si hay más) |
| `API_FOOTBALL_KEY` | No* | API key de api-sports.io |
| `SENTRY_DSN` | No | DSN de Sentry para error tracking |
| `LOG_LEVEL` | No | `INFO` (default) |
| `PORT` | No | Render lo setea automáticamente |

\* Requerido para que el ETL funcione, pero la app arranca sin él.

### 2.3 render.yaml

El archivo `render.yaml` en la raíz del proyecto permite despliegue Blueprint:
- Render > Dashboard > New > Blueprint > Seleccionar repo
- Configura automáticamente el web service
- Variables marcadas `sync: false` se configuran manualmente en el dashboard

## 3. Configuración Supabase

### 3.1 Obtener connection string

1. Supabase Dashboard → Project → Settings → Database
2. Copiar **Connection string** (URI format)
3. Formato: `postgres://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`

### 3.2 Configurar en Render

El `DATABASE_URL` se normaliza automáticamente:
- `postgres://` → `postgresql+asyncpg://`
- `postgresql://` → `postgresql+asyncpg://`

No es necesario modificar el string manualmente.

### 3.3 Ejecutar migraciones

Las migraciones corren automáticamente al inicio del container (`alembic upgrade head` en el CMD del Dockerfile).

Para ejecutar manualmente:
```bash
# Desde local con la URL de Supabase
DATABASE_URL="postgresql+asyncpg://..." alembic upgrade head
```

### 3.4 Extensiones PostgreSQL

La migración `001_initial_schema.py` crea la extensión `pg_trgm`. Supabase la incluye por defecto.

## 4. Configuración Vercel (Frontend)

### 4.1 Variables de entorno

| Variable | Valor |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://tu-app.onrender.com/api/v1` |

### 4.2 CORS

Agregar el dominio de Vercel a `ALLOWED_ORIGINS` en Render:
```
ALLOWED_ORIGINS=https://tu-app.vercel.app,https://custom-domain.com
```

## 5. Variables de entorno — Referencia completa

### Sensibles (nunca defaults seguros)

| Variable | Default | Validación en producción |
|----------|---------|--------------------------|
| `SECRET_KEY` | `""` | Requerido, mínimo 32 caracteres |
| `DATABASE_URL` | `""` | Requerido, no puede ser localhost |

### Configuración de aplicación

| Variable | Default | Descripción |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development`, `staging`, `production` |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `PORT` | `8000` | Puerto del servidor (Render lo sobreescribe) |
| `ALLOWED_ORIGINS` | `localhost:3000,localhost:8000` | Orígenes CORS permitidos |

### APIs externas

| Variable | Default | Descripción |
|----------|---------|-------------|
| `API_FOOTBALL_KEY` | `""` | API key para api-sports.io |
| `API_FOOTBALL_BASE_URL` | `https://v3.football.api-sports.io` | Base URL |
| `SENTRY_DSN` | `""` | Error tracking DSN |

## 6. Proceso de despliegue

### Primera vez

```
1. Fork/push repo a GitHub
2. Crear proyecto en Supabase → copiar connection string
3. En Render:
   a. New > Blueprint > seleccionar repo
   b. Configurar DATABASE_URL con string de Supabase
   c. Configurar ALLOWED_ORIGINS con dominio Vercel
   d. Deploy
4. Verificar: GET https://tu-app.onrender.com/health/ready
5. En Vercel:
   a. Import repo (frontend)
   b. Configurar NEXT_PUBLIC_API_URL
   c. Deploy
```

### Deploys subsiguientes

```
1. Push a main (o merge PR)
2. Render detecta cambio → rebuild automático
3. Migraciones corren automáticamente
4. Health check valida antes de rutear tráfico
```

## 7. Comportamiento por entorno

| Feature | Development | Staging | Production |
|---------|-------------|---------|------------|
| Swagger `/docs` | Habilitado | Habilitado | Deshabilitado |
| ReDoc `/redoc` | Habilitado | Habilitado | Deshabilitado |
| OpenAPI JSON | Habilitado | Habilitado | Deshabilitado |
| SQL echo | Habilitado | Deshabilitado | Deshabilitado |
| DB pool size | 5 | 10 | 10 |
| Sentry traces | 100% | 100% | 10% |
| SECRET_KEY validation | No | No | Sí (≥32 chars) |
| DATABASE_URL validation | No | No | Sí (no localhost) |

## 8. Troubleshooting

### "SECRET_KEY must be set to a secure random value in production"
Generar una key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Configurar como variable de entorno en Render.

### "DATABASE_URL must be set in production"
Copiar el connection string de Supabase y configurar en Render.

### "DATABASE_URL appears to use a local/Docker address in production"
El string de conexión contiene `localhost` o `postgres:5432`. Usar la URL de Supabase.

### Health check falla en Render
- Verificar que `/health/ready` responde 200 (solo depende de DB, no de scheduler)
- Verificar que `DATABASE_URL` es accesible desde Render
- Verificar que Supabase permite conexiones desde la IP de Render (Settings > Database > Network)

### CORS errors desde Vercel
- Verificar que `ALLOWED_ORIGINS` incluye el dominio exacto de Vercel (con `https://`)
- No incluir trailing slash
- Reiniciar el servicio en Render después de cambiar la variable

### Migraciones fallan en Supabase
- Verificar que la extensión `pg_trgm` está disponible
- Supabase > SQL Editor: `CREATE EXTENSION IF NOT EXISTS pg_trgm;`

### Logs no aparecen en Render
- Verificar `LOG_LEVEL=INFO` (no `WARNING`)
- Los logs son JSON estructurado a stdout — Render los captura automáticamente
