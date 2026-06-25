# MVP BACKLOG
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.1.0 _(revisado por comité de arquitectura 2026-06-12)_
**Fecha:** 2026-06-12
**Metodología:** Scrum — Sprints de 2 semanas
**Total:** 6 sprints = 12 semanas

---

## LEYENDA

| Símbolo | Significado |
|---------|-------------|
| 🔴 | Crítico — bloqueante para el sprint |
| 🟡 | Alta prioridad |
| 🟢 | Normal |
| `[Nh]` | Estimación en horas |

---

## ÉPICAS

| ID | Épica | Descripción |
|----|-------|-------------|
| E1 | Infraestructura Base | Docker (2 contenedores), BD, migraciones, APScheduler |
| E2 | ETL Datos Estructurales | Ligas, equipos, jugadores, temporadas |
| E3 | ETL Resultados y Predicciones | Fixtures, resultados, modelo Poisson |
| E4 | API REST + Auth | Todos los endpoints REST con JWT |
| E5 | Dashboard Jinja2 | Frontend SSR funcional |
| E6 | Calidad y Producción | Tests, Sentry, documentación |

---

## SPRINT 1 — Infraestructura y Modelo de Datos (Semanas 1-2)

**Objetivo:** Entorno de desarrollo funcional con base de datos creada y APScheduler integrado.

### Infraestructura

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-001 | Crear repositorio GitHub, estructura de carpetas, `.gitignore` | E1 | 2h | 🔴 |
| T-002 | Configurar `pyproject.toml` con uv y dependencias del MVP | E1 | 2h | 🔴 |
| T-003 | Crear `Dockerfile` multi-stage (base / dev / prod) | E1 | 3h | 🔴 |
| T-004 | Crear `docker-compose.yml` con **2 servicios**: api + postgres | E1 | 2h | 🔴 |
| T-005 | Configurar `app/config.py` con pydantic-settings + `.env.example` | E1 | 2h | 🔴 |
| T-006 | Configurar `app/database.py`: engine async, SessionLocal, `get_db` | E1 | 2h | 🔴 |
| T-007 | Integrar APScheduler en `app/main.py`: startup/shutdown hooks | E1 | 3h | 🔴 |
| T-008 | Configurar logging estructurado JSON (`app/core/logging.py`) | E1 | 2h | 🟡 |
| T-009 | Crear `Makefile` con comandos: `up`, `down`, `migrate`, `test`, `shell` | E1 | 2h | 🟡 |

### Base de Datos

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-010 | Crear modelos SQLAlchemy: `competition.py` (Country, League, Season, LeagueSeason) | E1 | 3h | 🔴 |
| T-011 | Crear modelos SQLAlchemy: `team.py` (Team, Venue, TeamAlias, TeamLeagueSeason, Standing) | E1 | 3h | 🔴 |
| T-012 | Crear modelos SQLAlchemy: `player.py` (Player, PlayerTeamContract, PlayerSeasonStats) | E1 | 3h | 🔴 |
| T-013 | Crear modelos SQLAlchemy: `match.py` (Match, MatchTeamStats, MatchEvent, MatchPlayerStats, Lineup) | E1 | 4h | 🔴 |
| T-014 | Crear modelos SQLAlchemy: `prediction.py` (Prediction, Odds) | E1 | 2h | 🔴 |
| T-015 | Crear modelos SQLAlchemy: `user.py` (User, RefreshToken, UserFavoriteTeam, UserFavoriteLeague) | E1 | 3h | 🔴 |
| T-016 | Crear modelos SQLAlchemy: `etl.py` (ETLJobLog) | E1 | 1h | 🔴 |
| T-017 | Configurar Alembic: `alembic.ini`, `env.py` async-compatible | E1 | 2h | 🔴 |
| T-018 | Generar migración inicial `001_initial_schema.py` y verificar con `alembic upgrade head` | E1 | 2h | 🔴 |
| T-019 | Crear migración de seeds `003_seed_leagues_and_countries.py` (países y ligas activas) | E1 | 2h | 🟡 |
| T-020 | Crear índices en migración `002_add_search_indexes.py` | E1 | 2h | 🟡 |

**Criterios de Aceptación Sprint 1:**
- [ ] `docker compose up` levanta api y postgres sin errores
- [ ] `alembic upgrade head` crea todas las tablas correctamente
- [ ] `GET /health` devuelve `{"status": "ok", "db": "ok", "scheduler": "running"}`
- [ ] APScheduler arranca y muestra jobs registrados en logs al startup
- [ ] Sin referencias a Celery, Redis ni `django_celery_beat` en ningún archivo

**Velocidad estimada:** 44h de desarrollo

---

## SPRINT 2 — ETL Datos Estructurales (Semanas 3-4)

**Objetivo:** Pipeline ETL funcional para ligas, equipos y jugadores desde API-Football.

### Fetchers y Transformers

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-021 | Implementar `BaseFetcher` con httpx: retry exponencial, timeout, logging | E2 | 4h | 🔴 |
| T-022 | Implementar `APIFootballFetcher`: auth con RapidAPI key, endpoints básicos | E2 | 4h | 🔴 |
| T-023 | Implementar `FootballDataFetcher`: auth con token, endpoints de ligas europeas | E2 | 3h | 🟡 |
| T-024 | Implementar `TeamTransformer.from_api_football()` + `from_football_data()` | E2 | 4h | 🔴 |
| T-025 | Implementar `MatchTransformer.from_api_football()` + `from_football_data()` | E2 | 4h | 🔴 |
| T-026 | Implementar `PlayerTransformer.from_api_football()` | E2 | 3h | 🟡 |

### Repositorios Base

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-027 | Implementar `BaseRepository` con `upsert` genérico via ON CONFLICT | E2 | 3h | 🔴 |
| T-028 | Implementar `TeamRepository`: `find_by_slug`, `find_by_external_id`, `upsert_from_external` | E2 | 3h | 🔴 |
| T-029 | Implementar `MatchRepository`: `find_upcoming`, `find_by_slug`, `upsert_from_external` | E2 | 3h | 🔴 |

### Jobs ETL Estructurales

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-030 | Implementar job `sync_fixtures`: sincroniza ligas activas con APScheduler (cada 6h) | E2 | 4h | 🔴 |
| T-031 | Implementar job `sync_standings`: actualiza tabla de posiciones (diario 04:00) | E2 | 3h | 🟡 |
| T-032 | Implementar auditoría en `etl_job_logs` para todos los jobs (INSERT al inicio, UPDATE al fin) | E2 | 3h | 🔴 |
| T-033 | Implementar retry manual desde admin (marcar job FAILED → re-trigger) | E2 | 2h | 🟢 |

**Criterios de Aceptación Sprint 2:**
- [ ] Ejecutar manualmente `sync_fixtures("la-liga")` inserta equipos y fixtures en BD
- [ ] Re-ejecutar el mismo job no duplica registros (upsert correcto)
- [ ] Cada ejecución registra entrada en `etl_job_logs` con estado, duración y registros procesados
- [ ] APScheduler ejecuta `sync_fixtures` automáticamente cada 6 horas (verificar en logs)

**Velocidad estimada:** 40h de desarrollo

---

## SPRINT 3 — ETL Resultados y Motor de Predicciones (Semanas 5-6)

**Objetivo:** Resultados de partidos sincronizados y predicciones Poisson generadas.

### ETL Resultados

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-034 | Implementar job `sync_results`: actualiza scores, stats y eventos post-partido (cada 1h) | E3 | 5h | 🔴 |
| T-035 | Implementar `sync_player_stats`: estadísticas individuales por partido | E3 | 4h | 🟡 |
| T-036 | Implementar `sync_lineups`: lineups confirmados de partidos próximos | E3 | 3h | 🟡 |
| T-037 | Implementar `sync_odds`: captura de cuotas de The Odds API | E3 | 3h | 🟢 |
| T-038 | Implementar job `cleanup_old_tokens`: limpia refresh_tokens expirados diariamente 03:00 | E3 | 2h | 🟡 |

### Motor de Predicciones

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-039 | Implementar `PoissonModel` en `app/ml/poisson_model.py`: cálculo bivariado con scipy | E3 | 6h | 🔴 |
| T-040 | Implementar `features.py`: extracción de features (form, H2H, medias de goles) | E3 | 5h | 🔴 |
| T-041 | Implementar `evaluation.py`: Brier score, log loss, accuracy 1X2 | E3 | 3h | 🟡 |
| T-042 | Implementar `PredictionRepository`: `create`, `find_by_match`, `find_history_paginated` | E3 | 3h | 🔴 |
| T-043 | Implementar job `generate_predictions`: corre diariamente 08:00, genera para partidos +24h | E3 | 4h | 🔴 |
| T-044 | Implementar `PredictionService`: orquesta features → modelo → persistencia | E3 | 4h | 🔴 |
| T-045 | Verificar constraint `probs_1x2_sum_check` con datos reales (normalizar si es necesario) | E3 | 2h | 🔴 |

**Criterios de Aceptación Sprint 3:**
- [ ] Partido finalizado → `sync_results` actualiza score y stats en < 10 min
- [ ] `generate_predictions` genera predicción 1X2 para todos los partidos de La Liga con +24h de anticipación
- [ ] Probabilidades 1X2 suman entre 0.9999 y 1.0001 (constraint verificado en BD)
- [ ] `etl_job_logs` registra éxito/fallo de todos los jobs de este sprint
- [ ] Cleanup de tokens expirados corre a las 03:00 sin errores

**Velocidad estimada:** 44h de desarrollo

---

## SPRINT 4 — API REST y Autenticación (Semanas 7-8)

**Objetivo:** API REST completa y documentada con autenticación JWT y control de acceso por rol.

### Auth y Seguridad

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-046 | Implementar `app/core/security.py`: JWT encode/decode, bcrypt hash/verify | E4 | 3h | 🔴 |
| T-047 | Implementar `POST /auth/register`: validación, hash password, crear usuario | E4 | 3h | 🔴 |
| T-048 | Implementar `POST /auth/login`: verificar credenciales, emitir access + refresh (cookie) | E4 | 4h | 🔴 |
| T-049 | Implementar `POST /auth/refresh`: rotar refresh token, emitir nuevo access token | E4 | 3h | 🔴 |
| T-050 | Implementar `POST /auth/logout`: revocar refresh token, limpiar cookie | E4 | 2h | 🔴 |
| T-051 | Implementar `POST /auth/change-password`: verificar contraseña actual, revocar todos los tokens | E4 | 3h | 🟡 |
| T-052 | Implementar `api/dependencies.py`: `get_current_user`, `require_pro`, `require_admin` | E4 | 3h | 🔴 |
| T-053 | Configurar slowapi: rate limiting por IP y por usuario | E4 | 2h | 🟡 |

### Endpoints REST

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-054 | Implementar `GET /matches` con filtros (fecha, liga, equipo, status) y paginación | E4 | 4h | 🔴 |
| T-055 | Implementar `GET /matches/{slug}` con stats y eventos | E4 | 3h | 🔴 |
| T-056 | Implementar `GET /matches/{slug}/prediction` con respuesta diferenciada por rol | E4 | 4h | 🔴 |
| T-057 | Implementar `GET /teams`, `GET /teams/{slug}` (declarar ANTES de `GET /teams/compare`) | E4 | 4h | 🔴 |
| T-058 | Implementar `GET /teams/compare` (declarar PRIMERO en el router) | E4 | 3h | 🟡 |
| T-059 | Implementar `GET /players`, `GET /players/{slug}` | E4 | 3h | 🟡 |
| T-060 | Implementar `GET /leagues`, `GET /leagues/{slug}/standings`, `GET /leagues/{slug}/matches` | E4 | 4h | 🔴 |
| T-061 | Implementar `GET /predictions/history` con stats separadas del meta de paginación | E4 | 3h | 🟡 |
| T-062 | Implementar `GET /users/me`, `PATCH /users/me` | E4 | 3h | 🔴 |
| T-063 | Implementar favoritos: `POST /users/me/favorites/teams`, `DELETE …/teams/{slug}`, leagues | E4 | 3h | 🟡 |
| T-064 | Implementar `GET /admin/etl/jobs` y `POST /admin/etl/jobs/trigger` | E4 | 3h | 🟡 |

**Criterios de Aceptación Sprint 4:**
- [ ] Swagger UI en `/docs` muestra todos los endpoints con schemas correctos
- [ ] Login devuelve access token válido y cookie httpOnly con refresh token
- [ ] `GET /matches/{slug}/prediction` devuelve `features: null` para usuario Free y datos completos para usuario Pro
- [ ] `GET /teams/compare` no colisiona con `GET /teams/{slug}` (declaración de ruta correcta verificada)
- [ ] Rate limiting devuelve 429 después del límite configurado
- [ ] Contraseña cambiada invalida todos los refresh tokens activos del usuario

**Velocidad estimada:** 57h de desarrollo

---

## SPRINT 5 — Dashboard Jinja2 (Semanas 9-10)

**Objetivo:** Frontend SSR funcional y usable que consuma la API REST interna.

### Templates Base

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-065 | Crear `templates/base.html`: layout, navbar, footer, variables de contexto | E5 | 4h | 🔴 |
| T-066 | Configurar assets estáticos: Tailwind CSS (via CDN en MVP), iconos | E5 | 3h | 🟡 |
| T-067 | Implementar `app/web/router.py` + `app/web/dependencies.py` (auth desde cookie) | E5 | 3h | 🔴 |

### Páginas

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-068 | Página Home: partidos del día + predicciones destacadas | E5 | 5h | 🔴 |
| T-069 | Página Partidos (`/matches`): listado con filtros básicos (liga, fecha) | E5 | 4h | 🔴 |
| T-070 | Página Detalle de Partido (`/matches/{slug}`): stats, eventos, predicción | E5 | 5h | 🔴 |
| T-071 | Página Liga (`/leagues/{slug}`): tabla de posiciones + próximos partidos | E5 | 4h | 🟡 |
| T-072 | Página Equipo (`/teams/{slug}`): ficha + forma reciente + estadísticas | E5 | 4h | 🟡 |
| T-073 | Páginas Auth: `/login`, `/register` con formularios | E5 | 4h | 🔴 |
| T-074 | Página Perfil (`/profile`): datos de usuario + favoritos + cambio de contraseña | E5 | 3h | 🟡 |
| T-075 | Página Admin ETL (`/admin/etl`): estado de jobs + trigger manual | E5 | 4h | 🟡 |
| T-076 | Mensajes de error: 404, 403, 500 personalizados | E5 | 2h | 🟢 |

**Criterios de Aceptación Sprint 5:**
- [ ] Dashboard muestra partidos del día con predicciones
- [ ] Usuario visitante ve predicciones parciales (solo 1X2); usuario Pro ve predicción completa
- [ ] Formularios de login y registro funcionan end-to-end
- [ ] Cambio de contraseña en `/profile` funciona y cierra otras sesiones
- [ ] Administrador puede ver estado de jobs ETL y ejecutar uno manualmente
- [ ] Páginas de error muestran mensaje útil (no stack trace)

**Velocidad estimada:** 45h de desarrollo

---

## SPRINT 6 — Calidad y Producción (Semanas 11-12)

**Objetivo:** Cobertura de tests > 80% en core, Sentry integrado, documentación completa.

### Testing

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-077 | Configurar `conftest.py`: fixtures `test_db` (PostgreSQL real), `test_client`, factories | E6 | 4h | 🔴 |
| T-078 | Tests unitarios `PoissonModel`: cálculo correcto, normalización de probabilidades | E6 | 3h | 🔴 |
| T-079 | Tests unitarios `TeamTransformer` y `MatchTransformer`: mapeo de fixtures JSON | E6 | 3h | 🔴 |
| T-080 | Tests unitarios `AuthService`: register, login, refresh, logout, change-password | E6 | 4h | 🔴 |
| T-081 | Tests de integración: `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` | E6 | 3h | 🔴 |
| T-082 | Tests de integración: `GET /matches`, `GET /matches/{slug}`, `GET /matches/{slug}/prediction` | E6 | 4h | 🔴 |
| T-083 | Tests de integración: `GET /teams/compare` (verificar no colisión de ruta con `/{slug}`) | E6 | 2h | 🟡 |
| T-084 | Tests de integración: favoritos (POST y DELETE de teams y leagues) | E6 | 3h | 🟡 |
| T-085 | Tests de integración: `PATCH /users/me` y `POST /auth/change-password` | E6 | 2h | 🟡 |
| T-086 | Medir cobertura con `pytest-cov`, alcanzar > 80% en `services/` y `ml/` | E6 | 2h | 🔴 |

### Observabilidad y Producción

| ID | Tarea | Épica | Estimación | Prioridad |
|----|-------|-------|-----------|-----------|
| T-087 | Integrar Sentry SDK: `sentry_sdk.init()` en `main.py`, captura automática de 5xx | E6 | 2h | 🟡 |
| T-088 | Implementar `GET /health` y `GET /health/ready` con checks de BD y scheduler | E6 | 2h | 🔴 |
| T-089 | Optimizar queries N+1 identificadas durante tests de integración | E6 | 4h | 🟡 |
| T-090 | Completar `README.md`: setup local, comandos make, variables de entorno, architecture overview | E6 | 3h | 🟡 |
| T-091 | Configurar GitHub Actions CI: lint (ruff) → test → build Docker image | E6 | 3h | 🟡 |
| T-092 | Demo con datos reales: ejecutar todos los jobs ETL, generar predicciones, revisar dashboard | E6 | 4h | 🔴 |

**Criterios de Aceptación Sprint 6 (Definition of Done del MVP):**
- [ ] `pytest --cov` reporta > 80% de cobertura en `app/services/` y `app/ml/`
- [ ] Sentry captura y alerta en errores 5xx
- [ ] CI de GitHub Actions pasa en cada push a `main`
- [ ] Dashboard muestra predicciones reales de La Liga y Premier League
- [ ] `GET /health` devuelve 200 con estado de BD y scheduler
- [ ] `README.md` permite que un desarrollador nuevo levante el proyecto en < 15 minutos
- [ ] Demo de 30 minutos con datos reales sin caídas

**Velocidad estimada:** 48h de desarrollo

---

## RESUMEN DE ESFUERZO

| Sprint | Semanas | Objetivo | Horas est. |
|--------|---------|----------|-----------|
| Sprint 1 | 1-2 | Infraestructura + BD (2 contenedores, APScheduler) | 44h |
| Sprint 2 | 3-4 | ETL datos estructurales | 40h |
| Sprint 3 | 5-6 | ETL resultados + Poisson | 44h |
| Sprint 4 | 7-8 | API REST + Auth completa | 57h |
| Sprint 5 | 9-10 | Dashboard Jinja2 | 45h |
| Sprint 6 | 11-12 | Tests + Producción | 48h |
| **TOTAL** | **12 semanas** | | **~278h** |

---

## DEFINICIÓN DE DONE (Global)

Un ítem está Done cuando:

1. Código en `main` sin conflictos
2. Tests escritos y pasando (unitarios + integración donde aplica)
3. Sin errores de linter (ruff)
4. Documentado en OpenAPI (si es endpoint) o en docstring (si es función pública)
5. CI de GitHub Actions verde
6. Revisado por el desarrollador en entorno local con datos reales

---

## DEUDA TÉCNICA CONOCIDA Y ACEPTADA

| Deuda | Descripción | Sprint de resolución |
|-------|-------------|---------------------|
| APScheduler single-process | Si el proceso cae, los jobs se detienen. Aceptable en MVP local. | Fase 2 (migrar a Celery+Redis) |
| N+1 queries | Identificadas en Sprint 6; optimización completa en Fase 2 con profiling | Sprint 6 (parcial) / Fase 2 |
| Jinja2 con algo de lógica | Se acepta en MVP; se elimina al migrar a React | Fase 2 |
| Sin cache | Queries analíticos sin cache. Aceptable con < 50 usuarios simultáneos | Fase 2 (Redis L2) |
| Sin particionado de tablas | `player_season_stats` sin particionado. Evaluar con profiling real | Fase 2 |
