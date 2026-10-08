"""
Agri-Connect — Alert Engine
Aggregates alerts from: Weather + Satellite + News + Crop Context
Produces prioritized alert list for the farmer dashboard.
"""

from datetime import datetime, timezone
from etl.weather_etl import get_forecast_by_coords
from etl.news_etl import get_recent_alerts_from_news


def generate_farm_alerts(
    lat: float,
    lon: float,
    current_weather: dict = None,
    forecast: dict = None,
    soil: dict = None,
    satellite: dict = None,
    news_alerts: list = None,
    active_crop: str = None,
    season: str = None,
) -> list:
    """
    Generate comprehensive farm alerts from multiple data sources.
    Returns list of alert dicts sorted by severity (danger → warning → info).
    """
    alerts = []

    # === WEATHER ALERTS ===
    if current_weather and current_weather.get("ok"):
        alerts.extend(_weather_current_alerts(current_weather))

    if forecast and forecast.get("ok") and forecast.get("advisory"):
        for adv in forecast["advisory"]:
            if adv["type"] in ("danger", "warning"):
                alerts.append({
                    "type": "weather",
                    "severity": adv["type"],
                    "title": adv["title"],
                    "message": adv["message"],
                    "source": "openweathermap_forecast",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

    # === SOIL ALERTS ===
    if soil and soil.get("ok"):
        alerts.extend(_soil_alerts(soil))

    # === SATELLITE ALERTS ===
    if satellite:
        alerts.extend(_satellite_alerts(satellite))

    # === NEWS ALERTS ===
    if news_alerts:
        for art in news_alerts:
            if art.get("severity") in ("danger", "warning"):
                alerts.append({
                    "type": "news",
                    "severity": art["severity"],
                    "title": f"📰 {art['title']}",
                    "message": art.get("message", ""),
                    "source": art.get("source", "newsapi"),
                    "url": art.get("url"),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

    # === CROP-CONTEXT SEASONAL ALERTS ===
    if active_crop and season:
        alerts.extend(_crop_seasonal_alerts(active_crop, season))

    # Sort: danger first, then warning, then info
    severity_order = {"danger": 0, "warning": 1, "info": 2, "tip": 3}
    alerts.sort(key=lambda a: severity_order.get(a.get("severity", "info"), 99))

    return alerts


def _weather_current_alerts(weather: dict) -> list:
    alerts = []
    temp = weather.get("temperature", 25)
    humidity = weather.get("humidity", 60)
    wind = weather.get("wind_speed", 5)
    rain = weather.get("rainfall", 0)

    if temp > 42:
        alerts.append({"type": "weather", "severity": "danger",
            "title": "⚠️ Extreme Heat — Crop Stress Risk",
            "message": f"Temperature is {temp}°C. Irrigate immediately. Use shade nets. Avoid field work 11am–4pm.",
            "source": "openweathermap_current", "created_at": datetime.now(timezone.utc).isoformat()})
    elif temp > 38:
        alerts.append({"type": "weather", "severity": "warning",
            "title": "🌡️ High Temperature Warning",
            "message": f"Temperature {temp}°C. Increase watering frequency. Mulch to retain soil moisture.",
            "source": "openweathermap_current", "created_at": datetime.now(timezone.utc).isoformat()})

    if humidity > 90:
        alerts.append({"type": "weather", "severity": "warning",
            "title": "💧 Very High Humidity — Disease Risk",
            "message": f"Humidity {humidity}%. High risk of fungal diseases (blight, mildew). Ensure good air circulation.",
            "source": "openweathermap_current", "created_at": datetime.now(timezone.utc).isoformat()})

    if wind > 15:
        alerts.append({"type": "weather", "severity": "warning",
            "title": "💨 Strong Wind Advisory",
            "message": f"Wind speed {wind} m/s. Avoid spraying pesticides. Stake tall crops to prevent lodging.",
            "source": "openweathermap_current", "created_at": datetime.now(timezone.utc).isoformat()})

    if rain > 20:
        alerts.append({"type": "weather", "severity": "warning",
            "title": "🌧️ Heavy Rainfall Detected",
            "message": f"{rain}mm rain in last hour. Check field drainage. Delay fertilizer application.",
            "source": "openweathermap_current", "created_at": datetime.now(timezone.utc).isoformat()})

    return alerts


def _soil_alerts(soil: dict) -> list:
    alerts = []
    ph = soil.get("ph", 7.0)
    n = soil.get("N", 50)
    oc = soil.get("organic_carbon", 50)

    if ph < 5.0:
        alerts.append({"type": "soil", "severity": "warning",
            "title": "🧪 Very Acidic Soil — pH Alert",
            "message": f"Soil pH is {ph:.1f} — too acidic for most crops. Apply agricultural lime 2-4 tonnes/ha.",
            "source": "soilgrids_isric", "created_at": datetime.now(timezone.utc).isoformat()})
    elif ph > 8.5:
        alerts.append({"type": "soil", "severity": "warning",
            "title": "🧪 Alkaline Soil — pH Alert",
            "message": f"Soil pH is {ph:.1f} — too alkaline. Apply gypsum or sulfur. Micronutrient deficiency likely.",
            "source": "soilgrids_isric", "created_at": datetime.now(timezone.utc).isoformat()})

    if n < 20:
        alerts.append({"type": "soil", "severity": "warning",
            "title": "🌿 Low Nitrogen Detected",
            "message": f"Soil nitrogen is low ({n} units). Apply Urea or DAP before sowing.",
            "source": "soilgrids_isric", "created_at": datetime.now(timezone.utc).isoformat()})

    if soil.get("data_quality") == "estimated":
        alerts.append({"type": "soil", "severity": "info",
            "title": "ℹ️ Soil Data is Estimated",
            "message": "Soil values are from SoilGrids model estimates. Upload your soil lab test report for precise recommendations.",
            "source": "soilgrids_isric", "created_at": datetime.now(timezone.utc).isoformat()})

    return alerts


def _satellite_alerts(satellite: dict) -> list:
    alerts = []
    if not satellite:
        return alerts

    ndvi = satellite.get("ndvi")
    cloud_quality = satellite.get("cloud_quality", "clear")
    image_date = satellite.get("image_date")

    if cloud_quality == "unavailable":
        alerts.append({"type": "satellite", "severity": "info",
            "title": "🛰️ Satellite Data Unavailable",
            "message": "Satellite imagery unavailable (heavy cloud cover). Reconnect in 3-5 days for crop health index.",
            "source": "earth_engine", "created_at": datetime.now(timezone.utc).isoformat()})
    elif cloud_quality == "cloudy":
        alerts.append({"type": "satellite", "severity": "info",
            "title": "☁️ Satellite Image Quality: Cloudy",
            "message": f"Latest image ({image_date}) has cloud cover. NDVI values may be inaccurate.",
            "source": "earth_engine", "created_at": datetime.now(timezone.utc).isoformat()})

    if ndvi is not None:
        if ndvi < 0.2:
            alerts.append({"type": "satellite", "severity": "warning",
                "title": "🛰️ Low Vegetation Index (NDVI)",
                "message": f"NDVI = {ndvi:.2f}. Very low vegetation density detected. Crop stress or bare soil possible.",
                "source": "earth_engine", "created_at": datetime.now(timezone.utc).isoformat()})
        elif ndvi < 0.4:
            alerts.append({"type": "satellite", "severity": "info",
                "title": "🛰️ Moderate Vegetation (NDVI)",
                "message": f"NDVI = {ndvi:.2f}. Moderate crop health. Monitor closely for stress progression.",
                "source": "earth_engine", "created_at": datetime.now(timezone.utc).isoformat()})

    return alerts


CROP_SEASONAL_RISKS = {
    "rice": {
        "Kharif": ["Stem borer active during July-August. Apply Carbofuran 3G if spotted.",
                   "Blast disease risk in high humidity. Use Tricyclazole if needed."],
        "Rabi": ["Rice requires warm weather — verify temperature suitability for Rabi planting."],
    },
    "wheat": {
        "Rabi": ["Aphid infestation peaks Dec-Jan. Monitor and apply neem oil spray.",
                 "Yellow rust pressure if temp <10°C with dew. Apply Propiconazole."],
    },
    "cotton": {
        "Kharif": ["Pink bollworm peak in Sep-Oct. Use pheromone traps.",
                   "Whitefly pressure elevated after rains. Apply yellow sticky traps."],
    },
    "maize": {
        "Kharif": ["Fall armyworm active June-September. Apply Emamectin benzoate."],
        "Rabi": ["Check for Stem borer in warmer Rabi maize."],
    },
}


def _crop_seasonal_alerts(crop: str, season: str) -> list:
    alerts = []
    crop_lower = crop.lower()
    risks = CROP_SEASONAL_RISKS.get(crop_lower, {})
    season_risks = risks.get(season, [])
    for risk in season_risks:
        alerts.append({"type": "crop", "severity": "info",
            "title": f"🌱 {crop.title()} — {season} Season Advisory",
            "message": risk,
            "source": "crop_calendar_knowledge_base",
            "created_at": datetime.now(timezone.utc).isoformat()})
    return alerts
