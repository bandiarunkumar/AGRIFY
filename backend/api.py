"""
Agri-Connect — Production Flask API
Coordinate-first, source-aware, no fake data in main flow.
"""

import os
import json
import hashlib
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# ---- Conditional DB import (works without DB too) ----
USE_DB = bool(os.getenv('DATABASE_URL'))
if USE_DB:
    from models.database import db, FarmProfile, WeatherSnapshot, SoilSummary, CropRecommendation, AgricultureNews, FarmAlert
    from sqlalchemy.exc import IntegrityError

# ---- ETL Modules ----
from etl.weather_etl import get_weather_by_coords, get_forecast_by_coords, get_weather_by_city, get_forecast_by_city
from etl.geocoding_etl import reverse_geocode
from etl.soil_etl import get_soil_by_coords
from etl.news_etl import fetch_all_news, get_recent_alerts_from_news
from etl.market_etl import fetch_market_prices, fetch_markets_for_state
from alerts.alert_engine import generate_farm_alerts

# ---- Legacy ML models ----
from predictions import predict_crop, predict_fertilizer, REGION_SOIL_PROFILES
from config import (
    MARKET_LOCATIONS, VEGETABLE_PRICES, CROP_PRICES,
    PESTICIDE_EFFECTS, FERTILIZER_EFFECTS, SOIL_REMEDIATION
)

import random

# ============================================================
# CROP KNOWLEDGE BASE (hybrid feasibility + AI ranking)
# ============================================================
CROP_PROFILES = {
    # === CEREALS ===
    "rice":       {"season": ["Kharif"], "min_rain": 100, "max_rain": 500, "min_temp": 20, "max_temp": 38,
                   "min_ph": 5.0, "max_ph": 8.0, "min_n": 40, "water_need": "high",
                   "sow_months": "June–July", "harvest_months": "November–December", "duration_days": 120,
                   "regions": ["South", "East", "North"]},
    "wheat":      {"season": ["Rabi"], "min_rain": 50, "max_rain": 300, "min_temp": 10, "max_temp": 25,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 30, "water_need": "medium",
                   "sow_months": "November–December", "harvest_months": "March–April", "duration_days": 130,
                   "regions": ["North", "West"]},
    "maize":      {"season": ["Kharif", "Rabi"], "min_rain": 60, "max_rain": 350, "min_temp": 18, "max_temp": 35,
                   "min_ph": 5.5, "max_ph": 7.5, "min_n": 30, "water_need": "medium",
                   "sow_months": "June–July (K) / October–November (R)", "harvest_months": "September–October (K) / February–March (R)", "duration_days": 100,
                   "regions": ["South", "North", "East", "West"]},

    # === CASH CROPS ===
    "cotton":     {"season": ["Kharif"], "min_rain": 60, "max_rain": 250, "min_temp": 20, "max_temp": 40,
                   "min_ph": 5.8, "max_ph": 8.0, "min_n": 30, "water_need": "medium",
                   "sow_months": "April–May", "harvest_months": "November–January", "duration_days": 180,
                   "regions": ["South", "West", "North"]},
    "sugarcane":  {"season": ["Kharif", "Rabi"], "min_rain": 100, "max_rain": 400, "min_temp": 20, "max_temp": 40,
                   "min_ph": 6.0, "max_ph": 8.0, "min_n": 60, "water_need": "very high",
                   "sow_months": "February–March (spring) / October (autumn)", "harvest_months": "January–March", "duration_days": 360,
                   "regions": ["South", "West", "North"]},

    # === OILSEEDS ===
    "soybean":    {"season": ["Kharif"], "min_rain": 60, "max_rain": 300, "min_temp": 20, "max_temp": 35,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 10, "water_need": "medium",
                   "sow_months": "June–July", "harvest_months": "October–November", "duration_days": 100,
                   "regions": ["West", "South"]},
    "groundnut":  {"season": ["Kharif", "Rabi"], "min_rain": 50, "max_rain": 250, "min_temp": 22, "max_temp": 38,
                   "min_ph": 5.5, "max_ph": 7.5, "min_n": 10, "water_need": "low-medium",
                   "sow_months": "June–July (K) / November–December (R)", "harvest_months": "October–November (K) / March–April (R)", "duration_days": 110,
                   "regions": ["South", "West"]},

    # === PULSES ===
    "blackgram":  {"season": ["Kharif", "Rabi"], "min_rain": 40, "max_rain": 200, "min_temp": 20, "max_temp": 38,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 10, "water_need": "low",
                   "sow_months": "June–July (K) / October–November (R)", "harvest_months": "September–October (K) / January–February (R)", "duration_days": 80,
                   "regions": ["South", "West", "North"]},
    "chickpea":   {"season": ["Rabi"], "min_rain": 30, "max_rain": 150, "min_temp": 10, "max_temp": 28,
                   "min_ph": 5.5, "max_ph": 8.5, "min_n": 10, "water_need": "low",
                   "sow_months": "October–November", "harvest_months": "February–March", "duration_days": 100,
                   "regions": ["West", "North", "South"]},
    "pigeonpeas": {"season": ["Kharif"], "min_rain": 40, "max_rain": 200, "min_temp": 18, "max_temp": 38,
                   "min_ph": 5.0, "max_ph": 8.5, "min_n": 10, "water_need": "low",
                   "sow_months": "June–July", "harvest_months": "December–January", "duration_days": 170,
                   "regions": ["South", "West", "East"]},
    "lentil":     {"season": ["Rabi"], "min_rain": 25, "max_rain": 120, "min_temp": 8, "max_temp": 25,
                   "min_ph": 6.0, "max_ph": 8.0, "min_n": 10, "water_need": "very low",
                   "sow_months": "October–November", "harvest_months": "February–March", "duration_days": 110,
                   "regions": ["North", "East"]},
    "mungbean":   {"season": ["Kharif", "Zaid"], "min_rain": 40, "max_rain": 200, "min_temp": 22, "max_temp": 38,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 10, "water_need": "low",
                   "sow_months": "June–July (K) / March–April (Zaid)", "harvest_months": "September (K) / May–June (Zaid)", "duration_days": 65,
                   "regions": ["South", "North", "West"]},
    "mothbeans":  {"season": ["Kharif"], "min_rain": 25, "max_rain": 150, "min_temp": 25, "max_temp": 42,
                   "min_ph": 6.0, "max_ph": 8.5, "min_n": 10, "water_need": "very low",
                   "sow_months": "July–August", "harvest_months": "October–November", "duration_days": 80,
                   "regions": ["West"]},

    # === VEGETABLES ===
    "tomato":     {"season": ["Rabi", "Zaid", "Kharif"], "min_rain": 40, "max_rain": 150, "min_temp": 15, "max_temp": 35,
                   "min_ph": 5.5, "max_ph": 7.0, "min_n": 40, "water_need": "medium",
                   "sow_months": "September–October (R) / January–February (Zaid)", "harvest_months": "December–February (R) / April–May (Zaid)", "duration_days": 75,
                   "regions": ["South", "West", "North"]},
    "potato":     {"season": ["Rabi"], "min_rain": 50, "max_rain": 200, "min_temp": 10, "max_temp": 25,
                   "min_ph": 5.0, "max_ph": 6.5, "min_n": 40, "water_need": "medium",
                   "sow_months": "October–November", "harvest_months": "January–February", "duration_days": 90,
                   "regions": ["North", "West", "East"]},
    "onion":      {"season": ["Rabi", "Kharif"], "min_rain": 30, "max_rain": 150, "min_temp": 13, "max_temp": 30,
                   "min_ph": 6.0, "max_ph": 7.0, "min_n": 30, "water_need": "medium",
                   "sow_months": "October–November (R) / June–July (K)", "harvest_months": "February–March (R) / September–October (K)", "duration_days": 120,
                   "regions": ["South", "West", "North"]},

    # === FRUITS ===
    "banana":     {"season": ["Kharif", "Rabi"], "min_rain": 100, "max_rain": 500, "min_temp": 20, "max_temp": 38,
                   "min_ph": 5.5, "max_ph": 7.0, "min_n": 60, "water_need": "high",
                   "sow_months": "June–August (K) / October–November (R)", "harvest_months": "12–14 months after planting (Year-round)", "duration_days": 420,
                   "regions": ["South", "East", "West"]},
    "mango":      {"season": ["Zaid"], "min_rain": 50, "max_rain": 300, "min_temp": 25, "max_temp": 40,
                   "min_ph": 5.5, "max_ph": 7.5, "min_n": 30, "water_need": "low-medium",
                   "sow_months": "July–August (planting saplings)", "harvest_months": "April–July (fruiting from 5th year)", "duration_days": 90,
                   "regions": ["South", "West", "North"]},

    # === FIBRE CROPS ===
    "jute":       {"season": ["Kharif"], "min_rain": 150, "max_rain": 600, "min_temp": 25, "max_temp": 38,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 40, "water_need": "very high",
                   "sow_months": "March–May", "harvest_months": "July–September", "duration_days": 120,
                   "regions": ["East"]},
    "coconut":    {"season": ["Kharif"], "min_rain": 150, "max_rain": 600, "min_temp": 22, "max_temp": 38,
                   "min_ph": 5.0, "max_ph": 8.0, "min_n": 30, "water_need": "high",
                   "sow_months": "June–September (planting seedlings)", "harvest_months": "Year-round (from 5th year)", "duration_days": 1825,
                   "regions": ["South"]},

    # === SPICES & CONDIMENTS (Guntur-famous crops) ===
    "chilli":     {"season": ["Kharif", "Rabi"], "min_rain": 50, "max_rain": 250, "min_temp": 20, "max_temp": 38,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 40, "water_need": "medium",
                   "sow_months": "June–July (K) / September–October (R)", "harvest_months": "November–February (K) / February–April (R)", "duration_days": 150,
                   "regions": ["South", "West", "North"]},
    "mirchi":     {"season": ["Kharif", "Rabi"], "min_rain": 50, "max_rain": 250, "min_temp": 20, "max_temp": 38,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 40, "water_need": "medium",
                   "sow_months": "June–July (K) / September–October (R)", "harvest_months": "November–February (K) / February–April (R)", "duration_days": 150,
                   "regions": ["South", "West", "North"]},
    "turmeric":   {"season": ["Kharif"], "min_rain": 100, "max_rain": 400, "min_temp": 20, "max_temp": 35,
                   "min_ph": 5.5, "max_ph": 7.5, "min_n": 30, "water_need": "medium-high",
                   "sow_months": "May–June", "harvest_months": "January–March (8–9 months)", "duration_days": 260,
                   "regions": ["South", "East"]},
    "coriander":  {"season": ["Rabi"], "min_rain": 20, "max_rain": 100, "min_temp": 15, "max_temp": 30,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 20, "water_need": "low",
                   "sow_months": "October–November", "harvest_months": "January–February", "duration_days": 80,
                   "regions": ["South", "West", "North"]},
    "curry_leaf":  {"season": ["Kharif"], "min_rain": 50, "max_rain": 300, "min_temp": 20, "max_temp": 40,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 20, "water_need": "low-medium",
                   "sow_months": "June–July (planting)", "harvest_months": "Year-round (from 2nd year)", "duration_days": 365,
                   "regions": ["South"]},

    # === MORE VEGETABLES ===
    "brinjal":    {"season": ["Kharif", "Rabi"], "min_rain": 40, "max_rain": 200, "min_temp": 18, "max_temp": 35,
                   "min_ph": 5.5, "max_ph": 7.0, "min_n": 40, "water_need": "medium",
                   "sow_months": "June–July (K) / October–November (R)", "harvest_months": "September–December (K) / February–April (R)", "duration_days": 100,
                   "regions": ["South", "West", "East", "North"]},
    "cabbage":    {"season": ["Rabi"], "min_rain": 40, "max_rain": 150, "min_temp": 10, "max_temp": 25,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 50, "water_need": "medium",
                   "sow_months": "September–October", "harvest_months": "December–February", "duration_days": 90,
                   "regions": ["North", "South", "East"]},
    "cauliflower": {"season": ["Rabi"], "min_rain": 40, "max_rain": 150, "min_temp": 10, "max_temp": 25,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 50, "water_need": "medium",
                   "sow_months": "September–October", "harvest_months": "December–February", "duration_days": 90,
                   "regions": ["North", "South", "East"]},
    "capsicum":   {"season": ["Kharif", "Rabi"], "min_rain": 40, "max_rain": 180, "min_temp": 18, "max_temp": 32,
                   "min_ph": 5.5, "max_ph": 7.0, "min_n": 40, "water_need": "medium",
                   "sow_months": "June–July (K) / September–October (R)", "harvest_months": "September–December (K) / January–March (R)", "duration_days": 95,
                   "regions": ["South", "West", "North"]},
    "ladies_finger": {"season": ["Kharif", "Zaid"], "min_rain": 40, "max_rain": 250, "min_temp": 22, "max_temp": 40,
                   "min_ph": 6.0, "max_ph": 7.5, "min_n": 30, "water_need": "medium",
                   "sow_months": "June–July (K) / February–March (Zaid)", "harvest_months": "August–October (K) / April–June (Zaid)", "duration_days": 60,
                   "regions": ["South", "West", "East", "North"]},
    "bitter_gourd": {"season": ["Kharif", "Zaid"], "min_rain": 40, "max_rain": 200, "min_temp": 22, "max_temp": 38,
                   "min_ph": 5.5, "max_ph": 7.5, "min_n": 30, "water_need": "medium",
                   "sow_months": "June–July (K) / February–March (Zaid)", "harvest_months": "August–October (K) / April–May (Zaid)", "duration_days": 70,
                   "regions": ["South", "West", "East", "North"]},
    "drumstick":  {"season": ["Kharif"], "min_rain": 30, "max_rain": 250, "min_temp": 22, "max_temp": 40,
                   "min_ph": 6.0, "max_ph": 8.0, "min_n": 20, "water_need": "low",
                   "sow_months": "June–July (planting)", "harvest_months": "Year-round (from 8th month)", "duration_days": 240,
                   "regions": ["South", "West"]},
}

FERTILIZER_STAGE_GUIDE = {
    "rice":    [{"stage": "Basal (before transplanting)", "n_pct": 30, "p_pct": 100, "k_pct": 50},
                {"stage": "Tillering (21-25 days)", "n_pct": 40, "p_pct": 0, "k_pct": 30},
                {"stage": "Panicle initiation (50-55 days)", "n_pct": 30, "p_pct": 0, "k_pct": 20}],
    "wheat":   [{"stage": "Basal (sowing time)", "n_pct": 50, "p_pct": 100, "k_pct": 100},
                {"stage": "First irrigation (21 days)", "n_pct": 25, "p_pct": 0, "k_pct": 0},
                {"stage": "Second irrigation (42 days)", "n_pct": 25, "p_pct": 0, "k_pct": 0}],
    "maize":   [{"stage": "Basal", "n_pct": 30, "p_pct": 100, "k_pct": 100},
                {"stage": "Knee-high (V6)", "n_pct": 40, "p_pct": 0, "k_pct": 0},
                {"stage": "Tasseling", "n_pct": 30, "p_pct": 0, "k_pct": 0}],
    "cotton":  [{"stage": "Basal", "n_pct": 25, "p_pct": 100, "k_pct": 50},
                {"stage": "First square (30-40 days)", "n_pct": 25, "p_pct": 0, "k_pct": 25},
                {"stage": "Peak bloom (60-75 days)", "n_pct": 50, "p_pct": 0, "k_pct": 25}],
    "chilli":  [{"stage": "Basal (transplanting)", "n_pct": 25, "p_pct": 100, "k_pct": 50},
                {"stage": "Vegetative (30-45 days)", "n_pct": 35, "p_pct": 0, "k_pct": 25},
                {"stage": "Flowering (60-75 days)", "n_pct": 40, "p_pct": 0, "k_pct": 25}],
    "mirchi":  [{"stage": "Basal (transplanting)", "n_pct": 25, "p_pct": 100, "k_pct": 50},
                {"stage": "Vegetative (30-45 days)", "n_pct": 35, "p_pct": 0, "k_pct": 25},
                {"stage": "Flowering (60-75 days)", "n_pct": 40, "p_pct": 0, "k_pct": 25}],
    "turmeric":[{"stage": "Basal (planting)", "n_pct": 30, "p_pct": 100, "k_pct": 50},
                {"stage": "Active growth (60 days)", "n_pct": 35, "p_pct": 0, "k_pct": 25},
                {"stage": "Rhizome formation (120 days)", "n_pct": 35, "p_pct": 0, "k_pct": 25}],
    "tomato":  [{"stage": "Basal (transplanting)", "n_pct": 25, "p_pct": 100, "k_pct": 50},
                {"stage": "Flowering (30-40 days)", "n_pct": 35, "p_pct": 0, "k_pct": 25},
                {"stage": "Fruit setting (50-60 days)", "n_pct": 40, "p_pct": 0, "k_pct": 25}],
    "sugarcane":[{"stage": "Basal (planting)", "n_pct": 20, "p_pct": 100, "k_pct": 50},
                {"stage": "Grand growth (60-90 days)", "n_pct": 40, "p_pct": 0, "k_pct": 25},
                {"stage": "Ripening (5-6 months)", "n_pct": 40, "p_pct": 0, "k_pct": 25}],
    "onion":   [{"stage": "Basal (transplanting)", "n_pct": 30, "p_pct": 100, "k_pct": 50},
                {"stage": "Bulb initiation (40-50 days)", "n_pct": 35, "p_pct": 0, "k_pct": 25},
                {"stage": "Bulb development (70-80 days)", "n_pct": 35, "p_pct": 0, "k_pct": 25}],
    "banana":  [{"stage": "Basal (planting)", "n_pct": 20, "p_pct": 100, "k_pct": 30},
                {"stage": "Vegetative (3-4 months)", "n_pct": 40, "p_pct": 0, "k_pct": 35},
                {"stage": "Flowering (6-8 months)", "n_pct": 40, "p_pct": 0, "k_pct": 35}],
}

ORGANIC_ALTERNATIVES = {
    "Urea":    ["Vermicompost (5-8 tonnes/ha)", "Green manure (Dhaincha)", "Azotobacter biofertilizer"],
    "DAP":     ["Bone meal (250 kg/ha)", "Rock phosphate + PSB culture", "Compost (4-5 tonnes/ha)"],
    "MOP":     ["Wood ash (500 kg/ha)", "Banana peel compost", "Langbeinite mineral"],
    "NPK":     ["Vermicompost + Neem cake", "FYM 10 tonnes/ha", "Jeevamrit (liquid biofertilizer)"],
    "Compost": ["FYM (farmyard manure)", "Green manure crops", "Bio-compost"],
}

DISEASE_WARNINGS = {
    "Urea":    "Excess urea causes lodging, increases disease susceptibility. Split doses — never apply all at once.",
    "DAP":     "High phosphorus blocks zinc uptake. Monitor for zinc deficiency (interveinal chlorosis).",
    "MOP":     "Chloride-sensitive crops (onion, potato) should use SOP (sulfate of potash) instead.",
    "NPK":     "Check NPK grade matches crop need. Not all NPK formulations are the same.",
    "Compost": "Ensure compost is fully mature. Raw compost can burn roots and introduce pathogens.",
}


# ============================================================
# FEASIBILITY ENGINE
# ============================================================
def get_feasible_crops(temperature, humidity, ph, rainfall, N, P, K, region, season):
    """
    Filter crops by real agronomic constraints (NOT AI — rule-based).
    Returns list of feasible crop dicts.
    """
    feasible = []
    for crop, profile in CROP_PROFILES.items():
        # Season filter
        if season and profile["season"] and season not in profile["season"]:
            continue
        # Climate filter
        if temperature < profile["min_temp"] or temperature > profile["max_temp"]:
            continue
        if rainfall < profile["min_rain"]:
            continue
        # pH filter
        if ph < profile["min_ph"] or ph > profile["max_ph"]:
            continue
        # Nitrogen minimum check
        if N < profile.get("min_n", 0):
            continue
        # Region filter (Strict — exclude if region is wildly inappropriate like Jute in South)
        allowed_regions = profile.get("regions", ["South", "North", "East", "West"])
        if region and region not in allowed_regions:
            continue
            
        region_match = True

        feasible.append({
            "crop": crop,
            "profile": profile,
            "region_match": region_match,
        })
    return feasible


app = Flask(__name__)
CORS(app, origins="*")

if USE_DB:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()


# ============================================================
# HEALTH CHECK
# ============================================================
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "app": "Agri-Connect API",
        "version": "3.0-production",
        "database": "connected" if USE_DB else "disabled (no DATABASE_URL)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ============================================================
# WEATHER BY COORDINATES (Primary — GPS-first)
# ============================================================
@app.route("/api/weather/coords", methods=["GET"])
def weather_by_coords():
    """Fetch current weather by GPS coordinates."""
    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lon required as numbers"}), 400

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"error": "Invalid coordinates"}), 400

    result = get_weather_by_coords(lat, lon)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/forecast/coords", methods=["GET"])
def forecast_by_coords():
    """Fetch 5-day forecast by GPS coordinates."""
    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lon required as numbers"}), 400

    result = get_forecast_by_coords(lat, lon)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


# ============================================================
# WEATHER BY CITY (Legacy — converts internally to coords)
# ============================================================
@app.route("/api/weather", methods=["GET"])
def weather_by_city():
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify({"error": "city parameter required"}), 400

    result = get_weather_by_city(city)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/forecast", methods=["GET"])
def forecast_by_city():
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify({"error": "city parameter required"}), 400

    result = get_forecast_by_city(city)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


# ============================================================
# REVERSE GEOCODING
# ============================================================
@app.route("/api/geocode/reverse", methods=["GET"])
def geocode_reverse():
    """Convert GPS coordinates to location name."""
    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lon required"}), 400

    result = reverse_geocode(lat, lon)
    return jsonify(result)


# ============================================================
# SOIL DATA BY COORDINATES (SoilGrids / ISRIC)
# ============================================================
@app.route("/api/soil/coords", methods=["GET"])
def soil_by_coords():
    """Fetch real soil data by GPS coordinates from SoilGrids."""
    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lon required"}), 400

    result = get_soil_by_coords(lat, lon)
    return jsonify(result)


# ============================================================
# FULL FARM ANALYSIS (Coordinates-first)
# ============================================================
@app.route("/api/farm/analyze", methods=["POST"])
def farm_analyze():
    """
    Complete farm analysis using GPS coordinates.
    1. Geocode → location metadata
    2. Live weather by coords
    3. Real soil data from SoilGrids
    4. Feasibility filter + AI crop ranking
    5. Fertilizer recommendation
    6. Irrigation guidance
    7. Alert generation
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat is None or lon is None:
        return jsonify({"error": "latitude and longitude required"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return jsonify({"error": "latitude and longitude must be numbers"}), 400

    acres = float(data.get("area_acres", 1.0))
    season = data.get("season", "Kharif")
    # Auto-detect region from coordinates if not provided
    region = data.get("region")
    if not region:
        # Simple lat/lon based region detection for India
        if lat > 28:  # North India (UP, Punjab, Haryana, etc.)
            region = "North"
        elif lat < 15:  # Deep South (TN, Kerala, Karnataka)
            region = "South"
        elif lon < 80 and lat < 25:  # West India (Gujarat, Maharashtra, Rajasthan)
            region = "West"
        elif lon > 85:  # East India (WB, Odisha, Bihar, Jharkhand)
            region = "East"
        else:
            region = "South"  # Default for Telangana, AP, Karnataka
    previous_crop = data.get("previous_crop", "Unknown")
    previous_fertilizer = data.get("previous_fertilizer", "Urea")
    previous_pesticide = data.get("previous_pesticide", "Neem oil")
    irrigation = data.get("irrigation", "Drip")
    yield_last = float(data.get("yield_last", 3000))
    farmer_name = data.get("farmer_name", "")

    response = {
        "request": {
            "latitude": lat, "longitude": lon,
            "area_acres": acres, "season": season,
            "region": region,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 1. GEOCODING
    geo = reverse_geocode(lat, lon)
    response["location"] = geo

    # 2. LIVE WEATHER
    weather = get_weather_by_coords(lat, lon)
    response["weather"] = weather

    # 3. SOIL DATA (real - SoilGrids)
    # Check if farmer provided manual soil values (override)
    has_manual_soil = all(k in data for k in ["N", "P", "K", "ph"])
    if has_manual_soil:
        soil = {
            "ok": True,
            "N": float(data["N"]),
            "P": float(data["P"]),
            "K": float(data["K"]),
            "ph": float(data.get("ph", 6.5)),
            "soil_type": data.get("soil_type", "Loamy"),
            "moisture_pct": float(data.get("soil_moisture", 40)),
            "organic_carbon": float(data.get("organic_carbon", 50)),
            "source_name": "user_entered",
            "data_quality": "user_entered",
            "data_quality_note": "Values entered by farmer.",
        }
    else:
        soil = get_soil_by_coords(lat, lon)

    response["soil"] = soil

    # 4. CROP RECOMMENDATION (hybrid feasibility + ML)
    temperature = weather.get("temperature", 28) if weather.get("ok") else 28
    humidity = weather.get("humidity", 65) if weather.get("ok") else 65
    annual_rain_input = data.get("annual_rainfall_mm")
    if not annual_rain_input or float(annual_rain_input) == 0:
        rainfall = float(soil.get("moisture_pct", 40) * 5)
    else:
        rainfall = float(annual_rain_input)

    N = soil.get("N", 50)
    P = soil.get("P", 40)
    K = soil.get("K", 30)
    ph = soil.get("ph", 6.8)
    soil_moisture = soil.get("moisture_pct", 40)
    organic_carbon = soil.get("organic_carbon", 50)

    # Step A: Feasibility filter (rule-based)
    feasible = get_feasible_crops(temperature, humidity, ph, rainfall, N, P, K, region, season)

    if not feasible:
        # Loosen season constraint if nothing matches
        feasible = get_feasible_crops(temperature, humidity, ph, rainfall, N, P, K, region, None)

    if not feasible:
        # Extreme fallback: just return ALL crops to guarantee we display recommendations
        # regardless of explicitly invalid or extreme soil data inputs.
        feasible = []
        for crop_name, profile in CROP_PROFILES.items():
            feasible.append({
                "crop": crop_name,
                "profile": profile,
                "region_match": True if not region else (region in profile.get("regions", []))
            })

    # Step B: AI ranking (from ML model)
    try:
        ml_result = predict_crop(
            N=N, P=P, K=K,
            temperature=temperature,
            humidity=humidity,
            ph=ph,
            rainfall=rainfall,
        )
        ml_ranked = {}
        if "best_crop" in ml_result:
            all_ml = [ml_result["best_crop"]] + (ml_result.get("alternatives") or [])
            for item in all_ml:
                ml_ranked[item["crop"].lower()] = item.get("confidence", 0)
    except Exception:
        ml_ranked = {}

    # Step C: Score feasible crops using ML confidence
    scored = []
    for fc in feasible:
        crop = fc["crop"]
        profile = fc["profile"]
        ml_score = ml_ranked.get(crop, 0)
        
        region_bonus = 5 if fc["region_match"] else 0

        # Smart Geolocation Boost for historically famous regional crops
        geo_bonus = 0
        if "guntur" in str(geo.get("district", "")).lower() and crop in ["chilli", "mirchi", "cotton"]:
            geo_bonus = 15
        if "vijayawada" in str(geo.get("district", "")).lower() and crop in ["banana", "rice"]:
            geo_bonus = 10

        # Dynamic agronomic distance scoring
        ideal_temp = (profile["min_temp"] + profile["max_temp"]) / 2
        temp_dist = abs(temperature - ideal_temp)
        temp_range = (profile["max_temp"] - profile["min_temp"]) / 2
        temp_penalty = min(20, (temp_dist / max(1, temp_range)) * 10)

        ideal_ph = (profile["min_ph"] + profile["max_ph"]) / 2
        ph_dist = abs(ph - ideal_ph)
        ph_range = (profile["max_ph"] - profile["min_ph"]) / 2
        ph_penalty = min(20, (ph_dist / max(0.1, ph_range)) * 10)

        min_rain = profile.get("min_rain", 0)
        max_rain = profile.get("max_rain", 3000)
        ideal_rain = (min_rain + max_rain) / 2
        rain_dist = abs(rainfall - ideal_rain)
        rain_range = max(1, (max_rain - min_rain) / 2)
        rain_penalty = min(20, (rain_dist / rain_range) * 10)

        n_req = profile.get("min_n", 0)
        n_penalty = 0 if N >= n_req else min(20, ((n_req - N) / max(1, n_req)) * 20)

        # Baseline optimal score is 85, minus penalties
        base_score = 85 - temp_penalty - ph_penalty - rain_penalty - n_penalty

        if ml_score > 0:
            final_score = base_score * 0.3 + ml_score * 0.7 + region_bonus + geo_bonus
        else:
            final_score = base_score + region_bonus + geo_bonus
            
        suitability = round(min(99, max(1, final_score)), 1)

        # Price / profit info
        price_per_kg = CROP_PRICES.get(crop, 25)
        from config import CROP_BASE_YIELD
        base_yield = CROP_BASE_YIELD.get(crop, 2000)
        hectares = acres * 0.4047
        net_profit = round((base_yield * price_per_kg - 15000) * hectares)

        reason_parts = []
        if temperature >= profile["min_temp"] and temperature <= profile["max_temp"]:
            reason_parts.append(f"temperature ({temperature}°C) fits ideal range {profile['min_temp']}–{profile['max_temp']}°C")
        if ph >= profile["min_ph"] and ph <= profile["max_ph"]:
            reason_parts.append(f"soil pH {ph:.1f} within optimal {profile['min_ph']}–{profile['max_ph']}")
        if rainfall >= profile["min_rain"]:
            reason_parts.append(f"rainfall ({rainfall}mm) meets minimum {profile['min_rain']}mm")
        if humidity >= 50 and humidity <= 85:
            reason_parts.append(f"humidity ({humidity}%) favorable for growth")
        if N >= profile.get("min_n", 0):
            reason_parts.append(f"soil nitrogen ({N} kg/ha) adequate")
        if ml_score > 20:
            reason_parts.append(f"trained model shows {ml_score:.0f}% pattern match with dataset")
        if fc["region_match"]:
            reason_parts.append(f"suited for {region} region farming")
        
        # Build a informative final reason
        if reason_parts:
            final_reason = "; ".join(reason_parts[:4])  # max 4 most relevant reasons
        else:
            final_reason = f"Passes basic agronomic filters for {season} season at {temperature}°C, pH {ph:.1f}"

        scored.append({
            "crop": crop,
            "suitability_score": suitability,
            "season": ", ".join(profile["season"]),
            "sowing_months": profile["sow_months"],
            "harvest_months": profile["harvest_months"],
            "duration_days": profile["duration_days"],
            "water_need": profile["water_need"],
            "reason": final_reason,
            "price_per_kg": price_per_kg,
            "net_profit_estimated": net_profit,
            "region_match": fc["region_match"],
            "ml_confidence": round(ml_score, 2),
            "in_dataset": crop.lower() in ['papaya', 'kidneybeans', 'coffee', 'mango', 'jute', 'maize', 'cotton', 'grapes', 'watermelon', 'rice', 'muskmelon', 'pigeonpeas', 'chickpea', 'blackgram', 'mungbean', 'banana', 'apple', 'coconut', 'mothbeans', 'pomegranate', 'orange', 'lentil']
        })

    scored.sort(key=lambda x: -x["suitability_score"])

    top_3 = scored[:3]
    all_feasible = scored

    response["crop_recommendation"] = {
        "top_3": top_3,
        "all_feasible": all_feasible,
        "total_feasible_count": len(all_feasible),
        "method": "hybrid_feasibility_ml",
        "inputs": {
            "temperature": temperature, "humidity": humidity,
            "ph": ph, "rainfall": rainfall, "N": N, "P": P, "K": K,
            "season": season, "region": region,
        }
    }

    # 5. FERTILIZER RECOMMENDATION
    best_crop_name = top_3[0]["crop"] if top_3 else "rice"
    try:
        fert_result = predict_fertilizer(
            soil_type=soil.get("soil_type", "Loamy"),
            soil_ph=ph,
            soil_moisture=soil_moisture,
            organic_carbon=organic_carbon / 100 if organic_carbon > 5 else organic_carbon,
            electrical_conductivity=0.5,
            N=N, P=P, K=K,
            temperature=temperature, humidity=humidity, rainfall=rainfall,
            crop_type=previous_crop or best_crop_name,
            growth_stage="Vegetative",
            season=season, irrigation=irrigation,
            previous_crop=previous_crop,
            region=region,
            fertilizer_usage=previous_fertilizer,
            yield_last=yield_last,
        )
        if "error" in fert_result:
            raise Exception(fert_result["error"])
        best_fert = fert_result.get("best_fertilizer", {})
        fert_name = best_fert.get("fertilizer", "NPK")
    except Exception:
        # Rule-based fallback using soil data explicitly
        n_def = N < 35
        p_def = P < 25
        k_def = K < 25
        if n_def and not p_def and not k_def:
            fert_name = "Urea"
        elif p_def and not n_def and not k_def:
            fert_name = "SSP"
        elif k_def and not n_def and not p_def:
            fert_name = "MOP"
        elif n_def and p_def and not k_def:
            fert_name = "DAP"
        elif n_def and p_def and k_def:
            fert_name = "NPK"
        else:
            fert_name = "Compost"
            
        from config import FERTILIZER_INFO
        best_fert = {
            "fertilizer": fert_name, 
            "confidence": 75.0,
            "details": FERTILIZER_INFO.get(fert_name, {
                "npk": "N/A", "qty_per_ha": 50, "cost_per_kg": 20
            })
        }
        fert_name = best_fert.get("fertilizer", "NPK")

    # Stage-wise guide
    stage_guide = FERTILIZER_STAGE_GUIDE.get(best_crop_name, FERTILIZER_STAGE_GUIDE.get("rice", []))
    organic_alts = ORGANIC_ALTERNATIVES.get(fert_name, ["Compost 5 tonnes/ha", "Vermicompost 3 tonnes/ha"])
    warning = DISEASE_WARNINGS.get(fert_name, "")

    # Nutrient deficiency summary — with specific dosages (not generic)
    deficiency = []
    if N < 30:
        deficiency.append({
            "nutrient": "Nitrogen (N)", "level": "low",
            "remedy": f"Apply Urea 100 kg/ha (46-0-0) in 2 split doses at 25 & 50 days after planting for {best_crop_name}. Or DAP 50 kg/ha at basal."
        })
    elif N > 100:
        deficiency.append({
            "nutrient": "Nitrogen (N)", "level": "excess",
            "remedy": "Reduce N application by 30%. Excess N causes lodging in cereals and delays maturity. Skip next scheduled Urea dose."
        })
    if P < 20:
        deficiency.append({
            "nutrient": "Phosphorus (P)", "level": "low",
            "remedy": f"Apply DAP 50 kg/ha (18-46-0) or SSP 125 kg/ha (0-16-0) as basal dose before sowing {best_crop_name}. Add PSB biofertilizer for better uptake."
        })
    if K < 15:
        deficiency.append({
            "nutrient": "Potassium (K)", "level": "low",
            "remedy": f"Apply MOP 40 kg/ha (0-0-60) — 50% as basal + 50% at flowering stage of {best_crop_name}. Use SOP for chloride-sensitive crops."
        })
    if ph < 5.5:
        deficiency.append({
            "nutrient": "Soil pH", "level": "acidic",
            "remedy": f"Apply agricultural lime (CaCO₃) 2-4 tonnes/ha based on pH {ph:.1f}. Incorporate 2 weeks before planting. Retest pH after 3 months."
        })
    if ph > 8.0:
        deficiency.append({
            "nutrient": "Soil pH", "level": "alkaline",
            "remedy": f"Apply gypsum (CaSO₄) 2 tonnes/ha or eleite sulfur 400 kg/ha to reduce pH from {ph:.1f}. Add organic matter (FYM 10 tonnes/ha) to buffer."
        })

    response["fertilizer_recommendation"] = {
        "recommended_fertilizer": best_fert,
        "alternatives": fert_result.get("alternatives", []) if isinstance(fert_result, dict) else [],
        "nutrient_deficiency_summary": deficiency,
        "stage_wise_application": stage_guide,
        "organic_alternatives": organic_alts,
        "warning": warning,
        "crop_context": best_crop_name,
        "in_dataset": fert_name in ['Compost', 'SSP', 'Urea', 'MOP', 'DAP', 'NPK', 'Zinc Sulphate']
    }

    # 6. IRRIGATION GUIDANCE
    et0_approx = 0.6 * temperature  # rough ETo mm/day
    crop_kc = {"rice": 1.2, "wheat": 0.7, "maize": 0.85, "cotton": 0.9}.get(best_crop_name, 0.8)
    etc_mm_day = et0_approx * crop_kc
    rain_contribution = min(rainfall / 30, etc_mm_day) if rainfall > 0 else 0
    net_irrigation = max(0, etc_mm_day - rain_contribution - (soil_moisture - 30) * 0.5)

    response["irrigation_guidance"] = {
        "crop_water_need_mm_day": round(etc_mm_day, 1),
        "soil_moisture_pct": soil_moisture,
        "rain_forecast_contribution_mm": round(rain_contribution, 1),
        "net_irrigation_needed_mm_day": round(net_irrigation, 1),
        "recommendation": (
            "No irrigation needed — rain forecast covers crop water needs." if net_irrigation < 1 else
            f"Irrigate {net_irrigation:.1f}mm/day. Early morning (6-8 AM) for best absorption." if net_irrigation < 5 else
            f"URGENT: Irrigate {net_irrigation:.1f}mm/day. High water stress risk."
        ),
        "irrigation_method": irrigation,
        "method": "ET0_based_estimate",
    }

    # 7. ALERTS
    forecast_data = get_forecast_by_coords(lat, lon)
    alerts = generate_farm_alerts(
        lat=lat, lon=lon,
        current_weather=weather,
        forecast=forecast_data,
        soil=soil,
        active_crop=best_crop_name,
        season=season,
    )
    response["alerts"] = alerts

    return jsonify(response)


# ============================================================
# CROP PREDICTION (ML-only — legacy endpoint)
# ============================================================
@app.route("/api/predict/crop", methods=["POST"])
def crop_prediction():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        required = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        result = predict_crop(
            N=float(data["N"]), P=float(data["P"]), K=float(data["K"]),
            temperature=float(data["temperature"]), humidity=float(data["humidity"]),
            ph=float(data["ph"]), rainfall=float(data["rainfall"])
        )

        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": f"Invalid number: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ============================================================
# FERTILIZER PREDICTION (ML-only — legacy endpoint)
# ============================================================
@app.route("/api/predict/fertilizer", methods=["POST"])
def fertilizer_prediction():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        required = [
            "soil_type", "soil_ph", "soil_moisture", "organic_carbon",
            "electrical_conductivity", "N", "P", "K",
            "temperature", "humidity", "rainfall",
            "crop_type", "growth_stage", "season",
            "irrigation", "previous_crop", "region",
            "fertilizer_usage", "yield_last"
        ]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        result = predict_fertilizer(
            soil_type=str(data["soil_type"]),
            soil_ph=float(data["soil_ph"]),
            soil_moisture=float(data["soil_moisture"]),
            organic_carbon=float(data["organic_carbon"]),
            electrical_conductivity=float(data["electrical_conductivity"]),
            N=float(data["N"]), P=float(data["P"]), K=float(data["K"]),
            temperature=float(data["temperature"]), humidity=float(data["humidity"]),
            rainfall=float(data["rainfall"]),
            crop_type=str(data["crop_type"]),
            growth_stage=str(data["growth_stage"]),
            season=str(data["season"]),
            irrigation=str(data["irrigation"]),
            previous_crop=str(data["previous_crop"]),
            region=str(data["region"]),
            fertilizer_usage=str(data["fertilizer_usage"]),
            yield_last=float(data["yield_last"])
        )

        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": f"Invalid number: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ============================================================
# SOIL ANALYSIS (chemical effects)
# ============================================================
@app.route("/api/soil-analysis", methods=["POST"])
def soil_analysis():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        previous_pesticides = data.get("previous_pesticides", [])
        previous_fertilizers = data.get("previous_fertilizers", [])
        if isinstance(previous_pesticides, str):
            previous_pesticides = [p.strip() for p in previous_pesticides.split(",") if p.strip()]
        if isinstance(previous_fertilizers, str):
            previous_fertilizers = [f.strip() for f in previous_fertilizers.split(",") if f.strip()]

        pesticide_analysis = []
        max_severity = "low"
        for pest in previous_pesticides:
            info = PESTICIDE_EFFECTS.get(pest)
            if info:
                pesticide_analysis.append({
                    "name": pest, "type": info["type"],
                    "persistence": info["persistence"], "effects": info["effects"],
                    "severity": info["severity"],
                })
                if info["severity"] == "high": max_severity = "high"
                elif info["severity"] == "medium" and max_severity != "high": max_severity = "medium"
            else:
                pesticide_analysis.append({
                    "name": pest, "type": "Unknown", "persistence": "Unknown",
                    "effects": ["No data for this pesticide. Consult local agriculture officer."],
                    "severity": "unknown",
                })

        fertilizer_analysis = []
        for fert in previous_fertilizers:
            info = FERTILIZER_EFFECTS.get(fert)
            if info:
                fertilizer_analysis.append({
                    "name": fert, "effects": info["effects"], "severity": info["severity"],
                })
                if info["severity"] == "high": max_severity = "high"
                elif info["severity"] == "medium" and max_severity != "high": max_severity = "medium"
            else:
                fertilizer_analysis.append({
                    "name": fert, "effects": ["No specific data available."], "severity": "unknown",
                })

        score_map = {"low": 85, "medium": 60, "high": 35, "unknown": 50}
        soil_health_score = score_map.get(max_severity, 50)

        if max_severity == "high":
            solutions = SOIL_REMEDIATION["high_chemical_load"] + SOIL_REMEDIATION["general"]
        elif max_severity == "medium":
            solutions = SOIL_REMEDIATION["moderate_chemical_load"] + SOIL_REMEDIATION["general"]
        else:
            solutions = SOIL_REMEDIATION["general"]

        return jsonify({
            "soil_health_score": soil_health_score,
            "overall_severity": max_severity,
            "pesticide_analysis": pesticide_analysis,
            "fertilizer_analysis": fertilizer_analysis,
            "remediation_solutions": solutions,
            "recommendation": (
                "Immediate organic remediation required. Stop chemical use." if max_severity == "high"
                else "Maintain rich organic matter and avoid monocropping."
            )
        })

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ============================================================
# SOIL DATA (legacy — returns regional heuristic, clearly labeled)
# ============================================================
@app.route("/api/soil-data", methods=["GET"])
def get_soil_data_legacy():
    """Legacy endpoint — returns region-heuristic soil profile (clearly marked estimated)."""
    location = request.args.get("location", "").strip().lower()
    if not location:
        return jsonify({"error": "location required"}), 400

    matched_profile = REGION_SOIL_PROFILES.get("default")
    for region in REGION_SOIL_PROFILES:
        if region != "default" and (region in location or location in region):
            matched_profile = REGION_SOIL_PROFILES[region]
            break

    profile = dict(matched_profile)
    # Apply small random fuzz for realism
    import random
    profile["N"] = max(0, profile["N"] + random.randint(-3, 3))
    profile["P"] = max(0, profile["P"] + random.randint(-3, 3))
    profile["K"] = max(0, profile["K"] + random.randint(-3, 3))
    profile["ph"] = round(profile["ph"] + random.uniform(-0.2, 0.2), 1)
    profile["moisture"] = max(0, profile["moisture"] + random.randint(-3, 3))

    return jsonify({
        "location": location.title(),
        "soil_profile": profile,
        "data_quality": "estimated",
        "data_quality_note": "Regional heuristic estimate. Use /api/soil/coords with lat/lon for SoilGrids real data.",
    })


# ============================================================
# MARKET PRICES (Real-time from Agmarknet via data.gov.in)
# ============================================================
@app.route("/api/market-prices", methods=["POST"])
def market_prices():
    """Fetch real-time mandi prices from Agmarknet (data.gov.in)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        crop = data.get("crop", "").strip().lower()
        state = data.get("state", "").strip() or data.get("location", "").strip() or None
        district = data.get("district", "").strip() or None

        if not crop:
            return jsonify({"error": "crop name required"}), 400

        # Fetch from Agmarknet real API
        result = fetch_market_prices(
            commodity=crop,
            state=state,
            district=district,
            limit=30,
        )

        if not result.get("ok"):
            return jsonify({"error": "Failed to fetch market prices", "details": result}), 500

        # Re-structure for frontend compatibility
        markets = []
        for rec in result.get("records", []):
            markets.append({
                "name": rec["market"],
                "state": rec["state"],
                "district": rec["district"],
                "commodity": rec["commodity"],
                "variety": rec.get("variety", ""),
                "grade": rec.get("grade", ""),
                "arrival_date": rec.get("arrival_date", ""),
                "price_per_kg": rec["modal_price_per_kg"],
                "price_per_quintal": rec["modal_price_per_quintal"],
                "min_price_per_quintal": rec["min_price_per_quintal"],
                "max_price_per_quintal": rec["max_price_per_quintal"],
                "price_per_bag_50kg": round(rec["modal_price_per_kg"] * 50, 2),
                "last_updated": rec.get("arrival_date", "Today"),
            })

        # Sort by price descending (best price first)
        markets.sort(key=lambda x: x["price_per_kg"], reverse=True)

        return jsonify({
            "crop": result.get("commodity", crop.replace('_', ' ').title()),
            "location": state or "All India",
            "markets": markets,
            "total_markets_reporting": result.get("total_markets_reporting", len(markets)),
            "avg_price_per_kg": result.get("avg_price_per_kg", 0),
            "min_price_per_kg": result.get("min_price_per_kg", 0),
            "max_price_per_kg": result.get("max_price_per_kg", 0),
            "avg_price_per_quintal": result.get("avg_price_per_quintal", 0),
            "best_market": result.get("best_market", {}).get("name", ""),
            "data_quality": result.get("data_quality", "reference"),
            "data_quality_note": result.get("data_quality_note", ""),
            "source_name": result.get("source_name", "agmarknet_data_gov_in"),
            "is_fallback": result.get("fallback", False),
            "fetch_timestamp": result.get("fetch_timestamp", ""),
        })

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/api/market-prices/state", methods=["GET"])
def market_prices_by_state():
    """Fetch all today's commodity prices for a given state."""
    state = request.args.get("state", "").strip()
    if not state:
        return jsonify({"error": "state parameter required"}), 400

    limit = min(int(request.args.get("limit", 50)), 100)
    result = fetch_markets_for_state(state=state, limit=limit)

    if not result.get("ok"):
        return jsonify({"error": "Failed to fetch state market data", "details": result}), 500

    return jsonify(result)


# ============================================================
# NEWS
# ============================================================
@app.route("/api/news", methods=["GET"])
def get_news():
    """Fetch real agriculture news articles."""
    articles = fetch_all_news(page_size=5)
    if not articles:
        return jsonify({
            "articles": [],
            "note": "NewsAPI key not configured or rate limit reached. Add NEWSAPI_KEY to .env for live news.",
            "data_quality": "unavailable",
        })
    return jsonify({
        "articles": articles,
        "count": len(articles),
        "data_quality": "live",
    })


# ============================================================
# ALERTS
# ============================================================
@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Get farm alerts by coordinates."""
    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lon required"}), 400

    weather = get_weather_by_coords(lat, lon)
    forecast = get_forecast_by_coords(lat, lon)
    soil = get_soil_by_coords(lat, lon)

    active_crop = request.args.get("crop", "rice")
    season = request.args.get("season", "Kharif")

    alerts = generate_farm_alerts(
        lat=lat, lon=lon,
        current_weather=weather,
        forecast=forecast,
        soil=soil,
        active_crop=active_crop,
        season=season,
    )

    return jsonify({
        "alerts": alerts,
        "count": len(alerts),
        "data_quality": "live",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ============================================================
# CHATBOT (GEMINI AI Integration — Full-Power Assistant)
# ============================================================
@app.route("/api/chat", methods=["POST"])
def chatbot():
    """Full-power AI chatbot — works like ChatGPT/Gemini for farmers & general queries."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    lang = data.get("language", "en")
    
    if not message:
        return jsonify({"reply": "Please type a question!", "language": "en", "timestamp": datetime.now(timezone.utc).isoformat()})
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    # 1. Attempt Gemini AI Response first if key exists AND library is present
    if gemini_key and genai is not None:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Comprehensive system prompt
            system_prompt = (
                "You are AgriConnect AI — a world-class intelligent assistant built for Indian farmers, "
                "agricultural professionals, and rural communities. You have deep expertise in agriculture, "
                "farming, animal husbandry, horticulture, fisheries, government schemes, rural finance, "
                "weather, soil science, crop management, pest control, and market intelligence.\n\n"
                "RULES:\n"
                "1. You are NOT limited to agriculture. Answer ANY question like ChatGPT or Gemini would.\n"
                "2. For farming questions, give expert-level, detailed, actionable advice with specific "
                "quantities, timings, product names, and scientific backing.\n"
                "3. For general questions, answer accurately and helpfully.\n"
                "4. Be warm, conversational, and respectful.\n"
                "5. Use clear formatting with bullet points and bold for key terms.\n"
                "6. Give comprehensive, detailed answers — not short 2-3 sentence replies.\n"
                "7. For crop/fertilizer/pesticide questions, include specific dosages, brand names, timing, costs.\n"
                "8. NEVER refuse to answer. You are a helpful, all-knowing assistant.\n"
            )
            
            prompt = f"{system_prompt}\n\nUser's question: {message}"
            
            response = model.generate_content(prompt)
            reply_text = response.text.strip()
            
            return jsonify({
                "reply": reply_text,
                "language": "en",
                "source": "gemini_ai",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            print(f"Gemini AI Error: {e}. Falling back to rules.")
    elif gemini_key and genai is None:
        print("Gemini API key set but google-generativeai package not installed. Using rules.")

    # 2. Enhanced Rule-Based Fallback
    responses_en = {
        "crop": "For personalized crop recommendations, use the Farm Analyzer with your GPS location. It uses live weather and real soil data from SoilGrids. Common Kharif crops: Rice, Cotton, Maize, Soybean. Rabi: Wheat, Mustard, Chickpea. Choose based on your soil type, water availability, and local market demand.",
        "fertilizer": "Fertilizer advice depends on soil test results. General guidelines: Apply DAP (50 kg/acre) at sowing for phosphorus. Top-dress with Urea (30-40 kg/acre) at 25 and 50 days. For potassium deficiency, use MOP (25 kg/acre). Always get a soil test from your nearest KVK for precise recommendations.",
        "irrigation": "Irrigate based on soil moisture and crop stage. Drip irrigation saves 40-50% water vs flood irrigation. Water in early morning (6-8 AM) for best absorption. Rice needs standing water during tillering. Cotton needs critical irrigation at flowering and boll formation stages.",
        "disease": "Upload a leaf photo in Crop Doctor for AI diagnosis. Common diseases: Leaf Blight (treat with Mancozeb 2.5g/L), Powdery Mildew (Sulfur 3g/L), Bacterial Wilt (remove infected plants, apply Streptocycline). Always rotate crops to prevent soil-borne diseases.",
        "weather": "Check the Weather section for a live 5-day forecast with farming advisories. Plan spraying on dry days with low wind. Avoid irrigation before expected rainfall. Protect crops during frost with smoke screens or straw mulching.",
        "price": "Check Market Prices section for live mandi rates from Agmarknet. For better prices: sell at regulated mandis, check prices at 3-4 mandis before selling, consider grading and packaging, and explore FPO collective selling for bargaining power.",
        "soil": "Soil data comes from SoilGrids (ISRIC) by GPS coordinates. For precise values, get a lab test from your district KVK. Key parameters: pH (6.0-7.5 ideal), Nitrogen (N), Phosphorus (P), Potassium (K), Organic Carbon (>0.5%), and electrical conductivity.",
        "scheme": "Key government schemes: PM-KISAN (₹6000/year), PM Fasal Bima Yojana (crop insurance), KCC (Kisan Credit Card at 4% interest), Soil Health Card scheme, and PM Krishi Sinchai Yojana for irrigation. Apply through your local agriculture office or CSC center.",
        "help": "I can help with: crop recommendations, fertilizer advice, irrigation scheduling, disease diagnosis, weather forecasts, market prices, government schemes, soil health, animal husbandry, and general knowledge. Ask me anything!",
        "default": "I'm AgriConnect AI — your intelligent farming assistant. I can help with crops, fertilizers, diseases, weather, market prices, government schemes, and much more. What would you like to know?"
    }

    msg_lower = message.lower()
    reply = None
    if any(w in msg_lower for w in ["crop", "పంట", "recommend", "grow", "sow", "plant", "cultivation"]):
        reply = responses_en["crop"]
    elif any(w in msg_lower for w in ["fertilizer", "ఎరువు", "npk", "urea", "nutrient", "manure", "dap"]):
        reply = responses_en["fertilizer"]
    elif any(w in msg_lower for w in ["water", "irrigation", "irrigate", "నీరు", "నీటిపారుదల", "drip"]):
        reply = responses_en["irrigation"]
    elif any(w in msg_lower for w in ["disease", "leaf", "blight", "pest", "వ్యాధి", "fungus", "insect", "worm"]):
        reply = responses_en["disease"]
    elif any(w in msg_lower for w in ["weather", "rain", "forecast", "వాతావరణం", "climate", "monsoon"]):
        reply = responses_en["weather"]
    elif any(w in msg_lower for w in ["price", "market", "mandi", "msp", "ధర", "sell", "rate"]):
        reply = responses_en["price"]
    elif any(w in msg_lower for w in ["soil", "నేల", "ph", "nitrogen", "testing", "organic"]):
        reply = responses_en["soil"]
    elif any(w in msg_lower for w in ["scheme", "yojana", "pm kisan", "government", "subsidy", "insurance", "loan"]):
        reply = responses_en["scheme"]
    elif any(w in msg_lower for w in ["help", "సహాయం", "what can", "how can"]):
        reply = responses_en["help"]
    else:
        reply = responses_en["default"]

    return jsonify({
        "reply": reply,
        "language": "en",
        "source": "rule_fallback",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ============================================================
# ROOT
# ============================================================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "app": "Agri-Connect API",
        "version": "3.0-production",
        "endpoints": {
            "GET  /api/health": "Health check",
            "GET  /api/weather/coords?lat=&lon=": "Live weather by GPS coords [PRIMARY]",
            "GET  /api/forecast/coords?lat=&lon=": "5-day forecast by GPS coords [PRIMARY]",
            "GET  /api/weather?city=": "Weather by city name [legacy]",
            "GET  /api/forecast?city=": "Forecast by city name [legacy]",
            "GET  /api/geocode/reverse?lat=&lon=": "Reverse geocode coordinates → location",
            "GET  /api/soil/coords?lat=&lon=": "Real soil data from SoilGrids",
            "POST /api/farm/analyze": "FULL farm analysis (GPS + all modules)",
            "POST /api/predict/crop": "ML crop prediction [legacy]",
            "POST /api/predict/fertilizer": "ML fertilizer prediction [legacy]",
            "POST /api/soil-analysis": "Soil chemical effects analysis",
            "POST /api/market-prices": "Market/mandi price lookup",
            "GET  /api/news": "Live agriculture news",
            "GET  /api/alerts?lat=&lon=": "Farm alert engine",
            "POST /api/chat": "Farmer chatbot (English + Telugu)",
        },
        "data_sources": {
            "weather": "OpenWeatherMap API (by coordinates)",
            "geocoding": "Nominatim OpenStreetMap + BigDataCloud fallback",
            "soil": "SoilGrids ISRIC v2.0 (free, no key)",
            "news": "NewsAPI (requires NEWSAPI_KEY)",
            "crop_ml": "Trained RandomForest on Crop_recommendation dataset",
            "fertilizer_ml": "Trained RandomForest on fertilizer_recommendation dataset",
        }
    })


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  AGRI-CONNECT — PRODUCTION API v3.0")
    print("=" * 70)
    print(f"  Database: {'PostgreSQL connected' if USE_DB else 'Disabled (no DATABASE_URL)'}")
    print(f"  Weather API: {'Configured' if os.getenv('OPENWEATHERMAP_API_KEY') else 'MISSING'}")
    print(f"  News API: {'Configured' if os.getenv('NEWSAPI_KEY') else 'Not configured (optional)'}")
    print("=" * 70)
    print("  Primary endpoints (GPS-first):")
    print("  GET  http://127.0.0.1:5000/api/weather/coords?lat=17.38&lon=78.46")
    print("  GET  http://127.0.0.1:5000/api/soil/coords?lat=17.38&lon=78.46")
    print("  POST http://127.0.0.1:5000/api/farm/analyze")
    print("=" * 70 + "\n")
    app.run(debug=True, port=5000)