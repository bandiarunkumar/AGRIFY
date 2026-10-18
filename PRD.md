# AGRIFY — Product Requirements Document (PRD)

**Status:** Current Implementation Audit & Engineering Baseline
**Version:** 3.0-production
**Updated:** October 2026

---

## 1. Executive Summary & Vision
AGRIFY (Agri-Connect) is an advisory platform designed for Indian farmers, agronomy extension officers, and Krishi Vigyan Kendra (KVK) workers. It provides localized, coordinate-first agricultural intelligence: weather forecasts, satellite soil metrics, APMC mandi commodity prices, foliar disease screening, and a multimodal voice assistant supporting regional Indian languages.

The core product design philosophy is **"Evidence & Provenance First"**: the platform avoids synthetic data in main user flows, explicitly marks satellite estimates versus laboratory tests, enforces agronomic safety guardrails on all AI interactions, and falls back to deterministic rule engines whenever external APIs fail.

---

## 2. Target Personas
1. **Smallholder Farmer (Primary):** Needs quick, actionable, voice-capable guidance in their native language regarding field preparation, irrigation timing, weather advisories, and nearby mandi prices.
2. **KVK Extension Officer / Agronomist:** Needs verified nutrient data, pesticide recommendations, disease escalation paths, and structured action plans to validate farmer field decisions.

---

## 3. Product Features & Route Matrix

| Route | Primary Component | Verified Capabilities | Documented Limitations / Edge Cases | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Home (`/`)** | `home.js` | Hero overview, live metric cards, quick-navigation tabs, dynamic agricultural news ticker. | Dependent on backend news/weather feeds; falls back to static cache if offline. | **VERIFIED** |
| **Farm Analysis (`/analysis`)** | `analysis.js` | Coordinate-first wizard (GPS/manual), soil estimations (SoilGrids), agronomic crop feasibility scoring, 7-day action plan generation. | Soil data is satellite-estimated (ISRIC), not certified lab tests. Scikit-learn tabular `.pkl` models are absent; feasibility uses agronomic rules in `CROP_PROFILES`. Persistence to DB is absent. | **VERIFIED (Stateless)** |
| **Weather (`/weather`)** | `weather.js` | Current weather + 5-day / 3-hour forecast by GPS coordinates via OpenWeatherMap One Call. | Requires valid `OPENWEATHERMAP_API_KEY`. Rejects out-of-range coordinates. No backend caching. | **VERIFIED** |
| **Market (`/market`)** | `market.js` | Live APMC wholesale mandi prices across Indian states/districts (Govt of India Agmarknet). | If Agmarknet API is unreachable, preserves provenance with fallback status without throwing unhandled exceptions. In-memory cache TTL: 600s. | **VERIFIED** |
| **Crop Doctor (`/cropDoctor`)** | `cropDoctor.js` | Image upload and live camera scanning for plant leaf pathology. | **Strictly limited to Potato leaves** (Early Blight, Late Blight, Healthy). Disclaims non-potato leaves or confidence < 65%. Client hardcodes Render URL; local HTTP inference unverified. | **IMPLEMENTED BUT UNVERIFIED (Local HTTP)** |
| **Chatbot (`/chatbot`)** | `chatbot.js` | Conversational text assistant with rule-based agronomic engine and optional Gemini fallback. | Does not execute tool invocations; for automated multi-step tool workflows, Voice Copilot is used. | **VERIFIED** |
| **Alerts (`/alerts`)** | `alerts.js` | Synthesized contextual farm alerts combining live weather anomalies, pest triggers, and news sentiment. | Rules are statically defined in `alert_engine.py`; severity levels: Info, Warning, Danger. | **VERIFIED** |
| **Experts (`/experts`)** | `experts.js` | Directory of verified agricultural extension centers, KVKs, and emergency helplines. | Static directory with direct calling links and location tagging. | **VERIFIED** |
| **Voice Copilot (Global Modal)** | `voiceAssistantModal.js`, `voice.js` | Floating Action Button (FAB), multi-lingual speech-to-text (Web Speech API), text-to-speech synthesis, display cards, action routing. | Speech recognition depends on browser Web Speech API support; offline TTS relies on local voice availability. | **VERIFIED** |

---

## 4. Language & Localization Matrix

| Language | Code | Static UI (`frontend/js/i18n.js`) | Voice Assistant Audio (TTS) | Speech Recognition (STT) | Action Plan & Rules (`action_plan.py`) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **English** | `en` | Complete (`i18n.js`) | Complete (`voice.js`) | Complete | Complete | **VERIFIED** |
| **Telugu** | `te` | Complete (`i18n.js`) | Complete (`voice.js`) | Complete | Complete | **VERIFIED** |
| **Hindi** | `hi` | **Not in `i18n.js`** (PLANNED) | Complete (`voice.js`) | Complete | Complete (`action_plan.py`) | **PARTIAL** |
| **Marathi** | `mr` | Not supported | Not supported | Not supported | Not supported (Disease DB only) | **LOCAL DICT ONLY** |

*Evidence:* `frontend/js/i18n.js` lines 10-315 define translation keys strictly for `en` and `te`. The language setter `setLang` specifically checks `lang = l === 'te' ? 'te' : 'en'`. Full Hindi UI localization across static template strings is **PLANNED**, while Hindi Voice Copilot STT/TTS and Action Plan rules are **VERIFIED**.

---

## 5. Agronomic Safety & Regulatory Constraints
1. **Dosage Guardrails (VERIFIED):** The platform **never** invents chemical dosages, pesticide quantities, or synthetic concentrations. If verified dosage data is missing, it explicitly outputs: *"AGRIFY does not have a verified fertilizer dosage for this specific field. Please check your Farm Analyzer report or consult your local agricultural extension officer before applying chemicals."*
2. **Pathology Boundaries (VERIFIED):** Crop Doctor provides screening, not certified laboratory diagnosis. All UI outputs mandate field verification before purchasing chemical fungicides.
3. **Price Provenance (VERIFIED):** Market prices explicitly report whether they are live official mandi transactions (`is_fallback: false`) or cached/unavailable fallback entries (`is_fallback: true`, `data_quality: "unavailable"`).

---

## 6. Implementation Reality vs. Planned Features

### Current Verified Implementation
- Coordinate-validated Flask REST API running on port 5000 (code-complete, passes 59 of 60 unit tests with 1 skipped).
- Standalone TensorFlow 2.21 vision service (`image_detection/`): Model file `potato_disease_model.keras` verified on disk and loads in Keras; 4 upload validation tests pass.
- Dual-provider AI Gateway (Gemini 2.5 Flash + OpenAI GPT-4o-mini) with verified fallback to deterministic rule engine in unit test suite.
- 53 verified frontend unit tests (28 Copilot UI, 24 TTS, 1 disease client contract) and Vite production build passing cleanly.
- 10 SQLAlchemy database models defined and verified for schema creation, commits, and constraint rollbacks on an isolated in-memory SQLite database.

### Planned / Dormant Enhancements
- **Active Database Persistence (PLANNED / DORMANT):** Wire active API endpoints (`/api/farm/analyze`, `/api/weather/coords`, etc.) to persist snapshots into PostgreSQL via `db.session`.
- **Tabular ML Retraining (BLOCKED / MISSING ASSETS):** Re-train and package `crop_model.pkl` and `fertilizer_model.pkl` using scikit-learn.
- **Local Disease Service HTTP Routing (PLANNED FIX):** Update `frontend/js/api.js` to route `DISEASE_API_BASE` to `127.0.0.1:5001` in local development.
- **Full Static UI Hindi Localization (PLANNED):** Add Hindi (`hi`) dictionary strings to `frontend/js/i18n.js`.
- **Configurable Rate Limiting (PLANNED):** Introduce rate limits for expensive AI and vision endpoints.
