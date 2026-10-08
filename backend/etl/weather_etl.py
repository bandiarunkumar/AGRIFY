"""
Agri-Connect — ETL: Real-time Weather by Coordinates
Uses OpenWeatherMap One Call API (or free 2.5 current+forecast)
RULE: Always fetch by latitude/longitude, never by city name
"""

import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

OWM_KEY = os.getenv('OPENWEATHERMAP_API_KEY', '').strip()
BASE_URL_CURRENT = "https://api.openweathermap.org/data/2.5/weather"
BASE_URL_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"
BASE_URL_ONECALL = "https://api.openweathermap.org/data/3.0/onecall"


def _make_source_url(endpoint, params):
    """Build a reproducible source URL for provenance tracking."""
    safe = {k: v for k, v in params.items() if k != 'appid'}
    qs = '&'.join(f"{k}={v}" for k, v in safe.items())
    return f"{endpoint}?{qs}"


def get_weather_by_coords(lat: float, lon: float) -> dict:
    """
    Fetch LIVE current weather by GPS coordinates.
    Returns structured dict with full provenance metadata.
    """
    if not OWM_KEY:
        return {"error": "OPENWEATHERMAP_API_KEY not configured in .env"}

    params = {
        "lat": lat,
        "lon": lon,
        "appid": OWM_KEY,
        "units": "metric"
    }

    source_url = _make_source_url(BASE_URL_CURRENT, params)

    try:
        resp = requests.get(BASE_URL_CURRENT, params=params, timeout=12)

        if resp.status_code == 401:
            return {"error": "Invalid OpenWeatherMap API key"}
        if resp.status_code == 429:
            return {"error": "API rate limit exceeded. Try again in 1 minute."}
        if resp.status_code != 200:
            return {"error": f"Weather API error: {resp.status_code} — {resp.text[:200]}"}

        d = resp.json()

        rainfall_1h = 0.0
        if "rain" in d:
            rainfall_1h = d["rain"].get("1h", d["rain"].get("3h", 0.0))

        return {
            "ok": True,
            "temperature": round(d["main"]["temp"], 1),
            "feels_like": round(d["main"]["feels_like"], 1),
            "temp_min": round(d["main"]["temp_min"], 1),
            "temp_max": round(d["main"]["temp_max"], 1),
            "humidity": round(d["main"]["humidity"], 1),
            "pressure": d["main"]["pressure"],
            "rainfall": round(rainfall_1h, 2),
            "wind_speed": round(d["wind"].get("speed", 0), 1),
            "wind_deg": d["wind"].get("deg", 0),
            "clouds": d["clouds"]["all"],
            "visibility": d.get("visibility", 0),
            "weather_main": d["weather"][0]["main"],
            "description": d["weather"][0]["description"].title(),
            "icon": d["weather"][0]["icon"],
            "city_name": d.get("name", ""),
            "latitude": lat,
            "longitude": lon,
            # Provenance
            "source_url": source_url,
            "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_quality": "live",
        }

    except requests.exceptions.Timeout:
        return {"error": "Weather API request timed out. Try again."}
    except requests.exceptions.ConnectionError:
        return {"error": "No internet connection."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def get_forecast_by_coords(lat: float, lon: float) -> dict:
    """
    Fetch 5-day/3-hour forecast by GPS coordinates.
    Aggregates to daily summary with farming advisory.
    """
    if not OWM_KEY:
        return {"error": "OPENWEATHERMAP_API_KEY not configured in .env"}

    params = {
        "lat": lat,
        "lon": lon,
        "appid": OWM_KEY,
        "units": "metric",
        "cnt": 40  # 5 days × 8 slots
    }

    source_url = _make_source_url(BASE_URL_FORECAST, params)

    try:
        resp = requests.get(BASE_URL_FORECAST, params=params, timeout=12)

        if resp.status_code == 401:
            return {"error": "Invalid OpenWeatherMap API key"}
        if resp.status_code != 200:
            return {"error": f"Forecast API error: {resp.status_code}"}

        data = resp.json()

        # Group by date
        daily = {}
        for item in data["list"]:
            date = item["dt_txt"].split(" ")[0]
            if date not in daily:
                daily[date] = {
                    "date": date,
                    "temps": [], "humidity": [], "rainfall": 0.0,
                    "descriptions": [], "icons": [],
                    "wind_speeds": [], "clouds": []
                }
            daily[date]["temps"].append(item["main"]["temp"])
            daily[date]["humidity"].append(item["main"]["humidity"])
            daily[date]["wind_speeds"].append(item["wind"]["speed"])
            daily[date]["descriptions"].append(item["weather"][0]["description"])
            daily[date]["icons"].append(item["weather"][0]["icon"])
            daily[date]["clouds"].append(item["clouds"]["all"])
            if "rain" in item:
                daily[date]["rainfall"] += item["rain"].get("3h", 0.0)

        forecast_days = []
        for date_str, info in list(daily.items())[:5]:
            from datetime import datetime as dt
            day_obj = dt.strptime(date_str, "%Y-%m-%d")
            forecast_days.append({
                "date": date_str,
                "day": day_obj.strftime("%A"),
                "short_day": day_obj.strftime("%a"),
                "temp_min": round(min(info["temps"]), 1),
                "temp_max": round(max(info["temps"]), 1),
                "temp_avg": round(sum(info["temps"]) / len(info["temps"]), 1),
                "humidity_avg": round(sum(info["humidity"]) / len(info["humidity"]), 1),
                "rainfall_total": round(info["rainfall"], 2),
                "wind_avg": round(sum(info["wind_speeds"]) / len(info["wind_speeds"]), 1),
                "cloud_avg": round(sum(info["clouds"]) / len(info["clouds"]), 1),
                "description": max(set(info["descriptions"]),
                                   key=info["descriptions"].count).title(),
                "icon": info["icons"][len(info["icons"]) // 2],
            })

        advisory = _generate_farming_advisory(forecast_days)

        return {
            "ok": True,
            "latitude": lat,
            "longitude": lon,
            "city_name": data["city"]["name"],
            "forecast": forecast_days,
            "advisory": advisory,
            "source_url": source_url,
            "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_quality": "live",
        }

    except Exception as e:
        return {"error": f"Forecast error: {str(e)}"}


def _generate_farming_advisory(forecast: list) -> list:
    """Generate actionable farming advisories from forecast data."""
    advisories = []
    if not forecast:
        return advisories

    total_rain = sum(d["rainfall_total"] for d in forecast)
    avg_temp = sum(d["temp_avg"] for d in forecast) / len(forecast)
    avg_humidity = sum(d["humidity_avg"] for d in forecast) / len(forecast)
    max_temp = max(d["temp_max"] for d in forecast)
    min_temp = min(d["temp_min"] for d in forecast)

    if total_rain > 100:
        advisories.append({"type": "danger", "title": "HEAVY RAIN ALERT 🌧️",
            "message": f"Total {total_rain:.1f}mm expected over 5 days. Ensure drainage channels are clear. Delay harvesting and pesticide spraying."})
    elif total_rain > 50:
        advisories.append({"type": "warning", "title": "Heavy Rain Expected",
            "message": f"Total {total_rain:.1f}mm rain. Delay spraying. Check drainage."})
    elif total_rain > 20:
        advisories.append({"type": "info", "title": "Moderate Rain Expected",
            "message": f"{total_rain:.1f}mm rain. Reduce irrigation. Good moisture expected."})
    elif total_rain < 5:
        advisories.append({"type": "warning", "title": "Dry Weather Alert",
            "message": "Very little rain expected. Increase irrigation. Use mulching to retain moisture."})

    if max_temp > 42:
        advisories.append({"type": "danger", "title": "EXTREME HEAT ALERT 🔥",
            "message": f"Max {max_temp:.1f}°C forecast! Water crops early morning & evening. Shade nets recommended."})
    elif max_temp > 38:
        advisories.append({"type": "warning", "title": "Heat Wave Warning",
            "message": f"Max {max_temp:.1f}°C. Increase watering frequency. Avoid midday field work."})
    elif min_temp < 5:
        advisories.append({"type": "danger", "title": "FROST RISK ALERT ❄️",
            "message": f"Min {min_temp:.1f}°C! Cover seedlings and sensitive crops. Frost protection urgently needed."})
    elif min_temp < 10:
        advisories.append({"type": "warning", "title": "Cold Night Alert",
            "message": f"Min {min_temp:.1f}°C. Cover rabi crops at night."})

    if avg_humidity > 85:
        advisories.append({"type": "warning", "title": "High Humidity – Disease Risk",
            "message": f"Avg humidity {avg_humidity:.0f}%. Elevated fungal/bacterial disease risk. Pre-emptive fungicide advised."})

    dry_days = [d for d in forecast if d["rainfall_total"] < 2 and d["wind_avg"] < 15]
    if dry_days:
        best = dry_days[0]
        advisories.append({"type": "tip", "title": "✅ Best Spray Day",
            "message": f"{best['day']} ({best['date']}) — Low rain & low wind. Ideal for pesticide/fertilizer spraying."})

    consecutive_dry = 0
    for d in forecast:
        if d["rainfall_total"] < 2:
            consecutive_dry += 1
        else:
            break
    if consecutive_dry >= 3:
        advisories.append({"type": "tip", "title": "Good Harvest Window",
            "message": f"Next {consecutive_dry} days are dry. Consider harvesting if crops are ready."})

    if not advisories:
        advisories.append({"type": "info", "title": "Normal Conditions",
            "message": f"Avg temp {avg_temp:.1f}°C, humidity {avg_humidity:.0f}%. Regular farming schedule recommended."})

    return advisories


# --- Backward compat: city-name weather (legacy, routes to coords via geocode) ---
def get_weather_by_city(city: str) -> dict:
    """
    Legacy: Fetch current weather by city name.
    Internally converts to coords for consistency.
    """
    if not OWM_KEY:
        return {"error": "OPENWEATHERMAP_API_KEY not configured in .env"}

    # First geocode the city to get coords
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    try:
        geo_resp = requests.get(geo_url, params={"q": city, "limit": 1, "appid": OWM_KEY}, timeout=10)
        if geo_resp.status_code == 200 and geo_resp.json():
            geo = geo_resp.json()[0]
            return get_weather_by_coords(geo["lat"], geo["lon"])
    except Exception:
        pass

    # Fallback to direct city call
    params = {"q": city, "appid": OWM_KEY, "units": "metric"}
    try:
        resp = requests.get(BASE_URL_CURRENT, params=params, timeout=10)
        if resp.status_code == 404:
            return {"error": f"City '{city}' not found"}
        if resp.status_code != 200:
            return {"error": f"API error {resp.status_code}"}
        d = resp.json()
        return get_weather_by_coords(d["coord"]["lat"], d["coord"]["lon"])
    except Exception as e:
        return {"error": str(e)}


def get_forecast_by_city(city: str) -> dict:
    """Legacy: forecast by city, internally converts to coords."""
    if not OWM_KEY:
        return {"error": "OPENWEATHERMAP_API_KEY not configured"}
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    try:
        geo_resp = requests.get(geo_url, params={"q": city, "limit": 1, "appid": OWM_KEY}, timeout=10)
        if geo_resp.status_code == 200 and geo_resp.json():
            geo = geo_resp.json()[0]
            return get_forecast_by_coords(geo["lat"], geo["lon"])
    except Exception:
        pass
    return {"error": f"Could not geocode city: {city}"}
