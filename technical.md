# Agri-Connect — Technology Stack & Rationale

This document outlines the core technologies used to build the **Agri-Connect** smart farming platform and provides the rationale for why each specific technology was chosen over alternatives.

---

## Frontend Architecture

### 1. Vanilla HTML / CSS / JavaScript
* **Why it is used:** Instead of using a heavy framework like React, Angular, or Vue.js, the project relies on vanilla web technologies. This was chosen to keep the frontend incredibly lightweight, ensure extremely fast initial load times, and eliminate complex dependency chains. It provides ultimate control over the DOM and allows for a highly customized, dynamic UI without the overhead of a virtual DOM.

### 2. Vite (Build Tool & Dev Server)
* **Why it is used:** Vite is used as the frontend tooling solution. It was chosen over older tools like Webpack because it leverages native ES modules in the browser, providing near-instantaneous Hot Module Replacement (HMR) during development. This significantly speeds up the development process. When building for production, it uses Rollup to create highly optimized static assets.

### 3. i18n (Internationalization — English + Telugu)
* **How it works:** A custom i18n module (`js/i18n.js`) provides full bilingual support across the entire application. Over 100+ translation keys cover every page: Home, Farm Analyzer, Weather, Market Prices, Chatbot, Alerts, and Crop Doctor. The language can be toggled via the navbar language button, and the entire application (including navigation, labels, descriptions, and data source labels) re-renders in the selected language.
* **Supported languages:** English (en) and Telugu (te).
* **No external API needed:** Translation is handled entirely client-side with a static dictionary. No Google Translate API or external translation service is required.

---

## Backend Architecture (Main API — Port 5000)

### 4. Python 3
* **Why it is used:** The universal language for Data Science and Machine Learning. Since the core functionality of the app revolves around predictive models and ETL pipelines, Python is the ideal choice to seamlessly integrate ML models, external API integrations, and a web server into a single coherent stack.

### 5. Flask
* **Why it is used:** Flask is a lightweight micro-framework for Python. It was chosen over Django because the backend strictly serves as an API layer (returning JSON data to the frontend) rather than rendering HTML templates or managing a massive relational database via an ORM. Flask provides exactly what is needed — routing, request handling, and CORS support — without unnecessary bloat.

### 6. Scikit-Learn (sklearn)
* **Why it is used:** Used for the Crop Recommendation and Fertilizer Prediction systems. Scikit-Learn provides robust, highly optimized algorithms for tabular data (like Random Forests and Decision Trees). It was chosen for its stability, ease of use, and efficient serialization (pickling) of trained models for fast inference in production.

### 7. Pandas & NumPy
* **Why it is used:** These libraries are the backbone of data manipulation in Python. They are used to clean, structure, and preprocess the agricultural datasets before they are fed into the Scikit-Learn models. NumPy is also heavily used in the API endpoints to rapidly format user inputs into the matrix dimensions expected by the prediction engine.

---

## Backend Architecture (Image Detection — Port 5001)

*Note: This runs on a separate port (5001) and in a separate virtual environment due to specific library requirements for deep learning (TensorFlow).*

### 8. TensorFlow & Keras
* **Why it is used:** Used specifically for the Plant Disease Image Detection feature. TensorFlow is the industry standard for Deep Learning. It was chosen because processing images requires Convolutional Neural Networks (CNNs), which are vastly superior in TensorFlow compared to standard tabular ML libraries like Scikit-Learn.

### 9. MobileNetV2 (Model Architecture)
* **Why it is used:** Rather than building a deep artificial neural network from scratch, the system uses Transfer Learning with the MobileNetV2 architecture. It was specifically chosen because it is designed to be highly efficient and fast, requiring significantly less computational power than architectures like ResNet or Inception, while still maintaining high accuracy for image classification.

---

## ETL (Extract-Transform-Load) Modules

The backend uses a modular ETL pipeline architecture. Each external data source has its own ETL module under `backend/etl/`, ensuring separation of concerns and clean fallback handling.

### 10. Weather ETL (`etl/weather_etl.py`)
* **Source:** OpenWeatherMap API (requires API key in `.env`)
* **What it does:** Fetches real-time current weather (temperature, humidity, wind, clouds) and 5-day forecast by GPS coordinates or city name. Used for crop feasibility assessment, irrigation guidance, and alert generation.
* **Why OpenWeatherMap:** Reliable, generous free tier, provides all specific meteorological data points required by the prediction models.

### 11. Geocoding ETL (`etl/geocoding_etl.py`)
* **Primary Source:** OpenStreetMap Nominatim (free, no key)
* **Fallback Source:** BigDataCloud Reverse Geocoding API (free, no key)
* **What it does:** Converts GPS coordinates (latitude/longitude) into human-readable location data — village/town, taluk, district, state, country, and pincode. This powers the location display on the farm analysis page.
* **Why dual-source:** Nominatim is the primary source for detailed Indian administrative data, but can be rate-limited or temporarily block some user agents. BigDataCloud serves as an automatic fallback to ensure the user always gets location information.

### 12. Soil ETL (`etl/soil_etl.py`)
* **Primary Source:** ISRIC SoilGrids v2.0 API (free, no key)
* **Fallback Source:** India regional heuristics (lat/lon-based profiles)
* **What it does:** Fetches satellite-modeled soil properties — nitrogen, pH, organic carbon, clay/sand/silt fractions, bulk density, CEC — by GPS coordinates. Derives N, P, K values, soil texture class (USDA triangle), and estimated field-capacity moisture. These are fed into the crop recommendation and fertilizer prediction models.
* **Why SoilGrids:** It is the most widely cited global soil database (250m resolution). No API key required. However, P and K are estimated since SoilGrids doesn't provide them directly.

### 13. Market Price ETL (`etl/market_etl.py`)
* **Source:** data.gov.in / Agmarknet API (Ministry of Agriculture, Govt. of India)
* **Resource:** `9ef84268-d588-465a-a308-a864a43d0070` — *Current Daily Price of Various Commodities from Various Markets (Mandi)*
* **Fallback Source:** Static reference prices from MSP/historical data
* **What it does:** Fetches **real-time, live wholesale market (mandi) prices** from over 3,000 APMC regulated markets across India. Returns min/max/modal prices per quintal and per kg, along with market name, state, district, arrival date, commodity, variety, and grade information.
* **Why data.gov.in Agmarknet:** This is the official government data source for agricultural commodity prices in India. It provides the most accurate, up-to-date mandi prices available. The API is free, requires no authentication for the default public key, and is updated daily as mandis report prices.
* **Caching:** Results are cached for 10 minutes in-memory to respect API rate limits while keeping data fresh.

### 14. News ETL (`etl/news_etl.py`)
* **Source:** NewsAPI (requires API key in `.env`)
* **What it does:** Fetches real agriculture-related news articles from Indian sources. These are displayed on the alerts page and used by the alert engine to generate news-based advisories (e.g., pest outbreak warnings, policy changes).

---

## Alert Engine (`alerts/alert_engine.py`)

* **What it does:** Generates contextual farm alerts by combining data from multiple sources — live weather, forecast, soil conditions, crop calendars, and news. Produces alerts at three severity levels: danger, warning, and info.
* **Why rule-based:** A rule-based engine was chosen over ML for alerts because farm alerts need to be explainable, predictable, and immediately actionable. Every alert has a clear source and reason.

---

## Chatbot (`/api/chat`)

* **What it does:** Provides instant answers to farming questions in English and Telugu. Uses keyword-based intent matching to detect what the user is asking about (crop, fertilizer, irrigation, disease, weather, market, soil) and returns relevant, accurate farming advice.
* **Languages supported:** English (en) and Telugu (te).
* **No external API required:** The chatbot runs entirely on the backend using rule-based keyword matching. No Gemini or OpenAI API key is needed for the chatbot to function. (API keys can optionally be added for enhanced responses.)

---

## Crop Recommendation System

* **Method:** Hybrid feasibility + ML ranking
* **Step 1 — Rule-Based Feasibility Filter:** Crops are first filtered using agronomic constraints from the `CROP_PROFILES` knowledge base: temperature range, pH range, minimum nitrogen, rainfall, season, and region suitability. Only crops passing all hard constraints are retained.
* **Step 2 — ML Confidence Scoring:** Feasible crops are then ranked using a trained RandomForest model that predicts crop suitability based on N, P, K, temperature, humidity, pH, and rainfall.
* **Auto-region detection:** When the user provides GPS coordinates, the system automatically determines the Indian farming region (North/South/East/West) from lat/lon, so crops are recommended based on what is actually grown in that area.
* **Crop Calendar Data:** All sowing and harvest months follow official Indian agricultural calendars as per ICAR/IARI standards. Dual-season crops (Kharif/Rabi) show separate timings for each season.

---

## External APIs & Integrations Summary

| Service | Purpose | Key Required | Fallback |
|---|---|---|---|
| OpenWeatherMap | Live weather & forecast | ✅ Yes (.env) | None (error displayed) |
| Nominatim (OSM) | Reverse geocoding (GPS → address) | ❌ No | BigDataCloud |
| BigDataCloud | Fallback reverse geocoding | ❌ No | Coordinate display |
| ISRIC SoilGrids | Satellite soil data (N, pH, OC, texture) | ❌ No | Regional heuristics |
| data.gov.in (Agmarknet) | Live mandi prices from APMC markets | ❌ No (public key) | Static reference prices |
| NewsAPI | Agriculture news headlines | ✅ Yes (.env, optional) | Empty news feed |

### API Keys You Need

| Key | Required? | How to Get |
|---|---|---|
| `OPENWEATHERMAP_API_KEY` | **Yes** — weather & forecast won't work without it | Sign up at https://openweathermap.org/api |
| `NEWSAPI_KEY` | **Optional** — news section shows empty if missing | Sign up at https://newsapi.org/ |
| `GEMINI_API_KEY` | **Optional** — not needed for chatbot (rule-based) | https://aistudio.google.com/app/apikey |
| `DATA_GOV_API_KEY` | **Optional** — default public key is built-in | https://data.gov.in/ |

---

## ML Models

| Model | Algorithm | Input | Output |
|---|---|---|---|
| Crop Recommendation | Random Forest (sklearn) | N, P, K, temp, humidity, pH, rainfall | Best crop + alternatives with confidence |
| Fertilizer Prediction | Random Forest (sklearn) | Soil type, pH, moisture, OC, EC, N, P, K, weather, crop, season, region | Best fertilizer + alternatives |
| Plant Disease Detection | CNN / MobileNetV2 (TensorFlow) | Leaf image (224×224) | Disease class + confidence + treatment |

---

## Key Design Principles

1. **GPS-first:** Every analysis starts with GPS coordinates. Weather, soil, and location data are all fetched by coordinates, not city names.
2. **Real data, clearly labeled:** Every data source is tagged with `data_quality` (live, estimated, user_entered, reference) and `source_name` so the user knows exactly where their data comes from.
3. **Graceful fallbacks:** Every external API has a fallback path. If SoilGrids is down, regional heuristics kick in. If Agmarknet is unavailable, reference prices are shown. The app never crashes due to an external API failure.
4. **Hybrid AI:** Crop recommendations use a hybrid approach — rule-based feasibility filtering (agronomic constraints) combined with ML confidence scoring — rather than blindly trusting AI output.
5. **Full bilingual support:** The entire interface supports English and Telugu, toggled via a single button in the navbar. All page content, labels, and navigation translate instantly.
6. **Auto-region detection:** The system detects the farming region (North/South/East/West India) from GPS coordinates so crop suggestions match what farmers in that area actually grow.
7. **Accurate crop calendar:** Sowing and harvest months follow official Indian agricultural schedules as per ICAR, with dual-season crops showing both Kharif and Rabi timings.
