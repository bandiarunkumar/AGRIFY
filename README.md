# 🌾 AGRIFY — GPS-First Precision Agriculture Platform

<div align="center">

![Platform](https://img.shields.io/badge/Platform-AgriTech-059669?style=for-the-badge&labelColor=ECFDF5)
![Status](https://img.shields.io/badge/Status-Active-3B82F6?style=for-the-badge&labelColor=F0F9FF)
![License](https://img.shields.io/badge/License-MIT-0D9488?style=for-the-badge&labelColor=ECFDF5)

[![Python](https://img.shields.io/badge/Python-3.11+-059669?style=flat-square&logo=python&logoColor=white&labelColor=ECFDF5)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-3B82F6?style=flat-square&logo=flask&logoColor=white&labelColor=F0F9FF)](https://flask.palletsprojects.com)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.x-0D9488?style=flat-square&logo=tailwindcss&logoColor=white&labelColor=ECFDF5)](https://tailwindcss.com)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-3.6_Flash-059669?style=flat-square&logo=google&logoColor=white&labelColor=ECFDF5)](https://ai.google.dev)
[![OpenWeather](https://img.shields.io/badge/OpenWeather-API-3B82F6?style=flat-square&logo=openweathermap&logoColor=white&labelColor=F0F9FF)](https://openweathermap.org)
[![ISRIC SoilGrids](https://img.shields.io/badge/ISRIC_SoilGrids-v2-0D9488?style=flat-square&logo=leaflet&logoColor=white&labelColor=ECFDF5)](https://soilgrids.org)

**Smart Farming. Made Simple. For Every Farmer.**

> AGRIFY is an enterprise-grade GPS-first precision agriculture platform that combines real-time telemetry, satellite soil intelligence, machine learning, and Google's Gemini 3.6 Flash to deliver actionable crop, fertilizer, irrigation, and disease insights tailored to agricultural ecosystems.

</div>

---

## 🏗️ System Architecture & Telemetry Pipeline

```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'fontFamily': 'sans-serif', 'fontSize': '14px', 'lineColor': '#2563EB', 'tertiaryColor': '#F3F4F6'}}}%%
flowchart TD
    subgraph INPUT ["📡 GPS-First Telemetry Input"]
        A1["🗺️ GPS Coordinates<br/>Lat / Lon"]
        A2["🌦️ OpenWeather API<br/>Live Conditions & Forecast"]
        A3["🛰️ ISRIC SoilGrids v2<br/>NPK, pH, Organic Carbon"]
    end
    
    subgraph CORE ["⚙️ Flask Core Engine"]
        B1["🔍 Geocoding & Location Validation"]
        B2["🧮 Feasibility Filter & Season-Aware Logic"]
        B3["📊 Data Normalization & Quality Checks"]
    end
    
    subgraph INTELLIGENCE ["🧠 AI & ML Intelligence Layer"]
        C1["🤖 Gemini 3.6 Flash<br/>Agricultural Copilot"]
        C2["🌾 ML Crop Recommendation<br/>Suitability Scoring"]
        C3["🧪 Stage-Wise NPK<br/>Fertilizer Engine"]
        C4["🔬 Crop Doctor<br/>Image Screening"]
    end
    
    subgraph OUTPUT ["💡 Client Interface & Advisory"]
        D1["📈 Interactive Dashboard"]
        D2["🗓️ Crop Advisory Cards"]
        D3["💧 Irrigation Guidance"]
        D4["🚨 Smart Alerts"]
    end
    
    A1 --> B1
    A2 --> B3
    A3 --> B3
    B1 --> B2
    B2 --> C2
    B3 --> C2
    B3 --> C3
    C2 --> D2
    C3 --> D3
    C1 --> D1
    C4 --> D2
    C1 --> D4
```

## 🚀 Key Modules

| Module | Description |
| :------- | :----------- |
| **🤖 Gemini 3.6 Flash Copilot** | Multilingual agricultural assistant with bilingual support (English/Telugu), agricultural safety checks, JSON-structured outputs, and intelligent rule-based fallback. |
| **🛰️ GPS-First Telemetry Engine** | Precise coordinate validation powering real-time OpenWeather telemetry and ISRIC SoilGrids v2 soil intelligence with full provenance tracking. |
| **🌾 ML Crop & Fertilizer Advisory** | Season-aware recommendations with perennial crop separation, hybrid ML+feasibility scoring, and stage-wise NPK guidance with organic alternatives. |

## ⚡ Quick Start

<details>
<summary><strong>🔧 Backend Setup (Flask)</strong></summary>

```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install PyJWT flask-limiter flask-wtf google-genai

# Start the server
python api.py
```

</details>

<details>
<summary><strong>⚙️ Environment Configuration (.env)</strong></summary>

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/agrify_dev

# AI & External APIs
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
NEWSAPI_KEY=your_newsapi_key

# Security
SECRET_KEY=your_secure_secret_key
JWT_SECRET_KEY=your_jwt_secret_key

# Optional
COOKIE_SECURE=false
FLASK_ENV=development
```

</details>

<details>
<summary><strong>🚀 Frontend Preview (Vite + Tailwind)</strong></summary>

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

</details>

## 📡 API Reference

| Method | Endpoint | Description | Request Payload |
| :------- | :--------- | :----------- | :-------------- |
| `GET` | `/api/health` | System health & database connectivity status | — |
| `POST` | `/api/farm/analyze` | GPS-first comprehensive farm analysis with crop recommendations | `{latitude, longitude, season, area_acres, ...}` |
| `POST` | `/api/chat` | Gemini 3.6 Flash bilingual agricultural copilot | `{message, language: "en\|te"}` |
| `GET` | `/api/weather/coords` | Live weather telemetry by GPS coordinates | `?lat={}&lon={}` |
| `GET` | `/api/soil/coords` | ISRIC SoilGrids v2 data by GPS coordinates | `?lat={}&lon={}` |
| `POST` | `/api/predict/crop` | ML-powered crop suitability prediction | `{N,P,K,temperature,humidity,ph,rainfall}` |
| `POST` | `/api/auth/login` | Secure authentication (HttpOnly cookies) | `{email, password}` |

## 🛠️ Technology Stack

| Category | Technologies |
| :-------- | :------------ |
| **Backend** | Flask 3.0.3, SQLAlchemy, Flask-CORS, Flask-WTF, Flask-Limiter |
| **AI/ML** | Google Gemini 3.6 Flash, scikit-learn, TensorFlow, NumPy, Pandas |
| **Data Sources** | OpenWeatherMap API, ISRIC SoilGrids v2, data.gov.in (Agmarknet), NewsAPI |
| **Frontend** | Vite, Vanilla JavaScript, Tailwind CSS, Lucide Icons |
| **Database** | PostgreSQL 17 |
| **Security** | JWT with HttpOnly cookies, CSRF protection, Rate limiting, Token blacklisting |

## ✨ Core Features

- **GPS-First Architecture**: All recommendations driven by precise latitude/longitude coordinates
- **Real-Time Telemetry**: Live weather forecasts and satellite-derived soil intelligence
- **AI-Powered Advisory**: Gemini 3.6 Flash provides multilingual, context-aware farming guidance
- **Smart Crop Recommendations**: Season-aware filtering with perennial crop separation
- **Precision Fertilization**: Stage-wise NPK calculations with organic alternatives
- **Crop Doctor**: AI-assisted disease detection with 5/5 regression-tested safety screening
- **Market Intelligence**: Live mandi prices across Indian markets
- **Bilingual Support**: Seamless English and Telugu interface
- **Responsive Design**: Optimized experience across desktop and mobile devices

## 🔐 Security & Compliance

- **Secure Secrets**: Credentials isolated in environment variables (`.env` git-ignored)
- **Authentication**: HttpOnly cookie-based JWT with CSRF protection
- **Rate Limiting**: Distributed protection on sensitive endpoints
- **Input Validation**: Comprehensive sanitization and SQL injection prevention
- **Password Security**: Werkzeug secure password hashing
- **Session Management**: Token revocation via blacklist

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<div align="center">

**Built with 💚 for Indian Farmers**

*Empowering precision agriculture through intelligent technology*

</div>
