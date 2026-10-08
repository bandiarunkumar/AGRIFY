# 🌾 AGRI CONNECT

**AGRI CONNECT** is an intelligent, comprehensive smart farming platform built to assist farmers by offering advanced predictive analysis, real-time weather and soil data, market prices, and dynamic crop recommendations. The platform supports multiple languages (English and Telugu) locally for a seamless user experience.

---

## 🚀 The Technology Stack

Agri Connect uses a highly efficient, separated frontend and backend architecture to keep the client application lightweight while offloading all complex Machine Learning and ETL pipelines to the robust Python backend.

### 🎨 Frontend Architecture
- **Vanilla HTML / CSS / JavaScript:** Built without heavy frameworks (like React or Angular) to ensure extremely fast initial loading times and no massive dependency graphs. It provides ultimate control over UI logic.
- **Vite:** Used as the frontend build tool and development server. It leverages native ES modules, providing instant Hot Module Replacements (HMR) during development and highly optimized asset bundling for production. 
- **Bilingual i18n System:** A custom translation module supports full frontend translations in English and Telugu simultaneously without relying on external APIs.

### ⚙️ Backend Architecture (Port 5000)
- **Python 3 & Flask:** Flask provides a lightweight, robust micro-framework to build a purely API-focused backend layer, omitting unneeded features found in larger ORMs like Django. 
- **Scikit-Learn (sklearn):** The backbone for our analytical machine-learning models (e.g., Random Forest for Crop Recommendation and Fertilizer Prediction Systems). It is universally trusted for tabular data optimizations.
- **Pandas & NumPy:** Handles data structuring, pre-processing agricultural datasets, and rapidly formatting matrix inputs. 

### 📸 Image Detection Layer (Port 5001)
- **TensorFlow & Keras (MobileNetV2):** Plant Leaf Disease detection runs on a completely separate model utilizing Deep Learning (CNN). MobileNetV2 was chosen as it efficiently executes transfer learning requiring drastically less computational power than larger networks, mapping diseases swiftly and accurately.

---

## 🔍 How it Works: The Analytical Backend

At its core, AGRI CONNECT does not just guess based on ML; it uses a strict **Hybrid AI System** and real-time **ETL (Extract, Transform, Load)** pipelines.

### 1. The ETL Pipelines (`backend/etl/`)
Instead of a single monolithic data grab, the backend features dedicated modules for retrieving fallback-safe data points:
- **Weather ETL:** Gathers live weather data and 5-day forecasts via OpenWeatherMap (temperature, humidity, rain).
- **Geocoding ETL:** Converts user GPS location securely to village/district/state details using *Nominatim (OSM)* with a *BigDataCloud* fallback.
- **Soil ETL:** Extracts satellite-modeled soil properties (Nitrogen, pH, Organic Carbon) from *ISRIC SoilGrids v2.0 API* or regional heuristics based on location.
- **Market Price ETL:** Connects to the official Govt. of India `data.gov.in` (Agmarknet) API to provide live, wholesale mandi prices for over 3,000 APMC markets.
- **News ETL:** Extracts local, real-world Indian agricultural news to display on the dashboard contextually.

### 2. The Alert Engine
A rule-based inference engine (`alerts/alert_engine.py`) takes inputs from all the active ETL modules (Weather, Agmarknet, News) and correlates them with stored knowledge graphs. It generates actionable context-aware alerts (e.g., Pest outbreak warnings, heavy rains) prioritizing safety logic over black-box ML.

### 3. Crop Recommendation System
- **Step 1 (Agronomic Filtering):** Constraints mapped by the Indian Agricultural Research Institute (ICAR) are checked against user data (e.g., minimum nitrogen thresholds, temperature ranges, and season). 
- **Step 2 (ML Confidence Scoring):** The remaining feasible crops are mapped into a Scikit-Learn **Random Forest Classifier** which ranks the output yielding the highest accuracy recommendations.

### 4. Interactive Chatbot
An internal keyword-matching/rule-based engine handles direct English and Telugu queries about crop growth, fertilizers, irrigation, and diseases. (Optionally integrates generalized AI responses if API keys are provided).

---

## 💻 Running the Project Locally

### Prerequisites
Make sure you have [Node.js](https://nodejs.org/) & [Python 3](https://www.python.org/) installed on your machine.
Ensure you have API Keys ready for `.env` if utilizing external live data (e.g., OpenWeatherMap, NewsAPI).

### 1. Run the Backend API
1. Open a terminal and navigate to the backend directory:
   ```bash
   cd "backend"
   ```
2. Activate the virtual environment (adjust for Mac/Linux):
   ```bash
   .\new_venv\Scripts\activate
   ```
3. Start the Flask Application:
   ```bash
   python api.py
   ```
   *(Ensure dependencies are installed with `pip install -r requirements.txt` if starting fresh.)*

### 2. Run the Frontend App
1. Open another terminal and navigate to the frontend directory:
   ```bash
   cd "frontend"
   ```
2. Make sure modules are installed:
   ```bash
   npm install
   ```
3. Boot the Vite Dev Server:
   ```bash
   npx vite
   ```
4. Access the portal at `http://localhost:5173/`

---
*Built tightly integrating Data Science, Data Warehousing, and Modern Web Standards to provide equitable access to precision agriculture.*
