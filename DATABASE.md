# AGRIFY — Database Architecture & Data Dictionary (DATABASE.md)

**Status:** Current Implementation Audit & Schema Verification Baseline
**Version:** 4.0-production
**Updated:** October 2026

---

## 1. Database Overview & Technology Stack

- **ORM:** SQLAlchemy 2.0.31 / Flask-SQLAlchemy 3.1.1.
- **Engine Target:** PostgreSQL (Production) / SQLite (Isolated Testing).
- **Driver:** `psycopg2-binary` 2.9.9.
- **Migration Framework:** Alembic 1.13.2 (`backend/alembic.ini`, `backend/migrations/`).
- **Connection Variable:** `DATABASE_URL` (configured via environment).
- **Configuration & Connection Management (`backend/database_config.py`):**
  - Normalizes legacy driver schemes (e.g. `postgres://` -> `postgresql://` required by SQLAlchemy 2.x).
  - Configures production connection pooling with `pool_pre_ping=True`, `pool_recycle=1800`, and `pool_timeout=30`.
  - Fallback: When `DATABASE_URL` is omitted, the API defaults to a safe in-memory fallback, and `is_db_available()` signals stateless mode without raising errors.

---

## 2. Entity-Relationship & Model Schema (11 Models Total)

All **11 database models** reside in `backend/models/database.py`. Every domain record incorporates audit trail metadata: `source_url`, `fetch_timestamp`, and `data_quality` (`live`, `estimated`, `cached`, `official`).

```
+-----------------------------------------------------------------+
|                          farm_profiles                          |
+-----------------------------------------------------------------+
| PK id                   : Integer                               |
|    farm_uid             : String(64) UNIQUE (SHA256 lat+lon+usr)|
|    farmer_name          : String(128)                           |
|    latitude, longitude  : Float (NOT NULL)                      |
|    area_acres           : Float                                 |
|    village, taluk       : String(128)                           |
|    district, state      : String(128)                           |
|    owner_token_hash     : String(64) (HMAC-SHA256 of auth token)|
|    geocode_source, url  : String(64), Text                      |
|    created_at           : DateTime(timezone=True)               |
+--------------------------------+--------------------------------+
                                 |
         +-----------------------+-----------------------+
         | 1:N                                           | 1:N
         v                                               v
+-------------------------------+               +-------------------------------+
|       weather_snapshots       |               |        soil_summaries         |
+-------------------------------+               +-------------------------------+
| PK id           : Integer     |               | PK id           : Integer     |
| FK farm_id      : Integer     |               | FK farm_id      : Integer     |
|    lat, lon     : Float       |               |    lat, lon     : Float       |
|    temperature  : Float       |               |    nitrogen     : Float       |
|    humidity     : Float       |               |    phosphorus   : Float       |
|    rainfall_1h  : Float       |               |    potassium    : Float       |
|    wind_speed   : Float       |               |    soil_ph      : Float       |
|    weather_desc : String(128) |               |    organic_carb : Float       |
|    data_quality : String(16)  |               |    soil_type    : String(64)  |
|    fetch_ts     : DateTime    |               |    data_quality : String(16)  |
+-------------------------------+               +-------------------------------+
                                 | 1:N
                                 v
+---------------------------------------------------------------+
|                      crop_recommendations                     |
+---------------------------------------------------------------+
| PK id                      : Integer                          |
| FK farm_id                 : Integer                          |
|    top_crops_json          : Text (JSON array of crops)       |
|    all_feasible_json       : Text (JSON array of feasibility) |
|    temperature_c, humidity : Float                            |
|    soil_n, soil_p, soil_k  : Float                            |
|    created_at              : DateTime                         |
+--------------------------------+------------------------------+
                                 | 1:N
                                 v
+---------------------------------------------------------------+
|                       farm_action_plans                       |
+---------------------------------------------------------------+
| PK id                      : Integer                          |
| FK farm_id                 : Integer                          |
| FK crop_recommendation_id  : Integer                          |
|    crop_name               : String(128)                      |
|    season, location_str    : String(32), String(256)          |
|    summary                 : Text                             |
|    immediate_actions_json  : Text (JSON array of actions)     |
|    this_week_plan_json     : Text (JSON array of daily tasks) |
|    disclaimer              : Text                             |
|    data_quality            : String(16)                       |
|    created_at, updated_at  : DateTime                         |
+---------------------------------------------------------------+
```

### Complete Inventory of Defined Models:
1. `FarmProfile` (`farm_profiles`): GPS-captured farm metadata with HMAC-SHA256 ownership verification.
2. `WeatherSnapshot` (`weather_snapshots`): Real-time coordinate weather conditions.
3. `WeatherForecast` (`weather_forecasts`): Daily aggregated 5-day forecasts.
4. `SoilSummary` (`soil_summaries`): Satellite and lab soil nutrient data.
5. `CropRecommendation` (`crop_recommendations`): Top ranked crop recommendations.
6. `DistrictCropHistory` (`district_crop_history`): Historical crop yield with unique constraint `('state', 'district', 'crop', 'year', 'season')`.
7. `SatelliteSummary` (`satellite_summaries`): Earth Engine indices (`ndvi`, `ndwi`, `evi`).
8. `AgricultureNews` (`agriculture_news`): Deduplicated news articles (`article_hash`).
9. `DiseaseDetection` (`disease_detections`): Plant foliar pathology screening history.
10. `FarmAlert` (`farm_alerts`): Contextual agronomic alerts.
11. `FarmActionPlan` (`farm_action_plans`): Prioritized 7-day agronomic execution plan.

---

## 3. Database Migrations Pipeline (Alembic)

Database schema evolution is managed via Alembic (`backend/migrations/`):
- **`0001_initial_10_models.py`**: Baseline schema creating the initial 10 core tables, foreign keys, and indexes.
- **`0002_farm_ownership_and_action_plans.py`** (revision `0002_ownership_action_plans`): Adds `owner_token_hash` to `farm_profiles` and creates the `farm_action_plans` table. Shortened to 27 characters to strictly comply with PostgreSQL `alembic_version.version_num` VARCHAR(32) constraint.
- **Batch Alteration Support:** `render_as_batch=True` enabled in `env.py` to allow uniform migration execution across PostgreSQL, SQLite, and MySQL dialects.
- **Verification Status:** Upgrade to `head` and downgrade to `base` verified via test automation.

---

## 4. Farm Ownership & Multi-Tenant Authorization (`backend/auth.py`)

To ensure strict farmer isolation without requiring heavy identity provider dependencies:
- **Token Generation:** On profile creation (`POST /api/farm/profile`), a high-entropy URL-safe token (`agf_<uuid>_<random>`) is generated and returned to the farmer once.
- **Secure Hashing:** The database stores only an HMAC-SHA256 hash computed with server salt (`owner_token_hash`). Plain-text tokens are never persisted or exposed in API responses.
- **Request Authorization:** Protected endpoints extract tokens from `X-Farm-Token`, `Authorization: Bearer <token>`, or the request body.
- **Constant-Time Verification:** Hash matching uses `hmac.compare_digest` to prevent timing attacks.
- **Access Control:**
  - Missing token: **401 Unauthorized**.
  - Token belonging to another farm: **403 Forbidden**.
  - Verified token: **200 OK**.

---

## 5. Runtime Persistence Implementation & Transaction Safety — **VERIFIED**

### 5.1 Active Endpoints
- `POST /api/farm/profile`: Creates or updates a farm profile, returning `farm_uid` and `owner_token`.
- `GET /api/farm/profile/<farm_uid>`: Retrieves farm metadata (protected by owner token).
- `GET /api/farm/history/<farm_uid>`: Retrieves chronological history of weather snapshots, soil summaries, crop recommendations, and action plans (protected by owner token).
- `GET /api/farm/action-plans/<farm_uid>`: Retrieves all saved 7-day action plans for the farm (protected by owner token).
- `POST /api/farm/analyze`: When `farm_uid` and valid token are provided, atomically records `WeatherSnapshot`, `SoilSummary`, and `CropRecommendation` in a single transaction.
- `POST /api/farm/action-plan`: When `farm_uid` and valid token are provided, persists the generated `FarmActionPlan`.

### 5.2 Transactional Integrity
Multi-table inserts are wrapped in `try ... db.session.commit() except ... db.session.rollback()`:
- If any insert fails, the session rolls back completely, ensuring no orphaned child records or corrupt states.
- Verified in automated test `test_transaction_rollback_on_failure`.

### 5.3 Stateless Fallback Mode
- If `DATABASE_URL` is omitted, the API operates statelessly. Calls to `/api/farm/analyze` and `/api/farm/action-plan` continue to compute full agronomic results and return `{ "persistence": { "persisted": false } }` without 500 errors.

---

## 6. Verification Status & Test Evidence

All database configuration, ownership, and persistence workflows are covered in `backend/test_database_persistence.py`:
- **Configuration tests:** PostgreSQL URL normalization, engine connection pooling.
- **Cryptographic tests:** Token entropy, HMAC-SHA256 hashing, timing-safe verification.
- **CRUD & Persistence tests:** Farm profile registration, multi-table atomic analysis storage, action plan saving.
- **Security & Isolation tests:** Unauthorized access rejection (401), cross-tenant access rejection (403).
- **Resilience tests:** Clean rollback on injected transaction error, stateless fallback execution.
- **Migration & Drill:** Alembic upgrade -> downgrade -> upgrade migration drill fully executed against SQLite/PostgreSQL schema.
- **Backend Test Suite Total:** **114 tests executed** (114 passed, 5 skipped live network opt-ins).
