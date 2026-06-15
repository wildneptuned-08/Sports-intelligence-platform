# PRODUCT & TECHNICAL ROADMAP
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.1.0 _(revisado por comité de arquitectura 2026-06-12)_
**Fecha:** 2026-06-12
**Horizonte:** 18 meses
**Estado:** Diseño Pre-Implementación — Aprobado

---

## 1. VISIÓN DE LARGO PLAZO

```
2026                    2027                    2027 (Q4+)
──────────────────────────────────────────────────────────────
Fase 1: MVP Local  →  Fase 2: Cloud Managed  →  Fase 3: Scale
(3 meses)             (3-6 meses adicionales)    (6+ meses)

Validación de         Crecimiento de              Plataforma
mercado con           usuarios, primer            enterprise con
datos reales          ingreso recurrente          ML avanzado
```

---

## 2. TIMELINE GANTT (ALTO NIVEL)

```
SEMANA:         1  2  3  4  5  6  7  8  9  10 11 12  13-16  17-20  21-24
                |  |  |  |  |  |  |  |  |  |  |  |   |      |      |
FASE 1 MVP ─────────────────────────────────────────────|
  Sprint 1:     [████████]
  Sprint 2:              [████████]
  Sprint 3:                       [████████]
  Sprint 4:                                [████████]
  Sprint 5:                                         [██████]
  Sprint 6:                                               [██████]

FASE 2 CLOUD ─────────────────────────────────────────────────────────────
  Migración FE:                                            [██████████████]
  Deploy Backend:                                                [█████████]
  DB Managed:                                                    [████████]
  Celery+Redis:                                                  [████████]
  Stripe:                                                              [██]

FASE 3 SCALE ──────────────────────────────────────────────────────────────
  (Semana 25+)
```

---

## 3. FASE 1 — MVP LOCAL (Semanas 1-12)

### Objetivo
Sistema completamente funcional en local que valide la propuesta de valor antes de invertir en infraestructura cloud.

### Hitos

| Hito | Semana | Descripción |
|------|--------|-------------|
| M1.1 | 2 | Docker (2 contenedores) funcional + schema BD creado + APScheduler integrado |
| M1.2 | 4 | ETL sincronizando ligas, equipos y standings automáticamente |
| M1.3 | 6 | Predicciones Poisson generadas para próximos partidos de La Liga |
| M1.4 | 8 | API REST completa con autenticación JWT |
| M1.5 | 10 | Dashboard Jinja2 usable (Home + Equipos + Partidos) |
| **M1.6** | **12** | **MVP completo — Demo con datos reales** |

### Entregables Fase 1

- [ ] Sistema corriendo con `docker compose up` (solo 2 contenedores)
- [ ] 2 ligas con datos completos (La Liga + Premier League)
- [ ] Dashboard web funcional (Jinja2 SSR)
- [ ] API REST documentada en OpenAPI (`/docs`)
- [ ] Modelo Poisson con Brier Score < 0.26
- [ ] Tests con cobertura > 80% en `services/` y `ml/`
- [ ] `README.md` con setup completo en < 15 minutos

### KPIs de Éxito Fase 1

| Métrica | Meta |
|---------|------|
| Ligas activas | 2 |
| Equipos en BD | > 40 |
| Partidos históricos | > 500 |
| Predicciones generadas | > 100 |
| Accuracy modelo 1X2 (histórico) | > 46% |
| Uptime local durante demo (30 min) | 100% |

---

## 4. FASE 2 — CLOUD MANAGED (Semanas 13-24)

### Objetivo
Migrar a infraestructura cloud, lanzar primeros usuarios reales, activar monetización y reemplazar Jinja2 con Next.js.

### 4.1 Bloque A — Deploy Cloud (Semanas 13-16)

**Sprint 7-8: Backend a Cloud + DB Managed + Workers distribuidos**

| Tarea | Descripción |
|-------|-------------|
| Seleccionar provider backend | Railway vs Fly.io: evaluar pricing, DX, regiones |
| Migrar variables de entorno | Usar secrets manager del provider |
| Setup PostgreSQL managed | Neon (serverless + branching) o Supabase |
| **Migrar APScheduler → Celery + Redis** | Agregar Upstash Redis; migrar jobs ETL a Celery tasks; agregar Celery Beat como servicio separado |
| Configurar CI/CD | GitHub Actions: test → build → deploy on push a `main` |
| Setup Sentry | Error tracking y performance monitoring |
| Configurar backups BD | Snapshot diario automático del provider |
| Configurar dominio y SSL | `api.sip.com` → HTTPS obligatorio |

**Migración APScheduler → Celery (detalle):**
```
Fase 1: APScheduler (in-process) → un proceso, suficiente para MVP local
Fase 2: Celery + Celery Beat       → workers distribuidos, reintentos durables,
                                     monitoreo con Flower, escalable en cloud
Effort estimado: 1 sprint de trabajo (~40h)
```

**Hito M2.1 (Semana 16):** Backend funcional en cloud, accesible en URL pública

---

### 4.2 Bloque B — Frontend Next.js (Semanas 15-20)

**Sprint 8-10: Migración de Jinja2 a React/Next.js**

| Tarea | Semana | Descripción |
|-------|--------|-------------|
| Scaffolding Next.js 15 (App Router) | 15 | Setup básico, estructura de carpetas |
| Design System con Shadcn/UI + Tailwind | 15-16 | Tokens de diseño, componentes base |
| Autenticación con custom JWT | 16 | Sesión persistida en cookie httpOnly, fetch wrapper |
| Configurar CORS en FastAPI | 16 | `CORSMiddleware` con whitelist del dominio Netlify |
| Migrar página Home/Dashboard | 17 | Partidos del día + predicciones (SSG + ISR) |
| Migrar página Leagues | 17 | Tabla de posiciones |
| Migrar página Teams | 18 | Perfil + stats + últimos partidos |
| Migrar página Matches | 18 | Detalle + predicciones |
| Migrar página Players | 19 | Perfil + estadísticas |
| Deploy en Netlify | 19 | CI/CD con GitHub, edge network |
| A/B: apuntar 10% tráfico a Next.js | 20 | Feature flag por dominio |
| Migración completa, deprecar Jinja2 | 20 | Go-live completo |

> **Por qué esta migración es fácil:** La API REST del MVP fue diseñada como contrato independiente desde el Sprint 4. El único cambio en backend es agregar `CORSMiddleware`. Jinja2 y Next.js son consumidores intercambiables de la misma API.

**Hito M2.2 (Semana 20):** Frontend Next.js en producción, Jinja2 deprecado

---

### 4.3 Bloque C — Monetización (Semanas 19-24)

**Sprint 11-12: Primeros Ingresos**

| Feature | Descripción | Semana |
|---------|-------------|--------|
| Planes de suscripción (Free/Pro) | Definir features por plan | 19 |
| Integración Stripe | Webhooks, checkout session, portal de cliente | 20-21 |
| Feature gates por plan | Restringir xG, features avanzadas | 21 |
| Migración Alembic: campos OAuth + Stripe en `users` | `oauth_provider`, `stripe_customer_id`, `subscription_status` | 20 |
| Email transaccional (SendGrid) | Bienvenida, renovación, recordatorios | 22 |
| OAuth Google | Registro/login con Google | 22 |
| Landing page de marketing | Pricing, features, testimonios | 23-24 |

**Hito M2.3 (Semana 24):** Primeros 100 usuarios, primeros 5 suscriptores Pro

---

### 4.4 Bloque D — Expansión de Datos (Paralelo con B y C)

| Feature | Semana |
|---------|--------|
| Agregar Liga BetPlay Colombia | 17 |
| Agregar Champions League | 18 |
| Agregar Serie A + Bundesliga | 20 |
| Estadísticas de jugadores más completas | 21 |
| Datos históricos 5 temporadas | 22 |
| Odds en tiempo real (The Odds API) | 22 |

### KPIs de Éxito Fase 2

| Métrica | Meta (Semana 24) |
|---------|-----------------|
| Usuarios registrados | 500 |
| Usuarios activos semanales | 150 |
| Suscriptores Pro | 20 |
| MRR | $200 USD |
| Ligas activas | 6 |
| Accuracy modelo 1X2 | > 50% |
| Uptime (SLA) | > 99.5% |
| p95 latencia API | < 200ms |

---

## 5. FASE 3 — ESCALA (Semanas 25-52)

### 5.1 Mejoras de Modelo ML (Semanas 25-36)

| Trimestre | Modelo | Features | Mejora esperada |
|-----------|--------|----------|----------------|
| Q3 2026 | Regresión Logística | 30 features: forma, H2H, lesiones, fatiga | +2-3% accuracy |
| Q4 2026 | XGBoost/LightGBM | 60+ features: xG por partido, PPDA, formaciones | +3-5% accuracy |
| Q1 2027 | Ensemble | Combinación calibrada Poisson + XGBoost | +1-2% accuracy |
| Q2 2027 | LSTM | Serie temporal de forma y momentum | +1-3% accuracy |

MLflow para tracking de experimentos desde el inicio de Fase 3.

---

### 5.2 Real-Time Data (Semanas 29-36)

| Feature | Descripción |
|---------|-------------|
| WebSocket API | Actualizaciones de score y eventos durante partidos |
| Predicciones en vivo | Recalcular probabilidades con cada gol/tarjeta |
| Push notifications | Browser push para equipos favoritos |

---

### 5.3 Funcionalidades Enterprise (Semanas 33-48)

| Feature | Plan | Descripción |
|---------|------|-------------|
| API pública con API Keys | Pro/Enterprise | Acceso programático con rate limits |
| Reportes PDF automatizados | Pro | Previa de partido, análisis de temporada |
| Exportación de datos (CSV) | Pro | Stats históricas en bulk |
| Dashboard personalizable | Pro | Widgets drag-and-drop |
| Alertas configurables | Pro | Email/Push por threshold de valor bet |
| White-label | Enterprise | Plataforma con branding del cliente |

---

### 5.4 Arquitectura Técnica Fase 3

| Cambio | Motivación | Semana |
|--------|-----------|--------|
| Separar ETL service | Escala independiente de la API | 30 |
| Kafka para eventos | Desacoplar sincronización de resultados | 32 |
| dbt para transformaciones SQL | Datos más limpios para ML | 30 |
| Airflow (reemplaza Celery Beat) | Pipelines ML complejos con dependencias | 34 |
| Read replica PostgreSQL | Descargar queries analíticos | 28 |
| Elasticsearch | Búsqueda full-text de jugadores y equipos | 36 |
| CDN para assets estáticos | Imágenes de escudos y jugadores | 26 |

### KPIs de Éxito Fase 3

| Métrica | Meta (Semana 52) |
|---------|-----------------|
| Usuarios registrados | 5,000 |
| MRR | $2,000+ USD |
| Suscriptores Pro | 100+ |
| Ligas activas | 12+ |
| Accuracy modelo 1X2 | > 53% |
| p95 latencia API | < 100ms |
| Uptime | > 99.9% |

---

## 6. EVOLUCIÓN DE LA STACK TECNOLÓGICA

```
COMPONENTE        FASE 1 (MVP Local)    FASE 2 (Cloud)         FASE 3 (Scale)
─────────────────────────────────────────────────────────────────────────────
Frontend          Jinja2 (SSR)          Next.js 15 + Netlify   Next.js + CDN
Backend           FastAPI (local)        FastAPI (cloud)        FastAPI + microservicios
Base de datos     PostgreSQL Docker      Neon PostgreSQL        Aurora PostgreSQL
Scheduler/Queue   APScheduler           Celery + Redis          Celery + Airflow
                  (in-process)          (workers distribuidos)
Cache             —                      Upstash Redis           Redis Cluster
ETL               APScheduler jobs       Celery tasks            Servicio separado
ML                scipy/numpy           scipy/numpy cloud       MLflow + LightGBM
Monitoring        Logs JSON + Sentry     Sentry + Grafana        DataDog/New Relic
Storage           Disco local            Cloudflare R2           R2 + CDN
Auth              JWT HS256              JWT RS256 + Google      Auth0 (evaluar)
Emails            —                      SendGrid                SendGrid
Pagos             —                      Stripe                  Stripe
CI/CD             GitHub Actions         GitHub Actions          GitHub Actions + ArgoCD
Infra             Docker Compose (2)     Docker + Railway        Kubernetes (EKS/GKE)
Contenedores MVP  api + postgres         api + worker + beat +   múltiples
                  (2 contenedores)       postgres + redis (5)
```

**La transición más importante de Fase 1 → Fase 2 es APScheduler → Celery + Redis.** Es intencionalmente simple en MVP (in-process, sin contenedores extra) y se reemplaza en Fase 2 con workers distribuidos cuando el cloud lo requiere. Effort estimado: 1 sprint.

---

## 7. DECISIONES DE ARQUITECTURA FUTURAS

### Decisión 1: Mobile App (Q4 2026)
- **Opción A:** React Native (compartir lógica con Next.js)
- **Opción B:** Flutter (mejor performance nativa)
- **Decisión:** Evaluar con feedback de usuarios en Fase 2. Priorizar si > 40% del tráfico es móvil.

### Decisión 2: Multi-tenancy Enterprise (Q2 2027)
- **Opción A:** Row-level security en PostgreSQL (RLS)
- **Opción B:** Schema separado por tenant
- **Decisión:** Depende del número de clientes Enterprise y sus requisitos de aislamiento.

### Decisión 3: Datos Propios vs APIs Externas
- Cuando supere 10,000 usuarios activos, evaluar scraping propio + partnerships
- Costo de API-Football escala linealmente; en cierto punto, pipeline propio es más económico

---

## 8. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Bajo engagement en MVP | Media | Alto | Beta privada con 20 usuarios desde Semana 10 |
| Costos cloud superan proyección | Baja | Medio | Budget alert en Railway/Neon; escalar verticalmente primero |
| Competidor lanza producto similar | Media | Medio | Diferenciación en explicabilidad y cobertura latinoamericana |
| API-Football sube precios | Media | Alto | Diversificar fuentes; football-data.org como fallback |
| Dificultad para conseguir Pro | Media | Alto | Trial Pro 30 días; colectar testimonios desde beta |

---

## 9. MÉTRICAS DE NEGOCIO A SEGUIR DESDE DÍA 1

```
ACQUISITION:
  - Usuarios registrados por semana
  - Canales: orgánico, redes sociales, comunidades fútbol

ACTIVATION:
  - % usuarios que ven una predicción en primera sesión
  - % usuarios que agregan un equipo favorito

RETENTION:
  - DAU / MAU ratio
  - Retención semana 1, semana 4

REVENUE:
  - Free-to-Pro conversion rate (objetivo: > 2%)
  - MRR y crecimiento mensual
  - Churn mensual Pro (objetivo: < 5%)

REFERRAL:
  - NPS (Net Promoter Score)
  - Usuarios que refieren por invitación
```
