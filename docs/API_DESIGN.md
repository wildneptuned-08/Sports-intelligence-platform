# API DESIGN
## Sports Intelligence Platform — Fútbol Predictivo

**Versión:** 1.0.0  
**Fecha:** 2026-06-12  
**Especificación:** OpenAPI 3.0  
**Base URL MVP:** `http://localhost:8000/api/v1`  
**Base URL Prod:** `https://api.sip.com/v1`

---

## 1. PRINCIPIOS DE DISEÑO DE LA API

### 1.1 Contratos Fundamentales

- **REST** con convenciones HTTP estándar (verbos, códigos de estado, headers)
- **Versionado en URL:** `/api/v1/`, `/api/v2/` (nunca por header en esta etapa)
- **Plural en recursos:** `/teams`, `/matches`, `/predictions`
- **Respuestas en JSON** con estructura consistente (envelope de respuesta)
- **Paginación cursor-based** para listas grandes; page-based para listas pequeñas
- **HATEOAS mínimo:** incluir `self` link en recursos individuales
- **Idempotencia:** GET, PUT, DELETE son idempotentes; POST no

### 1.2 Envelope de Respuesta

```json
// Éxito (colección)
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "per_page": 20,
    "pages": 8
  },
  "links": {
    "self": "/api/v1/matches?page=1",
    "next": "/api/v1/matches?page=2",
    "prev": null
  }
}

// Éxito (recurso individual)
{
  "data": { ... },
  "meta": {}
}

// Error
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "El campo 'date_from' tiene un formato inválido",
    "details": [
      {
        "field": "date_from",
        "message": "Expected format: YYYY-MM-DD"
      }
    ],
    "trace_id": "abc123xyz"
  }
}
```

### 1.3 Códigos de Estado HTTP Usados

| Código | Cuándo usarlo |
|--------|---------------|
| 200 OK | GET, PUT exitoso |
| 201 Created | POST exitoso que crea recurso |
| 204 No Content | DELETE exitoso |
| 400 Bad Request | Validación de input fallida |
| 401 Unauthorized | Token ausente o inválido |
| 403 Forbidden | Autenticado pero sin permiso |
| 404 Not Found | Recurso no existe |
| 409 Conflict | Violación de restricción única |
| 422 Unprocessable Entity | Semánticamente inválido |
| 429 Too Many Requests | Rate limit superado |
| 500 Internal Server Error | Error no controlado |
| 503 Service Unavailable | Mantenimiento o sobrecarga |

---

## 2. AUTENTICACIÓN Y AUTORIZACIÓN

### 2.1 Esquema JWT

```
Header: Authorization: Bearer <access_token>

Access Token:
  - Algoritmo: HS256 (MVP) → RS256 (Fase 2 con rotación de llaves)
  - Expiración: 15 minutos
  - Payload:
    {
      "sub": "user_id:123",
      "email": "user@example.com",
      "role": "pro",
      "iat": 1718000000,
      "exp": 1718000900,
      "jti": "uuid-único"
    }

Refresh Token:
  - Formato: opaque token (256 bits random, hash SHA-256 almacenado en DB)
  - Expiración: 30 días
  - Entregado en cookie httpOnly + SameSite=Strict
```

### 2.2 Control de Acceso por Rol

| Endpoint | Visitante | Free | Pro | Admin |
|----------|-----------|------|-----|-------|
| GET /matches (listado) | ✓ (limitado) | ✓ | ✓ | ✓ |
| GET /matches/{id}/prediction | ✗ | ✓ (básico) | ✓ (completo) | ✓ |
| GET /predictions/{id}/features | ✗ | ✗ | ✓ | ✓ |
| GET /teams/{id}/advanced-stats | ✗ | ✗ | ✓ | ✓ |
| POST /etl/sync | ✗ | ✗ | ✗ | ✓ |
| GET /admin/* | ✗ | ✗ | ✗ | ✓ |

### 2.3 Rate Limiting

```
Por IP (sin autenticar):    60 req/minuto
Usuario Free:               200 req/minuto
Usuario Pro:                1000 req/minuto
API Key Pro:                2000 req/minuto

Headers de respuesta:
  X-RateLimit-Limit: 200
  X-RateLimit-Remaining: 185
  X-RateLimit-Reset: 1718001000
  Retry-After: 60 (solo en 429)
```

---

## 3. ENDPOINTS DE AUTENTICACIÓN

### `POST /auth/register`

Registro de nuevo usuario.

**Request:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "MiPassword123!",
  "full_name": "Juan García"
}
```

**Response 201:**
```json
{
  "data": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "full_name": "Juan García",
    "role": "free",
    "is_verified": false,
    "created_at": "2026-06-12T10:00:00Z"
  }
}
```

**Validaciones:**
- `email`: formato válido, no existe previamente
- `password`: mínimo 8 chars, 1 mayúscula, 1 número

---

### `POST /auth/login`

**Request:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "MiPassword123!"
}
```

**Response 200:**
```json
{
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 900,
    "user": {
      "id": 1,
      "email": "usuario@ejemplo.com",
      "role": "pro"
    }
  }
}
```
`refresh_token` se entrega en cookie httpOnly.

---

### `POST /auth/refresh`

Usa el refresh token de la cookie para emitir nuevo access token.

**Response 200:** Mismo formato que `/auth/login`

---

### `POST /auth/logout`

Revoca el refresh token actual.

**Response 204:** Sin cuerpo.

---

### `GET /auth/me`

Retorna el perfil del usuario autenticado.

**Response 200:**
```json
{
  "data": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "full_name": "Juan García",
    "role": "pro",
    "subscription_status": "active",
    "subscription_ends_at": "2026-09-12T00:00:00Z"
  }
}
```

---

## 4. ENDPOINTS DE LIGAS

### `GET /leagues`

Lista todas las ligas activas.

**Query params:**
- `country_code` (string): filtrar por país (ej: "ES", "CO")
- `league_type` (string): "league", "cup", "international"
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)

**Response 200:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "La Liga",
      "slug": "laliga-esp",
      "logo_url": "https://cdn.sip.com/leagues/laliga.png",
      "country": {
        "code": "ES",
        "name": "España",
        "flag_url": "https://cdn.sip.com/flags/es.svg"
      },
      "current_season": "2025/26",
      "is_active": true
    }
  ],
  "meta": { "total": 6, "page": 1, "per_page": 20, "pages": 1 }
}
```

---

### `GET /leagues/{slug}`

Detalle de una liga.

**Response 200:**
```json
{
  "data": {
    "id": 1,
    "name": "La Liga",
    "slug": "laliga-esp",
    "logo_url": "...",
    "country": { "code": "ES", "name": "España" },
    "current_season": {
      "id": 10,
      "label": "2025/26",
      "start_date": "2025-08-15",
      "end_date": "2026-05-30"
    },
    "teams_count": 20
  }
}
```

---

### `GET /leagues/{slug}/standings`

Tabla de posiciones de la liga.

**Query params:**
- `season` (string, default: current): "2024/25"

**Response 200:**
```json
{
  "data": {
    "league": { "name": "La Liga", "slug": "laliga-esp" },
    "season": "2025/26",
    "standings": [
      {
        "position": 1,
        "team": {
          "id": 5,
          "name": "FC Barcelona",
          "slug": "barcelona-esp",
          "logo_url": "..."
        },
        "points": 72,
        "played": 30,
        "won": 23,
        "drawn": 3,
        "lost": 4,
        "goals_for": 78,
        "goals_against": 28,
        "goal_difference": 50,
        "form": "WWWDW"
      }
    ]
  }
}
```

---

## 5. ENDPOINTS DE EQUIPOS

### `GET /teams`

**Query params:**
- `league` (string): slug de liga
- `search` (string): búsqueda de texto en nombre
- `page`, `per_page`

**Response 200:** Lista de equipos (estructura compacta)

---

### `GET /teams/{slug}`

Perfil completo de un equipo.

**Response 200:**
```json
{
  "data": {
    "id": 5,
    "name": "FC Barcelona",
    "short_name": "Barça",
    "slug": "barcelona-esp",
    "code": "BAR",
    "logo_url": "...",
    "country": { "code": "ES", "name": "España" },
    "founded_year": 1899,
    "stadium": {
      "name": "Estadi Olímpic Lluís Companys",
      "capacity": 55000,
      "city": "Barcelona"
    },
    "current_squad_size": 25,
    "current_league": {
      "name": "La Liga",
      "slug": "laliga-esp"
    }
  }
}
```

---

### `GET /teams/{slug}/stats`

Estadísticas de temporada del equipo.

**Query params:**
- `season` (string, default: current)
- `league` (string): slug de liga (un equipo puede estar en varias competiciones)

**Response 200:**
```json
{
  "data": {
    "team": { "name": "FC Barcelona", "slug": "barcelona-esp" },
    "season": "2025/26",
    "league": "La Liga",
    "summary": {
      "played": 30,
      "won": 23,
      "drawn": 3,
      "lost": 4,
      "goals_for": 78,
      "goals_against": 28,
      "points": 72
    },
    "attack": {
      "goals_per_game": 2.6,
      "shots_per_game": 14.2,
      "shots_on_target_per_game": 6.1,
      "xg_per_game": 2.1,
      "xg_total": 63.0,
      "xg_overperformance": 15.0
    },
    "defense": {
      "goals_conceded_per_game": 0.93,
      "xga_per_game": 0.85,
      "clean_sheets": 14,
      "ppda": 8.2
    },
    "possession": {
      "avg_possession_pct": 61.3,
      "passes_per_game": 612,
      "pass_accuracy_pct": 87.4
    },
    "form": {
      "last_5": "WWWDW",
      "form_score": 87,
      "home_record": { "won": 14, "drawn": 1, "lost": 0 },
      "away_record": { "won": 9, "drawn": 2, "lost": 4 }
    },
    "ratings": {
      "attack_rating_percentile": 95,
      "defense_rating_percentile": 88,
      "overall_percentile": 92
    }
  }
}
```
*Campos `xg_*`, `ppda`, `*_percentile` requieren rol Pro.*

---

### `GET /teams/{slug}/matches`

Historial y próximos partidos del equipo.

**Query params:**
- `status` (string): "upcoming", "finished", "all"
- `season` (string)
- `limit` (int, default: 10)

---

### `GET /teams/compare`

Comparador head-to-head entre dos equipos.

**Query params:**
- `team1` (string, required): slug
- `team2` (string, required): slug
- `last_n` (int, default: 10): últimos N enfrentamientos

**Response 200:**
```json
{
  "data": {
    "team1": { "name": "Real Madrid", "slug": "real-madrid-esp" },
    "team2": { "name": "FC Barcelona", "slug": "barcelona-esp" },
    "all_time": {
      "team1_wins": 98,
      "draws": 54,
      "team2_wins": 97
    },
    "last_meetings": [
      {
        "match_id": 5432,
        "date": "2026-04-20",
        "home_team": "Real Madrid",
        "away_team": "FC Barcelona",
        "score": "2-1",
        "competition": "La Liga"
      }
    ],
    "last_n_stats": {
      "team1_wins": 6,
      "draws": 2,
      "team2_wins": 2,
      "team1_goals_avg": 1.8,
      "team2_goals_avg": 1.4,
      "btts_rate": 0.7,
      "over25_rate": 0.8
    }
  }
}
```

---

## 6. ENDPOINTS DE PARTIDOS

### `GET /matches`

Lista de partidos con filtros.

**Query params:**
- `date_from` (date): "2026-06-12"
- `date_to` (date): "2026-06-19"
- `league` (string): slug de liga
- `team` (string): slug de equipo (local o visitante)
- `status` (string): "SCHEDULED", "LIVE", "FT"
- `page`, `per_page`

**Response 200:**
```json
{
  "data": [
    {
      "id": 1001,
      "match_date": "2026-06-14T19:00:00Z",
      "status": "SCHEDULED",
      "round": "Regular Season - 36",
      "league": {
        "name": "La Liga",
        "slug": "laliga-esp",
        "logo_url": "..."
      },
      "home_team": {
        "id": 5,
        "name": "FC Barcelona",
        "slug": "barcelona-esp",
        "logo_url": "..."
      },
      "away_team": {
        "id": 2,
        "name": "Real Madrid",
        "slug": "real-madrid-esp",
        "logo_url": "..."
      },
      "score": null,
      "prediction_summary": {
        "prob_home_win": 0.4523,
        "prob_draw": 0.2341,
        "prob_away_win": 0.3136
      }
    }
  ],
  "meta": { "total": 45, "page": 1, "per_page": 20 }
}
```

---

### `GET /matches/today`

Shortcut: partidos del día actual.

**Response:** Igual que `/matches` filtrado por fecha de hoy.

---

### `GET /matches/{id}`

Detalle completo de un partido.

**Response 200:**
```json
{
  "data": {
    "id": 1001,
    "match_date": "2026-06-14T19:00:00Z",
    "status": "FT",
    "round": "Regular Season - 36",
    "venue": {
      "name": "Estadi Olímpic",
      "city": "Barcelona",
      "capacity": 55000
    },
    "referee": { "name": "Mateu Lahoz" },
    "league": { "name": "La Liga", "slug": "laliga-esp" },
    "home_team": {
      "id": 5,
      "name": "FC Barcelona",
      "slug": "barcelona-esp",
      "logo_url": "..."
    },
    "away_team": {
      "id": 2,
      "name": "Real Madrid",
      "slug": "real-madrid-esp",
      "logo_url": "..."
    },
    "score": {
      "full_time": { "home": 3, "away": 2 },
      "half_time": { "home": 1, "away": 1 }
    },
    "winner": "HOME",
    "attendance": 54000
  }
}
```

---

### `GET /matches/{id}/stats`

Estadísticas del partido (post-partido o en vivo).

**Response 200:**
```json
{
  "data": {
    "match_id": 1001,
    "home_stats": {
      "shots_total": 16,
      "shots_on_target": 7,
      "possession_pct": 58.3,
      "passes_total": 623,
      "passes_accuracy": 88.1,
      "fouls": 9,
      "corners": 7,
      "yellow_cards": 2,
      "red_cards": 0,
      "xg": 2.34
    },
    "away_stats": {
      "shots_total": 10,
      "shots_on_target": 4,
      "possession_pct": 41.7,
      "passes_total": 441,
      "passes_accuracy": 81.4,
      "fouls": 14,
      "corners": 3,
      "yellow_cards": 3,
      "red_cards": 0,
      "xg": 1.87
    }
  }
}
```

---

### `GET /matches/{id}/events`

Eventos del partido (goles, tarjetas, sustituciones).

**Response 200:**
```json
{
  "data": [
    {
      "minute": 23,
      "type": "goal",
      "team": "FC Barcelona",
      "player": "Robert Lewandowski",
      "assist": "Lamine Yamal",
      "detail": "Header"
    },
    {
      "minute": 67,
      "type": "yellow_card",
      "team": "Real Madrid",
      "player": "Jude Bellingham"
    }
  ]
}
```

---

### `GET /matches/{id}/lineups`

Alineaciones del partido.

**Response 200:**
```json
{
  "data": {
    "home_team": {
      "formation": "4-3-3",
      "starting_eleven": [
        { "position": "goalkeeper", "jersey": 1, "name": "Marc-André ter Stegen" }
      ],
      "substitutes": []
    },
    "away_team": {
      "formation": "4-2-3-1",
      "starting_eleven": [...],
      "substitutes": [...]
    }
  }
}
```

---

## 7. ENDPOINTS DE PREDICCIONES

### `GET /matches/{id}/prediction`

Predicción del partido para el usuario autenticado.

**Response 200 (usuario Free):**
```json
{
  "data": {
    "match_id": 1001,
    "model": "poisson_v1",
    "generated_at": "2026-06-13T08:00:00Z",
    "probabilities_1x2": {
      "home_win": 0.4523,
      "draw": 0.2341,
      "away_win": 0.3136
    },
    "expected_goals": {
      "home": 1.82,
      "away": 1.31
    },
    "markets": {
      "over_25": { "prob": 0.65 },
      "btts": { "prob": 0.58 }
    },
    "_restricted": ["top_scorelines", "features", "value_bets", "confidence_score"]
  }
}
```

**Response 200 (usuario Pro):**
```json
{
  "data": {
    "match_id": 1001,
    "model": "poisson_v1",
    "model_version": "1.3.2",
    "generated_at": "2026-06-13T08:00:00Z",
    "confidence_score": 0.73,
    "probabilities_1x2": {
      "home_win": 0.4523,
      "draw": 0.2341,
      "away_win": 0.3136
    },
    "expected_goals": {
      "home": 1.82,
      "away": 1.31
    },
    "markets": {
      "over_25": { "prob": 0.65, "implied_odd": 1.54 },
      "over_35": { "prob": 0.38, "implied_odd": 2.63 },
      "btts":    { "prob": 0.58, "implied_odd": 1.72 },
      "home_clean_sheet": { "prob": 0.21 },
      "away_clean_sheet": { "prob": 0.14 }
    },
    "top_scorelines": [
      { "score": "1-1", "prob": 0.0921 },
      { "score": "2-1", "prob": 0.0856 },
      { "score": "1-0", "prob": 0.0812 },
      { "score": "2-0", "prob": 0.0743 },
      { "score": "2-2", "prob": 0.0612 }
    ],
    "value_bets": [
      {
        "market": "over_25",
        "our_prob": 0.65,
        "market_odds_avg": 1.74,
        "implied_prob": 0.575,
        "value": 0.075,
        "recommendation": "VALUE"
      }
    ],
    "features": {
      "home_attack_strength": 1.42,
      "away_attack_strength": 0.98,
      "home_defense_strength": 0.81,
      "away_defense_strength": 1.12,
      "home_form_score": 87,
      "away_form_score": 71,
      "h2h_home_advantage": 0.12,
      "home_goals_avg_5": 2.2,
      "away_goals_avg_5": 1.4,
      "home_xg_avg_5": 1.95,
      "away_xg_avg_5": 1.28,
      "days_since_last_match_home": 7,
      "days_since_last_match_away": 4
    }
  }
}
```

---

### `GET /predictions/history`

Historial de predicciones resueltas con accuracy.

**Query params:**
- `league` (string): slug de liga
- `model` (string, default: "poisson_v1")
- `date_from`, `date_to`
- `page`, `per_page`

**Response 200:**
```json
{
  "data": [
    {
      "match_id": 990,
      "match_date": "2026-06-07T18:00:00Z",
      "home_team": "Atlético Madrid",
      "away_team": "Sevilla",
      "predicted_winner": "HOME",
      "actual_winner": "HOME",
      "correct": true,
      "prob_home_win": 0.52,
      "prob_draw": 0.27,
      "prob_away_win": 0.21,
      "brier_score": 0.186
    }
  ],
  "meta": {
    "total": 120,
    "accuracy_1x2": 0.5417,
    "avg_brier_score": 0.2234
  }
}
```

---

### `GET /predictions/performance`

Métricas de rendimiento del modelo.

**Query params:**
- `league` (string)
- `season` (string)
- `model` (string)

**Response 200:**
```json
{
  "data": {
    "model": "poisson_v1",
    "version": "1.3.2",
    "period": "2025/26",
    "league": "La Liga",
    "total_predictions": 250,
    "metrics": {
      "accuracy_1x2": 0.5240,
      "accuracy_home": 0.6122,
      "accuracy_draw": 0.3021,
      "accuracy_away": 0.5410,
      "avg_brier_score": 0.2201,
      "avg_log_loss": 0.9841,
      "roi_simulation": 0.034
    },
    "confusion_matrix": {
      "HOME_predicted_HOME": 78,
      "HOME_predicted_DRAW": 12,
      "HOME_predicted_AWAY": 8,
      "DRAW_predicted_HOME": 31,
      "DRAW_predicted_DRAW": 21,
      "DRAW_predicted_AWAY": 15,
      "AWAY_predicted_HOME": 22,
      "AWAY_predicted_DRAW": 18,
      "AWAY_predicted_AWAY": 45
    }
  }
}
```

---

## 8. ENDPOINTS DE JUGADORES

### `GET /players`

**Query params:**
- `team` (string): slug de equipo
- `position` (string): "goalkeeper", "defender", "midfielder", "forward"
- `search` (string): búsqueda de texto
- `page`, `per_page`

---

### `GET /players/{slug}`

Perfil de jugador.

**Response 200:**
```json
{
  "data": {
    "id": 501,
    "name": "Robert Lewandowski",
    "slug": "lewandowski-pol",
    "date_of_birth": "1988-08-21",
    "age": 37,
    "nationality": { "code": "PL", "name": "Polonia" },
    "height_cm": 185,
    "weight_kg": 81,
    "photo_url": "...",
    "current_team": {
      "name": "FC Barcelona",
      "slug": "barcelona-esp",
      "position": "forward",
      "jersey_number": 9
    }
  }
}
```

---

### `GET /players/{slug}/stats`

Estadísticas de temporada del jugador.

**Query params:**
- `season` (string, default: current)
- `competition` (string): slug de liga o copa

**Response 200:**
```json
{
  "data": {
    "player": { "name": "Robert Lewandowski" },
    "season": "2025/26",
    "team": "FC Barcelona",
    "competition": "La Liga",
    "appearances": 28,
    "starts": 26,
    "minutes": 2340,
    "goals": 22,
    "assists": 7,
    "yellow_cards": 3,
    "red_cards": 0,
    "shots_total": 98,
    "shots_on_target": 54,
    "shot_accuracy_pct": 55.1,
    "passes_accuracy_pct": 77.3,
    "dribbles_completed": 28,
    "avg_rating": 7.42,
    "advanced": {
      "xg": 19.3,
      "xa": 5.8,
      "npxg": 18.1,
      "xg_overperformance": 2.7,
      "goals_per_90": 0.85,
      "xa_per_90": 0.22
    }
  }
}
```
*Campos `advanced` requieren rol Pro.*

---

## 9. ENDPOINTS DE ODDS

### `GET /matches/{id}/odds`

Odds actuales de bookmakers para el partido.

**Requiere:** rol Free o superior.

**Response 200:**
```json
{
  "data": {
    "match_id": 1001,
    "last_updated": "2026-06-13T12:00:00Z",
    "markets": {
      "1x2": {
        "avg": { "home": 2.10, "draw": 3.40, "away": 3.60 },
        "best": { "home": 2.20, "draw": 3.60, "away": 3.80 },
        "bookmakers": [
          { "name": "Bet365", "home": 2.10, "draw": 3.30, "away": 3.50 },
          { "name": "Betfair", "home": 2.20, "draw": 3.60, "away": 3.80 }
        ]
      },
      "over_under_25": {
        "line": 2.5,
        "avg_over": 1.78,
        "avg_under": 2.10
      }
    }
  }
}
```

---

## 10. ENDPOINTS DE ADMINISTRACIÓN

### `GET /admin/etl/jobs`

Lista de jobs ETL recientes.

**Requiere:** rol Admin.

**Response 200:**
```json
{
  "data": [
    {
      "id": 890,
      "job_name": "sync_fixtures",
      "source": "api_football",
      "league": "La Liga",
      "status": "SUCCESS",
      "records_fetched": 10,
      "records_created": 2,
      "records_updated": 8,
      "started_at": "2026-06-12T06:00:00Z",
      "duration_ms": 1234
    }
  ]
}
```

---

### `POST /admin/etl/trigger`

Dispara un job ETL manualmente.

**Request:**
```json
{
  "job_name": "sync_fixtures",
  "league_slug": "laliga-esp",
  "season": "2025/26"
}
```

**Response 202:**
```json
{
  "data": {
    "job_id": 891,
    "status": "PENDING",
    "message": "Job encolado exitosamente"
  }
}
```

---

### `POST /admin/predictions/generate`

Fuerza el recálculo de predicciones para un partido.

**Request:**
```json
{
  "match_id": 1001,
  "model": "poisson_v1"
}
```

**Response 202:** Confirmación de encolamiento.

---

### `GET /admin/users`

Lista de usuarios con filtros.

**Query params:**
- `role` (string): "free", "pro"
- `search` (string): email o nombre
- `page`, `per_page`

---

## 11. ENDPOINTS DE USUARIO

### `GET /users/me/favorites`

Lista de favoritos del usuario.

**Response 200:**
```json
{
  "data": {
    "teams": [
      { "id": 5, "name": "FC Barcelona", "slug": "barcelona-esp" }
    ],
    "leagues": [
      { "id": 1, "name": "La Liga", "slug": "laliga-esp" }
    ]
  }
}
```

---

### `POST /users/me/favorites`

Agrega un favorito.

**Request:**
```json
{
  "entity_type": "team",
  "entity_id": 5
}
```

**Response 201:** Confirmación.

---

### `DELETE /users/me/favorites/{entity_type}/{entity_id}`

Elimina un favorito.

**Response 204:** Sin cuerpo.

---

## 12. SCHEMAS PYDANTIC CLAVE

### MatchResponse
```python
class MatchResponse(BaseModel):
    id: int
    match_date: datetime
    status: MatchStatus
    round: str | None
    league: LeagueCompact
    home_team: TeamCompact
    away_team: TeamCompact
    score: ScoreDetail | None
    winner: str | None
    prediction_summary: PredictionSummary | None

    model_config = ConfigDict(from_attributes=True)
```

### PredictionResponse (estratificada por rol)
```python
class PredictionBasic(BaseModel):
    match_id: int
    model: str
    generated_at: datetime
    probabilities_1x2: Probabilities1X2
    expected_goals: ExpectedGoals
    markets: MarketsBasic

class PredictionPro(PredictionBasic):
    confidence_score: float
    top_scorelines: list[ScoretlineProb]
    value_bets: list[ValueBet]
    features: dict[str, float]
```

---

## 13. WEBSOCKETS (FASE 2)

### `WS /ws/matches/{id}/live`

Actualizaciones en tiempo real para partidos en vivo.

**Mensaje del servidor:**
```json
{
  "type": "SCORE_UPDATE",
  "data": {
    "match_id": 1001,
    "minute": 67,
    "home_goals": 2,
    "away_goals": 1,
    "event": {
      "type": "goal",
      "player": "Lamine Yamal",
      "minute": 67
    }
  }
}
```

**Tipos de mensaje:**
- `SCORE_UPDATE` — cambio de marcador
- `MATCH_STATUS` — cambio de estado (HT, FT)
- `STATS_UPDATE` — actualización de estadísticas de partido
- `PREDICTION_UPDATE` — predicción recalculada por evento de partido

---

## 14. VERSIONADO Y DEPRECACIÓN

```
Política de versionado:
  - Versión en URL: /api/v1/, /api/v2/
  - Una versión mayor nueva requiere 6 meses de soporte de la versión anterior
  - Breaking changes NUNCA en la misma versión mayor
  - Deprecation notice: header "Deprecation: true" + "Sunset: <fecha>"
  - Changelog publicado en /api/changelog

Breaking changes (requieren nueva versión mayor):
  - Remover campo del response
  - Cambiar tipo de dato de campo existente
  - Cambiar semántica de parámetro existente

Non-breaking changes (pueden ir en misma versión):
  - Agregar campos opcionales al response
  - Agregar nuevos endpoints
  - Agregar parámetros opcionales de query
```
