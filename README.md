# AGRIFY — GPS-First Precision Agriculture Platform

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

AGRIFY is a GPS-first precision agriculture platform that combines real-time telemetry, satellite soil intelligence, machine learning, and Google's Gemini 3.6 Flash to deliver actionable crop, fertilizer, irrigation, and disease insights tailored to India's agricultural regions.

</div>

## Visual Architecture

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#ECFDF5', 'primaryTextColor':'#334155', 'primaryBorderColor':'#059669', 'lineColor':'#3B82F6', 'secondaryColor':'#F0F9FF', 'tertiaryColor':'#F8FAFC'}}}%%
flowchart TD
    subgraph INPUT["📡 GPS-First Telemetry Input"]
        A1[("🗺️ GPS Coordinates\nLat / Lon")]
        A2[("🌦️ OpenWeather API\nLive Conditions & Forecast")]
        A3[("🛰️ ISRIC SoilGrids v2\nNPK, pH, Organic Carbon")]
    end
    
    subgraph CORE["⚙️ Flask Core Engine"]
        B1["🔍 Geocoding &\nLocation Validation"]
        B2["🧮 Feasibility Filter\n& Season-Aware Logic"]
        B3["📊 Data Normalization\n& Quality Checks"]
    end
    
    subgraph INTELLIGENCE["🧠 AI & ML Intelligence Layer"]
        C1[("🤖 Gemini 3.6 Flash\nAgricultural Copilot")]
        C2[("🌾 ML Crop Recommendation\nSuitability Scoring")]
        C3[("🧪 Stage-Wise NPK\nFertilizer Engine")]
        C4[("🔬 Crop Doctor\nImage Screening")]
    end
    
    subgraph OUTPUT["💡 Light-Mode Frontend UI"]
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

## Key Modules

<table style="width:100%; border-collapse:collapse;">
<tr>
<td style="border:1px solid #E2E8F0; padding:16px; background:#ECFDF5; border-radius:8px;">
<h3>🤖 Gemini 3.6 Flash Copilot</h3>
<p style="color:#334155;">Multilingual agricultural assistant with agricultural safety checks, Telugu/English support, and intelligent rule-based fallback when connectivity is limited.</p>
</td>
<td style="border:1px solid #E2E8F0; padding:16px; background:#F0F9FF; border-radius:8px;">
<h3>🛰️ GPS-First Telemetry Engine</h3>
<p style="color:#334155;">Precise coordinate validation powering real-time weather from OpenWeather API and soil intelligence from ISRIC SoilGrids v2 with full provenance tracking.</p>
</td>
<td style="border:1px solid #E2E8F0; padding:16px; background:#ECFDF5; border-radius:8px;">
<h3>🌾 ML Crop & Fertilizer Advisory</h3>
<p style="color:#334155;">Season-aware crop recommendations with perennial crop separation, hybrid ML + feasibility scoring, and stage-wise NPK fertilizer guidance with organic alternatives.</p>
</td>
</tr>
</table>

## Interactive Quick Start

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

# Configure environment
cp .env.example .env
# Edit .env with your credentials (OPENWEATHERMAP_API_KEY, GEMINI_API_KEY, NEWSAPI_KEY, DATABASE_URL)
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

## API Reference

<table style="width:100%; border-collapse:collapse; border:1px solid #E2E8F0;">
<thead style="background:#ECFDF5;">
<tr>
<th style="padding:12px; text-align:left; border:1px solid #E2E8F0; color:#334155;">Method</th>
<th style="padding:12px; text-align:left; border:1px solid #E2E8F0; color:#334155;">Route</th>
<th style="padding:12px; text-align:left; border:1px solid #E2E8F0; color:#334155;">Description</th>
<th style="padding:12px; text-align:left; border:1px solid #E2E8F0; color:#334155;">Telemetry Payload</th>
</tr>
</thead>
<tbody>
<tr style="background:#F8FAFC;">
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#059669;">GET</code></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code>/api/health</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">System health & database status</td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">N/A</td>
</tr>
<tr>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#3B82F6;">POST</code></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code>/api/farm/analyze</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">GPS-first comprehensive farm analysis</td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;"><code>{latitude, longitude, season, area_acres, ...}</code></td>
</tr>
<tr style="background:#F8FAFC;">
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#3B82F6;">POST</code></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code>/api/chat</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">Gemini 3.6 Flash agricultural copilot</td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;"><code>{message, language: "en|te"}</code></td>
</tr>
<tr>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#059669;">GET</code></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code>/api/weather/coords</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">Live weather by GPS coordinates</td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;"><code>?lat={}&lon={}</code></td>
</tr>
<tr style="background:#F8FAFC;">
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#059669;">GET</code></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code>/api/soil/coords</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">ISRIC SoilGrids data by GPS</td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;"><code>?lat={}&lon={}</code></td>
</tr>
<tr>
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#3B82F6;">POST</code></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code>/api/predict/crop</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">ML crop suitability prediction</td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;"><code>{N,P,K,temperature,humidity,ph,rainfall}</code></td>
</tr>
<tr style="background:#F8FAFC;">
<td style="padding:12px; border:1px solid #E2E8F0;"><code style="color:#3B82F6;">POST</code></td>
<td style="padding:12px; border:1px solid #E2E8F0;"><code>/api/auth/login</code></td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;">Secure authentication (HttpOnly cookies)</td>
<td style="padding:12px; border:1px solid #E2E8F0; color:#334155;"><code>{email, password}</code></td>
</tr>
</tbody>
</table>

## Technology Stack

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

## Features

- **GPS-First Architecture**: All recommendations are driven by precise latitude/longitude coordinates
- **Real-Time Telemetry**: Live weather forecasts and satellite-derived soil intelligence
- **AI-Powered Advisory**: Gemini 3.6 Flash provides multilingual, context-aware farming guidance
- **Smart Crop Recommendations**: Season-aware filtering with perennial crop separation
- **Precision Fertilization**: Stage-wise NPK calculations with organic alternatives
- **Crop Doctor**: AI-assisted disease detection with safety screening
- **Market Intelligence**: Live mandi prices across Indian markets
- **Bilingual Support**: English and Telugu interface
- **Responsive Design**: Seamless experience across desktop and mobile devices

## Security & Compliance

- Credentials stored securely in environment variables (`.env` git-ignored)
- HttpOnly cookie-based authentication with CSRF protection
- Rate limiting on sensitive endpoints
- Input validation and SQL injection protection
- Secure password hashing with Werkzeug
- Token revocation via blacklist

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<div align="center">

**Built with 💚 for Indian Farmers**

*Empowering precision agriculture through intelligent technology*

</div>
