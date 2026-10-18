# AGRIFY — System Architecture & Topology (ARCHITECTURE.md)

**Status:** Current Implementation Audit & Engineering Baseline
**Version:** 3.0-production
**Updated:** October 2026

---

## 1. High-Level System Architecture

AGRIFY is structured as a decoupled multi-service architecture comprising a client web bundle, a primary Flask analytical API, an isolated TensorFlow deep learning vision microservice, and external agricultural data ETL pipelines.

```
+-------------------------------------------------------------------------+
|                                FRONTEND                                 |
|               Vite + Vanilla JavaScript (ES Modules, Port 5173)         |
|  - Router & App Shell (`app.js`, `navbar.js`)                           |
|  - 8 Route Modules (Home, Analysis, Weather, Market, CropDoctor, etc.)  |
|  - Voice Assistant Modal & Web Speech Engine (`voiceAssistantModal.js`) |
+------------------------------------+------------------------------------+
                                     |
                +--------------------+--------------------+
                | REST / JSON                             | Multipart / Form
                v                                         v
+----------------------------------+    +----------------------------------+
|           BACKEND API            |    |       DISEASE MICROSERVICE       |
|    Flask 3.0.3 (Port 5000)       |    |   Flask + TensorFlow 2.21 (5001) |
| - Health & Coordinate Validation |    | - Upload Validation (MIME, 5MB)  |
| - Feasibility & Agronomic Rules  |    | - MobileNetV2 (Potato Model)     |
| - Action Plan Engine             |    | - Multilingual Treatment DB      |
| - AI Voice Gateway (Gemini/OAI)  |    +----------------------------------+
| - ETL Orchestration Pipelines    |
+-----------------+----------------+
                  |
        +---------+---------+
        |                   |
        v                   v
+---------------+   +------------------------------------------------------+
|  POSTGRESQL   |   |                   EXTERNAL SERVICES                  |
|  (SQLAlchemy) |   | - OpenWeatherMap API (Current & 5-Day Forecast)      |
| - 10 Models   |   | - ISRIC SoilGrids v2.0 REST API (Soil nutrients)     |
| - Defined in  |   | - Agmarknet (data.gov.in) (Mandi wholesale rates)    |
|   database.py |   | - Nominatim / BigDataCloud (Reverse Geocoding)       |
+---------------+   | - Google Gemini 2.5 Flash / OpenAI GPT-4o-mini       |
                    +------------------------------------------------------+
```

---

## 2. Service Breakdown & Responsibilities

### 2.1 Frontend Client (`/frontend`) — **VERIFIED**
- **Runtime:** Browser (ES6 modules, zero heavy framework overhead).
- **Build Tool:** Vite 7.3.1 (`npm run build` compiles to static `dist/` bundle: HTML ~2.6KB, CSS ~196KB, JS ~263KB in ~174ms).
- **API Communication (`frontend/js/api.js`):**
  - Automatically identifies local development (`localhost` or `127.0.0.1`) versus production Render deployment (`https://agri-connect-main-app.onrender.com`).
  - **macOS Port Conflict Handling:** Binds explicit `127.0.0.1:5000` rather than `localhost:5000` to prevent macOS AirPlay Receiver (`*:5000`) request hijacking.
  - **Documented Gap:** Line 7 hardcodes `DISEASE_API_BASE = 'https://agri-connect-image.onrender.com'`. Unlike `getApiBase()`, it does not branch to `http://127.0.0.1:5001` for local development.

### 2.2 Primary Backend API (`/backend`) — **VERIFIED (Code & Unit Tests)**
- **Runtime:** Python 3.12, Flask 3.0.3, Gunicorn 20.1.0.
- **Port:** 5000 (Manual launch; not running as a persistent daemon in this audit).
- **Responsibilities:**
  - Coordinate validation and sanitation (rejects NaN, Infinity, and latitude/longitude outside WGS84 bounds before triggering network I/O).
  - Agronomic feasibility filtering (`CROP_PROFILES` with rainfall, temperature, pH, and nitrogen threshold constraints).
  - 7-Day Farm Action Plan synthesis (`backend/action_plan.py`).
  - Voice Assistant orchestration (`backend/voice_assistant.py`) and Agent Core subsystem (`backend/agent/`).
  - ETL retrieval for weather, soil, news, and market prices.

### 2.3 Image Disease Microservice (`/image_detection`) — **VERIFIED (Model & Validation)**
- **Runtime:** Python 3.12, Flask 3.0.3, TensorFlow 2.21.0, Keras 3.15.1.
- **Port:** 5001 (Production: `https://agri-connect-image.onrender.com`).
- **Memory Footprint Controls:**
  - `TF_CPP_MIN_LOG_LEVEL='2'`
  - Single-threaded CPU execution (`set_inter_op_parallelism_threads(1)`, `set_intra_op_parallelism_threads(1)`).
  - Explicitly configured for cloud containers with 512MB RAM limits (e.g. Render Free Tier).
- **Validation Pipeline:** Pre-ingestion validation (`upload_validation.py`) verifying file extensions (`.jpg`, `.jpeg`, `.png`, `.webp`), magic byte headers, and a strict 5MB payload limit. Passes 4 unit tests.
- **Service Status:** Model file is verified on disk (`potato_disease_model.keras`, 9.6MB) and loads in Keras. Local HTTP service endpoint invocation via browser/client is **IMPLEMENTED BUT UNVERIFIED** because port 5001 is not running locally during audit.

---

## 3. Data Integration & ETL Pipelines (`backend/etl/`)

1. **Market ETL (`market_etl.py`) — VERIFIED (Caching & Fallback):**
   - Connects to official Indian APMC Mandi database via `data.gov.in` (Agmarknet).
   - **In-Memory Cache:** Implemented via `_market_cache` dictionary with a 600-second (10-minute) TTL (`_CACHE_TTL = 600`).
   - Offline fallback preserving data provenance indicators (`is_fallback: true`, `data_quality: "unavailable"`).
2. **Weather ETL (`weather_etl.py`) — VERIFIED (No Caching):**
   - Direct coordinate querying of OpenWeatherMap One Call / Weather 2.5 API.
   - Extracts temperature, humidity, wind, rainfall probability, and UV index.
   - *Note:* Queries live on demand; **no backend caching is implemented**.
3. **Soil ETL (`soil_etl.py`) — VERIFIED (No Caching):**
   - Queries ISRIC SoilGrids v2.0 REST API for depth-averaged Nitrogen, Phosphorus, Potassium, pH, and Organic Carbon.
   - Falls back to regional Indian agro-climatic heuristics (`REGION_SOIL_PROFILES`) if SoilGrids is rate-limited or unreachable.
   - *Note:* Queries live on demand; **no backend caching is implemented**.
4. **Geocoding ETL (`geocoding_etl.py`) — VERIFIED:**
   - OpenStreetMap Nominatim reverse geocoding with user-agent headers and fallback to BigDataCloud.

---

## 4. AI Gateway & Multi-Provider Architecture (`backend/agent/gateway.py`)

- **Primary AI Provider:** Configured via `AI_PROVIDER_PRIMARY` (`gemini`, `openai`, or `auto`).
- **Execution Strategy:**
  1. Primary provider invocation with strict timeout (`AI_PROVIDER_TIMEOUT_SECONDS`, default 12s).
  2. If primary throws network error, authentication failure, or invalid JSON, automatically chains to secondary provider.
  3. If all external AI providers fail, execution seamlessly falls back to the local deterministic rule engine (`LOCALIZED_TEMPLATES` in `voice_assistant.py`).
- **Verification Status:** Fallback logic verified in unit test suite (`test_gateway_3f1.py`) with mocked provider responses (59 passed, 1 skipped). Live end-to-end multi-provider fallback against live external AI networks is **UNVERIFIED / UNTESTED** in this offline audit.
- **Data Privacy & API Key Protection:** API keys and credentials are stripped from all public classes, response payloads, and client-facing error objects.

---

## 5. Security & Network Configuration Status

- **CORS Configuration:** Currently set to open wildcard (`CORS(app, origins="*")` in `backend/api.py` and `image_detection/app.py`). Requires configuration to restrict origins to verified domains in production while retaining `127.0.0.1` and `localhost` for development. (**SECURITY GAP**)
- **Rate Limiting:** Currently unthrottled at the Flask application layer. Reverse proxy or Flask-Limiter controls are recommended for `/api/assistant/query`, `/api/chat`, and `/api/predict`. (**SECURITY GAP**)
