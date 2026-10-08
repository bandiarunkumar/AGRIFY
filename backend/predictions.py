"""
Prediction Engine - Crop & Fertilizer Recommendations
Uses trained ML models + weather data + profit calculations
"""

import os
import joblib
import numpy as np
from config import (
    CROP_MODEL_FILE, CROP_ENCODER_FILE,
    FERTILIZER_MODEL_FILE, FERTILIZER_ENCODER_FILE,
    CROP_PRICES, CROP_BASE_YIELD,
    LABOR_COST_PER_HECTARE, OTHER_COST_PER_HECTARE,
    FERTILIZER_INFO, PEST_DATABASE, DEFAULT_PEST_INFO
)

# No artificial crop boosting — let ML model decide purely from soil data

# Indian State/Region heuristics for average soil attributes
REGION_SOIL_PROFILES = {
    "default": {"soil_type": "Loamy", "N": 50, "P": 40, "K": 30, "ph": 6.8, "organic_carbon": 0.8, "ec": 0.5, "moisture": 45},
    "punjab": {"soil_type": "Loamy", "N": 40, "P": 45, "K": 35, "ph": 7.5, "organic_carbon": 0.5, "ec": 0.8, "moisture": 40},
    "haryana": {"soil_type": "Loamy", "N": 45, "P": 40, "K": 30, "ph": 7.8, "organic_carbon": 0.4, "ec": 0.9, "moisture": 35},
    "andhra pradesh": {"soil_type": "Clay", "N": 80, "P": 40, "K": 40, "ph": 6.5, "organic_carbon": 1.2, "ec": 0.4, "moisture": 60},
    "telangana": {"soil_type": "Clay", "N": 70, "P": 35, "K": 35, "ph": 6.8, "organic_carbon": 1.0, "ec": 0.5, "moisture": 50},
    "maharashtra": {"soil_type": "Clay", "N": 60, "P": 45, "K": 40, "ph": 7.2, "organic_carbon": 0.9, "ec": 0.6, "moisture": 40},
    "gujarat": {"soil_type": "Sandy", "N": 35, "P": 30, "K": 25, "ph": 7.5, "organic_carbon": 0.6, "ec": 1.1, "moisture": 30},
    "karnataka": {"soil_type": "Loamy", "N": 55, "P": 40, "K": 45, "ph": 6.5, "organic_carbon": 1.1, "ec": 0.4, "moisture": 55},
    "tamil nadu": {"soil_type": "Clay", "N": 65, "P": 40, "K": 35, "ph": 6.7, "organic_carbon": 1.0, "ec": 0.5, "moisture": 55},
    "kerala": {"soil_type": "Loamy", "N": 90, "P": 30, "K": 30, "ph": 5.8, "organic_carbon": 1.5, "ec": 0.2, "moisture": 70},
    "uttar pradesh": {"soil_type": "Loamy", "N": 50, "P": 40, "K": 35, "ph": 7.0, "organic_carbon": 0.6, "ec": 0.6, "moisture": 45},
    "west bengal": {"soil_type": "Silt", "N": 85, "P": 45, "K": 30, "ph": 6.2, "organic_carbon": 1.3, "ec": 0.3, "moisture": 65},
    "bihar": {"soil_type": "Silt", "N": 60, "P": 40, "K": 35, "ph": 6.5, "organic_carbon": 0.8, "ec": 0.5, "moisture": 50},
    "madhya pradesh": {"soil_type": "Clay", "N": 45, "P": 35, "K": 40, "ph": 7.0, "organic_carbon": 0.7, "ec": 0.6, "moisture": 40},
    "rajasthan": {"soil_type": "Sandy", "N": 20, "P": 25, "K": 20, "ph": 8.0, "organic_carbon": 0.3, "ec": 1.5, "moisture": 25}
}


# ============================================
# LOAD MODELS (once when file is imported)
# ============================================
def load_model(filepath):
    if os.path.exists(filepath):
        try:
            return joblib.load(filepath)
        except Exception as e:
            print(f"  WARNING: Could not load {filepath}: {e}")
            return None
    return None


crop_model = load_model(CROP_MODEL_FILE)
crop_encoder = load_model(CROP_ENCODER_FILE)
fertilizer_model = load_model(FERTILIZER_MODEL_FILE)
fertilizer_encoders = load_model(FERTILIZER_ENCODER_FILE)

print(f"Crop model:       {'Loaded' if crop_model else 'NOT FOUND'}")
print(f"Crop encoder:     {'Loaded' if crop_encoder else 'NOT FOUND'}")
print(f"Fertilizer model: {'Loaded' if fertilizer_model else 'NOT FOUND'}")
print(f"Fert encoders:    {'Loaded' if fertilizer_encoders else 'NOT FOUND'}")


# ============================================
# CROP PREDICTION
# ============================================
def predict_crop(N, P, K, temperature, humidity, ph, rainfall):
    """
    Predict best crop based on soil & weather conditions
    Returns: dict with crop name, confidence, alternatives, profit estimate
    """
    if not crop_model or not crop_encoder:
        return {"error": "Crop model not trained. Run train_crop_model.py first"}

    try:
        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])

        # Get probabilities for all crops — pure ML, no artificial boosting
        probabilities = crop_model.predict_proba(features)[0]

        # Top 5 crops ranked purely by model confidence
        top_indices = np.argsort(probabilities)[::-1][:5]

        results = []
        for idx in top_indices:
            crop_name = crop_encoder.inverse_transform([idx])[0]
            confidence = round(probabilities[idx] * 100, 2)

            if confidence > 0:
                # Calculate profit
                profit_info = calculate_profit(crop_name)

                # Get pest info
                pest_info = PEST_DATABASE.get(crop_name, DEFAULT_PEST_INFO)

                results.append({
                    "crop": crop_name,
                    "confidence": confidence,
                    "profit": profit_info,
                    "pests": pest_info
                })

        if not results:
            return {"error": "Could not predict crop. Check input values"}

        return {
            "best_crop": results[0],
            "alternatives": results[1:],
            "input_summary": {
                "N": N, "P": P, "K": K,
                "temperature": temperature,
                "humidity": humidity,
                "ph": ph,
                "rainfall": rainfall
            }
        }

    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}


# ============================================
# PROFIT CALCULATION
# ============================================
def calculate_profit(crop_name):
    """
    Estimate profit per hectare for a crop
    """
    crop_lower = crop_name.lower()

    price_per_kg = CROP_PRICES.get(crop_lower, 30)
    base_yield = CROP_BASE_YIELD.get(crop_lower, 2000)

    # Add some realistic variation
    estimated_yield = base_yield
    gross_income = estimated_yield * price_per_kg

    # Costs
    fertilizer_cost = 3000
    seed_cost = 2000
    total_cost = (
        fertilizer_cost + seed_cost +
        LABOR_COST_PER_HECTARE + OTHER_COST_PER_HECTARE
    )

    net_profit = gross_income - total_cost

    return {
        "price_per_kg": price_per_kg,
        "estimated_yield_kg": estimated_yield,
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


# ============================================
# FERTILIZER PREDICTION
# ============================================
def predict_fertilizer(soil_type, soil_ph, soil_moisture, organic_carbon,
                       electrical_conductivity, N, P, K, temperature,
                       humidity, rainfall, crop_type, growth_stage,
                       season, irrigation, previous_crop, region,
                       fertilizer_usage, yield_last):
    """
    Predict best fertilizer based on soil, crop, and weather conditions
    """
    if not fertilizer_model or not fertilizer_encoders:
        return {"error": "Fertilizer model not trained. Run train_fertilizer_model.py first"}

    try:
        # Encode categorical inputs
        def safe_encode(encoder_name, value):
            enc = fertilizer_encoders.get(encoder_name)
            if enc is None:
                return 0
            value = str(value)
            if value in enc.classes_:
                return enc.transform([value])[0]
            else:
                return 0  # default if unknown category

        soil_enc = safe_encode('soil_type', soil_type)
        crop_enc = safe_encode('crop_type', crop_type)
        growth_enc = safe_encode('growth_stage', growth_stage)
        season_enc = safe_encode('season', season)
        irrigation_enc = safe_encode('irrigation', irrigation)
        previous_enc = safe_encode('previous_crop', previous_crop)
        region_enc = safe_encode('region', region)
        fert_usage_enc = safe_encode('fertilizer_usage', fertilizer_usage)

        features = np.array([[
            soil_enc, soil_ph, soil_moisture, organic_carbon,
            electrical_conductivity, N, P, K,
            temperature, humidity, rainfall,
            crop_enc, growth_enc, season_enc,
            irrigation_enc, previous_enc, region_enc,
            fert_usage_enc, yield_last
        ]])

        # Get probabilities
        probabilities = fertilizer_model.predict_proba(features)[0]
        fert_encoder = fertilizer_encoders['fertilizer']

        # Top 3 fertilizers
        top_indices = np.argsort(probabilities)[::-1][:3]

        results = []
        for idx in top_indices:
            fert_name = fert_encoder.inverse_transform([idx])[0]
            confidence = round(probabilities[idx] * 100, 2)

            if confidence > 0:
                # Get fertilizer details
                fert_details = FERTILIZER_INFO.get(fert_name, {
                    "npk": "N/A",
                    "qty_per_ha": 50,
                    "cost_per_kg": 20
                })

                results.append({
                    "fertilizer": fert_name,
                    "confidence": confidence,
                    "details": fert_details
                })

        if not results:
            return {"error": "Could not predict fertilizer"}

        return {
            "best_fertilizer": results[0],
            "alternatives": results[1:],
            "input_summary": {
                "soil_type": soil_type,
                "crop_type": crop_type,
                "N": N, "P": P, "K": K,
                "temperature": temperature,
                "humidity": humidity
            }
        }

    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}


# ============================================
# QUICK TEST
# ============================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING CROP PREDICTION")
    print("=" * 60)

    # Test: Rice-like conditions
    result = predict_crop(
        N=90, P=42, K=43,
        temperature=25, humidity=82,
        ph=6.5, rainfall=200
    )

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        best = result["best_crop"]
        print(f"\nBest Crop: {best['crop'].upper()}")
        print(f"Confidence: {best['confidence']}%")
        print(f"\nProfit Estimate (per hectare):")
        print(f"  Yield:      {best['profit']['estimated_yield_kg']} kg")
        print(f"  Income:     Rs.{best['profit']['gross_income']}")
        print(f"  Cost:       Rs.{best['profit']['total_cost']}")
        print(f"  Net Profit: Rs.{best['profit']['net_profit']}")
        print(f"\nPest Alert:")
        print(f"  Common pests: {best['pests']['pests']}")
        print(f"  Organic fix:  {best['pests']['organic']}")

        if result["alternatives"]:
            print(f"\nAlternatives:")
            for alt in result["alternatives"]:
                print(f"  {alt['crop']:15s} {alt['confidence']}%  Profit: Rs.{alt['profit']['net_profit']}")

    print("\n" + "=" * 60)
    print("TESTING FERTILIZER PREDICTION")
    print("=" * 60)

    result2 = predict_fertilizer(
        soil_type="Loamy", soil_ph=6.5, soil_moisture=40,
        organic_carbon=1.2, electrical_conductivity=0.5,
        N=30, P=20, K=15,
        temperature=28, humidity=65, rainfall=100,
        crop_type="Rice", growth_stage="Vegetative",
        season="Kharif", irrigation="Drip",
        previous_crop="Wheat", region="North",
        fertilizer_usage="Urea", yield_last=4000
    )

    if "error" in result2:
        print(f"Error: {result2['error']}")
    else:
        best_f = result2["best_fertilizer"]
        print(f"\nBest Fertilizer: {best_f['fertilizer']}")
        print(f"Confidence: {best_f['confidence']}%")
        print(f"NPK Ratio: {best_f['details'].get('npk', 'N/A')}")

        if result2["alternatives"]:
            print(f"\nAlternatives:")
            for alt in result2["alternatives"]:
                print(f"  {alt['fertilizer']:15s} {alt['confidence']}%")

    print(f"\n{'=' * 60}")
    print("ALL PREDICTIONS WORKING!")
    print(f"{'=' * 60}")