"""
AGRIFY Agent — Intent Planner & Entity Extractor
Module: backend/agent/planner.py

Responsibilities:
  1. Classify the farmer's intent from the query text (multi-lingual)
  2. Extract entities: lat, lon, crop, state, district, city, season
  3. Build an AgentPlan describing which tools to run
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


# ============================================================
# TOOL SELECTION MATRIX
# Maps each intent to the tools that should be executed.
# Wave 1 tools are independent. Wave 2 tools may use Wave 1 results.
# ============================================================
INTENT_TOOLS: Dict[str, List[str]] = {
    "weather":           ["tool_weather"],
    "irrigation":        ["tool_weather", "tool_soil"],
    "alerts":            ["tool_weather", "tool_soil", "tool_alerts"],
    "market":            ["tool_market"],
    "crop":              ["tool_weather", "tool_soil", "tool_crop"],
    "fertilizer":        ["tool_soil", "tool_fertilizer"],
    "farm_analysis":     ["tool_weather", "tool_soil", "tool_alerts", "tool_crop", "tool_fertilizer"],
    "action_plan":       ["tool_weather", "tool_soil", "tool_alerts", "tool_crop", "tool_fertilizer"],
    "plant_health":      ["tool_weather", "tool_soil"],
    "general_agriculture": [],
    "unknown":           [],
}

# ============================================================
# KNOWN CROP NAMES (used for entity extraction from query text)
# ============================================================
KNOWN_CROPS = {
    "rice", "wheat", "maize", "corn", "cotton", "sugarcane", "soybean",
    "groundnut", "blackgram", "chickpea", "pigeonpeas", "lentil", "mungbean",
    "mothbeans", "tomato", "potato", "onion", "brinjal", "cabbage",
    "cauliflower", "banana", "mango", "coconut", "chilli", "mirchi",
    "turmeric", "coriander", "capsicum", "ladies_finger", "bitter_gourd",
    "drumstick", "jute", "coffee", "sunflower", "sesame", "castor",
    "jowar", "bajra", "ragi", "paddy",
}

CROP_ALIASES = {
    "paddy": "rice", "dhan": "rice",
    "corn": "maize",
    "moong": "mungbean", "green gram": "mungbean",
    "urad": "blackgram", "black gram": "blackgram",
    "arhar": "pigeonpeas", "tur": "pigeonpeas", "toor": "pigeonpeas",
    "red gram": "pigeonpeas",
    "mirchi": "chilli", "chilly": "chilli", "red chilli": "chilli",
    "groundnut": "groundnut", "peanut": "groundnut",
    "ladies finger": "ladies_finger", "okra": "ladies_finger",
    "bitter gourd": "bitter_gourd", "karela": "bitter_gourd",
    "drum stick": "drumstick", "moringa": "drumstick",
}

# ============================================================
# INDIAN LOCATION TABLES
# ============================================================
# Known farming cities/districts with approximate GPS coordinates
CITY_COORDS: Dict[str, tuple] = {
    # Andhra Pradesh
    "guntur":        (16.31, 80.44),
    "vijayawada":    (16.52, 80.62),
    "visakhapatnam": (17.69, 83.22),
    "vishakhapatnam":(17.69, 83.22),
    "vizag":         (17.69, 83.22),
    "nellore":       (14.44, 79.99),
    "kurnool":       (15.83, 78.04),
    "kadapa":        (14.47, 78.82),
    "tirupati":      (13.65, 79.42),
    "rajahmundry":   (17.00, 81.78),
    "eluru":         (16.71, 81.10),
    "ongole":        (15.50, 80.04),
    # Telangana
    "hyderabad":     (17.38, 78.46),
    "warangal":      (17.97, 79.59),
    "nizamabad":     (18.67, 78.09),
    "karimnagar":    (18.44, 79.12),
    "khammam":       (17.25, 80.15),
    "nalgonda":      (17.05, 79.27),
    "mahabubnagar":  (16.74, 77.99),
    "adilabad":      (19.66, 78.53),
    # Karnataka
    "bangalore":     (12.97, 77.59),
    "bengaluru":     (12.97, 77.59),
    "mysore":        (12.30, 76.66),
    "hubli":         (15.36, 75.12),
    "dharwad":       (15.45, 75.01),
    # Tamil Nadu
    "chennai":       (13.08, 80.27),
    "coimbatore":    (11.02, 76.97),
    "madurai":       ( 9.93, 78.12),
    # Kerala
    "thiruvananthapuram": ( 8.52, 76.94),
    "kochi":         ( 9.93, 76.27),
    # Maharashtra
    "mumbai":        (19.07, 72.87),
    "pune":          (18.52, 73.86),
    "nagpur":        (21.14, 79.09),
    "nashik":        (20.00, 73.79),
    "aurangabad":    (19.87, 75.34),
    # Gujarat
    "ahmedabad":     (23.02, 72.57),
    "surat":         (21.17, 72.83),
    "vadodara":      (22.31, 73.18),
    # Rajasthan
    "jaipur":        (26.91, 75.79),
    "jodhpur":       (26.29, 73.03),
    # Uttar Pradesh
    "lucknow":       (26.85, 80.95),
    "kanpur":        (26.46, 80.33),
    "varanasi":      (25.32, 83.01),
    "agra":          (27.18, 78.01),
    # Madhya Pradesh
    "bhopal":        (23.26, 77.41),
    "indore":        (22.72, 75.86),
    # Punjab
    "chandigarh":    (30.73, 76.78),
    "ludhiana":      (30.90, 75.85),
    "amritsar":      (31.63, 74.87),
    # Haryana
    "gurgaon":       (28.46, 77.03),
    "gurugram":      (28.46, 77.03),
    # West Bengal
    "kolkata":       (22.57, 88.37),
    # Bihar
    "patna":         (25.59, 85.14),
    # Delhi
    "delhi":         (28.61, 77.21),
    "new delhi":     (28.61, 77.21),
    # Odisha
    "bhubaneswar":   (20.30, 85.84),
    "cuttack":       (20.46, 85.88),
}

STATE_NAMES = {
    "andhra pradesh", "telangana", "karnataka", "tamil nadu", "kerala",
    "maharashtra", "gujarat", "rajasthan", "uttar pradesh", "madhya pradesh",
    "punjab", "haryana", "west bengal", "bihar", "odisha", "assam",
    "jharkhand", "chhattisgarh", "himachal pradesh", "uttarakhand", "goa",
    "ap", "ts",  # abbreviations
}


# ============================================================
# DATACLASS
# ============================================================
@dataclass
class AgentPlan:
    intent: str
    entities: Dict[str, Any]   # lat, lon, crop, state, district, city, season
    required_tools: List[str]
    language: str
    query: str


# ============================================================
# INTENT CLASSIFICATION
# (Multi-lingual keyword matching, consistent with voice_assistant.py)
# ============================================================
def classify_intent(query: str) -> str:
    """
    Classify the farmer's query into one of the supported intents.
    Uses multi-lingual keyword matching: English, Telugu, Hindi.
    """
    if not query or not isinstance(query, str) or not query.strip():
        return "unknown"

    q = query.lower()

    # 1. Action Plan
    if any(w in q for w in [
        "action plan", "7-day", "7 day", "schedule", "this week", "today's task",
        "కార్యాచరణ", "ప్రణాళిక", "ఈ వారం", "कार्य योजना", "योजना", "इस सप्ताह",
    ]):
        return "action_plan"

    # 2. Plant Health / Pest / Disease
    if any(w in q for w in [
        "disease", "pest", "leaf", "blight", "rot", "fungus", "caterpillar",
        "worm", "spots", "yellowing", "wilting", "infection", "mite",
        "వ్యాధి", "తెగులు", "పురుగు", "ఆకుమచ్చ", "రోగం",
        "बीमारी", "रोग", "कीट", "झुलसा", "पत्ती", "कीड़ा",
    ]):
        return "plant_health"

    # 3. Fertilizer / Nutrients
    if any(w in q for w in [
        "fertilizer", "fertiliser", "urea", "dap", "npk", "mop", "ssp",
        "manure", "compost", "nutrient", "nitrogen", "phosphorus", "potassium",
        "dose", "dosage", "deficiency",
        "ఎరువు", "ఎరువులు", "యూరియా", "పోషకాలు",
        "उर्वरक", "खाद", "डीएपी", "यूरिया", "पोषक",
    ]):
        return "fertilizer"

    # 4. Irrigation / Water
    if any(w in q for w in [
        "irrigate", "irrigation", "water", "watering", "drip", "sprinkler",
        "flood", "moisture", "should i water", "when to water",
        "నీరు", "నీటిపారుదల", "తడి", "సించాయి",
        "पानी", "सिंचाई", "ड्रिप", "नमी",
    ]):
        return "irrigation"

    # 5. Weather / Climate / Forecast / Rain
    if any(w in q for w in [
        "weather", "rain", "rainfall", "temperature", "forecast", "humidity",
        "wind", "storm", "monsoon", "climate", "hot", "cold",
        "వాతావరణం", "వర్షం", "ఎండ", "చలి", "వర్షపాతం",
        "मौसम", "बारिश", "तापमान", "बाढ़", "तूफान",
    ]):
        return "weather"

    # 6. Market / Mandi / Price
    if any(w in q for w in [
        "market", "mandi", "price", "prices", "rate", "rates", "msp", "sell",
        "cost", "today's price", "agmarknet", "buying price", "selling price",
        "ధర", "ధరలు", "మార్కెట్", "మండి", "అమ్మకం",
        "भाव", "दाम", "मंडी", "बाजार", "खरीद",
    ]):
        return "market"

    # 7. Alerts / Danger / Risks
    if any(w in q for w in [
        "alert", "alerts", "warning", "danger", "risk", "threat", "caution",
        "worry", "concerned", "problem",
        "హెచ్చరిక", "ప్రమాదం", "జాగ్రత్త",
        "चेतावनी", "खतरा", "जोखिम", "सावधान",
    ]):
        return "alerts"

    # 8. Farm Analysis
    if any(w in q for w in [
        "farm analysis", "my farm", "soil test", "field report", "full report",
        "overall", "complete analysis",
        "విశ్లేషణ", "నా పొలం", "నేల పరీక్ష",
        "विश्लेषण", "मेरा खेत", "पूरी जानकारी",
    ]):
        return "farm_analysis"

    # 9. Crop Suitability & Sowing
    if any(w in q for w in [
        "crop", "crops", "sow", "sowing", "plant", "planting", "seed",
        "variety", "harvest", "kharif", "rabi", "zaid",
        "which crop", "what crop", "best crop", "grow",
        "పంట", "వరి", "మొక్కజొన్న", "పంటలు", "సాగు",
        "फसल", "धान", "गेहूं", "कौन सी फसल",
    ]):
        return "crop"

    # 10. General Agriculture / Help
    if any(w in q for w in [
        "help", "what", "how", "who", "agri", "farming", "scheme",
        "pm kisan", "kvk", "extension", "officer",
        "నమస్కారం", "హలో", "సహాయం",
        "नमस्ते", "सहायता", "मदद",
    ]):
        return "general_agriculture"

    # Default: general if multiple words, unknown if too short
    return "general_agriculture" if len(q.split()) >= 2 else "unknown"


# ============================================================
# ENTITY EXTRACTION
# ============================================================
def extract_entities(query: str, client_context: dict, language: str = "en") -> dict:
    """
    Extract actionable entities from the query text and client context.
    Client context is treated as supplemental — backend-fetched data takes precedence.

    Returns dict with keys: lat, lon, crop, state, district, city, season
    """
    entities: Dict[str, Any] = {}
    q = query.lower() if query else ""

    # ---- 1. GPS coordinates from client context (highest priority) ----
    req = client_context.get("request") or {}
    if isinstance(req, dict):
        lat = req.get("latitude") or req.get("lat")
        lon = req.get("longitude") or req.get("lon")
        if lat is not None and lon is not None:
            try:
                entities["lat"] = float(lat)
                entities["lon"] = float(lon)
            except (TypeError, ValueError):
                pass

    if "lat" not in entities:
        loc_obj = client_context.get("location") or {}
        if isinstance(loc_obj, dict):
            lat = loc_obj.get("latitude") or loc_obj.get("lat")
            lon = loc_obj.get("longitude") or loc_obj.get("lon")
            if lat is not None and lon is not None:
                try:
                    entities["lat"] = float(lat)
                    entities["lon"] = float(lon)
                except (TypeError, ValueError):
                    pass

    if "lat" not in entities:
        lat = client_context.get("latitude") or client_context.get("lat")
        lon = client_context.get("longitude") or client_context.get("lon")
        if lat is not None and lon is not None:
            try:
                entities["lat"] = float(lat)
                entities["lon"] = float(lon)
            except (TypeError, ValueError):
                pass

    # ---- 2. Season from client context ----
    season = req.get("season")
    if season and isinstance(season, str):
        entities["season"] = season

    # ---- 3. Active crop from client context ----
    crop_from_context = (
        req.get("active_crop") or
        req.get("previous_crop") or
        _crop_from_recommendation(client_context)
    )
    if crop_from_context:
        entities["crop_hint"] = str(crop_from_context).lower().strip()

    # ---- 4. Location string from client context ----
    loc = client_context.get("location") or {}
    if isinstance(loc, dict):
        district = loc.get("district") or loc.get("village")
        state = loc.get("state")
        if district:
            entities["district"] = str(district).strip()
        if state:
            entities["state"] = str(state).strip()

    # ---- 5. Extract crop from query text ----
    crop_from_query = _extract_crop_from_query(q)
    if crop_from_query:
        entities["crop_query"] = crop_from_query

    # ---- 6. Extract location from query text (if no GPS) ----
    if "lat" not in entities:
        city_match = _extract_city_from_query(q)
        if city_match:
            coords = CITY_COORDS.get(city_match)
            if coords:
                entities["lat"] = coords[0]
                entities["lon"] = coords[1]
                entities["city"] = city_match
            else:
                entities["city"] = city_match

        state_match = _extract_state_from_query(q)
        if state_match and "state" not in entities:
            entities["state"] = state_match

    # ---- 7. Resolve active crop (query takes priority over context hint) ----
    entities["active_crop"] = (
        entities.get("crop_query") or
        entities.get("crop_hint") or
        "rice"  # safe default
    )

    return entities


def _crop_from_recommendation(client_context: dict) -> Optional[str]:
    """Try to extract active crop from farm analysis crop recommendation."""
    rec = client_context.get("crop_recommendation") or {}
    if isinstance(rec, dict):
        top3 = rec.get("top_3") or []
        if top3 and isinstance(top3[0], dict):
            return top3[0].get("crop")
    return None


def _extract_crop_from_query(q: str) -> Optional[str]:
    """Extract a known crop name from the query string."""
    # Check aliases — use word boundaries for short aliases to avoid partial matches
    for alias in sorted(CROP_ALIASES.keys(), key=len, reverse=True):
        if len(alias) <= 4:
            if re.search(r'\b' + re.escape(alias) + r'\b', q):
                return CROP_ALIASES[alias]
        else:
            if alias in q:
                return CROP_ALIASES[alias]
    # Check canonical names with word boundaries
    for crop in sorted(KNOWN_CROPS, key=len, reverse=True):
        if re.search(r'\b' + re.escape(crop) + r'\b', q):
            return crop
    return None


def _extract_city_from_query(q: str) -> Optional[str]:
    """Extract a known Indian farming city from the query string."""
    for city in sorted(CITY_COORDS.keys(), key=len, reverse=True):
        if city in q:
            return city
    return None


def _extract_state_from_query(q: str) -> Optional[str]:
    """Extract a known Indian state from the query string."""
    for state in sorted(STATE_NAMES, key=len, reverse=True):
        if state in q:
            return state
    return None


# ============================================================
# PLAN BUILDER
# ============================================================
def build_plan(payload: dict) -> AgentPlan:
    """
    Entry point: build a full AgentPlan from the raw /api/assistant/query payload.
    """
    query = (payload.get("query") or "").strip()
    language_raw = payload.get("language") or "en"
    language = language_raw if language_raw in ("en", "te", "hi") else "en"
    client_context = (
        payload.get("context")
        if isinstance(payload.get("context"), dict)
        else (payload.get("client_context") if isinstance(payload.get("client_context"), dict) else {})
    )

    if not query:
        return AgentPlan(
            intent="unknown",
            entities={},
            required_tools=[],
            language=language,
            query="",
        )

    intent = classify_intent(query)
    entities = extract_entities(query, client_context, language)

    required_tools = INTENT_TOOLS.get(intent, [])

    return AgentPlan(
        intent=intent,
        entities=entities,
        required_tools=required_tools,
        language=language,
        query=query,
    )
