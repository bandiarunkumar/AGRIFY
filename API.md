# AGRIFY — API Specification & Endpoint Contracts (API.md)

**Status:** Current Implementation Audit & Contract Verification Baseline
**Version:** 3.0-production
**Updated:** October 2026

---

## 1. System Endpoints Overview

The AGRIFY ecosystem exposes endpoints across two internal services:
- **Core Flask API Service:** Default port `5000` (Production: `https://agri-connect-main-app.onrender.com`).
- **Disease Vision AI Microservice:** Default port `5001` (Production: `https://agri-connect-image.onrender.com`).

*Notice on Response Formats:* The schemas below describe actual HTTP contracts. JSON values in this document represent **illustrative sample payloads** for structural reference and do not represent live production data guarantees.

Client validation errors return HTTP `400` with `{"status": "error", "error": "<description>"}`. Payload size limit breaches return HTTP `413`. Database persistence is **VERIFIED** via PostgreSQL/SQLite with stateless fallback mode when `DATABASE_URL` is omitted.

---

## 2. Core API Service Endpoints (`backend/api.py`)

### 2.1 Health Check — **VERIFIED**
- **Endpoint:** `GET /api/health`
- **Illustrative Response:**
  ```json
  {
    "status": "healthy",
    "app": "Agri-Connect API",
    "version": "3.0-production",
    "database": "disabled (no DATABASE_URL)",
    "timestamp": "2026-10-17T16:00:00.000000+00:00"
  }
  ```

### 2.2 Geocoding & Coordinates — **VERIFIED**
- **Endpoint:** `GET /api/geocode/reverse`
- **Query Params:** `lat` (Float, -90 to 90), `lon` (Float, -180 to 180)
- **Validation:** Rejects non-numeric, NaN, and out-of-range coordinates with `400 Bad Request`.
- **Illustrative Response:**
  ```json
  {
    "ok": true,
    "village": "Gachibowli",
    "taluk": "Serilingampally",
    "district": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "pincode": "500032",
    "source": "nominatim"
  }
  ```

### 2.3 Weather & Forecast — **VERIFIED (Live Queries, No Backend Cache)**
- **Endpoints:**
  - `GET /api/weather/coords?lat={lat}&lon={lon}`
  - `GET /api/forecast/coords?lat={lat}&lon={lon}`
  - `GET /api/weather?city={city}`
  - `GET /api/forecast?city={city}`
- **Illustrative Response (`/api/weather/coords`):**
  ```json
  {
    "ok": true,
    "temperature": 28.5,
    "feels_like": 30.1,
    "humidity": 65,
    "rainfall": 0.0,
    "wind_speed": 3.6,
    "description": "scattered clouds",
    "icon": "03d",
    "source_url": "https://api.openweathermap.org/...",
    "data_quality": "live"
  }
  ```

### 2.4 Soil Analysis — **VERIFIED (Live Queries, No Backend Cache)**
- **Endpoints:**
  - `GET /api/soil/coords?lat={lat}&lon={lon}`
  - `POST /api/soil-analysis`
- **Illustrative Response (`/api/soil/coords`):**
  ```json
  {
    "ok": true,
    "nitrogen": 45.2,
    "phosphorus": 32.1,
    "potassium": 28.4,
    "ph": 6.8,
    "organic_carbon": 0.75,
    "soil_type": "Loamy",
    "source_name": "soilgrids_isric",
    "data_quality": "estimated"
  }
  ```

### 2.5 Farm Analysis & Crop Feasibility — **VERIFIED (Rule-Based, Stateless)**
- **Endpoint:** `POST /api/farm/analyze`
- **Request Payload Contract:**
  ```json
  {
    "latitude": 17.385,
    "longitude": 78.486,
    "farmer_name": "Ramesh",
    "area_acres": 2.5,
    "season": "Kharif",
    "soil_n": 50,
    "soil_p": 40,
    "soil_k": 30,
    "soil_ph": 6.5
  }
  ```
- **Illustrative Response:**
  ```json
  {
    "status": "success",
    "location": { "village": "...", "district": "Hyderabad", "state": "Telangana" },
    "weather": { "temperature": 28.5, "humidity": 65, "rainfall": 120 },
    "soil": { "nitrogen": 50, "phosphorus": 40, "potassium": 30, "ph": 6.5 },
    "feasible_crops": [
      { "crop": "rice", "suitability_score": 92.5, "season": "Kharif" }
    ],
    "action_plan_available": true
  }
  ```

### 2.6 APMC Mandi Market Prices — **VERIFIED (In-Memory TTL Cache: 600s)**
- **Endpoint:** `POST /api/market-prices`
- **Request Payload Contract:**
  ```json
  { "crop": "tomato", "state": "Telangana", "district": "Hyderabad" }
  ```
- **Illustrative Response (Live Agmarknet Data):**
  ```json
  {
    "ok": true,
    "commodity": "Tomato",
    "markets": [
      { "name": "Bowenpally", "district": "Hyderabad", "price_per_kg": 22.5, "price_per_quintal": 2250 }
    ],
    "avg_price_per_kg": 22.5,
    "best_market": "Bowenpally",
    "is_fallback": false,
    "data_quality": "live",
    "source_name": "agmarknet_datagov"
  }
  ```

### 2.7 AI Voice Assistant Query — **VERIFIED (Rule Engine & Gateway Tests)**
- **Endpoint:** `POST /api/assistant/query`
- **Request Payload Contract:**
  ```json
  {
    "query": "What fertilizer should I apply for rice?",
    "language": "en",
    "context": {
      "crop": "rice",
      "location": "Telangana",
      "soil": { "N": 50, "P": 40, "K": 30 }
    }
  }
  ```
- **Illustrative Response (Agronomic Safety Guardrail Activated — Untrusted Dosage):**
  ```json
  {
    "status": "success",
    "intent": "fertilizer",
    "spoken_response": "AGRIFY does not have a verified fertilizer dosage for this specific field. Please check your Farm Analyzer report or consult your local agricultural extension officer before applying chemicals.",
    "display_card": {
      "title": "Nutrient Advisory (Advisory Only)",
      "key_points": [
        "No verified chemical dosage on file for this specific field",
        "Consult local KVK or Agriculture Extension Officer",
        "Conduct physical soil test to determine precise N-P-K requirement"
      ],
      "action_route": "/analysis"
    },
    "provider": "rule_engine"
  }
  ```
  *(Note: Strict safety guardrails forbid fabricating chemical dosage quantities when unverified.)*

### 2.8 Legacy Tabular Prediction Endpoints — **MIGRATED (Phase 2)**
- **Endpoints:**
  - `POST /api/predict/crop` — **MIGRATED** to ICAR agronomic feasibility engine
  - `POST /api/predict/fertilizer` — **GUARDED** (HTTP 503 with safety advisory)
- **`/api/predict/crop` Behavior (Migrated):**
  - **Required fields:** `N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall` (numeric, finite).
  - **Optional fields:** `region`, `season`.
  - **HTTP 200** response with `best_crop`, `alternatives` (top 4), `input_summary`, `engine: "agronomic_feasibility_v3"`.
  - Validation: Missing fields → 400; non-numeric/NaN/Inf → 400; booleans → 400.
- **`/api/predict/fertilizer` Behavior (Safety Guarded):**
  - **Required fields:** `soil_type`, `soil_ph`, `soil_moisture`, `organic_carbon`, `electrical_conductivity`, `N`, `P`, `K`, `temperature`, `humidity`, `rainfall`, `crop_type`, `growth_stage`, `season`, `irrigation`, `previous_crop`, `region`, `fertilizer_usage`, `yield_last`.
  - **HTTP 503** with `status: "unavailable"`, `advisory` referencing KVK/extension officer.
  - Agronomic safety guardrail: no chemical dosages fabricated.
- **Frontend:** `predictCrop()` and `predictFertilizer()` in `api.js` marked `@deprecated`. Removed from `analysis.js` imports (no active UI callers).
- **Tests:** 7 focused tests in `backend/test_legacy_endpoints.py` — all pass.

### 2.9 Farm Profile, Action Plans & History Persistence — **VERIFIED**
- **Endpoints:**
  - `POST /api/farm/profile` — Register or update a farm profile; returns `farm_uid` and `owner_token`.
  - `GET /api/farm/profile/<farm_uid>` — Retrieve farm profile metadata (requires Bearer `owner_token`).
  - `DELETE /api/farm/profile/<farm_uid>` — Delete farm profile (requires Bearer `owner_token`).
  - `POST /api/farm/profile/<farm_uid>/rotate-token` — Rotate owner token (requires current Bearer `owner_token`).
  - `GET /api/farm/history/<farm_uid>` — Retrieve historical crop recommendations, weather snapshots, and soil summaries (requires Bearer `owner_token`).
  - `GET /api/farm/action-plans/<farm_uid>` — Retrieve 7-day action plans persisted for this farm (requires Bearer `owner_token`).
  - `POST /api/farm/action-plan` — Generate 7-day action plan; persists to database when `farm_uid` and valid token are provided.
- **Access Control:** HMAC-SHA256 token verification with `hmac.compare_digest`. Rejects missing token (401), invalid/cross-farm token (403).
- **Tests:** Covered in `backend/test_database_persistence.py` (30 tests) and `backend/test_e2e_integration_phase5.py` (7 tests).

---

## 3. Disease Vision AI Service Endpoints (`image_detection/app.py`)

### 3.1 Plant Foliar Pathology Screening — **VERIFIED (Local Model Inference & Upload Validation)**
- **Endpoint:** `POST /api/predict` (Service port 5001)
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `file`: Image binary (JPG, PNG, WEBP, max 5MB).
  - `language`: `en`, `te`, `hi`, `mr` (default `en`).
- **Validation:** Enforces 5MB limit (`413 Request Entity Too Large`), validates file headers and extensions (`upload_validation.py`). Passes 4 unit tests.
- **Scope Limit:** Model file is verified on disk (`potato_disease_model.keras`) and exclusively screens **Potato leaves** for Early Blight, Late Blight, or Healthy tissue.
- **Illustrative Response (Supported Disease):**
  ```json
  {
    "status": "success",
    "is_recognized": true,
    "diagnosis": "Early Blight",
    "confidence": 0.942,
    "medicine": "Mancozeb or Chlorothalonil",
    "action_plan": "Apply fungicide immediately. Ensure good airflow.",
    "all_scores": [
      { "class": "Potato___Early_blight", "score": 0.942 },
      { "class": "Potato___Late_blight", "score": 0.045 },
      { "class": "Potato___healthy", "score": 0.013 }
    ]
  }
  ```
- **Illustrative Response (Confidence < 65% or Unrecognized Leaf):**
  ```json
  {
    "status": "success",
    "is_recognized": false,
    "error": "Image not recognized as a supported leaf or disease."
  }
  ```
