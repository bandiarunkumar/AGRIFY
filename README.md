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

> AGRIFY is an enterprise-grade GPS-first precision agriculture platform that integrates real-time telemetry, satellite soil intelligence, machine learning, and Google's Gemini 3.6 Flash for actionable crop, fertilizer, irrigation, and disease insights tailored to agricultural ecosystems.

</div>

## 📊 System Status Overview

<div align="center">

<table style="width:100%; border-collapse:collapse;">
<tr>
<td align="center" style="border:1px solid #E2E8F0; padding:12px; background:#ECFDF5; border-radius:8px; width:25%;">
<strong style="color:#059669;">🟢 Backend</strong><br/>
<span style="color:#334155;">Healthy (200)</span>
</td>
<td align="center" style="border:1px solid #E2E8F0; padding:12px; background:#F0F9FF; border-radius:8px; width:25%;">
<strong style="color:#3B82F6;">🗄️ Database</strong><br/>
<span style="color:#334155;">PostgreSQL agrify_dev</span>
</td>
<td align="center" style="border:1px solid #E2E8F0; padding:12px; background:#ECFDF5; border-radius:8px; width:25%;">
<strong style="color:#059669;">🤖 Gemini 3.6 Flash</strong><br/>
<span style="color:#334155;">Active & Integrated</span>
</td>
<td align="center" style="border:1px solid #E2E8F0; padding:12px; background:#F0F9FF; border-radius:8px; width:25%;">
<strong style="color:#3B82F6;">🔬 Crop Doctor</strong><br/>
<span style="color:#334155;">5/5 Tests Passing</span>
</td>
</tr>
<tr>
<td align="center" style="border:1px solid #E2E8F0; padding:12px; background:#F0F9FF; border-radius:8px;">
<strong style="color:#3B82F6;">🌦️ OpenWeather</strong><br/>
<span style="color:#334155;">Live & Responding</span>
</td>
<td align="center" style="border:1px solid #E2E8F0; padding:12px; background:#ECFDF5; border-radius:8px;">
<strong style="color:#059669;">🛰️ SoilGrids v2</strong><br/>
<span style="color:#334155;">ISRIC Telemetry</span>
</td>
<td align="center" style="border:1px solid #E2E8F0; padding:12px; background:#F0F9FF; border-radius:8px;">
<strong style="color:#3B82F6;">🧠 ML Models</strong><br/>
<span style="color:#334155;">Loaded & Optimized</span>
</td>
<td align="center" style="border:1px solid #E2E8F0; padding:12px; background:#ECFDF5; border-radius:8px;">
<strong style="color:#059669;">🎨 Frontend</strong><br/>
<span style="color:#334155;">Build Passing</span>
</td>
</tr>
</table>

</div>

---

## 🏗️ System Architecture & Telemetry Pipeline

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#ECFDF5', 'primaryTextColor':'#334155', 'primaryBorderColor':'#059669', 'lineColor':'#3B82F6', 'secondaryColor':'#F0F9FF', 'tertiaryColor':'#F8FAFC'}}}%%
flowchart TD
    subgraph INPUT ["📡 GPS-First Telemetry Input"]
        A1[("🗺️ GPS Coordinates\nLat / Lon")]
        A2[("🌦️ OpenWeather API\nLive Conditions & Forecast")]
        A3[("🛰️ ISRIC SoilGrids v2\nNPK, pH, Organic Carbon")]
    end
    
    subgraph CORE ["⚙️ Flask Core Engine"]
        B1["🔍 Geocoding &\nLocation Validation"]
        B2["🧮 Feasibility Filter\n& Season-Aware Logic"]
        B3["📊 Data Normalization\n& Quality Checks"]
    end
    
    subgraph INTELLIGENCE ["🧠 AI & ML Intelligence Layer"]
        C1[("🤖 Gemini 3.6 Flash\nAgricultural Copilot")]
        C2[("🌾 ML Crop Recommendation\nSuitability Scoring")]
        C3[("🧪 Stage-Wise NPK\nFertilizer Engine")]
        C4[("🔬 Crop Doctor\nImage Screening")]
    end
    
    subgraph OUTPUT ["💡 Light-Mode Frontend UI"]
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
    
    style INPUT fill:#F0F9FF,stroke:#3B82F6,color:#334155
    style CORE fill:#ECFDF5,stroke:#059669,color:#334155
    style INTELLIGENCE fill:#F8FAFC,stroke:#0D9488,color:#334155
    style OUTPUT fill:#F0F9FF,stroke:#3B82F6,color:#334155
```

## 🚀 Key Modules

<div align="center">

<table style="width:100%; border-collapse:collapse;">
<tr>
<td style="border:1px solid #E2E8F0; padding:16px; background:linear-gradient(135deg, #ECFDF5 0%, #F8FAFC 100%); border-radius:12px; width:33%;">
<h3 style="color:#059669; margin-top:0;">🤖 Gemini 3.6 Flash Copilot</h3>
<p style="color:#334155; margin-bottom:0;">Multilingual agricultural assistant with bilingual support (English/Telugu), agricultural safety checks, JSON-structured outputs, and intelligent rule-based fallback.</p>
</td>
<td style="border:1px solid #E2E8F0; padding:16px; background:linear-gradient(135deg, #F0F9FF 0%, #F8FAFC 100%); border-radius:12px; width:33%;">
<h3 style="color:#3B82F6; margin-top:0;">🛰️ GPS-First Telemetry Engine</h3>
<p style="color:#334155; margin-bottom:0;">Precise coordinate validation powering real-time OpenWeather telemetry and ISRIC SoilGrids v2 soil intelligence with full provenance tracking.</p>
</td>
<td style="border:1px solid #E2E8F0; padding:16px; background:linear-gradient(135deg, #ECFDF5 0%, #F8FAFC 100%); border-radius:12px; width:33%;">
<h3 style="color:#0D9488; margin-top:0;">🌾 ML Crop & Fertilizer Advisory</h3>
<p style="color:#334155; margin-bottom:0;">Season-aware recommendations with perennial crop separation, hybrid ML+feasibility scoring, and stage-wise NPK guidance with organic alternatives.</p>
</td>
</tr>
</table>

</div>

## ⚡ Interactive Quick Start

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

<table style="width:100%; border-collapse:collapse; border:1px solid #E2E8F0;">
<thead style="background:linear-gradient(90deg, #ECFDF5 0%, #F0F9FF 100%);">
<tr>
<th style="padding:12px; text-align:left; border:1px solid #E2E8F0; color:#334155;">Method</th>
<th style="padding:12px; text-align:left; border:1px solid #E2E8F0; color:#334155;">Endpoint</th>
<th style="padding:12px; text-align:left; border:1px solid #E2E8F0; color:#334155;">Description</th>
<th style="padding:12px; text-align:left; border:1px solid #E2E8F0; color:#334155;">Request Payload</th>
</tr>
</thead>
<tbody>
<tr style="background:#F8FAFC;">
<td style="padding:12px; border:1px solid #E2E8F0;"><span style="background:#ECFDF5; color:#059669; padding:4px 8px; border-radius:6px; font-weight:600;">GET</span></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#334155;">/api/health</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">System health & database connectivity status</td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#64748B;">—</td>
</tr>
<tr>
<td style="padding:12px; border:1px solid #E2E8F0;"><span style="background:#F0F9FF; color:#3B82F6; padding:4px 8px; border-radius:6px; font-weight:600;">POST</span></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#334155;">/api/farm/analyze</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">GPS-first comprehensive farm analysis with crop recommendations</td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#64748B;">{latitude, longitude, season, area_acres, ...}</code></td>
</tr>
<tr style="background:#F8FAFC;">
<td style="padding:12px; border:1px solid #E2E8F0;"><span style="background:#F0F9FF; color:#3B82F6; padding:4px 8px; border-radius:6px; font-weight:600;">POST</span></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#334155;">/api/chat</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">Gemini 3.6 Flash bilingual agricultural copilot</td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#64748B;">{message, language: "en|te"}</code></td>
</tr>
<tr>
<td style="padding:12px; border:1px solid #E2E8F0;"><span style="background:#ECFDF5; color:#059669; padding:4px 8px; border-radius:6px; font-weight:600;">GET</span></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#334155;">/api/weather/coords</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">Live weather telemetry by GPS coordinates</td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#64748B;">?lat={}&lon={}</code></td>
</tr>
<tr style="background:#F8FAFC;">
<td style="padding:12px; border:1px solid #E2E8F0;"><span style="background:#ECFDF5; color:#059669; padding:4px 8px; border-radius:6px; font-weight:600;">GET</span></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#334155;">/api/soil/coords</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">ISRIC SoilGrids v2 data by GPS coordinates</td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#64748B;">?lat={}&lon={}</code></td>
</tr>
<tr>
<td style="padding:12px; border:1px solid #E2E8F0;"><span style="background:#F0F9FF; color:#3B82F6; padding:4px 8px; border-radius:6px; font-weight:600;">POST</span></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#334155;">/api/predict/crop</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">ML-powered crop suitability prediction</td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#64748B;">{N,P,K,temperature,humidity,ph,rainfall}</code></td>
</tr>
<tr style="background:#F8FAFC;">
<td style="padding:12px; border:1px solid #E2E8F0;"><span style="background:#F0F9FF; color:#3B82F6; padding:4px 8px; border-radius:6px; font-weight:600;">POST</span></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#334155;">/api/auth/login</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">Secure authentication (HttpOnly cookies)</td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#64748B;">{email, password}</code></td>
</tr>
</tbody>
</table>

## 🛠️ Technology Stack

<div align="center">

| Category | Technologies |
| :-------- | :------------ |
| **Backend** | Flask 3.0.3, SQLAlchemy, Flask-CORS, Flask-WTF, Flask-Limiter |
| **AI/ML** | Google Gemini 3.6 Flash, scikit-learn, TensorFlow, NumPy, Pandas |
| **Data Sources** | OpenWeatherMap API, ISRIC SoilGrids v2, data.gov.in (Agmarknet), NewsAPI |
| **Frontend** | Vite, Vanilla JavaScript, Tailwind CSS, Lucide Icons |
| **Database** | PostgreSQL 17 |
| **Security** | JWT with HttpOnly cookies, CSRF protection, Rate limiting, Token blacklisting |

</div>

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
