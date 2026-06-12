# PRODUCT & TECHNICAL ROADMAP
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.0.0  
**Fecha:** 2026-06-12  
**Horizonte:** 18 meses  
**Estado:** Diseño Pre-Implementación

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
| M1.1 | 2 | Entorno Docker funcional + Schema BD creado |
| M1.2 | 4 | ETL sincronizando ligas y equipos automáticamente |
| M1.3 | 6 | Predicciones Poisson generadas para próximos partidos de La Liga |
| M1.4 | 8 | API REST completa con autenticación JWT |
| M1.5 | 10 | Dashboard Jinja2 usable (Home + Equipos + Partidos) |
| **M1.6** | **12** | **MVP completo — Demo con datos reales** |

### Entregables Fase 1

- [ ] Sistema corriendo con `docker compose up`
- [ ] 2 ligas con datos completos (La Liga + Premier League)
- [ ] Dashboard web funcional (Jinja2)
- [ ] API REST documentada en OpenAPI
- [ ] Modelo Poisson con Brier Score < 0.26
- [ ] Tests con cobertura > 80% en módulos core
- [ ] `README.md` con instrucciones completas de setup

### KPIs de Éxito Fase 1

| Métrica | Meta |
|---------|------|
| Ligas activas | 2 |
| Equipes en BD | > 40 |
| Partidos históricos | > 500 |
| Predicciones generadas | > 100 |
| Accuracy modelo 1X2 (histórico) | > 46% |
| Uptime local durante demo (30 min) | 100% |

---

## 4. FASE 2 — CLOUD MANAGED (Semanas 13-24)

### Objetivo
Migrar a infraestructura cloud, lanzar primeros usuarios reales, activar monetización y reemplazar Jinja2 con Next.js.

### 4.1 Bloque A — Deploy Cloud (Semanas 13-16)

**Sprint 7-8: Backend a Cloud + DB Managed**

| Tarea | Descripción |
|-------|-------------|
| Seleccionar provider backend | Railway vs Fly.io: evaluar pricing, DX, regiones |
| Migrar variables de entorno | Usar secrets manager del provider |
| Setup PostgreSQL managed | Neon (serverless) o Supabase |
| Setup Redis managed | Upstash (serverless, pay-per-use) |
| Configurar CI/CD | GitHub Actions: test → build → deploy on push to main |
| Setup Sentry | Error tracking y performance monitoring |
| Configurar backups BD | Snapshot diario automático |
| Configurar dominio y SSL | api.sip.com → HTTPS obligatorio |

**Hito M2.1 (Semana 16):** Backend funcional en cloud, accesible en URL pública

---

### 4.2 Bloque B — Frontend Next.js (Semanas 15-20)

**Sprint 8-10: Migración de Jinja2 a React/Next.js**

| Tarea | Semana | Descripción |
|-------|--------|-------------|
| Scaffolding Next.js 15 (App Router) | 15 | Setup básico, estructura de carpetas |
| Design System con Shadcn/UI + Tailwind | 15-16 | Tokens de diseño, componentes base |
| Autenticación con NextAuth o custom JWT | 16 | Sesión persistida en cookie httpOnly |
| Configurar CORS en FastAPI | 16 | Whitelist de dominios |
| Migrar página Home/Dashboard | 17 | Partidos del día + predicciones |
| Migrar página Leagues | 17 | Tabla de posiciones |
| Migrar página Teams | 18 | Perfil + stats + últimos partidos |
| Migrar página Matches | 18 | Detalle + predicciones |
| Migrar página Players | 19 | Perfil + estadísticas |
| Deploy en Netlify | 19 | CI/CD con GitHub, edge network |
| A/B: apuntar 10% tráfico a Next.js | 20 | Feature flag por dominio |
| Migración completa, deprecar Jinja2 | 20 | Go-live completo |

**Hito M2.2 (Semana 20):** Frontend Next.js en producción, Jinja2 deprecado

---

### 4.3 Bloque C — Monetización (Semanas 19-24)

**Sprint 11-12: Primeros Ingresos**

| Feature | Descripción | Semana |
|---------|-------------|--------|
| Planes de suscripción (Free/Pro) | Definir features por plan | 19 |
| Integración Stripe | Webhooks, checkout session, portal de cliente | 20-21 |
| Feature gates por plan | Restringir xG, features avanzadas, exportación | 21 |
| Email transaccional (SendGrid) | Bienvenida, renovación, recordatorios | 22 |
| OAuth Google | Registro/login con Google | 22 |
| Landing page de marketing | Pricing, features, testimonios | 23-24 |
| Campaña de lanzamiento | SEO, redes sociales, comunidades fútbol | 24 |

**Hito M2.3 (Semana 24):** Primeros 100 usuarios registrados, primeros 5 suscriptores Pro

---

### 4.4 Bloque D — Expansión de Datos (Paralelo con B y C)

| Feature | Semana | Descripción |
|---------|--------|-------------|
| Agregar Liga BetPlay Colombia | 17 | Alta demanda en mercado hispanohablante |
| Agregar Champions League | 18 | Mayor visibilidad, partidos top |
| Agregar Serie A + Bundesliga | 20 | Cobertura europea completa |
| Estadísticas de jugadores más completas | 21 | API-Football plan pagado |
| Datos históricos 5 temporadas | 22 | Retroalimentar modelo ML |
| Odds en tiempo real (The Odds API) | 22 | Value bets para usuarios Pro |

### KPIs de Éxito Fase 2

| Métrica | Meta (Semana 24) |
|---------|-----------------|
| Usuarios registrados | 500 |
| Usuarios activos semanales | 150 |
| Suscriptores Pro | 20 |
| MRR (Monthly Recurring Revenue) | $200 USD |
| Ligas activas | 6 |
| Accuracy modelo 1X2 | > 50% |
| Uptime (SLA) | > 99.5% |
| p95 latencia API | < 200ms |

---

## 5. FASE 3 — ESCALA (Semanas 25-52)

### Objetivo
Convertir la plataforma en un producto maduro con ML avanzado, real-time data y primeras señales de product-market fit sólidas.

### 5.1 Mejoras de Modelo ML (Semanas 25-36)

| Trimestre | Modelo | Features | Mejora Esperada |
|-----------|--------|----------|----------------|
| Q3 2026 | Regresión Logística | 30 features: forma, H2H, lesiones, fatiga | +2-3% accuracy |
| Q4 2026 | XGBoost/LightGBM | 60+ features: xG por partido, PPDA, formaciones | +3-5% accuracy |
| Q1 2027 | Ensemble (Poisson + XGBoost) | Combinación calibrada de modelos | +1-2% accuracy |
| Q2 2027 | LSTM (datos temporales) | Serie temporal de forma, momentum | +1-3% accuracy |

**MLflow** para tracking de experimentos desde el inicio de Fase 3.

---

### 5.2 Real-Time Data (Semanas 29-36)

| Feature | Descripción |
|---------|-------------|
| WebSocket API | Actualizaciones de score y eventos durante partidos |
| Predicciones en vivo | Recalcular probabilidades con cada gol/tarjeta |
| Push notifications | App nativa o browser push |
| Live match tracking | Posición y momentum visual |

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
| Scouting reports | Enterprise | Análisis de jugadores para clubes |

---

### 5.4 Arquitectura Técnica Fase 3

| Cambio | Motivación | Semana |
|--------|-----------|--------|
| Separar ETL service | Escala independiente de la API | 30 |
| Kafka para eventos | Desacoplar sincronización de resultados | 32 |
| dbt para transformaciones SQL | Datos más limpios para ML | 30 |
| Airflow para pipelines ML | Reemplazar Celery Beat para jobs complejos | 34 |
| Read replica PostgreSQL | Descargar queries analíticos de la primaria | 28 |
| Redis Cluster | Alta disponibilidad del cache | 32 |
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
COMPONENTE          FASE 1              FASE 2              FASE 3
───────────────────────────────────────────────────────────────────────
Frontend            Jinja2 (SSR)        Next.js + Netlify   Next.js + CDN
Backend             FastAPI (local)     FastAPI (cloud)     FastAPI + microservicios
Base de datos       PostgreSQL Docker   Neon/Supabase       Aurora PostgreSQL
Cache               Redis Docker        Upstash             Redis Cluster
Task Queue          Celery + Redis      Celery (cloud)      Celery + Airflow
Scheduler           Celery Beat         Celery Beat         Apache Airflow
ETL                 Celery tasks        Celery tasks        Servicio separado
ML                  scipy/numpy local   scipy/numpy cloud   MLflow + LightGBM
Monitoring          Logs básicos        Sentry + Grafana    DataDog/New Relic
Storage             Disco local         Cloudflare R2       R2 + CDN
Auth                JWT custom          JWT + Google OAuth  Auth0 (Fase 3)
Emails              -                   SendGrid            SendGrid
Pagos               -                   Stripe              Stripe
CI/CD               Manual              GitHub Actions      GitHub Actions + ArgoCD
Infra               Docker Compose      Docker + Railway    Kubernetes (EKS/GKE)
```

---

## 7. DECISIONES DE ARQUITECTURA FUTURAS (Por Evaluar)

### Decisión 1: Mobile App (Q4 2026)
- **Opción A:** React Native (compartir lógica con Next.js)
- **Opción B:** Flutter (mejor performance nativa)
- **Decisión:** Evaluar con feedback de usuarios en Fase 2. Priorizar si > 40% del tráfico es móvil.

### Decisión 2: Multi-tenancy Enterprise (Q2 2027)
- **Opción A:** Row-level security en PostgreSQL (RLS)
- **Opción B:** Schema separado por tenant
- **Decisión:** Depende del número de clientes Enterprise y sus requisitos de aislamiento.

### Decisión 3: Datos Propios vs APIs Externas
- Cuando supere 10,000 usuarios activos, evaluar scraping propio + partnerships con proveedores de datos
- Costo de API-Football escala linealmente; en cierto punto, propio pipeline es más económico

---

## 8. RIESGOS Y MITIGACIONES DE ROADMAP

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Bajo engagement en MVP → no validar | Media | Alto | Lanzar beta privada con 20 usuarios reales desde Semana 10 |
| Costos cloud superan proyección | Baja | Medio | Budget alert en Railway/Neon; escalar verticalmente antes que horizontalmente |
| Competidor lanza producto similar | Media | Medio | Diferenciación en explicabilidad del modelo y cobertura latinoamericana |
| API-Football sube precios | Media | Alto | Diversificar fuentes de datos; football-data.org como fallback principal |
| Dificultad para conseguir suscriptores Pro | Media | Alto | Ofrecer período de prueba Pro de 30 días; colectar testimonios desde beta |

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
