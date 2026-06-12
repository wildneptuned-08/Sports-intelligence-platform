# MASTER PROJECT SPECIFICATION
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.0.0  
**Fecha:** 2026-06-12  
**Rol:** CTO / Arquitecto de Software  
**Estado:** Diseño Pre-Implementación

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
| Latencia en actualización de estadísticas de partidos | Todos los segmentos | Pipeline de ingesta con latencia < 5 minutos |

### 1.3 Propuesta de Valor Única

- **Precisión verificable:** cada predicción incluye histórico de accuracy del modelo
- **Explicabilidad:** las predicciones exponen los factores más influyentes (no cajas negras)
- **Cobertura:** inicialmente Liga Española, Liga Colombiana, Premier League, Champions League
- **Tiempo real:** actualizaciones de estadísticas durante el partido con websockets

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
├── M6: Gestión de Usuarios y Suscripciones
└── M7: Administración (Backoffice)
```

### 2.2 Módulo 1 — Gestión de Datos (ETL)

**Objetivo:** Ingestar, normalizar y persistir datos de fuentes externas.

**Funcionalidades:**
- Conectar con APIs externas (Football-Data.org, API-Football, OpenLigaDB)
- Jobs programados (cron) para sincronización de fixtures, resultados y estadísticas
- Cola de trabajo para ingesta asíncrona (evitar timeouts en scraping)
- Normalización de entidades: equipos, jugadores, ligas, árbitros
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
- Estadísticas de temporada: goles, asistencias, tarjetas, posesión, xG, xGA
- Comparador de equipos (head-to-head histórico)
- Métricas avanzadas: xG by match, PPDA (Passes Allowed Per Defensive Action), Build-up play
- Tabla de posiciones por liga y temporada
- Historial de enfrentamientos directos con filtros por competición y localía

**Métricas Clave:**
- `form_score`: puntuación 0-100 calculada sobre últimos 5 partidos ponderados por adversario
- `attack_rating` / `defense_rating`: percentiles vs liga
- `home_advantage_factor`: ratio rendimiento local vs visitante
- `fatigue_index`: carga de partidos en ventana de 30 días

### 2.4 Módulo 3 — Analytics de Jugadores

**Objetivo:** Métricas individuales por jugador con contexto de equipo.

**Funcionalidades:**
- Perfil de jugador: foto, posición, edad, nacionalidad, valor de mercado
- Estadísticas por temporada y por partido
- Heatmaps de posición (zona de influencia)
- Comparador de jugadores (hasta 3 simultáneos)
- Tracking de lesiones y ausencias
- Contribución a métricas de equipo (goles esperados generados, pases clave)
- Rating de rendimiento por partido (0-10 basado en métricas)

### 2.5 Módulo 4 — Motor de Predicciones

**Objetivo:** Generar predicciones de resultados y métricas con intervalos de confianza.

**Funcionalidades:**
- Predicción 1X2 (local gana / empate / visitante gana) con probabilidades
- Predicción de marcador exacto (top 5 más probables)
- Predicción de goles totales (Over/Under 2.5)
- Predicción de ambos equipos marcan (BTTS)
- Predicción de tarjetas y córneres
- Comparación con odds del mercado para identificar value bets
- Historial de predicciones con resolución y accuracy tracking
- Métricas del modelo: Brier Score, Log Loss, ROI simulado

**Modelos a Implementar (por fase):**

| Fase | Modelo | Descripción |
|------|--------|-------------|
| MVP | Poisson Bivariado | Modelado de goles como procesos de Poisson independientes |
| Fase 2 | Regresión Logística | Predicción 1X2 con features de equipo y contexto |
| Fase 3 | XGBoost / LightGBM | Modelo de ensamble con 50+ features |
| Fase 4 | Red Neuronal (LSTM) | Captura de secuencias temporales de forma |

### 2.6 Módulo 5 — Dashboard e Informes

**Funcionalidades:**
- Dashboard personalizable con widgets
- Partido del día con predicciones destacadas
- Calendario de partidos con filtros por liga/equipo
- Generación de informes PDF: previa de partido, análisis de temporada
- Alertas: resultados de partidos seguidos, cambios bruscos en odds

### 2.7 Módulo 6 — Gestión de Usuarios

**Funcionalidades:**
- Registro y autenticación (email + password, OAuth Google)
- Roles: Visitante, Free, Pro, Enterprise, Admin
- Suscripciones con Stripe (Fase 2)
- Equipos favoritos y partidos guardados
- Historial de predicciones consultadas
- API Keys para acceso programático (plan Pro+)

### 2.8 Módulo 7 — Administración (Backoffice)

**Funcionalidades:**
- Gestión de ligas, equipos y jugadores (CRUD manual)
- Monitoreo de jobs ETL y reintento manual
- Gestión de usuarios y suscripciones
- Configuración de modelos predictivos (habilitar/deshabilitar, parámetros)
- Logs del sistema y alertas operativas

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
        CRITERIO: Probabilidades visibles, score exacto y desglose de features bloqueados.

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
        con todas las métricas relevantes para compartir con mi equipo.

HU-022: Como usuario Pro, quiero acceder a métricas avanzadas (xG, PPDA, xGA)
        de todos los equipos de las ligas suscritas.

HU-023: Como usuario Pro, quiero consultar el historial de accuracy de las
        predicciones del modelo para calibrar mi confianza en él.

HU-024: Como usuario Pro, quiero recibir alertas cuando el modelo detecte
        value bets (probabilidad modelo vs odds de mercado > threshold configurado).
```

### 3.4 Administrador

```
HU-030: Como administrador, quiero ejecutar manualmente un job de sincronización
        de datos para una liga específica sin esperar al cron programado.

HU-031: Como administrador, quiero ver el estado de todos los jobs ETL en tiempo
        real para detectar y resolver fallas rápidamente.

HU-032: Como administrador, quiero gestionar el catálogo de ligas activas
        (habilitar/deshabilitar) para controlar el alcance de la plataforma.
```

---

## 4. REQUERIMIENTOS FUNCIONALES

### 4.1 RF — Datos

| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-D01 | El sistema debe sincronizar resultados de partidos en < 5 minutos post-final | Alta |
| RF-D02 | El sistema debe mantener histórico mínimo de 5 temporadas por liga | Alta |
| RF-D03 | El sistema debe normalizar entidades entre múltiples fuentes externas | Alta |
| RF-D04 | El sistema debe registrar auditoría de cada operación ETL | Media |
| RF-D05 | El sistema debe manejar indisponibilidad de APIs externas con retry exponencial | Alta |

### 4.2 RF — Predicciones

| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-P01 | El sistema debe generar predicción 1X2 para todo partido con +24h de anticipación | Alta |
| RF-P02 | Las probabilidades del modelo deben sumar 1.0 (calibración) | Alta |
| RF-P03 | El sistema debe calcular accuracy histórico por liga y tipo de predicción | Media |
| RF-P04 | Las predicciones deben generarse o regenerarse cuando cambie el lineup oficial | Alta |

### 4.3 RF — Usuarios

| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-U01 | Autenticación con JWT de corta duración + refresh tokens | Alta |
| RF-U02 | Rate limiting por usuario y por IP | Alta |
| RF-U03 | El sistema debe respetar GDPR: exportación y eliminación de datos de usuario | Media |

---

## 5. REQUERIMIENTOS NO FUNCIONALES

### 5.1 Rendimiento

| Métrica | Objetivo MVP (Local) | Objetivo Fase 2 (Cloud) |
|---------|---------------------|------------------------|
| Tiempo de respuesta p95 (API) | < 500ms | < 200ms |
| Tiempo de carga dashboard | < 2s | < 1s |
| Throughput concurrente | 50 usuarios | 1,000 usuarios |
| Disponibilidad | 95% (sin SLA) | 99.5% |
| Latencia actualización datos | < 10 min | < 3 min |

### 5.2 Seguridad

- Contraseñas hasheadas con bcrypt (cost factor 12)
- HTTPS obligatorio en producción
- OWASP Top 10 como checklist de revisión
- Secretos gestionados por variables de entorno (nunca en código)
- Tokens JWT firmados con RS256 en producción
- SQL generado exclusivamente por ORM (sin queries raw que tomen input de usuario)

### 5.3 Escalabilidad

- Arquitectura stateless en API para escala horizontal
- Base de datos con separación read/write desde Fase 2
- Predicciones pre-calculadas y cacheadas (no on-demand)
- ETL desacoplado del API mediante cola de mensajes (Fase 2)

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
| R-01 | APIs externas con rate limits agresivos o cambio de precios | Alta | Alto | Implementar caché agresivo; tener 2+ fuentes por dato; scraping como fallback |
| R-02 | Calidad de datos inconsistente entre fuentes (nombres de equipos, IDs) | Alta | Alto | Capa de normalización con tabla de aliases; proceso de reconciliación manual |
| R-03 | Modelo predictivo con bajo accuracy en arranque (cold start) | Media | Alto | Poisson bivariado como baseline determinista; publicar métricas de accuracy transparentemente |
| R-04 | Migración de Jinja2 → React introduce deuda técnica | Media | Medio | Diseñar API REST desde inicio aunque se consuma con Jinja2; evitar lógica en templates |

### 6.2 Riesgos Medios (Gestionar activamente)

| ID | Riesgo | Mitigación |
|----|--------|------------|
| R-05 | Crecimiento de datos sin partición → degradación de queries | Particionado por temporada en tablas de stats desde el diseño inicial |
| R-06 | Jobs ETL bloqueantes que degradan la API | Celery + Redis para jobs asíncronos desde MVP |
| R-07 | Falta de datos de lineups oficiales para predicción | Usar probabilidades condicionadas a lineup tipo; mostrar disclaimer |
| R-08 | Violación de ToS de fuentes de datos por scraping | Priorizar APIs con licencia; documentar política de uso |

### 6.3 Deuda Técnica Aceptada en MVP

- ORM sin optimización de N+1 queries (se resolverá con profiling en Fase 2)
- Celery beat como scheduler (escala limitada; migrar a Airflow en Fase 3)
- Sin separación de dominios en modelo de datos (monolito de datos en Fase 1)
- Templates Jinja2 con algo de lógica de presentación (se elimina al migrar a React)

---

## 7. INTEGRACIONES EXTERNAS

### 7.1 Fuentes de Datos

| Fuente | Tipo | Datos | Plan Recomendado |
|--------|------|-------|-----------------|
| API-Football (RapidAPI) | REST API | Fixtures, resultados, estadísticas, lineups, odds | Free (100 req/día) → Basic ($10/mes) |
| Football-Data.org | REST API | Ligas europeas, resultados, tabla de posiciones | Free (10 req/min) |
| OpenLigaDB | REST API | Bundesliga (abierto y gratuito) | Free |
| FBref / StatsBomb Open | Scraping/CSV | Métricas avanzadas (xG, PPDA) | Open Data |
| The Odds API | REST API | Odds de múltiples bookmakers | Free (500 req/mes) |

### 7.2 Integraciones de Plataforma

| Servicio | Propósito | Fase |
|----------|-----------|------|
| Stripe | Pagos y suscripciones | Fase 2 |
| SendGrid | Emails transaccionales y alertas | Fase 2 |
| Sentry | Error tracking y performance | MVP |
| Google OAuth | Autenticación social | Fase 2 |
| AWS S3 / Cloudflare R2 | Almacenamiento de imágenes y PDFs | Fase 2 |

---

## 8. MÉTRICAS DE ÉXITO

### 8.1 KPIs de Producto

| Métrica | Meta MVP (3 meses) | Meta Fase 2 (6 meses) |
|---------|-------------------|----------------------|
| Usuarios registrados | 200 | 2,000 |
| Usuarios activos diarios | 30 | 300 |
| Ligas con datos completos | 3 | 8 |
| Accuracy modelo 1X2 | > 48% | > 52% |
| Brier Score modelo | < 0.25 | < 0.22 |
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

### ADR-002: PostgreSQL como única base de datos en MVP
**Decisión:** Sin Redis, sin Elasticsearch en MVP.  
**Razón:** PostgreSQL con extensiones (pg_trgm, pg_stat) cubre los casos de uso iniciales.  
**Consecuencia:** Agregar Redis para cache y Elasticsearch para búsqueda en Fase 2.

### ADR-003: API REST sobre GraphQL
**Decisión:** API REST con OpenAPI 3.0.  
**Razón:** Mayor ecosistema de herramientas; más simple para el consumo inicial con Jinja2.  
**Consecuencia:** Si la Fase 3 requiere flexibilidad en queries, evaluar GraphQL o JSONAPI.

### ADR-004: Pre-cálculo de predicciones sobre cálculo on-demand
**Decisión:** Las predicciones se calculan en jobs programados y se almacenan.  
**Razón:** El modelo puede ser costoso computacionalmente; no se puede ejecutar en request time.  
**Consecuencia:** Las predicciones pueden estar desactualizadas si hay cambios de lineup tardíos.

### ADR-005: Separación estricta de capas desde el inicio
**Decisión:** Schemas Pydantic ≠ Modelos SQLAlchemy ≠ DTOs de respuesta de API.  
**Razón:** Facilitar la migración a React; evitar acoplar la vista al modelo de datos.  
**Consecuencia:** Más código boilerplate, justificado por la mantenibilidad a largo plazo.
