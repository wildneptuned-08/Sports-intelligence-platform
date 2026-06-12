# MVP BACKLOG
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.0.0  
**Fecha:** 2026-06-12  
**Metodología:** Agile / Sprint Planning  
**Sprint Duration:** 2 semanas  
**Objetivo MVP:** Sistema funcional en local con datos reales, predicciones automáticas y dashboard usable

---

## 1. DEFINICIÓN DE MVP

El MVP se considera completado cuando:

1. El sistema ingesta automáticamente datos de al menos 2 ligas (La Liga + Premier League)
2. El modelo Poisson genera predicciones para todos los partidos con +24h de anticipación
3. Un usuario puede registrarse, iniciar sesión y ver el dashboard
4. El dashboard muestra partidos del día con predicciones básicas
5. Los perfiles de equipo muestran estadísticas de la temporada actual
6. Todo corre en local con un solo comando (`docker compose up`)

**No está en scope del MVP:**
- Pagos / Stripe
- OAuth social (Google)
- Websockets / tiempo real
- Generación de PDFs
- Comparador de jugadores
- Métricas avanzadas (xG, PPDA) — dependen de fuentes premium
- Aplicación móvil
- Multi-idioma

---

## 2. ÉPICAS

| ID | Épica | Descripción |
|----|-------|-------------|
| E1 | Infraestructura Base | Setup Docker, PostgreSQL, Redis, FastAPI skeleton |
| E2 | Modelo de Datos | Implementar todas las tablas y relaciones definidas en DATABASE_DESIGN.md |
| E3 | Pipeline ETL | Ingesta automática de datos de fuentes externas |
| E4 | Motor de Predicciones | Modelo Poisson Bivariado + generación automática |
| E5 | API REST | Endpoints definidos en API_DESIGN.md |
| E6 | Autenticación | Registro, login, JWT, roles |
| E7 | Dashboard (Jinja2) | Frontend server-side con Jinja2 y CSS básico |
| E8 | Testing | Tests unitarios e integración para módulos core |
| E9 | Observabilidad | Logging estructurado, health checks, monitoreo ETL |

---

## 3. SPRINT PLAN (6 SPRINTS × 2 SEMANAS)

---

### SPRINT 1 — Infraestructura y Modelo de Datos
**Duración:** Semanas 1-2  
**Objetivo:** Entorno de desarrollo completamente funcional con schema de BD creado

#### Tareas

**E1 — Infraestructura**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-001 | Configurar `docker-compose.yml` con servicios: api, postgres, redis, worker | 3h | Ver DEPLOYMENT_STRATEGY.md |
| T-002 | Crear `Dockerfile` multi-stage para la API (dev + prod) | 2h | Python 3.12 slim |
| T-003 | Setup `pyproject.toml` con dependencias y scripts | 2h | Usar uv o pip-tools |
| T-004 | Configurar `alembic` con `env.py` async-compatible | 2h | SQLAlchemy 2.0 async |
| T-005 | Implementar `core/config.py` con Pydantic BaseSettings | 2h | Variables de entorno |
| T-006 | Implementar `core/database.py` con engine async + SessionLocal | 2h | AsyncSession factory |
| T-007 | Configurar Celery + Redis broker + beat scheduler | 3h | |
| T-008 | Configurar Ruff + Mypy en pre-commit hooks | 1h | |

**E2 — Modelo de Datos**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-010 | Crear modelos SQLAlchemy: `Country`, `League`, `Season`, `LeagueSeason` | 3h | |
| T-011 | Crear modelos SQLAlchemy: `Team`, `TeamAlias`, `TeamLeagueSeason` | 3h | |
| T-012 | Crear modelos SQLAlchemy: `Player`, `PlayerTeamContract` | 2h | |
| T-013 | Crear modelos SQLAlchemy: `Match`, `Venue`, `Referee` | 3h | |
| T-014 | Crear modelos SQLAlchemy: `MatchTeamStats`, `MatchPlayerStats`, `MatchEvent` | 3h | |
| T-015 | Crear modelos SQLAlchemy: `Prediction`, `Odd`, `Standing` | 2h | |
| T-016 | Crear modelos SQLAlchemy: `User`, `RefreshToken`, `ApiKey` | 2h | |
| T-017 | Crear modelos SQLAlchemy: `EtlJobLog`, `ModelPerformance` | 1h | |
| T-018 | Crear migración inicial con Alembic (todas las tablas) | 3h | |
| T-019 | Seed data: países, ligas iniciales, temporadas | 2h | |
| T-020 | Configurar `init.sql` con extensiones PostgreSQL (pg_trgm) | 1h | |

**Criterios de Aceptación Sprint 1:**
- [ ] `docker compose up` levanta todos los servicios sin errores
- [ ] `alembic upgrade head` crea todas las tablas correctamente
- [ ] Las tablas reflejan el diseño de DATABASE_DESIGN.md
- [ ] Seed data poblado en base de datos
- [ ] Health check `/health` responde 200

---

### SPRINT 2 — Pipeline ETL (Fase 1: Datos Estructurales)
**Duración:** Semanas 3-4  
**Objetivo:** Ingesta automática de ligas, equipos y fixtures

#### Tareas

**E3 — ETL Core**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-030 | Implementar `BaseAPIClient` con httpx: retry exponencial, timeout, rate limiting | 4h | |
| T-031 | Implementar `APIFootballClient`: autenticación, endpoints /leagues, /teams, /fixtures | 6h | RapidAPI |
| T-032 | Implementar `TeamTransformer`: mapear JSON de API-Football a modelo de dominio | 4h | Incluir normalización de nombres |
| T-033 | Implementar `LeagueTransformer` y `MatchTransformer` | 4h | |
| T-034 | Implementar `TeamRepository.upsert()`: insertar o actualizar por clave natural | 3h | |
| T-035 | Implementar `MatchRepository.upsert()` | 3h | Idempotente por external_id |
| T-036 | Implementar tarea Celery `sync_leagues_and_teams` | 3h | |
| T-037 | Implementar tarea Celery `sync_fixtures`: sincronizar calendario de partidos | 4h | |
| T-038 | Implementar `EtlJobLog` tracker: registrar inicio, fin, métricas y errores | 2h | |
| T-039 | Configurar Celery Beat: `sync_fixtures` cada 6h, `sync_leagues` cada 24h | 1h | |
| T-040 | Tests unitarios para Transformers (con fixtures JSON mockeados) | 4h | |
| T-041 | Test de integración: run completo de `sync_fixtures` con BD real | 3h | |

**Criterios de Aceptación Sprint 2:**
- [ ] `sync_leagues_and_teams` popula correctamente equipos de La Liga en BD
- [ ] `sync_fixtures` crea fixtures de la temporada actual
- [ ] `EtlJobLog` registra éxitos y fallas correctamente
- [ ] Si la API externa está caída, el job falla graciosamente y registra el error
- [ ] Cobertura de tests Transformers: > 90%

---

### SPRINT 3 — ETL Resultados + Motor de Predicciones
**Duración:** Semanas 5-6  
**Objetivo:** Ingesta de resultados y estadísticas + primera versión del modelo Poisson

#### Tareas

**E3 — ETL Resultados**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-050 | Implementar `sync_results`: actualizar score, estado y ganador de partidos jugados | 5h | |
| T-051 | Implementar `sync_match_stats`: estadísticas de equipo por partido | 5h | |
| T-052 | Implementar `sync_events`: goles, tarjetas, sustituciones | 4h | |
| T-053 | Implementar `sync_lineups`: alineaciones disponibles pre-partido | 3h | |
| T-054 | Implementar `sync_standings`: tabla de posiciones por liga | 3h | |
| T-055 | Configurar Celery Beat: `sync_results` cada 5 min durante partidos en vivo | 2h | Lógica de ventana temporal |

**E4 — Motor de Predicciones**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-060 | Implementar `BasePredictionModel`: interfaz abstracta del modelo | 2h | |
| T-061 | Implementar `TeamFeatureBuilder`: calcular features por equipo (form, goles promedio, localía) | 6h | |
| T-062 | Implementar `PoissonModel.predict()`: calcular prob 1X2, Over/Under, BTTS usando distribución de Poisson bivariada | 8h | scipy.stats.poisson |
| T-063 | Implementar `PoissonModel.predict_top_scorelines()`: top 5 marcadores exactos | 3h | |
| T-064 | Implementar `PredictionRepository.save()` con upsert por (match_id, model_name, version) | 2h | |
| T-065 | Implementar tarea Celery `generate_predictions_for_upcoming`: generar para todos los partidos SCHEDULED +24h | 4h | |
| T-066 | Implementar tarea `resolve_predictions`: después del partido, calcular Brier Score | 3h | |
| T-067 | Tests unitarios del modelo Poisson con datos conocidos | 4h | Verificar que probs suman 1.0 |

**Criterios de Aceptación Sprint 3:**
- [ ] Los resultados de partidos jugados se actualizan automáticamente
- [ ] El modelo Poisson genera predicciones para todos los próximos partidos de La Liga
- [ ] Las probabilidades 1X2 suman exactamente 1.0
- [ ] Las predicciones se resuelven y el Brier Score se calcula post-partido
- [ ] Test del modelo con Liverpool vs Manchester City devuelve probabilidades razonables

---

### SPRINT 4 — API REST y Autenticación
**Duración:** Semanas 7-8  
**Objetivo:** Todos los endpoints definidos en API_DESIGN.md implementados y probados

#### Tareas

**E6 — Autenticación**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-070 | Implementar `UserService`: registro, login, perfil | 4h | |
| T-071 | Implementar `SecurityService`: hash password, generar/validar JWT, refresh tokens | 4h | |
| T-072 | Implementar `RefreshTokenRepository`: crear, validar, revocar | 2h | |
| T-073 | Implementar `auth_middleware`: dependencia FastAPI para extraer user del JWT | 2h | |
| T-074 | Implementar `require_role()`: dependencia de control de acceso por rol | 2h | |
| T-075 | Implementar rate limiter por IP y por usuario | 3h | slowapi o custom |
| T-076 | Endpoints: POST /auth/register, /login, /refresh, /logout, GET /auth/me | 4h | |
| T-077 | Tests de integración de autenticación (full flow) | 4h | |

**E5 — API REST**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-080 | Implementar schemas Pydantic para todos los recursos (matches, teams, players, predictions) | 6h | |
| T-081 | Implementar endpoints GET /leagues, /leagues/{slug}, /leagues/{slug}/standings | 4h | |
| T-082 | Implementar endpoints GET /teams, /teams/{slug}, /teams/{slug}/stats, /teams/compare | 6h | |
| T-083 | Implementar endpoints GET /matches, /matches/today, /matches/{id}, /matches/{id}/stats, /matches/{id}/events | 6h | |
| T-084 | Implementar endpoint GET /matches/{id}/prediction (con estratificación por rol) | 4h | |
| T-085 | Implementar endpoints GET /players, /players/{slug}, /players/{slug}/stats | 4h | |
| T-086 | Implementar endpoints GET /admin/etl/jobs, POST /admin/etl/trigger | 3h | |
| T-087 | Implementar endpoints de favoritos del usuario | 2h | |
| T-088 | Configurar OpenAPI con descripción, tags y ejemplos | 2h | |
| T-089 | Tests de integración para endpoints principales | 6h | pytest + httpx AsyncClient |

**Criterios de Aceptación Sprint 4:**
- [ ] Todos los endpoints responden con el formato de envelope correcto
- [ ] El endpoint de predicción devuelve datos restringidos según rol
- [ ] La autenticación protege correctamente los endpoints /admin/*
- [ ] Rate limiting bloquea correctamente con 429
- [ ] OpenAPI disponible en `/docs` con ejemplos completos

---

### SPRINT 5 — Dashboard Jinja2
**Duración:** Semanas 9-10  
**Objetivo:** Interfaz web funcional consumiendo la propia API REST

#### Tareas

**E7 — Templates Jinja2**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-090 | Setup de templates Jinja2: `base.html` con layout, navbar, footer | 4h | HTML + CSS básico |
| T-091 | Integrar Tailwind CSS vía CDN (sin build step en MVP) | 1h | |
| T-092 | Implementar página `/` (Home/Dashboard): partidos de hoy con predicciones | 6h | |
| T-093 | Implementar página `/login` y `/register` con formularios | 3h | |
| T-094 | Implementar página `/leagues/{slug}`: tabla de posiciones + próximos partidos | 4h | |
| T-095 | Implementar página `/teams/{slug}`: perfil + estadísticas + últimos partidos | 5h | |
| T-096 | Implementar página `/matches/{id}`: detalle de partido + predicción + stats | 5h | |
| T-097 | Implementar página `/players/{slug}`: perfil + estadísticas | 3h | |
| T-098 | Implementar página `/admin/etl`: lista de jobs con opción de reejecutar | 4h | |
| T-099 | Implementar componente de predicción: barras de probabilidad visuales | 3h | SVG o CSS |
| T-100 | Implementar responsive básico (mobile-friendly) | 2h | |
| T-101 | Proteger rutas con middleware de sesión (cookie-based en Jinja2) | 2h | |
| T-102 | Manejo de errores: páginas 404, 500 custom | 1h | |
| T-103 | Favicon, meta tags SEO básico | 1h | |

**Criterios de Aceptación Sprint 5:**
- [ ] Un usuario puede registrarse, iniciar sesión y ver el dashboard
- [ ] El dashboard muestra los partidos del día con probabilidades visualizadas
- [ ] El perfil de equipo muestra estadísticas reales de la temporada
- [ ] El detalle de partido muestra predicción (limitada para Free, completa para Pro)
- [ ] La interfaz funciona correctamente en mobile (responsive básico)

---

### SPRINT 6 — Testing, Pulido y Go-Live Local
**Duración:** Semanas 11-12  
**Objetivo:** MVP estable, bien testeado, documentado y listo para demo

#### Tareas

**E8 — Testing**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-110 | Completar tests unitarios de ServiceLayer (todos los servicios) | 8h | Mock repositories |
| T-111 | Completar tests de integración de ETL jobs | 4h | Base de datos de test |
| T-112 | Tests E2E del flujo de autenticación completo | 3h | |
| T-113 | Tests de accuracy del modelo Poisson con datos históricos reales | 4h | Verificar Brier Score < 0.26 |
| T-114 | Load test básico: 50 usuarios concurrentes al dashboard | 2h | locust |

**E9 — Observabilidad**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-120 | Configurar logging estructurado JSON en todos los módulos | 3h | |
| T-121 | Implementar endpoints /health, /health/ready, /health/live | 2h | |
| T-122 | Dashboard de monitoreo ETL en la interfaz de admin | 3h | |
| T-123 | Alertas en logs para fallas críticas de ETL | 2h | |

**Pulido y Documentación**

| ID | Tarea | Estimación | Notas |
|----|-------|-----------|-------|
| T-130 | Completar `.env.example` con todas las variables necesarias | 1h | |
| T-131 | Crear `Makefile` con comandos frecuentes (up, down, migrate, test, seed) | 2h | |
| T-132 | Revisar y completar `README.md` con instrucciones de setup local | 2h | |
| T-133 | Revisión de seguridad: checklist OWASP básico | 3h | |
| T-134 | Optimización de queries lentos detectados en load test | 4h | EXPLAIN ANALYZE |
| T-135 | Demo de stakeholders: preparar datos de ejemplo atractivos | 2h | |

**Criterios de Aceptación Sprint 6 (MVP Complete):**
- [ ] Cobertura de tests: > 80% en servicios de predicción y ETL
- [ ] `docker compose up && make seed && make migrate` levanta el sistema completamente
- [ ] 0 errores 5xx en flujo normal de uso (10 minutos de demo)
- [ ] El modelo Poisson tiene Brier Score < 0.26 en datos históricos de La Liga
- [ ] `/health/ready` reporta todos los servicios saludables
- [ ] No hay secretos hardcodeados en el código (revisión manual)

---

## 4. BACKLOG DE PRODUCTO (POST-MVP)

Ordenado por prioridad para planificación de sprints futuros:

| Prioridad | Feature | Épica | Esfuerzo |
|-----------|---------|-------|---------|
| Alta | Generación de PDF: previa de partido | Informes | 5 días |
| Alta | Comparador de equipos en la UI | Dashboard | 3 días |
| Alta | Migración frontend a Next.js (Fase 2) | Arquitectura | 4 semanas |
| Alta | OAuth con Google | Autenticación | 2 días |
| Alta | Mejora modelo: Regresión Logística con más features | ML | 2 semanas |
| Media | Suscripciones con Stripe | Monetización | 1 semana |
| Media | Alertas de predicciones por email | Notificaciones | 3 días |
| Media | Estadísticas de jugadores por partido (heatmap) | Analytics | 1 semana |
| Media | Soporte Liga BetPlay Colombia | ETL | 3 días |
| Media | Segunda liga: Champions League | ETL | 3 días |
| Baja | App móvil React Native | Plataforma | 8 semanas |
| Baja | Websockets para partidos en vivo | Tiempo Real | 1 semana |
| Baja | API pública con API Keys | Monetización | 1 semana |

---

## 5. DEFINITION OF DONE (DoD)

Una tarea se considera HECHA cuando:

1. El código está escrito y committeado en la rama correspondiente
2. Los tests relevantes están escritos y pasan (unitarios + integración si aplica)
3. El código pasa Ruff (linting) y Mypy (type checking) sin errores
4. La funcionalidad fue verificada manualmente en el entorno Docker local
5. El PR fue revisado (en equipo) antes de mergear a main
6. Si es un endpoint nuevo: está documentado en OpenAPI
7. Si es un cambio de schema: la migración Alembic está incluida

---

## 6. RIESGOS DE BACKLOG

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| API-Football cambia sus endpoints | Bloquea ETL completamente | Implementar `FootballDataClient` como fallback alternativo desde Sprint 2 |
| Datos insuficientes para entrenar modelo con buen accuracy | Predicciones poco confiables | Usar al menos 2 temporadas históricas; comunicar Brier Score públicamente |
| Sprint 5 (Jinja2) subestimado | Retrasa demo | Priorizar dashboard y match detail; omitir players y comparador para MVP |
| Rate limits de API gratuita (100 req/día) | Limita actualización de datos | Implementar caché agresivo + sync incremental (solo partidos recientes) |
