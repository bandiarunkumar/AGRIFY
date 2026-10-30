"""
Season-aware crop calendar and location mapping for AGRIFY
"""
import json
import os

# Normalized crop season mapping (supplemental, traceable)
CROP_SEASON_CALENDAR = {
    # Cereals
    "rice": {"seasons": ["Kharif"], "sow_months": {"Kharif": [6,7]}, "harvest_months": {"Kharif": [11,12]}, "duration_days": 120, "perennial": False, "boro_rice_eligible": True},
    "wheat": {"seasons": ["Rabi"], "sow_months": {"Rabi": [11,12]}, "harvest_months": {"Rabi": [3,4]}, "duration_days": 130, "perennial": False},
    "maize": {"seasons": ["Kharif", "Rabi"], "sow_months": {"Kharif": [6,7], "Rabi": [10,11]}, "harvest_months": {"Kharif": [9,10], "Rabi": [2,3]}, "duration_days": 100, "perennial": False},
    # Pulses
    "chickpea": {"seasons": ["Rabi"], "sow_months": {"Rabi": [10,11]}, "harvest_months": {"Rabi": [2,3]}, "duration_days": 100, "perennial": False},
    "lentil": {"seasons": ["Rabi"], "sow_months": {"Rabi": [10,11]}, "harvest_months": {"Rabi": [2,3]}, "duration_days": 110, "perennial": False},
    "blackgram": {"seasons": ["Kharif", "Rabi"], "sow_months": {"Kharif": [6,7], "Rabi": [10,11]}, "harvest_months": {"Kharif": [9,10], "Rabi": [1,2]}, "duration_days": 80, "perennial": False},
    "mungbean": {"seasons": ["Kharif", "Zaid"], "sow_months": {"Kharif": [6,7], "Zaid": [3,4]}, "harvest_months": {"Kharif": [9], "Zaid": [5,6]}, "duration_days": 65, "perennial": False},
    "pigeonpeas": {"seasons": ["Kharif"], "sow_months": {"Kharif": [6,7]}, "harvest_months": {"Kharif": [12,1]}, "duration_days": 170, "perennial": False},
    # Oilseeds
    "mustard": {"seasons": ["Rabi"], "sow_months": {"Rabi": [10,11]}, "harvest_months": {"Rabi": [2,3]}, "duration_days": 110, "perennial": False},
    "groundnut": {"seasons": ["Kharif", "Rabi"], "sow_months": {"Kharif": [6,7], "Rabi": [11,12]}, "harvest_months": {"Kharif": [10,11], "Rabi": [3,4]}, "duration_days": 110, "perennial": False},
    "soybean": {"seasons": ["Kharif"], "sow_months": {"Kharif": [6,7]}, "harvest_months": {"Kharif": [10,11]}, "duration_days": 100, "perennial": False},
    # Vegetables
    "potato": {"seasons": ["Rabi"], "sow_months": {"Rabi": [10,11]}, "harvest_months": {"Rabi": [1,2]}, "duration_days": 90, "perennial": False},
    "tomato": {"seasons": ["Rabi", "Zaid"], "sow_months": {"Rabi": [10,11], "Zaid": [1,2]}, "harvest_months": {"Rabi": [1,2], "Zaid": [4,5]}, "duration_days": 75, "perennial": False},
    "onion": {"seasons": ["Rabi", "Kharif"], "sow_months": {"Rabi": [10,11], "Kharif": [6,7]}, "harvest_months": {"Rabi": [2,3], "Kharif": [9,10]}, "duration_days": 120, "perennial": False},
    "cabbage": {"seasons": ["Rabi"], "sow_months": {"Rabi": [9,10]}, "harvest_months": {"Rabi": [12,1]}, "duration_days": 90, "perennial": False},
    "cauliflower": {"seasons": ["Rabi"], "sow_months": {"Rabi": [9,10]}, "harvest_months": {"Rabi": [12,1]}, "duration_days": 90, "perennial": False},
    # Perennial/long-term
    "coconut": {"seasons": ["Perennial"], "sow_months": {"Perennial": [6,7,8,9]}, "harvest_months": {"Perennial": [1,2,3,4,5,6,7,8,9,10,11,12]}, "duration_days": 365, "perennial": True, "time_to_first_yield_years": 5, "productive_lifespan_years": 60, "harvest_frequency": "year-round"},
    "mango": {"seasons": ["Perennial"], "sow_months": {"Perennial": [7,8]}, "harvest_months": {"Perennial": [4,5,6,7]}, "duration_days": 90, "perennial": True, "time_to_first_yield_years": 4, "productive_lifespan_years": 40, "harvest_frequency": "seasonal"},
    "banana": {"seasons": ["Perennial"], "sow_months": {"Perennial": [6,7,8,10,11]}, "harvest_months": {"Perennial": [1,2,3,4,5,6,7,8,9,10,11,12]}, "duration_days": 420, "perennial": True, "time_to_first_yield_years": 1, "productive_lifespan_years": 25, "harvest_frequency": "year-round"},
    "sugarcane": {"seasons": ["Kharif", "Rabi"], "sow_months": {"Kharif": [6,7], "Rabi": [10,11,2,3]}, "harvest_months": {"Kharif": [12,1,2,3], "Rabi": [12,1,2,3]}, "duration_days": 360, "perennial": False},
}

# Agro-climatic zones mapping (simplified)
AGRO_CLIMATIC_ZONES = {
    "assam": "North Eastern Hills and Terai",
    "arunachal pradesh": "North Eastern Hills and Terai",
    "manipur": "North Eastern Hills and Terai",
    "meghalaya": "North Eastern Hills and Terai",
    "mizoram": "North Eastern Hills and Terai",
    "nagaland": "North Eastern Hills and Terai",
    "tripura": "North Eastern Hills and Terai",
    "sikkim": "North Eastern Hills and Terai",
}

# District to state mapping (minimal)
DISTRICT_STATE = {
    "dhemaji": "Assam",
    "lakhimpur": "Assam",
    "jorhat": "Assam",
    "guwahati": "Assam",
}

def get_location_info(lat, lon, district=None, state=None):
    district_norm = (district or '').lower().strip()
    state_norm = (state or '').lower().strip()
    if district_norm in DISTRICT_STATE:
        state_norm = DISTRICT_STATE[district_norm].lower()
    zone = AGRO_CLIMATIC_ZONES.get(state_norm, None)
    return {"district": district, "state": state, "agro_climatic_zone": zone}

def is_season_compatible(crop, season, irrigation='Rainfed'):
    cal = CROP_SEASON_CALENDAR.get(crop.lower())
    if not cal:
        return True, 0.5  # unknown, don't block aggressively
    seasons = cal.get("seasons", [])
    if "Perennial" in seasons:
        return False, 0.0  # perennials handled separately
    if season in seasons:
        return True, 1.0
    # Boro rice special case
    if crop.lower() == "rice" and season == "Rabi" and irrigation and irrigation.lower() in ["irrigated", "drip", "canal", "tube well", "well"]:
        return True, 0.7  # lower confidence
    return False, 0.0

def get_seasonal_crop(crop):
    cal = CROP_SEASON_CALENDAR.get(crop.lower(), {})
    return cal.get("seasons", []), cal.get("perennial", False)
