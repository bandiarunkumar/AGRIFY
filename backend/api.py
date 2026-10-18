"""
Agri-Connect — Production Flask API
Coordinate-first, source-aware, no fake data in main flow.
"""

import os
import json
import hashlib
import math
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# ---- Database & Persistence Setup ----
import database_config
from auth import (
    generate_owner_token,
    hash_owner_token,
    verify_owner_token,
    extract_bearer_or_header_token,
)
from models.database import (
    db,
    FarmProfile,
    WeatherSnapshot,
    WeatherForecast,
    SoilSummary,
    CropRecommendation,
    DistrictCropHistory,
    SatelliteSummary,
    AgricultureNews,
    DiseaseDetection,
    FarmAlert,
    FarmActionPlan,
)
from sqlalchemy.exc import IntegrityError

DATABASE_URI = database_config.get_database_uri()
USE_DB = bool(DATABASE_URI)


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
    PESTICIDE_EFFECTS, FERTILIZER_EFFECTS, SOIL_REMEDIATION,
    PEST_DATABASE, DEFAULT_PEST_INFO
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


def get_allowed_origins():
    """
    Resolve allowed CORS origins from environment variables.
    Supports ALLOWED_ORIGINS (comma-separated list) and FRONTEND_URL.
    In development, safely permits localhost and 127.0.0.1 development ports by default.
    In production, strictly restricts to configured domains.
    """
    default_dev_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:5001",
        "http://127.0.0.1:5001",
    ]
    env_allowed = os.getenv("ALLOWED_ORIGINS", "").strip()
    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    is_prod = os.getenv("FLASK_ENV", "").lower() == "production"

    origins = []
    if env_allowed:
        origins.extend([o.strip() for o in env_allowed.split(",") if o.strip()])
    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url)

    if not is_prod:
        for dev_origin in default_dev_origins:
            if dev_origin not in origins:
                origins.append(dev_origin)
    elif not origins:
        # SECURITY: In production, do NOT silently fall back to dev localhost origins.
        # Log a warning so operators know CORS is blocking all cross-origin requests.
        import logging
        logging.getLogger(__name__).warning(
            "CORS: No ALLOWED_ORIGINS or FRONTEND_URL configured in production mode. "
            "All cross-origin requests will be blocked. Set ALLOWED_ORIGINS or FRONTEND_URL."
        )
        origins = []

    return origins


CORS(app, origins=get_allowed_origins())


def _parse_coordinates(lat_value, lon_value):
    """Parse finite WGS84 coordinates, rejecting invalid values before I/O."""
    try:
        lat = float(lat_value)
        lon = float(lon_value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(lat) or not math.isfinite(lon):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return lat, lon


def _validate_optional_numbers(data, ranges):
    """Validate present numeric form fields without accepting NaN or infinity."""
    for field, (minimum, maximum) in ranges.items():
        if field not in data or data[field] is None:
            continue
        if isinstance(data[field], bool):
            return f"{field} must be a finite number"
        try:
            value = float(data[field])
        except (TypeError, ValueError):
            return f"{field} must be a finite number"
        if not math.isfinite(value) or value < minimum or value > maximum:
            return f"{field} must be between {minimum} and {maximum}"
    return None

def is_db_available():
    """Check if a persistent database is configured and enabled in environment or testing."""
    if app.config.get("TESTING") and app.config.get("SQLALCHEMY_DATABASE_URI"):
        return True
    return bool(database_config.get_database_uri())

# Configure and bind database extension at application initialization
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI or "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = database_config.get_sqlalchemy_engine_options(app.config['SQLALCHEMY_DATABASE_URI'])
db.init_app(app)

if DATABASE_URI:
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Database init note: {e}")



# ============================================================
# HEALTH CHECK
# ============================================================
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "app": "Agri-Connect API",
        "version": "3.0-production",
        "database": "connected" if is_db_available() else "disabled (no DATABASE_URL)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })



# ============================================================
# TRANSLATION (server-side credential handling)
# ============================================================
@app.route("/api/translate", methods=["POST"])
def translate_text():
    """Translate text with a server-side Google API key when configured."""
    data = request.get_json(silent=True) or {}
    text = data.get("q", "")
    target = data.get("target", "")

    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Text is required"}), 400
    if len(text) > 5000:
        return jsonify({"error": "Text must be 5000 characters or fewer"}), 400
    if not isinstance(target, str) or not target.isalpha() or not 2 <= len(target) <= 3:
        return jsonify({"error": "A valid target language is required"}), 400

    api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    if not api_key:
        return jsonify({"error": "Translation service is not configured"}), 503

    try:
        response = requests.post(
            "https://translation.googleapis.com/language/translate/v2",
            params={"key": api_key},
            json={"q": text, "target": target.lower()},
            timeout=10,
        )
        response.raise_for_status()
        translated = response.json()["data"]["translations"][0]["translatedText"]
        return jsonify({"translatedText": translated})
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return jsonify({"error": "Translation service is temporarily unavailable"}), 502


# ============================================================
# WEATHER BY COORDINATES (Primary — GPS-first)
# ============================================================
@app.route("/api/weather/coords", methods=["GET"])
def weather_by_coords():
    """Fetch current weather by GPS coordinates."""
    coordinates = _parse_coordinates(request.args.get("lat"), request.args.get("lon"))
    if coordinates is None:
        return jsonify({"error": "Valid latitude and longitude are required"}), 400
    lat, lon = coordinates

    result = get_weather_by_coords(lat, lon)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/forecast/coords", methods=["GET"])
def forecast_by_coords():
    """Fetch 5-day forecast by GPS coordinates."""
    coordinates = _parse_coordinates(request.args.get("lat"), request.args.get("lon"))
    if coordinates is None:
        return jsonify({"error": "Valid latitude and longitude are required"}), 400
    lat, lon = coordinates

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
    coordinates = _parse_coordinates(request.args.get("lat"), request.args.get("lon"))
    if coordinates is None:
        return jsonify({"error": "Valid latitude and longitude are required"}), 400
    lat, lon = coordinates

    result = reverse_geocode(lat, lon)
    return jsonify(result)


# ============================================================
# SOIL DATA BY COORDINATES (SoilGrids / ISRIC)
# ============================================================
@app.route("/api/soil/coords", methods=["GET"])
def soil_by_coords():
    """Fetch real soil data by GPS coordinates from SoilGrids."""
    coordinates = _parse_coordinates(request.args.get("lat"), request.args.get("lon"))
    if coordinates is None:
        return jsonify({"error": "Valid latitude and longitude are required"}), 400
    lat, lon = coordinates

    result = get_soil_by_coords(lat, lon)
    return jsonify(result)


# ============================================================
# FARM PROFILE & PERSISTENT INTELLIGENCE
# ============================================================
@app.route("/api/farm/profile", methods=["POST"])
def create_or_update_farm_profile():
    """
    Create or update a persistent farm profile.
    Generates a secure owner token on registration. The hash is persisted;
    the plaintext token is returned only once to the client.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "JSON body required"}), 400

    lat = data.get("latitude")
    lon = data.get("longitude")
    if lat is None or lon is None:
        return jsonify({"error": "latitude and longitude required"}), 400

    coordinates = _parse_coordinates(lat, lon)
    if coordinates is None:
        return jsonify({"error": "Valid latitude and longitude are required"}), 400
    lat, lon = coordinates

    farmer_name = str(data.get("farmer_name", "")).strip()
    try:
        acres = float(data.get("area_acres", 1.0))
    except (TypeError, ValueError):
        return jsonify({"error": "area_acres must be a number"}), 400
    if not math.isfinite(acres) or acres <= 0 or acres > 100000:
        return jsonify({"error": "area_acres must be greater than 0 and at most 100000"}), 400

    if not is_db_available():
        stateless_uid = f"stateless_{lat:.4f}_{lon:.4f}"
        return jsonify({
            "farm_uid": stateless_uid,
            "farmer_name": farmer_name,
            "owner_token": None,
            "stateless": True,
            "message": "Stateless mode: database not configured.",
        }), 200

    import hashlib
    default_uid = f"farm_{hashlib.sha256(f'{lat:.6f}_{lon:.6f}_{farmer_name}'.encode()).hexdigest()[:16]}"
    farm_uid = str(data.get("farm_uid", default_uid)).strip()

    existing_farm = FarmProfile.query.filter_by(farm_uid=farm_uid).first()
    if existing_farm:
        token = extract_bearer_or_header_token(request) or data.get("owner_token")
        if not token or not verify_owner_token(token, existing_farm.owner_token_hash):
            return jsonify({"error": "Farm profile already exists. Valid owner_token required to update."}), 403

        if farmer_name:
            existing_farm.farmer_name = farmer_name
        existing_farm.latitude = lat
        existing_farm.longitude = lon
        existing_farm.area_acres = acres
        if "village" in data:
            existing_farm.village = data.get("village")
        if "taluk" in data:
            existing_farm.taluk = data.get("taluk")
        if "district" in data:
            existing_farm.district = data.get("district")
        if "state" in data:
            existing_farm.state = data.get("state")
        if "pincode" in data:
            existing_farm.pincode = data.get("pincode")

        try:
            db.session.commit()
            return jsonify({
                "farm_uid": existing_farm.farm_uid,
                "farmer_name": existing_farm.farmer_name,
                "message": "Farm profile updated successfully.",
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update farm profile: {str(e)}"}), 500

    owner_token = generate_owner_token()
    owner_token_hash = hash_owner_token(owner_token)

    new_farm = FarmProfile(
        farm_uid=farm_uid,
        farmer_name=farmer_name,
        latitude=lat,
        longitude=lon,
        area_acres=acres,
        village=data.get("village"),
        taluk=data.get("taluk"),
        district=data.get("district"),
        state=data.get("state"),
        country=data.get("country", "India"),
        pincode=data.get("pincode"),
        owner_token_hash=owner_token_hash,
    )
    try:
        db.session.add(new_farm)
        db.session.commit()
        return jsonify({
            "farm_uid": new_farm.farm_uid,
            "farmer_name": new_farm.farmer_name,
            "owner_token": owner_token,
            "message": "Farm profile created successfully. Store owner_token securely to access your farm history.",
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Farm profile with this UID already exists"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create farm profile: {str(e)}"}), 500


@app.route("/api/farm/profile/<farm_uid>", methods=["GET"])
def get_farm_profile(farm_uid):
    """Retrieve farm profile metadata, protected by owner token."""
    if not is_db_available():
        return jsonify({"error": "Farm persistence not enabled"}), 404

    token = extract_bearer_or_header_token(request)
    if not token:
        return jsonify({"error": "Authentication token required via X-Farm-Token or Authorization header"}), 401

    farm = FarmProfile.query.filter_by(farm_uid=farm_uid).first()
    if not farm:
        return jsonify({"error": "Farm profile not found"}), 404

    if not verify_owner_token(token, farm.owner_token_hash):
        return jsonify({"error": "Forbidden: invalid owner token for this farm"}), 403

    return jsonify(farm.to_dict()), 200


@app.route("/api/farm/history/<farm_uid>", methods=["GET"])
def get_farm_history(farm_uid):
    """Retrieve comprehensive agronomic history for a verified farm."""
    if not is_db_available():
        return jsonify({"error": "Farm persistence not enabled"}), 404

    token = extract_bearer_or_header_token(request)
    if not token:
        return jsonify({"error": "Authentication token required via X-Farm-Token or Authorization header"}), 401

    farm = FarmProfile.query.filter_by(farm_uid=farm_uid).first()
    if not farm:
        return jsonify({"error": "Farm profile not found"}), 404

    if not verify_owner_token(token, farm.owner_token_hash):
        return jsonify({"error": "Forbidden: invalid owner token for this farm"}), 403

    recommendations = (
        CropRecommendation.query.filter_by(farm_id=farm.id)
        .order_by(CropRecommendation.created_at.desc())
        .limit(20)
        .all()
    )
    action_plans = (
        FarmActionPlan.query.filter_by(farm_id=farm.id)
        .order_by(FarmActionPlan.created_at.desc())
        .limit(20)
        .all()
    )
    weather_snapshots = (
        WeatherSnapshot.query.filter_by(farm_id=farm.id)
        .order_by(WeatherSnapshot.fetch_timestamp.desc())
        .limit(10)
        .all()
    )
    soil_summaries = (
        SoilSummary.query.filter_by(farm_id=farm.id)
        .order_by(SoilSummary.fetch_timestamp.desc())
        .limit(10)
        .all()
    )

    return jsonify({
        "farm": farm.to_dict(),
        "crop_recommendations": [r.to_dict() for r in recommendations],
        "action_plans": [a.to_dict() for a in action_plans],
        "weather_snapshots": [w.to_dict() for w in weather_snapshots],
        "soil_summaries": [s.to_dict() for s in soil_summaries],
    }), 200


@app.route("/api/farm/action-plans/<farm_uid>", methods=["GET"])
def get_farm_action_plans(farm_uid):
    """Retrieve historical action plans for a verified farm."""
    if not is_db_available():
        return jsonify({"error": "Farm persistence not enabled"}), 404

    token = extract_bearer_or_header_token(request)
    if not token:
        return jsonify({"error": "Authentication token required via X-Farm-Token or Authorization header"}), 401

    farm = FarmProfile.query.filter_by(farm_uid=farm_uid).first()
    if not farm:
        return jsonify({"error": "Farm profile not found"}), 404

    if not verify_owner_token(token, farm.owner_token_hash):
        return jsonify({"error": "Forbidden: invalid owner token for this farm"}), 403

    plans = (
        FarmActionPlan.query.filter_by(farm_id=farm.id)
        .order_by(FarmActionPlan.created_at.desc())
        .all()
    )
    return jsonify({
        "farm_uid": farm.farm_uid,
        "action_plans": [p.to_dict() for p in plans],
    }), 200


@app.route("/api/farm/profile/<farm_uid>/rotate-token", methods=["POST"])
def rotate_farm_token(farm_uid):
    """
    Safely rotate owner token for a verified farm profile.
    Requires current valid owner token; generates and returns a new token,
    immediately invalidating the old token hash.
    """
    if not is_db_available():
        return jsonify({"error": "Farm persistence not enabled"}), 404

    token = extract_bearer_or_header_token(request)
    if not token:
        data = request.get_json(silent=True) or {}
        token = data.get("owner_token")

    if not token:
        return jsonify({"error": "Current authentication token required via X-Farm-Token or Authorization header"}), 401

    farm = FarmProfile.query.filter_by(farm_uid=farm_uid).first()
    if not farm:
        return jsonify({"error": "Farm profile not found"}), 404

    if not verify_owner_token(token, farm.owner_token_hash):
        return jsonify({"error": "Forbidden: invalid current owner token"}), 403

    new_token = generate_owner_token()
    farm.owner_token_hash = hash_owner_token(new_token)

    try:
        db.session.commit()
        return jsonify({
            "farm_uid": farm.farm_uid,
            "owner_token": new_token,
            "message": "Owner token successfully rotated. Store new token securely; previous token is invalidated.",
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to rotate token: {str(e)}"}), 500


@app.route("/api/farm/profile/<farm_uid>", methods=["DELETE"])
def delete_farm_profile(farm_uid):
    """
    Permanently delete a farm profile and all linked records (GDPR / DPDP data erasure).
    Protected by owner token. Cascades to recommendations, action plans, weather, and soil.
    """
    if not is_db_available():
        return jsonify({"error": "Farm persistence not enabled"}), 404

    token = extract_bearer_or_header_token(request)
    if not token:
        data = request.get_json(silent=True) or {}
        token = data.get("owner_token")

    if not token:
        return jsonify({"error": "Authentication token required via X-Farm-Token or Authorization header"}), 401

    farm = FarmProfile.query.filter_by(farm_uid=farm_uid).first()
    if not farm:
        return jsonify({"error": "Farm profile not found"}), 404

    if not verify_owner_token(token, farm.owner_token_hash):
        return jsonify({"error": "Forbidden: invalid owner token for this farm"}), 403

    try:
        db.session.delete(farm)
        db.session.commit()
        return jsonify({
            "farm_uid": farm_uid,
            "message": "Farm profile and all associated agronomic records permanently deleted.",
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete farm profile: {str(e)}"}), 500


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
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "JSON body required"}), 400

    numeric_error = _validate_optional_numbers(data, {
        "area_acres": (0, 100000), "N": (0, 10000), "P": (0, 10000), "K": (0, 10000),
        "ph": (0, 14), "soil_moisture": (0, 100), "organic_carbon": (0, 100),
        "annual_rainfall_mm": (0, 20000), "yield_last": (0, 1000000),
    })
    if numeric_error:
        return jsonify({"error": numeric_error}), 400

    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat is None or lon is None:
        return jsonify({"error": "latitude and longitude required"}), 400

    coordinates = _parse_coordinates(lat, lon)
    if coordinates is None:
        return jsonify({"error": "Valid latitude and longitude are required"}), 400
    lat, lon = coordinates

    try:
        acres = float(data.get("area_acres", 1.0))
    except (TypeError, ValueError):
        return jsonify({"error": "area_acres must be a number"}), 400
    if not math.isfinite(acres) or not (0 < acres <= 100000):
        return jsonify({"error": "area_acres must be greater than 0 and at most 100000"}), 400
    season = data.get("season", "Kharif")
    if not isinstance(season, str) or season not in {"Kharif", "Rabi", "Zaid"}:
        return jsonify({"error": "season must be Kharif, Rabi, or Zaid"}), 400
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

    # Upfront authorization check if persisting to an existing farm profile
    target_farm = None
    if is_db_available() and data.get("farm_uid"):
        target_uid = str(data.get("farm_uid")).strip()
        target_farm = FarmProfile.query.filter_by(farm_uid=target_uid).first()
        if not target_farm:
            return jsonify({"error": f"Farm profile '{target_uid}' not found"}), 404

        auth_token = extract_bearer_or_header_token(request) or data.get("owner_token")
        if not auth_token or not verify_owner_token(auth_token, target_farm.owner_token_hash):
            return jsonify({"error": "Forbidden: invalid owner token for this farm"}), 403

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

    # Ensure top_3 has diverse crops by deduplicating botanical aliases (e.g. mirchi -> chilli)
    deduped_top_3 = []
    seen_canonical = set()
    crop_aliases = {"mirchi": "chilli"}
    for item in scored:
        canonical = crop_aliases.get(item["crop"], item["crop"])
        if canonical not in seen_canonical:
            seen_canonical.add(canonical)
            deduped_top_3.append(item)
            if len(deduped_top_3) == 3:
                break

    top_3 = deduped_top_3
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
    soil_quality = soil.get("data_quality", "unavailable")
    weather_available = bool(weather.get("ok"))
    recommendation_is_estimated = (
        not weather_available
        or soil_quality in {"estimated", "user_entered", "unavailable"}
        or bool(soil.get("fallback"))
    )
    response["crop_recommendation"]["data_quality"] = "estimated" if recommendation_is_estimated else "live"
    response["crop_recommendation"]["data_quality_note"] = (
        "Weather was unavailable, so regional fallback values were used for ranking; soil inputs may also be modeled. Treat this as a preliminary estimate."
        if not weather_available else
        "Soil values are modeled or farmer-entered. Use a lab report and local agronomist advice to refine this recommendation."
        if recommendation_is_estimated else
        "Weather and soil providers returned data for this request."
    )

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


    if target_farm:
        try:
            import json
            # 1. Weather Snapshot
            weather_row = WeatherSnapshot(
                farm_id=target_farm.id,
                latitude=lat,
                longitude=lon,
                temperature_c=float(temperature),
                humidity_pct=float(humidity),
                source_url="api.openweathermap.org",
                data_quality=response.get("weather", {}).get("data_quality", "live"),
            )
            db.session.add(weather_row)

            # 2. Soil Summary
            soil_row = SoilSummary(
                farm_id=target_farm.id,
                latitude=lat,
                longitude=lon,
                nitrogen_mg_kg=float(N),
                phosphorus_mg_kg=float(P),
                potassium_cmolkg=float(K),
                soil_ph=float(ph),
                organic_carbon_dg_kg=float(organic_carbon),
                soil_type=soil.get("soil_type", "Loamy") if isinstance(soil, dict) else "Loamy",
                data_quality=soil.get("data_quality", "estimated") if isinstance(soil, dict) else "estimated",
            )
            db.session.add(soil_row)

            # 3. Crop Recommendation
            rec_row = CropRecommendation(
                farm_id=target_farm.id,
                latitude=lat,
                longitude=lon,
                season=season,
                district=geo.get("district", "") if isinstance(geo, dict) else "",
                top_crops_json=json.dumps(top_3),
                all_feasible_json=json.dumps(all_feasible),
                temperature_c=float(temperature),
                humidity_pct=float(humidity),
                soil_n=float(N),
                soil_p=float(P),
                soil_k=float(K),
                soil_ph=float(ph),
                rainfall_mm=float(rainfall),
                soil_moisture=float(soil_moisture),
                model_version="3.0-hybrid",
                data_quality=response["crop_recommendation"]["data_quality"],
            )
            db.session.add(rec_row)

            db.session.commit()

            response["persistence"] = {
                "persisted": True,
                "farm_uid": target_farm.farm_uid,
                "crop_recommendation_id": rec_row.id,
            }
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Transaction rollback during farm analysis persistence: {e}")
            return jsonify({"error": "Failed to persist farm analysis due to database transaction error"}), 500
    else:
        response["persistence"] = {"persisted": False}

    return jsonify(response)




# ============================================================
# CROP PREDICTION (Backward-compatible legacy endpoint)
# ============================================================
def _evaluate_agronomic_crops(N, P, K, temperature, humidity, ph, rainfall, region=None, season=None):
    """
    Evaluate crop suitability using the active agronomic feasibility engine (CROP_PROFILES).
    Produces a ranked list of recommended crops matching the legacy predict_crop contract.
    """
    feasible = get_feasible_crops(temperature, humidity, ph, rainfall, N, P, K, region, season)
    if not feasible:
        feasible = get_feasible_crops(temperature, humidity, ph, rainfall, N, P, K, region, None)
    if not feasible:
        # Distance-scored fallback across all supported crops
        feasible = [
            {"crop": name, "profile": prof, "region_match": True}
            for name, prof in CROP_PROFILES.items()
        ]

    scored = []
    for item in feasible:
        crop = item["crop"]
        profile = item["profile"]

        # Calculate agronomic distance penalty
        ideal_temp = (profile["min_temp"] + profile["max_temp"]) / 2
        temp_dist = abs(temperature - ideal_temp)
        temp_range = max(1, (profile["max_temp"] - profile["min_temp"]) / 2)
        temp_penalty = min(20, (temp_dist / temp_range) * 10)

        ideal_ph = (profile["min_ph"] + profile["max_ph"]) / 2
        ph_dist = abs(ph - ideal_ph)
        ph_range = max(0.1, (profile["max_ph"] - profile["min_ph"]) / 2)
        ph_penalty = min(20, (ph_dist / ph_range) * 10)

        min_rain = profile.get("min_rain", 0)
        max_rain = profile.get("max_rain", 3000)
        ideal_rain = (min_rain + max_rain) / 2
        rain_dist = abs(rainfall - ideal_rain)
        rain_range = max(1, (max_rain - min_rain) / 2)
        rain_penalty = min(20, (rain_dist / rain_range) * 10)

        n_req = profile.get("min_n", 0)
        n_penalty = 0 if N >= n_req else min(20, ((n_req - N) / max(1, n_req)) * 20)

        base_score = 85 - temp_penalty - ph_penalty - rain_penalty - n_penalty
        suitability = round(min(99.0, max(5.0, base_score)), 2)

        from config import CROP_BASE_YIELD, LABOR_COST_PER_HECTARE, OTHER_COST_PER_HECTARE
        price_per_kg = CROP_PRICES.get(crop, 25)
        base_yield = CROP_BASE_YIELD.get(crop, 2000)
        gross_income = base_yield * price_per_kg
        fertilizer_cost = 3000
        seed_cost = 2000
        total_cost = fertilizer_cost + seed_cost + LABOR_COST_PER_HECTARE + OTHER_COST_PER_HECTARE
        net_profit = max(0, gross_income - total_cost)

        profit_info = {
            "estimated_yield_kg_per_ha": base_yield,
            "price_per_kg": price_per_kg,
            "gross_income": gross_income,
            "total_cost": total_cost,
            "net_profit": net_profit,
            "cost_breakdown": {
                "fertilizer": fertilizer_cost,
                "seeds": seed_cost,
                "labor": LABOR_COST_PER_HECTARE,
                "other": OTHER_COST_PER_HECTARE
            }
        }
        pest_info = PEST_DATABASE.get(crop, DEFAULT_PEST_INFO)

        scored.append({
            "crop": crop,
            "confidence": suitability,
            "profit": profit_info,
            "pests": pest_info,
        })

    scored.sort(key=lambda x: x["confidence"], reverse=True)
    return scored


@app.route("/api/predict/crop", methods=["POST"])
def crop_prediction():
    """
    Crop prediction endpoint (backward-compatible legacy route).
    Delegates to the active rule-based ICAR agronomic feasibility engine (CROP_PROFILES).
    """
    try:
        data = request.get_json()
        if not isinstance(data, dict) or not data:
            return jsonify({"error": "No data provided"}), 400

        required = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        numeric_values = {}
        for f in required:
            val = data[f]
            if isinstance(val, bool):
                return jsonify({"error": f"Invalid number for field: {f}"}), 400
            try:
                parsed = float(val)
                if not math.isfinite(parsed):
                    return jsonify({"error": f"Invalid number for field: {f}"}), 400
                numeric_values[f] = parsed
            except (TypeError, ValueError) as e:
                return jsonify({"error": f"Invalid number: {str(e)}"}), 400

        region = data.get("region")
        season = data.get("season")

        ranked = _evaluate_agronomic_crops(
            N=numeric_values["N"],
            P=numeric_values["P"],
            K=numeric_values["K"],
            temperature=numeric_values["temperature"],
            humidity=numeric_values["humidity"],
            ph=numeric_values["ph"],
            rainfall=numeric_values["rainfall"],
            region=str(region) if region else None,
            season=str(season) if season else None,
        )

        if not ranked:
            return jsonify({"error": "No crops match given parameters"}), 500

        return jsonify({
            "status": "success",
            "best_crop": ranked[0],
            "alternatives": ranked[1:5],
            "input_summary": {
                "N": numeric_values["N"],
                "P": numeric_values["P"],
                "K": numeric_values["K"],
                "temperature": numeric_values["temperature"],
                "humidity": numeric_values["humidity"],
                "ph": numeric_values["ph"],
                "rainfall": numeric_values["rainfall"],
            },
            "engine": "agronomic_feasibility_v3",
            "advisory_note": "Recommendations generated via deterministic ICAR/agronomic feasibility rules (ML model retired)."
        })

    except (TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid number: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ============================================================
# FERTILIZER PREDICTION (Legacy endpoint — strict safety guardrail)
# ============================================================
@app.route("/api/predict/fertilizer", methods=["POST"])
def fertilizer_prediction():
    """
    Fertilizer prediction endpoint (legacy route).
    In accordance with AGRIFY strict agronomic safety guardrails, chemical dosages
    are not fabricated without verified lab calibration.
    Returns HTTP 503 structured unavailable response.
    """
    try:
        data = request.get_json()
        if not isinstance(data, dict) or not data:
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

        numeric_fields = [
            "soil_ph", "soil_moisture", "organic_carbon", "electrical_conductivity",
            "N", "P", "K", "temperature", "humidity", "rainfall", "yield_last"
        ]
        for f in numeric_fields:
            val = data[f]
            if isinstance(val, bool):
                return jsonify({"error": f"Invalid number for field: {f}"}), 400
            try:
                parsed = float(val)
                if not math.isfinite(parsed):
                    return jsonify({"error": f"Invalid number for field: {f}"}), 400
            except (TypeError, ValueError) as e:
                return jsonify({"error": f"Invalid number: {str(e)}"}), 400

        # Strict Agronomic Guardrail: Return structured unavailable response without dosage fabrication
        return jsonify({
            "status": "unavailable",
            "error": "Fertilizer dosage prediction model is unavailable. In accordance with AGRIFY strict agronomic safety guardrails, chemical dosages are not fabricated without verified laboratory calibration.",
            "service": "predict_fertilizer",
            "model_status": "unverified_or_absent",
            "crop_type": str(data["crop_type"]),
            "advisory": "AGRIFY does not have a verified fertilizer dosage for this specific field. Please check your Farm Analyzer report or consult your local KVK (Krishi Vigyan Kendra) officer or agricultural extension officer before applying chemicals."
        }), 503

    except (TypeError, ValueError) as e:
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
        if not isinstance(data, dict) or not data:
            return jsonify({"error": "No data provided"}), 400

        crop_value = data.get("crop", "")
        state_value = data.get("state", "")
        location_value = data.get("location", "")
        district_value = data.get("district", "")
        if not all(isinstance(value, str) for value in (crop_value, state_value, location_value, district_value)):
            return jsonify({"error": "crop and location filters must be text"}), 400
        if any(len(value) > 100 for value in (crop_value, state_value, location_value, district_value)):
            return jsonify({"error": "crop and location filters must be 100 characters or fewer"}), 400
        crop = crop_value.strip().lower()
        state = state_value.strip() or location_value.strip() or None
        district = district_value.strip() or None

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
            "best_market": (result.get("best_market") or {}).get("name", ""),
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
    if len(state) > 100:
        return jsonify({"error": "state must be 100 characters or fewer"}), 400

    try:
        limit = int(request.args.get("limit", 50))
    except ValueError:
        return jsonify({"error": "limit must be an integer from 1 to 100"}), 400
    if not 1 <= limit <= 100:
        return jsonify({"error": "limit must be an integer from 1 to 100"}), 400
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
    coordinates = _parse_coordinates(request.args.get("lat"), request.args.get("lon"))
    if coordinates is None:
        return jsonify({"error": "Valid latitude and longitude are required"}), 400
    lat, lon = coordinates

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

    weather_available = bool(weather.get("ok"))
    forecast_available = bool(forecast.get("ok"))
    soil_available = bool(soil.get("ok"))
    sources_available = {
        "weather": weather_available,
        "forecast": forecast_available,
        "soil_estimate": soil_available,
        "crop_season_rules": True,
    }
    if not (weather_available or forecast_available or soil_available):
        data_quality = "unavailable"
        data_quality_note = "Weather and soil providers were unavailable. An empty alert list is not an all-clear."
    elif not (weather_available and forecast_available and soil_available):
        data_quality = "partial"
        data_quality_note = "Some weather or soil sources were unavailable. Review alerts with local conditions."
    elif soil.get("data_quality") == "estimated":
        data_quality = "estimated"
        data_quality_note = "Weather feeds are available; soil values are model estimates, not a lab test."
    else:
        data_quality = "live"
        data_quality_note = "Weather and soil providers returned data for this request."

    return jsonify({
        "alerts": alerts,
        "count": len(alerts),
        "data_quality": data_quality,
        "data_quality_note": data_quality_note,
        "sources_available": sources_available,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ============================================================
# CHATBOT (AGRIFY Safe Agricultural Assistant)
# ============================================================
@app.route("/api/chat", methods=["POST"])
def chatbot():
    """AGRIFY safe agricultural chatbot with Gemini AI and rule-based fallback."""
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400
    message_value = data.get("message", "")
    if not isinstance(message_value, str):
        return jsonify({"error": "message must be text"}), 400
    if len(message_value) > 4000:
        return jsonify({"error": "message must be 4000 characters or fewer"}), 400
    message = message_value.strip()
    lang = data.get("language", "en")
    if not isinstance(lang, str) or lang not in {"en", "te", "hi"}:
        lang = "en"
    has_image = bool(data.get("has_image", False))

    if not message and not has_image:
        return jsonify({
            "reply": "Please type a question!",
            "language": lang,
            "source": "system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # Image-only path: no vision in this phase — redirect to Crop Doctor
    if has_image and not message:
        return jsonify({
            "reply": (
                "📷 **Image Analysis Not Available in Chat**\n\n"
                "This chatbot cannot analyse crop images. "
                "For accurate AI-powered disease detection from photos, please use the "
                "**Crop Doctor** feature (available in the navigation menu).\n\n"
                "Crop Doctor uses a dedicated plant disease model to identify possible "
                "symptoms from leaf or plant images and suggest next steps."
            ),
            "language": lang,
            "source": "system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    gemini_key = os.getenv("GEMINI_API_KEY")

    # ── AGRIFY SAFE SYSTEM PROMPT ──────────────────────────────────
    # This prompt enforces AGRIFY safety principles.
    # Do NOT weaken, remove, or bypass these rules.
    AGRIFY_SAFE_SYSTEM_PROMPT = (
        "You are AGRIFY — a safe, responsible agricultural advisory assistant "
        "for Indian farmers.\n\n"

        "YOUR IDENTITY:\n"
        "- You are a farming advisor, NOT a general-purpose chatbot.\n"
        "- You specialise in crop management, soil health, irrigation, pest/disease "
        "awareness, government schemes, and rural market intelligence.\n"
        "- You are warm, respectful, and use simple language suitable for farmers.\n\n"

        "SAFETY RULES — NEVER VIOLATE THESE:\n"
        "1. FERTILIZER & PESTICIDE DOSAGES: Do NOT invent or fabricate specific "
        "quantities (kg/acre, ml/litre, etc.) unless you are citing a well-known "
        "general agronomy guideline. Always recommend confirming dosages with the "
        "local KVK (Krishi Vigyan Kendra) or a licensed agronomist.\n"
        "2. PESTICIDE BRANDS: Do NOT recommend specific pesticide brand names. "
        "You may name the active ingredient (e.g. mancozeb, imidacloprid) but not "
        "commercial brand products. Always advise consulting a licensed dealer.\n"
        "3. DISEASE DIAGNOSIS: Do NOT confirm a specific disease from text alone. "
        "Use phrases such as 'possible symptoms of', 'may indicate', "
        "'cannot confirm without field inspection'. Direct users to Crop Doctor "
        "for image-based assessment.\n"
        "4. YIELD & PROFIT GUARANTEES: Do NOT guarantee any yield, profit, or "
        "income figure. Use phrases such as 'typical range under good conditions' "
        "or 'estimated — actual results vary'.\n"
        "5. LIVE DATA (weather, soil, market): Do NOT fabricate current weather, "
        "real-time soil readings, or live mandi prices. Direct users to the "
        "AGRIFY Weather, Farm Analyzer, or Market Price features for live data.\n"
        "6. IMAGE ANALYSIS: If the user mentions uploading or attaching an image, "
        "state clearly that this chat cannot analyse images and direct them to "
        "Crop Doctor.\n"
        "7. GENERAL KNOWLEDGE: You may answer general agriculture and rural "
        "livelihood questions helpfully. For non-agriculture topics, politely "
        "redirect to agriculture.\n\n"

        "DISCLAIMER: End responses that contain advisory information with a brief "
        "note that farmers should verify critical decisions with their local "
        "agriculture officer or KVK.\n\n"

        "FORMAT: Use clear markdown formatting — bullet points for lists, bold "
        "for key terms. Keep responses focused and practical."
    )

    # 1. Attempt Gemini AI Response
    if gemini_key and genai is not None:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"{AGRIFY_SAFE_SYSTEM_PROMPT}\n\nUser's question: {message}"
            response = model.generate_content(prompt)
            reply_text = response.text.strip() if response.text else ""
            if not reply_text:
                raise ValueError("Empty Gemini response")
            return jsonify({
                "reply": reply_text,
                "language": lang,
                "source": "gemini_ai",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            print(f"[AGRIFY Chatbot] Gemini error: {e}. Falling back to rules.")
    elif gemini_key and genai is None:
        print("[AGRIFY Chatbot] Gemini key set but library not installed. Using rules.")

    # 2. Safe Rule-Based Fallback
    # All responses must comply with AGRIFY safety principles.
    responses_en = {
        "image": (
            "📷 **Image Analysis Not Available in Chat**\n\n"
            "This chatbot cannot analyse crop images. "
            "Please use the **Crop Doctor** feature in the navigation menu for "
            "AI-powered plant disease detection from photos."
        ),
        "dosage": (
            "⚠️ **Exact Dosage Not Available**\n\n"
            "I cannot safely provide a specific fertilizer or pesticide dosage "
            "without verified soil test data and a field assessment for your crop.\n\n"
            "**Recommended steps:**\n"
            "- Get a soil test from your nearest KVK (Krishi Vigyan Kendra)\n"
            "- Use the AGRIFY **Farm Analyzer** with your GPS location for "
            "personalised soil-based recommendations\n"
            "- Consult a licensed agronomist or local agriculture officer\n\n"
            "*AGRIFY does not invent dosages — incorrect application can damage "
            "crops or soil health.*"
        ),
        "pesticide_brand": (
            "⚠️ **Pesticide Brand Recommendation Not Available**\n\n"
            "I cannot recommend specific pesticide brand names. "
            "The correct product depends on your crop variety, local pest species, "
            "and current resistance patterns.\n\n"
            "**Please consult:**\n"
            "- A licensed pesticide dealer in your district\n"
            "- Your nearest KVK (Krishi Vigyan Kendra)\n"
            "- State agriculture department extension officer\n\n"
            "*Always follow the label directions and use PPE when applying any "
            "pesticide.*"
        ),
        "disease": (
            "🔍 **Possible Symptom — Field Confirmation Required**\n\n"
            "Based on your description, the symptoms *may indicate* a fungal, "
            "bacterial, or pest-related issue — but I cannot confirm a specific "
            "disease from text alone.\n\n"
            "**Recommended steps:**\n"
            "- Use the **Crop Doctor** feature to upload a clear leaf photo for "
            "AI-based analysis\n"
            "- Consult your local KVK or agriculture extension officer for a "
            "field diagnosis\n"
            "- Until confirmed, avoid applying pesticides speculatively"
        ),
        "yield_guarantee": (
            "📊 **Yield Estimates — Not a Guarantee**\n\n"
            "Yield depends on many factors: soil health, variety, irrigation, "
            "weather, and pest pressure. I cannot guarantee any specific yield "
            "or profit figure.\n\n"
            "Under good conditions, typical ranges for common crops in India:\n"
            "- Rice: 20–35 qtl/acre (varies by variety and region)\n"
            "- Wheat: 15–25 qtl/acre\n"
            "- Cotton: 8–15 qtl/acre\n\n"
            "Use the AGRIFY **Farm Analyzer** for a personalised crop suitability "
            "assessment. *Actual results vary — consult your local agriculture officer.*"
        ),
        "live_market": (
            "📈 **Live Market Prices**\n\n"
            "I do not have access to real-time mandi prices in this chat. "
            "Please check the **Market Prices** section in AGRIFY for live rates "
            "sourced from Agmarknet (data.gov.in).\n\n"
            "For better selling decisions:\n"
            "- Compare prices at 2–3 nearby mandis before selling\n"
            "- Check the MSP (Minimum Support Price) announced by the Government of India\n"
            "- Consider FPO collective selling for better bargaining power"
        ),
        "live_soil": (
            "🧪 **Real-Time Soil Data**\n\n"
            "I cannot provide your current field soil readings — soil values "
            "are specific to your location and require measurement.\n\n"
            "**How to get your soil data:**\n"
            "- Use the AGRIFY **Farm Analyzer** with GPS for satellite-based "
            "SoilGrids data for your coordinates\n"
            "- Get a lab soil test from your nearest KVK for precise N, P, K, pH values"
        ),
        "live_weather": (
            "🌤️ **Live Weather Forecast**\n\n"
            "For your GPS-specific 5-day weather forecast and farming advisories, "
            "please use the **Weather** section in AGRIFY.\n\n"
            "General tips:\n"
            "- Plan spraying on dry days with wind below 15 km/h\n"
            "- Avoid irrigation 24 hours before forecast rainfall\n"
            "- Monitor for frost during Rabi season in northern regions"
        ),
        "crop": (
            "🌱 **Crop Recommendations**\n\n"
            "For personalised crop recommendations based on your actual soil and "
            "GPS location, use the **Farm Analyzer** in AGRIFY.\n\n"
            "General Kharif crops suited to South India: Rice, Cotton, Maize, "
            "Soybean, Groundnut, Chilli.\n"
            "General Rabi crops: Wheat, Mustard, Chickpea, Sunflower.\n\n"
            "Choice depends on your soil type, water source, and local market. "
            "*Consult your local KVK for variety-specific advice.*"
        ),
        "fertilizer_general": (
            "🧪 **Fertilizer Guidance**\n\n"
            "Fertilizer recommendations depend on your soil test results. "
            "Without a soil test, I cannot provide safe dosage figures.\n\n"
            "**General process:**\n"
            "- Get a soil test from your nearest KVK or soil testing lab\n"
            "- Use the AGRIFY **Farm Analyzer** for GPS-based soil data\n"
            "- Apply based on the Soil Health Card recommendations\n\n"
            "*Do not apply fertilizers speculatively — excess application "
            "reduces soil health and wastes money.*"
        ),
        "irrigation": (
            "💧 **Irrigation Guidance**\n\n"
            "Irrigate based on soil moisture, crop stage, and weather forecast.\n\n"
            "- Drip irrigation saves 40–50% water compared to flood irrigation\n"
            "- Water in early morning (6–8 AM) for best absorption\n"
            "- Rice needs standing water during tillering stage\n"
            "- Cotton needs irrigation at flowering and boll formation stages\n\n"
            "Check the **Weather** section for rainfall forecasts before scheduling irrigation."
        ),
        "scheme": (
            "🏛️ **Government Schemes for Farmers**\n\n"
            "Key schemes available:\n"
            "- **PM-KISAN**: ₹6,000/year direct income support\n"
            "- **PM Fasal Bima Yojana**: Crop insurance at subsidised premiums\n"
            "- **KCC (Kisan Credit Card)**: Short-term credit at 4% interest\n"
            "- **Soil Health Card Scheme**: Free soil testing and card\n"
            "- **PM Krishi Sinchai Yojana**: Irrigation infrastructure support\n\n"
            "Apply at your local agriculture office, Common Service Centre (CSC), "
            "or through the PM-KISAN portal."
        ),
        "help": (
            "🌾 **How I Can Help**\n\n"
            "I can assist with:\n"
            "- Crop selection and management guidance\n"
            "- General soil health and irrigation advice\n"
            "- Disease symptom awareness (use Crop Doctor for image diagnosis)\n"
            "- Government schemes and rural finance\n"
            "- Live weather: use the Weather tab\n"
            "- Live prices: use the Market Prices tab\n"
            "- GPS farm analysis: use the Farm Analyzer\n\n"
            "*For exact dosages and disease confirmation, always consult your "
            "local KVK or agriculture officer.*"
        ),
        "default": (
            "🌾 **AGRIFY Agricultural Assistant**\n\n"
            "I'm here to help with farming, soil health, irrigation, crop diseases, "
            "government schemes, and agricultural guidance.\n\n"
            "For live data, please use:\n"
            "- 📍 **Farm Analyzer** — GPS-based soil & crop analysis\n"
            "- 🌤️ **Weather** — live 5-day forecast\n"
            "- 📊 **Market Prices** — live mandi rates\n"
            "- 🔬 **Crop Doctor** — image-based plant disease detection\n\n"
            "What would you like to know?"
        ),
    }

    msg_lower = message.lower() if message else ""

    # Image mention in text → redirect to Crop Doctor
    if has_image or any(w in msg_lower for w in ["image", "photo", "picture", "upload", "attached", "analyze it", "analyse it"]):
        reply = responses_en["image"]
    # Pesticide dosage / exact application rate
    elif any(w in msg_lower for w in ["how much", "dosage", "dose", "per acre", "per litre", "per liter", "ml/l", "kg/acre", "grams", "quantity", "amount of fertilizer", "amount of pesticide"]):
        reply = responses_en["dosage"]
    # Pesticide brand
    elif any(w in msg_lower for w in ["which pesticide", "which brand", "which product", "best pesticide", "pesticide brand", "buy pesticide", "which chemical"]):
        reply = responses_en["pesticide_brand"]
    # Disease confirmation request
    elif any(w in msg_lower for w in ["disease", "blight", "leaf", "pest", "వ్యాధి", "fungus", "insect", "worm", "yellowing", "spots", "rot"]):
        reply = responses_en["disease"]
    # Yield/profit guarantees
    elif any(w in msg_lower for w in ["guarantee", "assured", "definitely", "tonnes per acre", "ton per acre", "how much yield", "how much profit"]):
        reply = responses_en["yield_guarantee"]
    # Live market prices
    elif any(w in msg_lower for w in ["price", "market", "mandi", "msp", "ధర", "sell", "rate", "today's price", "current price"]):
        reply = responses_en["live_market"]
    # Live soil data
    elif any(w in msg_lower for w in ["my soil", "soil nitrogen", "soil right now", "soil ph", "soil today", "field soil", "నేల", "nitrogen level", "ph level"]):
        reply = responses_en["live_soil"]
    # Live weather
    elif any(w in msg_lower for w in ["weather", "rain", "forecast", "వాతావరణం", "climate", "monsoon", "temperature today"]):
        reply = responses_en["live_weather"]
    # Crop recommendations
    elif any(w in msg_lower for w in ["crop", "పంట", "recommend", "grow", "sow", "plant", "cultivation", "kharif", "rabi"]):
        reply = responses_en["crop"]
    # Fertilizer (general)
    elif any(w in msg_lower for w in ["fertilizer", "fertiliser", "ఎరువు", "npk", "urea", "nutrient", "manure", "dap", "mop"]):
        reply = responses_en["fertilizer_general"]
    # Irrigation
    elif any(w in msg_lower for w in ["water", "irrigation", "irrigate", "నీరు", "నీటిపారుదల", "drip", "sprinkler"]):
        reply = responses_en["irrigation"]
    # Schemes
    elif any(w in msg_lower for w in ["scheme", "yojana", "pm kisan", "government", "subsidy", "insurance", "loan", "kcc"]):
        reply = responses_en["scheme"]
    # Help
    elif any(w in msg_lower for w in ["help", "సహాయం", "what can", "how can", "what do you"]):
        reply = responses_en["help"]
    else:
        reply = responses_en["default"]

    return jsonify({
        "reply": reply,
        "language": lang,
        "source": "rule_fallback",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ============================================================
# AGRIFY AI FARM ACTION PLAN (Isolated Extension)
# ============================================================
@app.route("/api/farm/action-plan", methods=["POST"])
def farm_action_plan():
    """
    Generate a prioritized 7-day action plan from existing farm analysis output.
    Purely consumes existing analysis results without altering any calculations.
    """
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    target_farm = None
    if is_db_available() and data.get("farm_uid"):
        target_uid = str(data.get("farm_uid")).strip()
        target_farm = FarmProfile.query.filter_by(farm_uid=target_uid).first()
        if not target_farm:
            return jsonify({"error": f"Farm profile '{target_uid}' not found"}), 404

        auth_token = extract_bearer_or_header_token(request) or data.get("owner_token")
        if not auth_token or not verify_owner_token(auth_token, target_farm.owner_token_hash):
            return jsonify({"error": "Forbidden: invalid owner token for this farm"}), 403

    try:
        from action_plan import generate_action_plan
        plan = generate_action_plan(data)

        if target_farm:
            try:
                import json
                crop_rec_id = data.get("crop_recommendation_id")
                plan_row = FarmActionPlan(
                    farm_id=target_farm.id,
                    crop_recommendation_id=int(crop_rec_id) if crop_rec_id is not None else None,
                    crop_name=plan.get("crop", "Unknown"),
                    season=plan.get("season", "Kharif"),
                    location_str=plan.get("location", ""),
                    summary=plan.get("summary", ""),
                    immediate_actions_json=json.dumps(plan.get("immediate_actions", [])),
                    this_week_plan_json=json.dumps(plan.get("this_week_plan", [])),
                    disclaimer=plan.get("disclaimer", ""),
                    data_quality=plan.get("data_quality", "live"),
                )
                db.session.add(plan_row)
                db.session.commit()
                plan["persistence"] = {
                    "persisted": True,
                    "farm_uid": target_farm.farm_uid,
                    "action_plan_id": plan_row.id,
                }
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Transaction rollback during action plan persistence: {e}")
                return jsonify({"error": "Failed to persist action plan due to database transaction error"}), 500
        else:
            plan["persistence"] = {"persisted": False}

        return jsonify(plan)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error generating action plan: {e}")
        return jsonify({"error": "Failed to generate action plan"}), 500


# ============================================================
# AGRIFY AI VOICE ASSISTANT (Isolated Orchestration Extension)
# ============================================================
@app.route("/api/assistant/query", methods=["POST"])
def assistant_query():
    """
    Orchestrates voice AI queries, deterministic intent classification,
    fact-anchored context filtering, and safe response generation.
    """
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        # Gracefully handle malformed or non-dict JSON body
        data = {}

    query = data.get("query", "")
    if not isinstance(query, str):
        return jsonify({"error": "query must be text"}), 400
    if len(query) > 4000:
        return jsonify({"error": "query must be 4000 characters or fewer"}), 400
    if "context" in data and not isinstance(data["context"], dict):
        return jsonify({"error": "context must be an object"}), 400
    data["query"] = query

    try:
        from voice_assistant import query_voice_assistant
        result = query_voice_assistant(data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error in voice assistant query: {e}")
        return jsonify({"error": "Failed to process voice query"}), 500


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
            "POST /api/farm/action-plan": "Prioritized 7-day action plan from farm analysis",
            "POST /api/assistant/query": "AI Voice Assistant orchestration endpoint",
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
    debug_enabled = (
        os.getenv("FLASK_DEBUG", "false").strip().lower() == "true"
        and os.getenv("FLASK_ENV", "").strip().lower() == "development"
    )
    app.run(debug=debug_enabled, port=5000)
