# API DESIGN
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.1.0 _(revisado por comité de arquitectura 2026-06-12)_
**Fecha:** 2026-06-12
**Estado:** Diseño Pre-Implementación — Aprobado

---

## 1. PRINCIPIOS DE DISEÑO

| Principio | Implementación |
|-----------|---------------|
| REST semántico | Verbos HTTP correctos; sustantivos en plural para colecciones |
| Versionado en URL | `/api/v1/` — permite deprecar versiones sin romper clientes |
| Slugs como identificadores | `/teams/real-madrid` en lugar de `/teams/42` en URLs públicas |
| Paginación consistente | Cursor-based para colecciones grandes; offset para tablas simples |
| Errores estructurados | `{"error": {"code": "...", "message": "...", "details": {...}}}` |
| Separación de capas | DTOs de respuesta independientes de modelos ORM y schemas internos |
| Nulos explícitos | Campos de plan Pro devuelven `null` para usuarios Free (no se ocultan) |

---

## 2. AUTENTICACIÓN Y AUTORIZACIÓN

### 2.1 JWT Schema

```
Access Token:
  - Algoritmo: HS256 (MVP) → RS256 (Fase 2)
  - TTL: 15 minutos
  - Payload: { sub: user_id, role: "free"|"pro"|"admin", iat, exp }
  - Enviado en: Authorization: Bearer <token>

Refresh Token:
  - TTL: 7 días
  - Almacenamiento servidor: hash SHA-256 en tabla refresh_tokens
  - Enviado en: httpOnly cookie (Secure en producción, SameSite=Lax)
  - Rotación: cada refresh genera un nuevo token y revoca el anterior
```

### 2.2 Control de Acceso por Rol

| Endpoint | Visitante | Free | Pro | Admin |
|----------|-----------|------|-----|-------|
| GET /matches | ✅ (limitado) | ✅ | ✅ | ✅ |
| GET /matches/{slug} | ✅ | ✅ | ✅ | ✅ |
| GET /matches/{slug}/prediction | ✅ (prob 1X2 solo) | ✅ (prob 1X2) | ✅ (completo) | ✅ |
| GET /teams | ✅ | ✅ | ✅ | ✅ |
| GET /teams/{slug} | ✅ | ✅ | ✅ | ✅ |
| GET /teams/compare | ❌ | ✅ | ✅ | ✅ |
| GET /players/{slug} | ✅ | ✅ | ✅ | ✅ |
| GET /predictions/history | ❌ | ✅ | ✅ | ✅ |
| GET /users/me | ❌ | ✅ | ✅ | ✅ |
| PATCH /users/me | ❌ | ✅ | ✅ | ✅ |
| POST /auth/change-password | ❌ | ✅ | ✅ | ✅ |
| GET /admin/* | ❌ | ❌ | ❌ | ✅ |

### 2.3 Rate Limiting

| Perfil | Límite |
|--------|--------|
| Visitante (por IP) | 30 req/min |
| Usuario Free (por user_id) | 60 req/min |
| Usuario Pro (por user_id) | 200 req/min |
| Admin | Sin límite |

---

## 3. ENDPOINTS — AUTENTICACIÓN

### POST /api/v1/auth/register

**Request:**
```json
{
  "email": "user@example.com",
  "username": "juanfutbol",
  "password": "SecurePass123!",
  "full_name": "Juan García"
}
```

**Response 201:**
```json
{
  "id": 42,
  "email": "user@example.com",
  "username": "juanfutbol",
  "role": "free",
  "created_at": "2026-06-12T10:00:00Z"
}
```

---

### POST /api/v1/auth/login

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 42,
    "email": "user@example.com",
    "username": "juanfutbol",
    "role": "free"
  }
}
```
*El refresh token se envía en cookie httpOnly `sip_refresh` — no en el body.*

---

### POST /api/v1/auth/refresh

Usa la cookie `sip_refresh` automáticamente. Sin body.

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### POST /api/v1/auth/logout

Revoca el refresh token de la cookie y la limpia.

**Response 204:** No content.

---

### POST /api/v1/auth/change-password

Requiere autenticación (cualquier rol).

**Request:**
```json
{
  "current_password": "SecurePass123!",
  "new_password": "EvenMoreSecure456!"
}
```

**Response 204:** No content. Todos los refresh tokens del usuario son revocados.

---

## 4. ENDPOINTS — PARTIDOS

### GET /api/v1/matches

Parámetros de query:

| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `league_slug` | string | - | Filtrar por liga |
| `team_slug` | string | - | Partidos del equipo (local o visitante) |
| `date_from` | date (YYYY-MM-DD) | hoy | Fecha inicio |
| `date_to` | date (YYYY-MM-DD) | hoy+7 | Fecha fin |
| `status` | string | - | SCHEDULED, FINISHED, LIVE |
| `page` | int | 1 | Página (offset-based) |
| `per_page` | int | 20 | Resultados por página (máx 50) |

**Response 200:**
```json
{
  "data": [
    {
      "id": 1001,
      "slug": "real-madrid-vs-barcelona-2026-06-15",
      "kickoff_utc": "2026-06-15T19:00:00Z",
      "status": "SCHEDULED",
      "round": "Jornada 38",
      "league": {
        "name": "La Liga",
        "slug": "la-liga",
        "logo_url": "https://..."
      },
      "home_team": {
        "id": 5,
        "name": "Real Madrid",
        "slug": "real-madrid",
        "logo_url": "https://..."
      },
      "away_team": {
        "id": 3,
        "name": "FC Barcelona",
        "slug": "fc-barcelona",
        "logo_url": "https://..."
      },
      "score": null,
      "prediction_summary": {
        "prob_home_win": 0.452,
        "prob_draw": 0.271,
        "prob_away_win": 0.277
      }
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

---

### GET /api/v1/matches/{slug}

**Response 200:**
```json
{
  "id": 1001,
  "slug": "real-madrid-vs-barcelona-2026-06-15",
  "kickoff_utc": "2026-06-15T19:00:00Z",
  "status": "FINISHED",
  "round": "Jornada 38",
  "venue": {
    "name": "Santiago Bernabéu",
    "city": "Madrid",
    "capacity": 81044
  },
  "referee_name": "Antonio López",
  "league": { "name": "La Liga", "slug": "la-liga" },
  "home_team": { "id": 5, "name": "Real Madrid", "slug": "real-madrid", "logo_url": "..." },
  "away_team": { "id": 3, "name": "FC Barcelona", "slug": "fc-barcelona", "logo_url": "..." },
  "score": {
    "home": 2,
    "away": 1,
    "home_ht": 1,
    "away_ht": 0
  },
  "stats": {
    "home": { "shots_total": 14, "shots_on_goal": 6, "possession_pct": 52.3, "corners": 5 },
    "away": { "shots_total": 10, "shots_on_goal": 4, "possession_pct": 47.7, "corners": 3 }
  },
  "events": [
    {
      "minute": 23,
      "extra_minute": null,
      "event_type": "GOAL",
      "team_slug": "real-madrid",
      "player_name": "Vinícius Júnior",
      "assist_player_name": "Bellingham"
    }
  ]
}
```

---

### GET /api/v1/matches/{slug}/prediction

Devuelve predicción con detalle diferente según el rol del usuario. No hay campo `_restricted` — los campos Pro devuelven `null` para usuarios Free.

**Response 200 (usuario Free):**
```json
{
  "match_slug": "real-madrid-vs-barcelona-2026-06-15",
  "model_version": "poisson_v1",
  "generated_at": "2026-06-14T08:05:00Z",
  "probabilities": {
    "home_win": 0.452,
    "draw": 0.271,
    "away_win": 0.277
  },
  "over_under_2_5": {
    "over": null,
    "under": null
  },
  "btts": {
    "yes": null,
    "no": null
  },
  "expected_goals": null,
  "most_likely_score": null,
  "features": null,
  "upgrade_prompt": "Suscríbete a Pro para ver goles esperados, BTTS y análisis completo."
}
```

**Response 200 (usuario Pro):**
```json
{
  "match_slug": "real-madrid-vs-barcelona-2026-06-15",
  "model_version": "poisson_v1",
  "generated_at": "2026-06-14T08:05:00Z",
  "probabilities": {
    "home_win": 0.452,
    "draw": 0.271,
    "away_win": 0.277
  },
  "over_under_2_5": {
    "over": 0.613,
    "under": 0.387
  },
  "btts": {
    "yes": 0.558,
    "no": 0.442
  },
  "expected_goals": {
    "home": 1.82,
    "away": 1.41
  },
  "most_likely_score": "2-1",
  "features": {
    "home_avg_goals_scored": 2.1,
    "home_avg_goals_conceded": 0.9,
    "away_avg_goals_scored": 1.8,
    "away_avg_goals_conceded": 1.1,
    "h2h_home_win_rate": 0.45,
    "home_form_last5": "WWDWW",
    "away_form_last5": "WDWLW"
  },
  "upgrade_prompt": null
}
```

---

## 5. ENDPOINTS — EQUIPOS

> **Nota de implementación:** `GET /teams/compare` DEBE declararse ANTES de `GET /teams/{slug}` en el router de FastAPI, ya que de lo contrario "compare" es interpretado como un valor de slug.

```python
# app/api/v1/teams.py — orden obligatorio
router.add_api_route("/compare", compare_teams, methods=["GET"])
router.add_api_route("/{slug}", get_team, methods=["GET"])
```

### GET /api/v1/teams

Parámetros: `league_slug`, `search` (texto — usa pg_trgm), `page`, `per_page`.

**Response 200:**
```json
{
  "data": [
    {
      "id": 5,
      "name": "Real Madrid",
      "slug": "real-madrid",
      "short_name": "Real Madrid",
      "logo_url": "https://...",
      "country": { "name": "Spain", "code": "ES" },
      "current_league": "La Liga"
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 80 }
}
```

---

### GET /api/v1/teams/{slug}

**Response 200:**
```json
{
  "id": 5,
  "name": "Real Madrid",
  "slug": "real-madrid",
  "logo_url": "https://...",
  "founded_year": 1902,
  "venue": {
    "name": "Santiago Bernabéu",
    "city": "Madrid",
    "capacity": 81044
  },
  "current_season_stats": {
    "league": "La Liga",
    "rank": 1,
    "played": 37,
    "points": 90,
    "goals_for": 85,
    "goals_against": 26,
    "form": "WWWDW"
  },
  "recent_matches": [
    {
      "slug": "real-madrid-vs-barcelona-2026-06-15",
      "kickoff_utc": "2026-06-15T19:00:00Z",
      "opponent": "FC Barcelona",
      "home_away": "home",
      "score": "2-1",
      "result": "W"
    }
  ]
}
```

---

### GET /api/v1/teams/compare

Requiere autenticación (Free o superior).

Parámetros: `team_a` (slug), `team_b` (slug), `league_slug` (opcional, filtro H2H).

**Response 200:**
```json
{
  "team_a": { "name": "Real Madrid", "slug": "real-madrid", "logo_url": "..." },
  "team_b": { "name": "FC Barcelona", "slug": "fc-barcelona", "logo_url": "..." },
  "current_season": {
    "team_a": { "rank": 1, "points": 90, "goals_for": 85, "form": "WWWDW" },
    "team_b": { "rank": 2, "points": 85, "goals_for": 78, "form": "WDWWW" }
  },
  "head_to_head": {
    "total_matches": 12,
    "team_a_wins": 5,
    "draws": 3,
    "team_b_wins": 4,
    "last_matches": [
      {
        "slug": "real-madrid-vs-barcelona-2026-06-15",
        "date": "2026-06-15",
        "score": "2-1",
        "winner": "team_a"
      }
    ]
  }
}
```

---

## 6. ENDPOINTS — JUGADORES

### GET /api/v1/players

Parámetros: `team_slug`, `league_slug`, `position`, `search`, `page`, `per_page`.

### GET /api/v1/players/{slug}

**Response 200:**
```json
{
  "id": 200,
  "name": "Vinícius Júnior",
  "slug": "vinicius-junior",
  "photo_url": "https://...",
  "date_of_birth": "2000-07-12",
  "nationality": "Brazil",
  "position": "Attacker",
  "height_cm": 176,
  "current_team": {
    "name": "Real Madrid",
    "slug": "real-madrid"
  },
  "current_season_stats": {
    "league": "La Liga",
    "appearances": 33,
    "goals": 24,
    "assists": 9,
    "minutes_played": 2847,
    "yellow_cards": 3,
    "red_cards": 0
  }
}
```

---

## 7. ENDPOINTS — LIGAS

### GET /api/v1/leagues

**Response 200:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "La Liga",
      "slug": "la-liga",
      "country": { "name": "Spain", "code": "ES" },
      "logo_url": "https://...",
      "current_season": "2025/26",
      "is_active": true
    }
  ]
}
```

### GET /api/v1/leagues/{slug}/standings

**Response 200:**
```json
{
  "league": { "name": "La Liga", "slug": "la-liga" },
  "season": "2025/26",
  "round": "Jornada 37",
  "table": [
    {
      "rank": 1,
      "team": { "name": "Real Madrid", "slug": "real-madrid", "logo_url": "..." },
      "played": 37,
      "won": 29,
      "drawn": 3,
      "lost": 5,
      "goals_for": 85,
      "goals_against": 26,
      "goal_diff": 59,
      "points": 90,
      "form": "WWWDW"
    }
  ]
}
```

### GET /api/v1/leagues/{slug}/matches

Parámetros: `season` (year, default current), `round`, `status`, `page`, `per_page`.

---

## 8. ENDPOINTS — PREDICCIONES

### GET /api/v1/predictions/history

Historial de resolución de predicciones del modelo. Separación clara entre estadísticas de negocio y metadatos de paginación.

Parámetros: `league_slug`, `model_version`, `from_date`, `to_date`, `page`, `per_page`.

**Response 200:**
```json
{
  "data": [
    {
      "match_slug": "atletico-madrid-vs-sevilla-2026-06-10",
      "match_date": "2026-06-10",
      "prediction": { "home_win": 0.51, "draw": 0.28, "away_win": 0.21 },
      "actual_outcome": "HOME",
      "correct": true,
      "brier_score": 0.194
    }
  ],
  "stats": {
    "total_predictions": 150,
    "correct_predictions": 73,
    "accuracy_1x2": 0.487,
    "avg_brier_score": 0.221,
    "model_version": "poisson_v1"
  },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

---

## 9. ENDPOINTS — USUARIOS

### GET /api/v1/users/me

**Response 200:**
```json
{
  "id": 42,
  "email": "user@example.com",
  "username": "juanfutbol",
  "full_name": "Juan García",
  "avatar_url": null,
  "role": "free",
  "is_verified": true,
  "created_at": "2026-01-15T10:00:00Z",
  "favorites": {
    "teams": [
      { "name": "Real Madrid", "slug": "real-madrid", "logo_url": "..." }
    ],
    "leagues": [
      { "name": "La Liga", "slug": "la-liga" }
    ]
  }
}
```

---

### PATCH /api/v1/users/me

Actualización parcial del perfil. Solo los campos enviados son actualizados.

**Request:**
```json
{
  "full_name": "Juan García López",
  "avatar_url": "https://..."
}
```

**Response 200:** Objeto usuario actualizado (mismo schema que GET /users/me).

---

### POST /api/v1/users/me/favorites/teams

**Request:**
```json
{ "team_slug": "real-madrid" }
```

**Response 201:**
```json
{ "team": { "name": "Real Madrid", "slug": "real-madrid", "logo_url": "..." } }
```

---

### DELETE /api/v1/users/me/favorites/teams/{slug}

**Response 204:** No content.

---

### POST /api/v1/users/me/favorites/leagues

**Request:**
```json
{ "league_slug": "la-liga" }
```

**Response 201:**
```json
{ "league": { "name": "La Liga", "slug": "la-liga" } }
```

---

### DELETE /api/v1/users/me/favorites/leagues/{slug}

**Response 204:** No content.

---

## 10. ENDPOINTS — ADMIN

Todos requieren rol `admin`.

### GET /api/v1/admin/etl/jobs

Parámetros: `job_name`, `status`, `page`, `per_page`.

**Response 200:**
```json
{
  "data": [
    {
      "id": 501,
      "job_name": "sync_results",
      "source": "api_football",
      "league": "La Liga",
      "status": "SUCCESS",
      "started_at": "2026-06-12T10:00:00Z",
      "finished_at": "2026-06-12T10:00:23Z",
      "duration_ms": 23456.789,
      "records_processed": 45,
      "records_failed": 0,
      "error_message": null
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 280 }
}
```

### POST /api/v1/admin/etl/jobs/trigger

Ejecución manual de un job.

**Request:**
```json
{
  "job_name": "sync_fixtures",
  "league_slug": "la-liga"
}
```

**Response 202:**
```json
{
  "message": "Job sync_fixtures enqueued for la-liga",
  "job_log_id": 502
}
```

---

## 11. SCHEMAS PYDANTIC (REFERENCIA)

```python
# app/schemas/prediction.py

from pydantic import BaseModel
from datetime import datetime

class PredictionProbabilities(BaseModel):
    home_win: float
    draw: float
    away_win: float

class OverUnder(BaseModel):
    over: float | None
    under: float | None

class BTTS(BaseModel):
    yes: float | None
    no: float | None

class PredictionFeatures(BaseModel):
    home_avg_goals_scored: float | None
    home_avg_goals_conceded: float | None
    away_avg_goals_scored: float | None
    away_avg_goals_conceded: float | None
    h2h_home_win_rate: float | None
    home_form_last5: str | None
    away_form_last5: str | None

class PredictionResponse(BaseModel):
    match_slug: str
    model_version: str
    generated_at: datetime
    probabilities: PredictionProbabilities
    over_under_2_5: OverUnder
    btts: BTTS
    expected_goals: dict[str, float] | None
    most_likely_score: str | None
    features: PredictionFeatures | None    # None para usuarios Free
    upgrade_prompt: str | None             # None para usuarios Pro/Admin

    model_config = {"from_attributes": True}
```

---

## 12. MANEJO DE ERRORES

### Formato de error estándar

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Match 'xxx-yyy-zzz' not found",
    "details": {}
  }
}
```

### Códigos de error internos

| HTTP | Code | Situación |
|------|------|-----------|
| 400 | VALIDATION_ERROR | Input inválido (Pydantic) |
| 401 | UNAUTHORIZED | Token ausente o expirado |
| 401 | INVALID_CREDENTIALS | Email/password incorrectos |
| 403 | FORBIDDEN | Rol insuficiente para el recurso |
| 404 | RESOURCE_NOT_FOUND | Recurso no existe |
| 409 | DUPLICATE_RESOURCE | Email o username ya registrado |
| 422 | UNPROCESSABLE_ENTITY | Datos bien formados pero inválidos lógicamente |
| 429 | RATE_LIMIT_EXCEEDED | Demasiadas requests |
| 500 | INTERNAL_ERROR | Error no esperado (registrado en Sentry) |

---

## 13. VERSIONADO Y DEPRECACIÓN

```
Versión actual:  /api/v1/
Próxima versión: /api/v2/  (cuando haya cambios breaking)

Política:
  - Una versión se depreca con mínimo 3 meses de aviso
  - Se agrega header: Deprecation: true, Sunset: <fecha>
  - Se documenta en CHANGELOG.md
  - Las versiones nuevas son aditivas — nuevos campos, nuevos endpoints
  - Los cambios breaking requieren nueva versión mayor
```

---

## 14. OPENAPI Y DOCUMENTACIÓN

FastAPI genera automáticamente OpenAPI 3.0. En local:

```
http://localhost:8000/docs      → Swagger UI interactivo
http://localhost:8000/redoc     → ReDoc (documentación limpia)
http://localhost:8000/openapi.json → Schema JSON exportable
```

Todos los endpoints incluyen:
- Descripción del endpoint
- Tags por módulo (auth, matches, teams, players, leagues, predictions, users, admin)
- Ejemplos de request y response
- Códigos de error documentados
