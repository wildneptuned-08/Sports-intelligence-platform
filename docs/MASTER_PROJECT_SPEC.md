# MASTER PROJECT SPECIFICATION
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.1.0 _(revisado por comité de arquitectura 2026-06-12)_  
**Fecha:** 2026-06-12  
**Estado:** Diseño Pre-Implementación — Aprobado para desarrollo

---

## 1. VISIÓN DEL PRODUCTO

### 1.1 Declaración de Visión

Construir la plataforma de inteligencia deportiva más confiable de habla hispana para analistas, apostadores profesionales, periodistas deportivos y equipos de fútbol, que transforme datos históricos y en tiempo real en predicciones accionables mediante modelos estadísticos y de machine learning.

### 1.2 Problema que Resuelve

| Problema | Segmento Afectado | Solución |
|----------|-------------------|----------|
| Dispersión de datos en múltiples fuentes sin consolidación | Analistas deportivos | Dashboard unificado con ETL automatizado |
| Predicciones basadas en intuición sin soporte estadístico | Periodistas / Apostadores | Modelos predictivos con probabilidades calibradas |
| Acceso a métricas avanzadas reservado para grandes clubes | Equipos amateur y semi-pro | Democratización de analytics avanzados |
| Latencia en actualización de estadísticas de partidos | Todos los segmentos | Pipeline de ingesta con latencia < 10 minutos |

### 1.3 Propuesta de Valor Única

- **Precisión verificable:** cada predicción incluye histórico de accuracy del modelo
- **Explicabilidad:** las predicciones exponen los factores más influyentes (no cajas negras)
- **Cobertura:** inicialmente Liga Española, Premier League y Liga BetPlay Colombia
- **Datos actualizados:** sincronización automática post-partido con monitoreo de salud del pipeline

> **Nota MVP:** Las actualizaciones en tiempo real con WebSockets son un objetivo de Fase 3. El MVP entrega datos con latencia de sincronización de 5-10 minutos post-evento.

---

## 2. ANÁLISIS FUNCIONAL COMPLETO

### 2.1 Módulos del Sistema

```
PLATAFORMA
├── M1: Gestión de Datos (Ingesta y ETL)
├── M2: Analytics de Equipos
├── M3: Analytics de Jugadores
├── M4: Motor de Predicciones
├── M5: Dashboard e Informes
├── M6: Gestión de Usuarios
└── M7: Administración (Backoffice)
```

### 2.2 Módulo 1 — Gestión de Datos (ETL)

**Objetivo:** Ingestar, normalizar y persistir datos de fuentes externas.

**Funcionalidades:**
- Conectar con APIs externas (Football-Data.org, API-Football, OpenLigaDB)
- Jobs programados (APScheduler) para sincronización de fixtures, resultados y estadísticas
- Normalización de entidades: equipos, jugadores, ligas
- Deduplicación por claves naturales (slug + temporada)
- Registro de auditoría de cada operación ETL (estado, registros procesados, errores)
- Panel de monitoreo de salud de fuentes de datos

**Reglas de Negocio:**
- Un partido solo puede ser procesado una vez; reintentos se aplican únicamente si el estado es `FAILED` o `PENDING`
- Los datos de estadísticas de partido se congelan 24 horas después del partido
- La ingesta de odds se realiza cada 6 horas para partidos con +7 días de anticipación, cada hora para partidos en las próximas 48 horas

### 2.3 Módulo 2 — Analytics de Equipos

**Objetivo:** Proporcionar métricas de rendimiento y forma de equipos.

**Funcionalidades:**
- Ficha de equipo: escudo, nombre, liga, estadio, entrenador actual
- Forma reciente (últimos N partidos): W/D/L con visualización gráfica
- Estadísticas de temporada: goles, asistencias, tarjetas, posesión
- Comparador de equipos (head-to-head histórico)
- Métricas avanzadas: xG, xGA (Plan Pro — dependen de fuente de datos premium)
- Tabla de posiciones por liga y temporada
- Historial de enfrentamientos directos con filtros por competición y localía

**Métricas Clave:**
- `form_score`: puntuación 0-100 calculada sobre últimos 5 partidos ponderados por adversario
- `attack_rating` / `defense_rating`: percentiles vs liga
- `home_advantage_factor`: ratio rendimiento local vs visitante

### 2.4 Módulo 3 — Analytics de Jugadores

**Objetivo:** Métricas individuales por jugador con contexto de equipo.

**Funcionalidades:**
- Perfil de jugador: foto, posición, edad, nacionalidad
- Estadísticas por temporada y por partido
- Tracking de ausencias y sanciones
- Rating de rendimiento por partido (basado en métricas disponibles)

### 2.5 Módulo 4 — Motor de Predicciones

**Objetivo:** Generar predicciones de resultados con intervalos de confianza.

**Funcionalidades:**
- Predicción 1X2 (local gana / empate / visitante gana) con probabilidades
- Predicción de goles totales (Over/Under 2.5)
- Predicción de ambos equipos marcan (BTTS)
- Top 5 marcadores exactos más probables
- Historial de predicciones con resolución y accuracy tracking
- Métricas del modelo: Brier Score, Log Loss

**Modelos a Implementar (por fase):**

| Fase | Modelo | Descripción |
|------|--------|-------------|
| MVP | Poisson Bivariado | Modelado de goles con distribución de Poisson |
| Fase 2 | Regresión Logística | Predicción 1X2 con features adicionales de equipo y contexto |
| Fase 3 | XGBoost / LightGBM | Modelo de ensamble con 50+ features |

### 2.6 Módulo 5 — Dashboard e Informes

**Funcionalidades:**
- Dashboard con partidos del día y predicciones destacadas
- Calendario de partidos con filtros por liga/equipo
- Generación de informes PDF de previa de partido (Fase 2)
- Alertas de resultados de equipos seguidos

### 2.7 Módulo 6 — Gestión de Usuarios

**Funcionalidades:**
- Registro y autenticación (email + password)
- OAuth Google (Fase 2)
- Roles: Visitante, Free, Pro, Admin
- Suscripciones con Stripe (Fase 2)
- Equipos y ligas favoritas
- Actualización de perfil y cambio de contraseña

### 2.8 Módulo 7 — Administración (Backoffice)

**Funcionalidades:**
- Gestión de ligas, equipos y jugadores (CRUD manual)
- Monitoreo de jobs ETL y reintento manual
- Gestión de usuarios
- Logs del sistema y estado del scheduler

---

## 3. HISTORIAS DE USUARIO

### 3.1 Visitante (sin cuenta)

```
HU-001: Como visitante, quiero ver las predicciones del día sin registrarme
        para evaluar la calidad de la plataforma antes de suscribirme.
        CRITERIO: Máximo 3 predicciones visibles, resto bloqueadas con CTA de registro.

HU-002: Como visitante, quiero ver la tabla de posiciones de una liga seleccionada
        para obtener contexto rápido de la situación actual.
```

### 3.2 Usuario Free

```
HU-010: Como usuario free, quiero ver las probabilidades de resultado (1X2)
        de todos los partidos del día para planificar mi análisis.
        CRITERIO: Probabilidades 1X2 visibles; marcador exacto y features bloqueados.

HU-011: Como usuario free, quiero hacer seguimiento a 2 equipos favoritos
        para recibir notificaciones de sus próximos partidos.

HU-012: Como usuario free, quiero ver el historial de enfrentamientos directos
        entre dos equipos para los últimos 5 partidos.
```

### 3.3 Usuario Pro

```
HU-020: Como usuario Pro, quiero ver el desglose completo de features que
        influyen en una predicción para entender el razonamiento del modelo.

HU-021: Como usuario Pro, quiero generar un informe PDF de previa de partido
        con todas las métricas relevantes para compartir con mi equipo. (Fase 2)

HU-022: Como usuario Pro, quiero acceder a métricas avanzadas (xG, xGA)
        de todos los equipos de las ligas suscritas.

HU-023: Como usuario Pro, quiero consultar el historial de accuracy de las
        predicciones del modelo para calibrar mi confianza en él.

HU-024: Como usuario Pro, quiero recibir alertas cuando el modelo detecte
        value bets (probabilidad modelo vs odds de mercado > threshold configurado).
```

### 3.4 Administrador

```
HU-030: Como administrador, quiero ejecutar manualmente un job de sincronización
        de datos para una liga específica sin esperar al schedule programado.

HU-031: Como administrador, quiero ver el estado de todos los jobs ETL
        para detectar y resolver fallas rápidamente.

HU-032: Como administrador, quiero gestionar el catálogo de ligas activas
        (habilitar/deshabilitar) para controlar el alcance de la plataforma.
```

---

## 4. REQUERIMIENTOS FUNCIONALES

### 4.1 RF — Datos

| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-D01 | El sistema debe sincronizar resultados de partidos en < 10 minutos post-final | Alta |
| RF-D02 | El sistema debe mantener histórico mínimo de 3 temporadas por liga | Alta |
| RF-D03 | El sistema debe normalizar entidades entre múltiples fuentes externas | Alta |
| RF-D04 | El sistema debe registrar auditoría de cada operación ETL | Media |
| RF-D05 | El sistema debe manejar indisponibilidad de APIs externas con retry exponencial | Alta |

### 4.2 RF — Predicciones

| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-P01 | El sistema debe generar predicción 1X2 para todo partido con +24h de anticipación | Alta |
| RF-P02 | Las probabilidades del modelo deben sumar 1.0 con tolerancia < 0.0001 (calibración estricta) | Alta |
| RF-P03 | El sistema debe calcular accuracy histórico por liga y tipo de predicción | Media |
| RF-P04 | Las predicciones deben regenerarse cuando cambie el lineup oficial | Alta |

### 4.3 RF — Usuarios

| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-U01 | Autenticación con JWT de corta duración + refresh tokens | Alta |
| RF-U02 | Rate limiting por usuario y por IP | Alta |
| RF-U03 | El usuario puede actualizar su perfil y cambiar su contraseña | Alta |
| RF-U04 | El sistema debe respetar GDPR: exportación y eliminación de datos (Fase 2) | Media |

---

## 5. REQUERIMIENTOS NO FUNCIONALES

### 5.1 Rendimiento

| Métrica | Objetivo MVP (Local) | Objetivo Fase 2 (Cloud) |
|---------|---------------------|------------------------|
| Tiempo de respuesta p95 (API) | < 500ms | < 200ms |
| Tiempo de carga dashboard | < 2s | < 1s |
| Throughput concurrente | 50 usuarios | 1,000 usuarios |
| Disponibilidad | 95% (sin SLA) | 99.5% |
| Latencia actualización datos | < 10 min | < 5 min |

### 5.2 Seguridad

- Contraseñas hasheadas con bcrypt (cost factor 12)
- HTTPS obligatorio en producción
- OWASP Top 10 como checklist de revisión
- Secretos gestionados por variables de entorno (nunca en código)
- Tokens JWT firmados con HS256 (MVP) → RS256 (Fase 2)
- SQL generado exclusivamente por ORM (sin queries raw con input de usuario)

### 5.3 Escalabilidad

- Arquitectura stateless en API para escala horizontal
- Base de datos con separación read/write desde Fase 2
- Predicciones pre-calculadas y cacheadas (no on-demand)
- ETL como jobs APScheduler en MVP; migrar a Celery+Redis en Fase 2 para workers distribuidos

### 5.4 Mantenibilidad

- Cobertura de tests: 80% mínimo en servicios críticos (predicciones, ETL)
- Documentación OpenAPI auto-generada y actualizada
- Logs estructurados en JSON con niveles INFO/WARNING/ERROR/CRITICAL
- Migraciones de base de datos versionadas con Alembic

---

## 6. ANÁLISIS DE RIESGOS TÉCNICOS

### 6.1 Riesgos Críticos (Alta Probabilidad × Alto Impacto)

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|-------------|---------|------------|
| R-01 | APIs externas con rate limits agresivos o cambio de precios | Alta | Alto | Implementar caché agresivo; plan Basic ($10/mes) como mínimo real de MVP operacional; fallback a football-data.org |
| R-02 | Calidad de datos inconsistente entre fuentes (nombres de equipos, IDs) | Alta | Alto | Capa de normalización con tabla de aliases; proceso de reconciliación manual |
| R-03 | Modelo predictivo con bajo accuracy en arranque (cold start) | Media | Alto | Poisson bivariado como baseline determinista; publicar métricas de accuracy transparentemente |
| R-04 | Migración de Jinja2 → React introduce deuda técnica | Media | Medio | API REST diseñada como contrato independiente desde inicio; lógica de negocio nunca en templates |

### 6.2 Riesgos Medios (Gestionar activamente)

| ID | Riesgo | Mitigación |
|----|--------|------------|
| R-05 | Crecimiento de datos sin partición → degradación de queries | Índices correctos desde el diseño inicial; particionado cuando el profiling lo justifique (Fase 2) |
| R-06 | Jobs ETL bloqueantes que degradan la API | APScheduler con jobs en thread pool separado; timeouts explícitos en todos los clientes HTTP |
| R-07 | Falta de datos de lineups oficiales para predicción | Usar probabilidades con lineup tipo; mostrar disclaimer de confianza |
| R-08 | Violación de ToS de fuentes de datos por scraping | Priorizar APIs con licencia; documentar política de uso |

### 6.3 Deuda Técnica Aceptada en MVP

- ORM sin optimización explícita de N+1 queries (se resolverá con profiling en Fase 2)
- APScheduler como scheduler (escala limitada a un proceso; migrar a Celery+Redis en Fase 2 para workers distribuidos en cloud)
- Templates Jinja2 con algo de lógica de presentación (se elimina al migrar a React)
- Sin Redis en MVP (se agrega en Fase 2 junto con Celery para jobs distribuidos y cache L2)

---

## 7. INTEGRACIONES EXTERNAS

### 7.1 Fuentes de Datos

| Fuente | Tipo | Datos | Plan Recomendado |
|--------|------|-------|-----------------|
| API-Football (RapidAPI) | REST API | Fixtures, resultados, estadísticas, lineups, odds | Basic ($10/mes) — mínimo operacional para MVP con 2 ligas |
| Football-Data.org | REST API | Ligas europeas, resultados, tabla de posiciones | Free (10 req/min) — fallback y validación cruzada |
| OpenLigaDB | REST API | Bundesliga (abierto y gratuito) | Free |
| The Odds API | REST API | Odds de múltiples bookmakers | Free (500 req/mes) — suficiente para MVP |

> **Análisis de consumo real de API-Football:** Una jornada de Liga con 10 partidos consume ~45 requests (sync_results + stats + lineups). Con 2 ligas activas, el plan Free (100 req/día) no es suficiente en fines de semana. **El plan Basic ($10/mes) es el mínimo real para MVP operacional.**

### 7.2 Integraciones de Plataforma

| Servicio | Propósito | Fase |
|----------|-----------|------|
| Stripe | Pagos y suscripciones | Fase 2 |
| SendGrid | Emails transaccionales y alertas | Fase 2 |
| Sentry | Error tracking | MVP (Sprint 6) |
| Google OAuth | Autenticación social | Fase 2 |
| Cloudflare R2 | Almacenamiento de imágenes y PDFs | Fase 2 |

---

## 8. MÉTRICAS DE ÉXITO

### 8.1 KPIs de Producto

| Métrica | Meta MVP (3 meses) | Meta Fase 2 (6 meses) |
|---------|-------------------|----------------------|
| Usuarios registrados | 200 | 2,000 |
| Usuarios activos diarios | 30 | 300 |
| Ligas con datos completos | 2 | 6 |
| Accuracy modelo 1X2 | > 46% | > 50% |
| Brier Score modelo | < 0.26 | < 0.23 |
| NPS usuarios Pro | N/A | > 40 |

### 8.2 KPIs Técnicos

| Métrica | Meta |
|---------|------|
| Uptime plataforma | > 99% |
| Tasa de error API (5xx) | < 0.1% |
| Jobs ETL exitosos | > 98% |
| Tiempo de deploy | < 10 minutos |
| Cobertura de tests | > 80% en core |

---

## 9. DECISIONES ARQUITECTÓNICAS CLAVE (ADRs)

### ADR-001: Monolito Modular sobre Microservicios en MVP
**Decisión:** Iniciar con un monolito FastAPI bien modularizado.  
**Razón:** Menor complejidad operacional; el team size no justifica microservicios.  
**Consecuencia:** Diseñar módulos con interfaces claras para extraerlos en Fase 3.

### ADR-002: Sin Redis ni Celery en MVP — APScheduler integrado
**Decisión:** APScheduler con `BackgroundScheduler` integrado en el proceso FastAPI. Sin Redis, sin contenedor worker, sin contenedor beat.  
**Razón:** Con 100-500 req/día de APIs externas y jobs de sincronización cada 5-60 minutos, un sistema de colas distribuidas es sobreingeniería. APScheduler maneja este volumen trivialmente en un solo proceso. La migración a Celery+Redis en Fase 2 es un sprint de trabajo cuando los workers distribuidos sean necesarios para el cloud.  
**Consecuencia:** Los jobs ETL corren en el mismo proceso que la API. Si el proceso cae, los jobs se detienen (aceptable en MVP local; se resuelve en Fase 2 con Celery).

### ADR-003: API REST sobre GraphQL
**Decisión:** API REST con OpenAPI 3.0.  
**Razón:** Mayor ecosistema de herramientas; más simple para el consumo inicial con Jinja2 y futuro con Next.js.  
**Consecuencia:** Si la Fase 3 requiere flexibilidad extrema en queries, evaluar GraphQL.

### ADR-004: Pre-cálculo de predicciones sobre cálculo on-demand
**Decisión:** Las predicciones se calculan en jobs programados (APScheduler) y se almacenan en BD.  
**Razón:** El modelo puede ser costoso computacionalmente en Fase 2+; desacoplar cálculo de request mejora latencia de respuesta.  
**Consecuencia:** Las predicciones pueden estar desactualizadas si hay cambios de lineup tardíos. Se muestra timestamp de generación en el response.

### ADR-005: Separación de capas SQLAlchemy / Pydantic / DTO
**Decisión:** Schemas Pydantic ≠ Modelos SQLAlchemy ≠ DTOs de respuesta de API.  
**Razón:** Esta separación es el contrato que permite que Jinja2 y Next.js consuman la misma API sin cambios en la capa de datos. Es la inversión más importante para la migración a React.  
**Consecuencia:** Más código boilerplate, justificado por ser el enabler central de la evolución a cloud.

### ADR-006: PostgreSQL como única base de datos en MVP
**Decisión:** Sin Redis, sin Elasticsearch en MVP.  
**Razón:** PostgreSQL con `pg_trgm` cubre búsqueda de texto. Las queries analíticas de MVP no requieren motor de búsqueda dedicado.  
**Consecuencia:** Agregar Redis (como cache + Celery broker) y Elasticsearch en Fase 2 según métricas de latencia reales.
