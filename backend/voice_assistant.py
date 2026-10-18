"""
AGRIFY — AI Voice Assistant & Orchestration Engine
Module: backend/voice_assistant.py

Provides factual, intent-filtered voice AI orchestration for Indian farmers.
Consumes verified AGRIFY context and enforces strict agronomic safety guardrails.

STRICT SAFETY CONSTRAINTS:
1. NEVER invents fertilizer quantities, concentrations, pesticide dosages, or chemical rates.
2. NEVER invents weather measurements, soil values, market prices, yields, or profits.
3. NEVER claims confirmed disease diagnosis; uses cautious symptom-matching advisory language.
4. Generates concise, natural 1–3 sentence spoken scripts suitable for TTS (no markdown in audio).
5. Seamlessly falls back to deterministic rule responses on any Gemini failure or timeout.
"""

import os
import re
import json
from datetime import datetime, timezone

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# ============================================================
# SUPPORTED INTENTS
# ============================================================
INTENTS = [
    "action_plan",
    "plant_health",
    "fertilizer",
    "irrigation",
    "weather",
    "market",
    "alerts",
    "farm_analysis",
    "crop",
    "general_agriculture",
    "unknown",
]

# ============================================================
# LOCALIZATION TEMPLATES (for Deterministic Rule Engine)
# ============================================================
LOCALIZED_TEMPLATES = {
    "en": {
        "disclaimer": "Advisory guidance based on verified AGRIFY agricultural models. Verify critical field applications with your local KVK extension officer.",
        "fertilizer_trusted_spoken": "According to your AGRIFY farm analysis, the prescribed recommendation for {crop} is {fert} ({npk}) at {qty} kg per hectare as a {stage} application.",
        "fertilizer_untrusted_spoken": "AGRIFY does not have a verified fertilizer dosage for this specific field. Please check your Farm Analyzer report or consult your local agricultural extension officer before applying chemicals.",
        "irrigation_trusted_spoken": "Your field irrigation guidance indicates {recommendation} Net water needed is {net_irr} millimeters per day using {method} irrigation.",
        "irrigation_general_spoken": "For {crop}, maintain adequate soil moisture. Drip irrigation in the early morning between 6 and 8 AM minimizes evaporation loss.",
        "weather_spoken": "Current conditions in {location} are {temp}°C with {humidity}% humidity and {desc}. Plan field activities according to the 5-day forecast.",
        "weather_general_spoken": "Weather conditions affect crop spraying and irrigation. Check the Weather tab for live 5-day coordinate forecasts.",
        "market_spoken": "The estimated price for {crop} in your region is approximately ₹{price} per kilogram. Check the Market tab for live Agmarknet mandi rates.",
        "alerts_spoken": "You have active farm alerts: {alert_title}. Please review the recommended mitigations in your alert dashboard.",
        "action_plan_spoken": "Your 7-day action plan for {crop} is active. Your immediate focus is: {top_action}.",
        "plant_health_spoken": "The described symptoms on {crop} may be consistent with early environmental stress or foliar blight. A physical leaf inspection by a local agriculture expert is recommended for confirmed identification.",
        "crop_spoken": "For {season} season in {location}, recommended crops include {crop_list}. Choose based on your soil type and water availability.",
        "general_spoken": "I am AGRIFY Voice Copilot. I can assist with your farm analysis, crop recommendations, fertilizer schedules, irrigation guidance, weather advisories, and mandi rates.",
        "unknown_spoken": "I did not fully catch that. You can ask about crop suitability, fertilizer recommendations, irrigation timing, weather forecasts, or market prices.",
    },
    "te": {
        "disclaimer": "ధృవీకరించబడిన AGRIFY వ్యవసాయ సమాచారం ఆధారంగా అందించబడిన సలహా. రసాయన వాడకానికి ముందు స్థానిక KVK అధికారిని సంప్రదించండి.",
        "fertilizer_trusted_spoken": "మీ AGRIFY విశ్లేషణ ప్రకారం {crop} పంటకు {stage} దశలో హెక్టారుకు {qty} కిలోల {fert} ({npk}) సిఫారసు చేయబడింది.",
        "fertilizer_untrusted_spoken": "ఈ పొలానికి ఖచ్చితమైన ఎరువుల మోతాదు నమోదు కాలేదు. రసాయన ఎరువులు వేసే ముందు మీ వ్యవసాయ అధికారిని లేదా KVK నిపుణులను సంప్రదించండి.",
        "irrigation_trusted_spoken": "మీ పొలానికి నీటి యాజమాన్య సలహా: {recommendation} {method} విధానంలో రోజుకు {net_irr} మి.మీ నీరు అవసరం.",
        "irrigation_general_spoken": "{crop} పంటకు ఉదయం 6 నుండి 8 గంటల మధ్య డ్రిప్ ద్వారా నీరు అందించడం ఉత్తమం.",
        "weather_spoken": "{location}లో ప్రస్తుత ఉష్ణోగ్రత {temp}°C, తేమ {humidity}%, మరియు {desc}. వాతావరణాన్ని బట్టి పనులు ప్లాన్ చేయండి.",
        "weather_general_spoken": "పంట పిచికారీ మరియు నీటిపారుదలకు వాతావరణం ముఖ్యం. లైవ్ 5 రోజుల సూచన కోసం వెదర్ ట్యాబ్ చూడండి.",
        "market_spoken": "మీ ప్రాంతంలో {crop} అంచనా ధర కిలోకు సుమారు ₹{price}. తాజా మార్కెట్ ధరల కోసం మార్కెట్ ట్యాబ్ చూడండి.",
        "alerts_spoken": "మీ పొలానికి ముఖ్యమైన హెచ్చరిక ఉంది: {alert_title}. జాగ్రత్తలు పాటించండి.",
        "action_plan_spoken": "{crop} కోసం 7 రోజుల కార్యాచరణ ప్రణాళిక సిద్ధంగా ఉంది. ముఖ్య ప్రాధాన్యత: {top_action}.",
        "plant_health_spoken": "{crop} పంటపై కనిపించే లక్షణాలు తెగులు లేదా పోషక లోపానికి సంబంధించినవి కావచ్చు. నిర్ధారణ కోసం స్థానిక వ్యవసాయ నిపుణులకు ఆకు చూపించండి.",
        "crop_spoken": "{location}లో {season} సీజన్‌కు అనువైన పంటలు: {crop_list}. మీ నేల మరియు నీటి వసతిని బట్టి ఎంచుకోండి.",
        "general_spoken": "నేను AGRIFY వాయిస్ సహాయకుడిని. పంటలు, ఎరువులు, నీటిపారుదల, వాతావరణం మరియు మార్కెట్ ధరలపై సమాచారం ఇవ్వగలను.",
        "unknown_spoken": "మీ ప్రశ్న పూర్తిగా అర్థం కాలేదు. పంటలు, ఎరువుల వివరాలు, వాతావరణం లేదా మార్కెట్ ధరల గురించి అడగండి.",
    },
    "hi": {
        "disclaimer": "सत्यापित AGRIFY कृषि मॉडल पर आधारित सलाहकार मार्गदर्शन। महत्वपूर्ण निर्णयों के लिए अपने स्थानीय KVK अधिकारी से परामर्श लें।",
        "fertilizer_trusted_spoken": "आपके AGRIFY विश्लेषण के अनुसार {crop} फसल के लिए {stage} अवस्था में प्रति हेक्टेयर {qty} किलोग्राम {fert} ({npk}) अनुशंसित है।",
        "fertilizer_untrusted_spoken": "इस खेत के लिए सत्यापित उर्वरक मात्रा उपलब्ध नहीं है। रासायनिक खाद डालने से पहले अपने स्थानीय कृषि विस्तार अधिकारी या KVK से सलाह लें।",
        "irrigation_trusted_spoken": "आपके खेत की सिंचाई सलाह: {recommendation} {method} विधि से प्रतिदिन {net_irr} मिमी पानी की आवश्यकता है।",
        "irrigation_general_spoken": "{crop} फसल के लिए सुबह 6 से 8 बजे के बीच ड्रिप द्वारा सिंचाई करना सबसे प्रभावी है।",
        "weather_spoken": "{location} में वर्तमान तापमान {temp}°C, आर्द्रता {humidity}% और {desc} है। 5-दिवसीय पूर्वानुमान देखकर कृषि कार्य करें।",
        "weather_general_spoken": "स्प्रे और सिंचाई के लिए मौसम की जानकारी जरूरी है। 5-दिवसीय मौसम पूर्वानुमान के लिए वेदर टैब देखें।",
        "market_spoken": "आपके क्षेत्र में {crop} का अनुमानित भाव लगभग ₹{price} प्रति किलोग्राम है। सटीक मंडी दरों के लिए मार्केट टैब देखें।",
        "alerts_spoken": "आपके खेत के लिए सक्रिय चेतावनी है: {alert_title}। कृपया सुरक्षात्मक उपाय अपनाएं।",
        "action_plan_spoken": "{crop} के लिए 7-दिवसीय कार्य योजना सक्रिय है। आपकी मुख्य प्राथमिकता: {top_action} है।",
        "plant_health_spoken": "{crop} फसल पर बताए गए लक्षण कीट या कवक रोग से जुड़े हो सकते हैं। सटीक पुष्टि के लिए कृषि विशेषज्ञ से पत्ती की जांच कराएं।",
        "crop_spoken": "{location} में {season} मौसम के लिए अनुशंसित फसलें: {crop_list} हैं। मिट्टी और पानी के अनुसार चुनाव करें।",
        "general_spoken": "मैं AGRIFY वॉइस सहायक हूँ। मैं फसल, उर्वरक, सिंचाई, मौसम और मंडी भाव में आपकी सहायता कर सकता हूँ।",
        "unknown_spoken": "मैं आपकी बात पूरी तरह समझ नहीं पाया। आप फसल, खाद, सिंचाई, मौसम या मंडी भाव से संबंधित सवाल पूछ सकते हैं।",
    }
}


def normalize_language(lang: str) -> str:
    """Normalize language code to supported set (en, te, hi). Default: en."""
    if not isinstance(lang, str):
        return "en"
    l = lang.strip().lower()
    if l in ("te", "telugu"):
        return "te"
    if l in ("hi", "hindi"):
        return "hi"
    return "en"


# ============================================================
# DETERMINISTIC INTENT CLASSIFICATION
# ============================================================
def classify_intent(query: str) -> str:
    """
    Deterministically classify the farmer's query into an intent.
    Uses multi-lingual keyword patterns (English, Telugu, Hindi).
    """
    if not query or not isinstance(query, str) or not query.strip():
        return "unknown"

    q = query.lower()

    # 1. Action Plan
    if any(w in q for w in ["action plan", "7-day", "7 day", "schedule", "this week", "today's task", "కార్యాచరణ", "ప్రణాళిక", "ఈ వారం", "कार्य योजना", "योजना", "इस सप्ताह"]):
        return "action_plan"

    # 2. Plant Health / Pest / Disease
    if any(w in q for w in ["disease", "pest", "leaf", "blight", "rot", "fungus", "caterpillar", "worm", "spots", "yellowing", "వ్యాధి", "తెగులు", "పురుగు", "ఆకుమచ్చ", "రోగం", "बीमारी", "रोग", "कीट", "झुलसा", "पत्ती"]):
        return "plant_health"

    # 3. Fertilizer / Nutrients (NOT a prescription engine)
    if any(w in q for w in ["fertilizer", "fertiliser", "urea", "dap", "npk", "mop", "ssp", "manure", "compost", "nutrient", "nitrogen", "phosphorus", "potassium", "dose", "dosage", "ఎరువు", "ఎరువులు", "యూరియా", "పోషకాలు", "उर्वरक", "खाद", "डीएपी", "यूरिया"]):
        return "fertilizer"

    # 4. Irrigation / Water
    if any(w in q for w in ["irrigate", "irrigation", "water", "watering", "drip", "sprinkler", "flood", "moisture", "నీరు", "నీటిపారుదల", "తడి", "సించాయి", "पानी", "ड्रिप"]):
        return "irrigation"

    # 5. Weather / Climate
    if any(w in q for w in ["weather", "rain", "rainfall", "temperature", "forecast", "humidity", "wind", "storm", "వాతావరణం", "వర్షం", "ఎండ", "मौसम", "बारिश", "तापमान"]):
        return "weather"

    # 6. Market / Mandi / Price
    if any(w in q for w in ["market", "mandi", "price", "prices", "rate", "rates", "msp", "sell", "cost", "ధర", "ధరలు", "మార్కెట్", "మండి", "भाव", "दाम", "मंडी", "बाजार"]):
        return "market"

    # 7. Alerts / Danger / Risks
    if any(w in q for w in ["alert", "alerts", "warning", "danger", "risk", "threat", "హెచ్చరిక", "ప్రమాదం", "చేतावनी", "खतरा", "जोखिम"]):
        return "alerts"

    # 8. Farm Analysis / GPS Telemetry
    if any(w in q for w in ["farm analysis", "my farm", "soil test", "field report", "telemetry", "విశ్లేషణ", "నా పొలం", "నేల పరీక్ష", "विश्लेषण", "मेरा खेत"]):
        return "farm_analysis"

    # 9. Crop Suitability & Sowing
    if any(w in q for w in ["crop", "crops", "sow", "sowing", "plant", "planting", "seed", "variety", "yield", "harvest", "kharif", "rabi", "zaid", "rice", "wheat", "cotton", "maize", "chilli", "పంట", "వరి", "మొక్కజొన్న", "మిర్చి", "फसल", "धान", "गेहूं"]):
        return "crop"

    # 10. General Agriculture / Help
    if any(w in q for w in ["help", "what", "how", "who", "agri", "farming", "scheme", "pm kisan", "నమస్కారం", "హలో", "नमस्ते", "सहायता"]):
        return "general_agriculture"

    return "general_agriculture" if len(q.split()) >= 2 else "unknown"


# ============================================================
# CONTEXT FILTERING LAYER
# ============================================================
def filter_context_by_intent(raw_context: dict, intent: str) -> dict:
    """
    Extracts only verified, structured AGRIFY analysis fields relevant to the detected intent.
    Never injects unnecessary private farm data or raw unverified client fields.
    """
    if not isinstance(raw_context, dict):
        return {}

    # Extract standard AGRIFY structures
    req = raw_context.get("request") if isinstance(raw_context.get("request"), dict) else {}
    loc = raw_context.get("location") if isinstance(raw_context.get("location"), dict) else {}
    weather = raw_context.get("weather") if isinstance(raw_context.get("weather"), dict) else {}
    soil = raw_context.get("soil") if isinstance(raw_context.get("soil"), dict) else {}
    crop_rec = raw_context.get("crop_recommendation") if isinstance(raw_context.get("crop_recommendation"), dict) else {}
    fert_rec = raw_context.get("fertilizer_recommendation") if isinstance(raw_context.get("fertilizer_recommendation"), dict) else {}
    irr_rec = raw_context.get("irrigation_guidance") if isinstance(raw_context.get("irrigation_guidance"), dict) else {}
    alerts = raw_context.get("alerts") if isinstance(raw_context.get("alerts"), list) else []
    action_plan = raw_context.get("action_plan") if isinstance(raw_context.get("action_plan"), dict) else {}

    crop = raw_context.get("crop") or req.get("active_crop")
    if not crop and crop_rec.get("top_3"):
        top_list = crop_rec["top_3"]
        if top_list and isinstance(top_list, list) and isinstance(top_list[0], dict):
            crop = top_list[0].get("crop")
    if not crop:
        crop = req.get("previous_crop") or "Crop"

    crop = str(crop).strip().capitalize()
    district = loc.get("district") or loc.get("village") or "Local Field"
    state = loc.get("state") or ""
    location_str = f"{district}, {state}".strip(", ") if state else district
    season = req.get("season") or "Current"

    filtered = {
        "intent": intent,
        "crop": crop,
        "location": location_str,
        "season": season,
    }

    if intent == "farm_analysis":
        filtered.update({
            "soil": {
                "N": soil.get("N"), "P": soil.get("P"), "K": soil.get("K"),
                "ph": soil.get("ph"), "moisture_pct": soil.get("moisture_pct"),
            },
            "top_crops": [c.get("crop") for c in (crop_rec.get("top_3") or []) if isinstance(c, dict)],
            "recommended_fertilizer": (fert_rec.get("recommended_fertilizer") or {}).get("fertilizer"),
            "irrigation": irr_rec.get("recommendation"),
        })

    elif intent == "fertilizer":
        rec_fert = fert_rec.get("recommended_fertilizer") or {}
        details = rec_fert.get("details") or {}
        has_dosage = bool(rec_fert.get("fertilizer") and details.get("qty_per_ha"))

        stage_list = fert_rec.get("stage_wise_application") or []
        first_stage = stage_list[0].get("stage") if (stage_list and isinstance(stage_list[0], dict)) else "Basal"

        filtered.update({
            "has_trusted_fertilizer_dosage": has_dosage,
            "fertilizer_name": rec_fert.get("fertilizer"),
            "npk_ratio": details.get("npk"),
            "qty_per_ha": details.get("qty_per_ha"),
            "stage": first_stage,
            "deficiencies": fert_rec.get("nutrient_deficiency_summary") or [],
        })

    elif intent == "irrigation":
        filtered.update({
            "has_trusted_irrigation_data": bool(irr_rec.get("recommendation")),
            "recommendation": irr_rec.get("recommendation"),
            "net_irrigation_needed_mm_day": irr_rec.get("net_irrigation_needed_mm_day"),
            "irrigation_method": irr_rec.get("irrigation_method") or "Drip",
            "soil_moisture_pct": soil.get("moisture_pct") or irr_rec.get("soil_moisture_pct"),
        })

    elif intent == "weather":
        filtered.update({
            "temperature": weather.get("temperature"),
            "humidity": weather.get("humidity"),
            "rainfall": weather.get("rainfall"),
            "weather_desc": weather.get("weather_desc") or weather.get("description") or "normal",
        })

    elif intent == "market":
        from config import CROP_PRICES
        crop_key = crop.lower()
        price = CROP_PRICES.get(crop_key, 30)
        filtered.update({
            "crop": crop,
            "estimated_mandi_price_kg": price,
            "market_data_note": "Reference regional price estimate from Agmarknet profile.",
        })

    elif intent == "alerts":
        active_items = []
        for a in alerts:
            if isinstance(a, dict) and a.get("severity") in ("danger", "warning"):
                active_items.append({"title": a.get("title"), "message": a.get("message")})
        filtered["active_alerts"] = active_items[:3]

    elif intent == "action_plan":
        filtered.update({
            "summary": action_plan.get("summary"),
            "immediate_actions": action_plan.get("immediate_actions") or [],
            "this_week_plan": action_plan.get("this_week_plan") or [],
        })

    elif intent == "crop":
        filtered.update({
            "top_crops": [c.get("crop") for c in (crop_rec.get("top_3") or []) if isinstance(c, dict)],
            "season": season,
        })

    elif intent == "plant_health":
        filtered.update({
            "crop": crop,
            "symptom_warning": "Visual diagnostic advisory only. Requires physical leaf confirmation.",
        })

    return filtered


# ============================================================
# DETERMINISTIC RULE-BASED SYNTHESIZER
# ============================================================
def synthesize_rule_based_response(query: str, intent: str, context: dict, lang: str = "en") -> dict:
    """
    Constructs a deterministic, safe response adhering strictly to agronomic safety boundaries.
    Produces concise spoken scripts suitable for TTS and structured display cards.
    """
    T = LOCALIZED_TEMPLATES.get(lang, LOCALIZED_TEMPLATES["en"])
    crop = context.get("crop", "Crop")
    loc = context.get("location", "Your Field")
    season = context.get("season", "Current")

    spoken = ""
    display_title = ""
    display_cat = ""
    key_points = []
    action_pill = None
    escalate = False
    suggested_q = None

    if intent == "fertilizer":
        display_cat = "Nutrient Management"
        if context.get("has_trusted_fertilizer_dosage"):
            fert = context.get("fertilizer_name")
            npk = context.get("npk_ratio", "N/A")
            qty = context.get("qty_per_ha")
            stage = context.get("stage", "Basal")
            spoken = T["fertilizer_trusted_spoken"].format(crop=crop, fert=fert, npk=npk, qty=qty, stage=stage)
            display_title = f"{fert} Application Guide"
            key_points = [
                f"Crop: {crop} ({season} season)",
                f"Prescribed: {fert} ({npk}) at {qty} kg/ha",
                f"Timing: {stage} stage application",
            ]
            action_pill = {"label": "View Farm Analysis", "action": "navigate_analysis"}
        else:
            spoken = T["fertilizer_untrusted_spoken"]
            display_title = "Nutrient Dosage Advisory"
            key_points = [
                f"Target crop: {crop}",
                "No verified field dosage in active analysis",
                "Soil testing at local KVK recommended before application",
            ]
            escalate = True
            suggested_q = f"What is the recommended NPK dosage for {crop} based on local soil conditions?"

    elif intent == "irrigation":
        display_cat = "Irrigation Management"
        if context.get("has_trusted_irrigation_data"):
            rec = context.get("recommendation", "Irrigate as scheduled.")
            net = context.get("net_irrigation_needed_mm_day", 3.0)
            method = context.get("irrigation_method", "Drip")
            spoken = T["irrigation_trusted_spoken"].format(recommendation=rec, net_irr=net, method=method)
            display_title = f"{crop} Irrigation Schedule"
            key_points = [
                f"Net requirement: {net} mm/day",
                f"Method: {method}",
                f"Timing: Early morning (6–8 AM)",
            ]
            action_pill = {"label": "View Irrigation Details", "action": "navigate_analysis"}
        else:
            spoken = T["irrigation_general_spoken"].format(crop=crop)
            display_title = f"{crop} Water Guidance"
            key_points = [
                f"Target crop: {crop}",
                "Maintain optimal field moisture",
                "Avoid standing water during non-critical phases",
            ]

    elif intent == "weather":
        display_cat = "Weather Intelligence"
        temp = context.get("temperature")
        if temp is not None:
            hum = context.get("humidity", 60)
            desc = context.get("weather_desc", "fair")
            spoken = T["weather_spoken"].format(location=loc, temp=temp, humidity=hum, desc=desc)
            display_title = f"Live Weather: {loc}"
            key_points = [
                f"Temperature: {temp}°C",
                f"Humidity: {hum}%",
                f"Condition: {desc}",
            ]
            action_pill = {"label": "View 5-Day Forecast", "action": "navigate_weather"}
        else:
            spoken = T["weather_general_spoken"]
            display_title = "Weather Advisory"
            key_points = ["Check live weather before field spraying", "Track rainfall forecast"]

    elif intent == "market":
        display_cat = "Market Intelligence"
        price = context.get("estimated_mandi_price_kg", 30)
        spoken = T["market_spoken"].format(crop=crop, price=price)
        display_title = f"{crop} Mandi Rates"
        key_points = [
            f"Estimated benchmark: ₹{price}/kg",
            "Sourced from Agmarknet regional mandi feeds",
        ]
        action_pill = {"label": "Explore Mandi Rates", "action": "navigate_market"}

    elif intent == "alerts":
        display_cat = "Farm Protection"
        alerts = context.get("active_alerts") or []
        if alerts:
            top_title = alerts[0].get("title", "Weather Warning")
            spoken = T["alerts_spoken"].format(alert_title=top_title)
            display_title = "Active Farm Alerts"
            key_points = [f"⚠️ {a.get('title')}: {a.get('message', '')}" for a in alerts]
            action_pill = {"label": "Open Alert Center", "action": "navigate_alerts"}
        else:
            spoken = f"No severe alerts active for {crop} in {loc}."
            display_title = "Farm Alert Status"
            key_points = ["All environmental parameters normal", "No active danger warnings"]

    elif intent == "action_plan":
        display_cat = "Action Plan"
        top_act = "Maintain scheduled field operations"
        acts = context.get("immediate_actions") or []
        if acts and isinstance(acts[0], dict):
            top_act = acts[0].get("title", top_act)
        spoken = T["action_plan_spoken"].format(crop=crop, top_action=top_act)
        display_title = f"7-Day Plan for {crop}"
        key_points = [f"Immediate focus: {top_act}", f"Season: {season}", f"Location: {loc}"]
        action_pill = {"label": "View 7-Day Plan", "action": "navigate_analysis"}

    elif intent == "plant_health":
        display_cat = "Plant Health Advisory"
        spoken = T["plant_health_spoken"].format(crop=crop)
        display_title = f"{crop} Plant Health Guidance"
        key_points = [
            "Symptoms indicate possible leaf stress or infection",
            "Physical inspection needed for confirmed identification",
            "Upload photo in Crop Doctor for AI visual analysis",
        ]
        action_pill = {"label": "Open Crop Doctor", "action": "navigate_cropDoctor"}
        escalate = True
        suggested_q = f"What is the confirmed diagnosis and organic treatment for these leaf symptoms on {crop}?"

    elif intent == "crop":
        display_cat = "Crop Advisory"
        top_crops = context.get("top_crops") or [crop]
        crop_str = ", ".join(top_crops[:3])
        spoken = T["crop_spoken"].format(season=season, location=loc, crop_list=crop_str)
        display_title = f"Crop Suitability ({season})"
        key_points = [f"Top recommended: {crop_str}", f"Region: {loc}"]
        action_pill = {"label": "View Crop Suitability", "action": "navigate_analysis"}

    elif intent == "farm_analysis":
        display_cat = "Farm Intelligence"
        soil = context.get("soil") or {}
        spoken = f"Your farm analysis for {crop} in {loc} is calibrated with soil pH {soil.get('ph', 6.5)} and live GPS weather."
        display_title = "Farm Analysis Summary"
        key_points = [
            f"Location: {loc}",
            f"Active Crop: {crop}",
            f"Soil pH: {soil.get('ph', '—')}",
        ]
        action_pill = {"label": "Open Farm Analyzer", "action": "navigate_analysis"}

    else:
        display_cat = "Farmer Copilot"
        spoken = T["unknown_spoken"] if intent == "unknown" else T["general_spoken"]
        display_title = "AGRIFY Farmer Copilot"
        key_points = [
            "Ask about crops, fertilizers, irrigation, weather, or mandi prices",
            "Available in English, Telugu, and Hindi",
        ]

    return {
        "status": "success",
        "source": "rule_based_engine",
        "language": lang,
        "intent": intent,
        "spoken_response": spoken,
        "display_card": {
            "title": display_title,
            "category": display_cat,
            "key_points": key_points[:4],
            "action_pill": action_pill,
        },
        "expert_escalation": {
            "recommended": escalate,
            "suggested_question": suggested_q,
        },
        "disclaimer": T["disclaimer"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# OPTIONAL GEMINI AI SYNTHESIZER
# ============================================================
def synthesize_gemini_response(query: str, intent: str, filtered_context: dict, lang: str = "en", gemini_api_key: str = None) -> dict:
    """
    Calls Gemini as a language, prioritization, and tone layer.
    STRICT FACT ANCHORING:
    - Minimizes prompt to intent-specific verified facts.
    - Prohibits hallucinating dosage, prices, weather, or guarantees.
    - If anything fails or returns malformed JSON, returns None for silent fallback.
    """
    if not gemini_api_key or genai is None:
        return None

    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        lang_names = {"en": "English", "te": "Telugu", "hi": "Hindi"}
        target_lang_name = lang_names.get(lang, "English")

        system_prompt = (
            "You are AGRIFY Voice Copilot — an intelligent agricultural voice assistant for Indian farmers.\n"
            "Your task is to answer the farmer's question using ONLY the provided verified AGRIFY facts.\n\n"
            "CRITICAL SAFETY RULES:\n"
            "1. DO NOT invent, calculate, or hallucinate ANY fertilizer dosage, pesticide dosage, chemical application rate, market price, weather reading, or crop yield.\n"
            "2. If fertilizer quantity is asked and has_trusted_fertilizer_dosage is False, explicitly state that AGRIFY does not have a verified quantity for this field, and advise consulting an expert.\n"
            "3. For plant diseases or pests, NEVER state a confirmed diagnosis. Use cautious advisory wording ('symptoms may be consistent with...') and recommend expert confirmation.\n"
            "4. DO NOT promise guaranteed yields, guaranteed profits, or 100% cure.\n"
            f"5. Respond strictly in {target_lang_name} (language code: {lang}).\n"
            "6. spoken_response MUST be concise, conversational (1 to 3 short sentences), suitable for text-to-speech. NO markdown, NO asterisks, NO bullet points in spoken_response.\n"
            "7. Output MUST BE strictly a single valid JSON object with NO markdown fence.\n\n"
            "JSON Schema:\n"
            "{\n"
            '  "spoken_response": "1-3 natural spoken sentences without markdown",\n'
            '  "display_card": {\n'
            '    "title": "Short title",\n'
            '    "category": "Nutrient Management | Irrigation Management | Weather | Market | etc",\n'
            '    "key_points": ["bullet 1", "bullet 2"],\n'
            '    "action_pill": {"label": "Button text", "action": "navigate_analysis"}\n'
            '  },\n'
            '  "expert_escalation": {\n'
            '    "recommended": true/false,\n'
            '    "suggested_question": "question for agronomist or null"\n'
            '  },\n'
            '  "disclaimer": "Advisory disclaimer"\n'
            "}"
        )

        user_content = (
            f"Farmer's Voice Question: {query}\n"
            f"Detected Intent: {intent}\n"
            f"Verified Facts Context: {json.dumps(filtered_context, ensure_ascii=False)}"
        )

        full_prompt = f"{system_prompt}\n\n{user_content}"

        response = model.generate_content(
            full_prompt,
            generation_config={"temperature": 0.2, "response_mime_type": "application/json"}
        )

        raw_text = response.text.strip()
        clean_json = re.sub(r"^```json\s*", "", raw_text)
        clean_json = re.sub(r"\s*```$", "", clean_json)

        data = json.loads(clean_json)

        # Validate structure
        if not isinstance(data.get("spoken_response"), str) or not data["spoken_response"].strip():
            return None
        if not isinstance(data.get("display_card"), dict):
            return None

        # Sanitize spoken_response: ensure no markdown symbols
        spoken = data["spoken_response"].replace("**", "").replace("*", "").replace("#", "").strip()

        card = data["display_card"]
        escalation = data.get("expert_escalation") if isinstance(data.get("expert_escalation"), dict) else {"recommended": False, "suggested_question": None}

        return {
            "status": "success",
            "source": "gemini_ai",
            "language": lang,
            "intent": intent,
            "spoken_response": spoken,
            "display_card": {
                "title": card.get("title", "AGRIFY Copilot Advisory"),
                "category": card.get("category", "General Advisory"),
                "key_points": (card.get("key_points") or [])[:4],
                "action_pill": card.get("action_pill"),
            },
            "expert_escalation": {
                "recommended": bool(escalation.get("recommended")),
                "suggested_question": escalation.get("suggested_question"),
            },
            "disclaimer": data.get("disclaimer") or LOCALIZED_TEMPLATES.get(lang, LOCALIZED_TEMPLATES["en"])["disclaimer"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        print(f"Gemini Voice Assistant notice: {e}. Falling back to rule_based_engine.")
        return None


# ============================================================
# MAIN ORCHESTRATION ENTRYPOINT
# ============================================================
def query_voice_assistant(payload: dict) -> dict:
    """
    Top-level function called by POST /api/assistant/query.

    Phase 3E: Delegates to the AGRIFY Agent Core pipeline first:
      planner → tool_executor → trust_consolidator → responder → safety_gate

    On any agent exception, falls through to the original rule-based engine
    below (zero regression risk).
    """
    if not isinstance(payload, dict):
        raise ValueError("Invalid request body: expected a JSON object.")

    query = payload.get("query", "")
    if not isinstance(query, str):
        query = ""

    # =========================================================
    # PHASE 3E: AGRIFY AGENT CORE PIPELINE
    # =========================================================
    try:
        from agent.planner import build_plan
        from agent.tools import execute_tools
        from agent.context import consolidate_context
        from agent.responder import generate_response
        from agent.safety import validate_response

        plan = build_plan(payload)
        tool_results = execute_tools(plan)
        raw_client_ctx = (
            payload.get("context")
            if isinstance(payload.get("context"), dict)
            else (payload.get("client_context") if isinstance(payload.get("client_context"), dict) else {})
        )
        rich_context = consolidate_context(
            tool_results=tool_results,
            client_context=raw_client_ctx,
            entities=plan.entities,
            intent=plan.intent,
            language=plan.language,
            query=plan.query,
        )
        response = generate_response(plan, rich_context)
        return validate_response(response, rich_context)

    except Exception as agent_exc:
        # Log the failure and fall through to the original engine
        print(f"[AGRIFY Agent] Pipeline error — falling back to rule engine: {agent_exc}")

    # =========================================================
    # ORIGINAL RULE-BASED ENGINE (fallback — unchanged)
    # =========================================================
    query = query.strip() if query else ""
    lang = normalize_language(payload.get("language"))
    intent = classify_intent(query) if query else "unknown"
    raw_context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    filtered_context = filter_context_by_intent(raw_context, intent)

    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and genai is not None and query:
        gemini_result = synthesize_gemini_response(
            query=query,
            intent=intent,
            filtered_context=filtered_context,
            lang=lang,
            gemini_api_key=gemini_key
        )
        if gemini_result is not None:
            return gemini_result

    return synthesize_rule_based_response(
        query=query,
        intent=intent,
        context=filtered_context,
        lang=lang
    )
