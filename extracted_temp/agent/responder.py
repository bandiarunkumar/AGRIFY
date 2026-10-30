"""
AGRIFY Agent — Enhanced Response Generator
Module: backend/agent/responder.py

Generates context-aware spoken + display responses using the rich, trust-labeled
context produced by context.py.

Priority order:
  1. If Gemini API key is set → try Gemini with fact-anchored prompt
  2. If Gemini fails or key absent → enhanced rule-based engine (this file)
  3. If rule-based fails → minimal safe fallback

The rule-based engine now uses REAL data from tool results:
  - Actual temperature, humidity, description from OpenWeatherMap
  - Actual soil N/P/K from SoilGrids
  - Actual mandi prices from Agmarknet
  - ML-ranked crop recommendations
  - ML-based fertilizer with NPK and stage guide
  - Generated alerts from the alert engine

Return contract is IDENTICAL to the existing /api/assistant/query contract
so the frontend (voiceAssistantModal.js) requires zero changes.
"""

import os
import re
import json
from datetime import datetime, timezone
from typing import Optional

from .context import get_trusted_weather, get_trusted_soil, get_trusted_market, get_active_alerts


# ============================================================
# LOCALIZATION TEMPLATES
# ============================================================
T = {
    "en": {
        "disclaimer": (
            "Advisory guidance based on verified AGRIFY agricultural models. "
            "Verify critical field applications with your local KVK extension officer."
        ),
        "source_note_live":    "Source: OpenWeatherMap live data.",
        "source_note_soil":    "Source: SoilGrids ISRIC satellite data.",
        "source_note_market":  "Source: Agmarknet (data.gov.in).",
        "source_note_ref":     "Reference estimate — verify at local mandi.",
        "source_note_ml":      "Based on AGRIFY ML models.",
        "no_location":         (
            "For location-specific answers, please run the Farm Analyzer "
            "with your GPS location, or check the Weather tab for current forecasts."
        ),
        "no_weather":          (
            "Live weather data is currently unavailable for your location. "
            "Check your internet connection or use the Weather tab for the latest forecast."
        ),
        "no_market":           (
            "Agmarknet data is temporarily unavailable. "
            "Check the Market tab or visit your local mandi for current prices."
        ),
    },
    "te": {
        "disclaimer": (
            "ధృవీకరించబడిన AGRIFY వ్యవసాయ సమాచారం ఆధారంగా అందించబడిన సలహా. "
            "రసాయన వాడకానికి ముందు స్థానిక KVK అధికారిని సంప్రదించండి."
        ),
        "source_note_live":    "మూలం: OpenWeatherMap తాజా సమాచారం.",
        "source_note_soil":    "మూలం: SoilGrids ISRIC ఉపగ్రహ సమాచారం.",
        "source_note_market":  "మూలం: Agmarknet (data.gov.in).",
        "source_note_ref":     "అంచనా ధర — స్థానిక మండిలో నిర్ధారించుకోండి.",
        "source_note_ml":      "AGRIFY ML నమూనాల ఆధారంగా.",
        "no_location":         (
            "స్థాన ఆధారిత సమాచారం కోసం GPS తో ఫార్మ్ అనాలైజర్ నడిపించండి "
            "లేదా మీ నగరం పేరు చెప్పండి."
        ),
        "no_weather":          (
            "మీ ప్రాంతానికి తాజా వాతావరణ సమాచారం అందుబాటులో లేదు. "
            "ఇంటర్నెట్ కనెక్షన్ తనిఖీ చేయండి లేదా వెదర్ ట్యాబ్ వాడండి."
        ),
        "no_market":           (
            "Agmarknet డేటా అందుబాటులో లేదు. "
            "మార్కెట్ ట్యాబ్ లేదా స్థానిక మండిలో ధరలు తనిఖీ చేయండి."
        ),
    },
    "hi": {
        "disclaimer": (
            "सत्यापित AGRIFY कृषि मॉडल पर आधारित सलाहकार मार्गदर्शन। "
            "महत्वपूर्ण निर्णयों के लिए अपने स्थानीय KVK अधिकारी से परामर्श लें।"
        ),
        "source_note_live":    "स्रोत: OpenWeatherMap लाइव डेटा।",
        "source_note_soil":    "स्रोत: SoilGrids ISRIC सैटेलाइट डेटा।",
        "source_note_market":  "स्रोत: Agmarknet (data.gov.in)।",
        "source_note_ref":     "संदर्भ अनुमान — स्थानीय मंडी से सत्यापित करें।",
        "source_note_ml":      "AGRIFY ML मॉडल के आधार पर।",
        "no_location":         (
            "स्थान-विशिष्ट उत्तर के लिए GPS के साथ Farm Analyzer चलाएं "
            "या अपने शहर का नाम बताएं।"
        ),
        "no_weather":          (
            "आपके स्थान के लिए लाइव मौसम डेटा उपलब्ध नहीं है। "
            "इंटरनेट कनेक्शन जांचें या Weather Tab देखें।"
        ),
        "no_market":           (
            "Agmarknet डेटा अस्थायी रूप से अनुपलब्ध है। "
            "Market Tab या स्थानीय मंडी में मौजूदा भाव देखें।"
        ),
    },
}

def _t(lang: str, key: str) -> str:
    return T.get(lang, T["en"]).get(key, T["en"].get(key, ""))


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def generate_response(plan, rich_context: dict) -> dict:
    """
    Generate the full response dict for the given plan and rich context.

    Phase 3F-1: Delegates AI generation to ModelGateway (provider-agnostic).
    ModelGateway tries primary provider -> secondary provider -> None.
    On None, falls back to the deterministic rule-based engine.

    Returns the same contract as the existing /api/assistant/query endpoint.
    """
    try:
        from .gateway import ModelGateway, AIRequest, AGRIFY_AGENT_SYSTEM_PROMPT

        facts = _build_gemini_facts(rich_context)
        lang = rich_context.get("language", "en")
        intent = rich_context.get("intent", "general_agriculture")
        query = rich_context.get("query", "")

        request = AIRequest(
            system_prompt=AGRIFY_AGENT_SYSTEM_PROMPT,
            user_content=(
                f"Farmer query: {query}\n"
                f"Detected intent: {intent}"
            ),
            verified_facts=facts,
            intent=intent,
            language=lang,
            temperature=0.15,
            response_mime_type="application/json",
        )

        gateway = ModelGateway()
        ai_result = gateway.query(request)

        if ai_result is not None:
            return _ai_result_to_response(ai_result, rich_context)

    except Exception as exc:
        print(f"[AGRIFY Responder] Gateway error: {type(exc).__name__} — using rule engine")

    return _rule_based_response(plan, rich_context)


def _ai_result_to_response(ai_result, ctx: dict) -> dict:
    """
    Map an AIResult from the gateway into the existing /api/assistant/query
    response contract. Structure is identical to what _gemini_response() produced.
    """
    lang = ctx.get("language", "en")
    return {
        "status": "success",
        "source": ai_result.source,
        "language": lang,
        "intent": ctx.get("intent"),
        "spoken_response": ai_result.spoken_response,
        "display_card": ai_result.display_card,
        "expert_escalation": ai_result.expert_escalation,
        "disclaimer": ai_result.disclaimer or _t(lang, "disclaimer"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# RULE-BASED RESPONSE ENGINE (enhanced — uses real data)
# ============================================================
def _rule_based_response(plan, ctx: dict) -> dict:
    """
    Produce a context-aware response using real data from tool results.
    """
    intent = ctx.get("intent", "general_agriculture")
    lang = ctx.get("language", "en")
    loc = ctx.get("location_str", "Your Field")
    crop = ctx.get("active_crop", "crop")
    season = ctx.get("season", "Kharif")

    handler = {
        "weather":           _respond_weather,
        "irrigation":        _respond_irrigation,
        "market":            _respond_market,
        "fertilizer":        _respond_fertilizer,
        "crop":              _respond_crop,
        "alerts":            _respond_alerts,
        "plant_health":      _respond_plant_health,
        "farm_analysis":     _respond_farm_analysis,
        "action_plan":       _respond_action_plan,
        "general_agriculture": _respond_general,
        "unknown":           _respond_unknown,
    }.get(intent, _respond_general)

    try:
        return handler(ctx, lang, loc, crop, season)
    except Exception as e:
        print(f"[AGRIFY Responder] Rule engine error in {intent}: {e}")
        return _respond_general(ctx, lang, loc, crop, season)


# ============================================================
# INTENT HANDLERS
# ============================================================

def _respond_weather(ctx, lang, loc, crop, season):
    weather = get_trusted_weather(ctx)
    forecast_sec = ctx.get("forecast", {})
    forecast_data = (forecast_sec.get("data") or {}).get("forecast") or []
    advisory_list = (forecast_sec.get("data") or {}).get("advisory") or []

    if weather and weather.get("temperature") is not None:
        temp   = weather["temperature"]
        hum    = weather.get("humidity", "—")
        desc   = weather.get("description", "")
        rain   = weather.get("rainfall", 0)
        wind   = weather.get("wind_speed", "—")
        ts     = weather.get("fetch_timestamp", "")

        # 5-day summary
        if forecast_data:
            total_rain = sum(d.get("rainfall_total", 0) for d in forecast_data)
            max_temp   = max((d.get("temp_max", 0) for d in forecast_data), default=0)

            # Best spray day: first dry day with low wind
            spray_day = None
            for d in forecast_data:
                if d.get("rainfall_total", 1) < 2 and d.get("wind_avg", 20) < 15:
                    spray_day = d.get("day", "")
                    break

            forecast_part = (
                f" Over the next 5 days, expect {total_rain:.0f}mm total rainfall"
                f" with a high of {max_temp:.0f}°C."
            )
            if spray_day:
                forecast_part += f" Best day for spraying: {spray_day}."
        else:
            forecast_part = ""

        # Top advisory
        top_adv = ""
        danger_adv = [a for a in advisory_list if a.get("type") == "danger"]
        if danger_adv:
            top_adv = f" ⚠️ {danger_adv[0]['message']}"
        elif advisory_list:
            top_adv = f" {advisory_list[0]['message']}"

        spoken = {
            "en": f"Current weather in {loc}: {temp}°C, humidity {hum}%, {desc}.{forecast_part}{top_adv}",
            "te": f"{loc}లో ప్రస్తుత వాతావరణం: {temp}°C, తేమ {hum}%, {desc}.{forecast_part}{top_adv}",
            "hi": f"{loc} में अभी: {temp}°C, आर्द्रता {hum}%, {desc}.{forecast_part}{top_adv}",
        }.get(lang, f"Current weather in {loc}: {temp}°C, humidity {hum}%, {desc}.{forecast_part}")

        key_points = [
            f"🌡️ Temperature: {temp}°C (feels like {weather.get('feels_like', temp)}°C)",
            f"💧 Humidity: {hum}%  |  Wind: {wind} m/s",
            f"🌦️ Condition: {desc}",
        ]
        if forecast_data:
            key_points.append(f"📅 5-Day Rainfall: {total_rain:.0f}mm expected")
        for adv in advisory_list[:2]:
            key_points.append(f"{'⚠️' if adv['type'] in ('danger','warning') else '✅'} {adv['title']}: {adv['message'][:80]}")

        action_pill = {"label": "View 5-Day Forecast", "action": "navigate_weather"}
        category = "Weather Intelligence"
        title = f"Live Weather — {loc}"
        trust_note = _t(lang, "source_note_live")

    else:
        # No live weather — give useful guidance
        err = (ctx.get("current_weather") or {}).get("error", "")
        spoken_msg = _t(lang, "no_weather")
        if not ctx.get("lat"):
            spoken_msg = _t(lang, "no_location")

        spoken = spoken_msg
        key_points = [
            "Live weather data not available for your location",
            err or "Check internet connection or GPS access",
            "Weather tab has 5-day forecast with farming advisories",
        ]
        action_pill = {"label": "Open Weather Tab", "action": "navigate_weather"}
        category = "Weather Advisory"
        title = "Weather Status"
        trust_note = ""

    return _build_response(
        intent="weather", lang=lang, spoken=spoken,
        title=title, category=category,
        key_points=key_points, action_pill=action_pill,
        escalate=False, trust_note=trust_note,
    )


def _respond_irrigation(ctx, lang, loc, crop, season):
    weather = get_trusted_weather(ctx)
    soil = get_trusted_soil(ctx)
    client_irr = ((ctx.get("client") or {}).get("irrigation_guidance") or {})

    # Build irrigation picture from available data
    has_trusted_irr = bool(client_irr.get("recommendation"))
    moisture = None
    net_irr  = None
    rec      = None
    method   = "Drip"

    if has_trusted_irr:
        rec     = client_irr.get("recommendation", "")
        net_irr = client_irr.get("net_irrigation_needed_mm_day")
        method  = client_irr.get("irrigation_method", "Drip")
        moisture = client_irr.get("soil_moisture_pct")

    if soil:
        moisture = moisture or soil.get("moisture_pct")

    if weather:
        rain = weather.get("rainfall", 0)
        temp = weather.get("temperature", 28)
        # Rough ETo-based calculation if no client guidance
        if not has_trusted_irr:
            kc = {"rice": 1.2, "wheat": 0.7, "maize": 0.85, "cotton": 0.9}.get(crop.lower(), 0.8)
            et0 = 0.6 * temp
            etc = et0 * kc
            rain_contrib = min(rain / 30, etc)
            net_irr_calc = max(0, etc - rain_contrib - ((moisture or 40) - 30) * 0.5)
            if not rec:
                if net_irr_calc < 1:
                    rec = f"No irrigation needed — rain forecast covers {crop} water needs."
                elif net_irr_calc < 5:
                    rec = f"Irrigate {net_irr_calc:.1f}mm/day. Early morning (6–8 AM) recommended."
                else:
                    rec = f"URGENT: Irrigate {net_irr_calc:.1f}mm/day. High water stress risk."
                net_irr = round(net_irr_calc, 1)

    if rec:
        net_str = f" Using {method} method, net requirement is {net_irr} mm/day." if net_irr is not None else f" Recommended method: {method}."
        spoken = {
            "en": f"Irrigation guidance for {crop} in {loc}: {rec}{net_str}",
            "te": f"{loc}లో {crop} పంటకు నీటి సలహా: {rec} {method} పద్ధతిలో రోజుకు {net_irr or 3} మి.మీ. నీరు అవసరం.",
            "hi": f"{loc} में {crop} के लिए सिंचाई सलाह: {rec} {method} विधि से प्रतिदिन {net_irr or 3} मिमी पानी की आवश्यकता है।",
        }.get(lang, f"Irrigation: {rec}{net_str}")

        key_points = []
        if moisture:
            key_points.append(f"💧 Soil Moisture: {moisture:.0f}%")
        if net_irr is not None:
            key_points.append(f"🚿 Net Requirement: {net_irr}mm/day via {method}")
        if weather:
            key_points.append(f"🌧️ Current Rainfall: {weather.get('rainfall', 0):.1f}mm/hr")
        key_points.append("⏰ Best time: 6–8 AM to minimize evaporation")

        action_pill = {"label": "Full Farm Analysis", "action": "navigate_analysis"}
    else:
        spoken = {
            "en": f"For {crop}, maintain adequate soil moisture and use drip irrigation between 6–8 AM to minimize evaporation. Run the Farm Analyzer for a field-specific water schedule.",
            "te": f"{crop}కు తగిన తేమ నిర్వహించండి. నష్టం తగ్గించడానికి ఉదయం 6-8 గంటలకు డ్రిప్ సేద్యం వాడండి.",
            "hi": f"{crop} के लिए पर्याप्त मिट्टी की नमी बनाए रखें। वाष्पीकरण कम करने के लिए सुबह 6-8 बजे ड्रिप सिंचाई करें।",
        }.get(lang, f"Maintain adequate moisture for {crop}. Use drip irrigation at 6–8 AM.")

        key_points = [
            f"No precise field data available for {crop}",
            "Run Farm Analyzer for GPS-based irrigation schedule",
            "General: Water in early morning to reduce evaporation",
        ]
        action_pill = {"label": "Run Farm Analyzer", "action": "navigate_analysis"}

    return _build_response(
        intent="irrigation", lang=lang, spoken=spoken,
        title=f"{crop.title()} Irrigation Schedule",
        category="Irrigation Management",
        key_points=key_points, action_pill=action_pill,
        escalate=False,
    )


def _respond_market(ctx, lang, loc, crop, season):
    market_sec = get_trusted_market(ctx)

    if market_sec:
        data = market_sec.get("data", {})
        trust = market_sec.get("trust_level", "reference_estimate")
        crop_name = data.get("commodity") or data.get("crop") or crop

        if data.get("is_reference"):
            # Config reference fallback
            ref_price = data.get("reference_price", 25)
            spoken = {
                "en": f"Agmarknet is temporarily unavailable. Reference price for {crop_name}: approximately ₹{ref_price}/kg. Verify at your local mandi before selling.",
                "te": f"Agmarknet అందుబాటులో లేదు. {crop_name} అంచనా ధర: సుమారు ₹{ref_price}/కిలో. అమ్మకానికి ముందు స్థానిక మండి నిర్ధారించండి.",
                "hi": f"Agmarknet अनुपलब्ध है। {crop_name} का अनुमानित भाव: लगभग ₹{ref_price}/kg। बेचने से पहले स्थानीय मंडी से पुष्टि करें।",
            }.get(lang, f"Reference price for {crop_name}: ~₹{ref_price}/kg. Verify at mandi.")

            key_points = [
                f"Reference price: ₹{ref_price}/kg (config estimate)",
                "Not a live mandi quote — verify before selling",
                "Market tab has live Agmarknet feed when available",
            ]
            action_pill = {"label": "Check Market Prices", "action": "navigate_market"}
            title = f"{crop_name.title()} Price Reference"
            category = "Market Intelligence"

        else:
            # Real Agmarknet data
            avg_price = data.get("avg_price_per_kg", 0)
            min_price = data.get("min_price_per_kg", 0)
            max_price = data.get("max_price_per_kg", 0)
            best_mkt_raw = data.get("best_market", "")
            # best_market may be a dict {name, state, ...} or a plain string
            if isinstance(best_mkt_raw, dict):
                best_mkt = best_mkt_raw.get("name") or best_mkt_raw.get("market") or ""
            else:
                best_mkt = str(best_mkt_raw) if best_mkt_raw else ""
            markets   = data.get("markets", [])
            n_markets = data.get("total_markets_reporting", len(markets))
            fetch_ts  = data.get("fetch_timestamp", "")
            is_fallback = data.get("is_fallback", False)
            data_note = "Telangana mandi database" if is_fallback else "Agmarknet data.gov.in"

            spoken = {
                "en": (
                    f"Today's mandi price for {crop_name}: average ₹{avg_price:.0f}/kg, "
                    f"ranging from ₹{min_price:.0f} to ₹{max_price:.0f}/kg across {n_markets} markets."
                    + (f" Best price at {best_mkt}." if best_mkt else "")
                    + (f" Data from {data_note}." if is_fallback else "")
                ),
                "te": (
                    f"{crop_name} నేటి మండి ధర: సగటు ₹{avg_price:.0f}/కిలో, "
                    f"₹{min_price:.0f} నుండి ₹{max_price:.0f} వరకు {n_markets} మండీలలో."
                    + (f" అత్యుత్తమ ధర: {best_mkt}." if best_mkt else "")
                ),
                "hi": (
                    f"{crop_name} का आज का मंडी भाव: औसत ₹{avg_price:.0f}/kg, "
                    f"₹{min_price:.0f} से ₹{max_price:.0f}/kg — {n_markets} मंडियों में।"
                    + (f" सबसे अच्छा भाव: {best_mkt}।" if best_mkt else "")
                ),
            }.get(lang, f"Today's average price for {crop_name}: ₹{avg_price:.0f}/kg.")

            key_points = [
                f"📊 Average: ₹{avg_price:.0f}/kg",
                f"📈 Range: ₹{min_price:.0f} – ₹{max_price:.0f}/kg",
            ]
            if best_mkt:
                key_points.append(f"🏆 Best market: {best_mkt}")
            key_points.append(f"🏪 {n_markets} markets reporting — {data_note}")
            if fetch_ts:
                key_points.append(f"🕐 Updated: {fetch_ts[:10]}")

            action_pill = {"label": "Explore All Mandi Rates", "action": "navigate_market"}
            title = f"{crop_name.title()} — Mandi Prices Today"
            category = "Market Intelligence"
    else:
        spoken = {
            "en": _t(lang, "no_market"),
            "te": _t("te", "no_market"),
            "hi": _t("hi", "no_market"),
        }.get(lang, _t("en", "no_market"))
        key_points = ["Market data unavailable", "Check Market tab or local mandi"]
        action_pill = {"label": "Open Market Tab", "action": "navigate_market"}
        title = "Market Price Status"
        category = "Market Intelligence"
        trust = "unavailable"

    return _build_response(
        intent="market", lang=lang, spoken=spoken,
        title=title, category=category,
        key_points=key_points, action_pill=action_pill,
        escalate=False,
        trust_note=_t(lang, "source_note_market") if (market_sec and not (market_sec.get("data") or {}).get("is_reference")) else _t(lang, "source_note_ref"),
    )


def _respond_fertilizer(ctx, lang, loc, crop, season):
    fert_sec = ctx.get("fertilizer", {})
    fert_data = fert_sec.get("data") or {}
    trust = fert_sec.get("trust_level", "unavailable")
    soil = get_trusted_soil(ctx)

    client_fert = (ctx.get("client") or {}).get("fertilizer_recommendation") or {}
    rec_fert = client_fert.get("recommended_fertilizer") or {}

    if isinstance(rec_fert, dict) and rec_fert.get("fertilizer"):
        fert_name = rec_fert["fertilizer"]
        details = rec_fert.get("details") or {}
        qty = details.get("qty_per_ha", 50)
        npk = details.get("npk", "N/A")
        stages = client_fert.get("stage_wise_application") or []
        stage = stages[0].get("stage", "Basal") if stages and isinstance(stages[0], dict) else "Basal"
        has_trusted_dosage = True
    elif client_fert.get("fertilizer"):
        fert_name = client_fert["fertilizer"]
        qty = client_fert.get("qty_per_ha") or client_fert.get("quantity_per_hectare") or 50
        npk = client_fert.get("npk") or client_fert.get("npk_ratio") or "N/A"
        stage = client_fert.get("stage", "Basal")
        has_trusted_dosage = True
    elif fert_data.get("fertilizer") and trust in ("ml_model", "rule_based") and ctx.get("soil", {}).get("trust_level") in ("soilgrids", "user_entered"):
        fert_name = fert_data["fertilizer"]
        npk = fert_data.get("npk", "N/A")
        qty = fert_data.get("qty_per_ha", 50)
        stage = "Basal"
        has_trusted_dosage = True
    else:
        has_trusted_dosage = False

    if has_trusted_dosage:
        spoken = {
            "en": (
                f"According to your AGRIFY analysis, {qty} kg/ha of {fert_name} ({npk}) is recommended for {crop} at {stage} stage. "
                f"Always split the dose — apply in stages as prescribed. "
                f"Verify quantities with your local KVK before application."
            ),
            "te": (
                f"{loc}లో {crop} కోసం {stage} దశలో {qty} kg/ha {fert_name} ({npk}) సిఫారసు చేయబడింది. "
                f"ఒకేసారి వేయకుండా దశలవారీగా వేయండి. "
                f"రసాయనాలు వేసే ముందు స్థానిక KVK నిర్ధారించుకోండి."
            ),
            "hi": (
                f"{loc} में {crop} के लिए {stage} अवस्था में {qty} किग्रा/हेक्टेयर {fert_name} ({npk}) अनुशंसित है। "
                f"मात्रा को विभाजित करके डालें। उपयोग से पहले स्थानीय KVK से सत्यापित करें।"
            ),
        }.get(lang, f"Recommended fertilizer for {crop}: {fert_name} at {qty} kg/ha.")

        key_points = [
            f"Recommended: {fert_name} ({npk})",
            f"Qty: {qty} kg/ha at {stage} stage",
        ]
        if soil:
            key_points.append(
                f"Soil: N={soil.get('N','—')}, P={soil.get('P','—')}, "
                f"K={soil.get('K','—')}, pH={soil.get('ph','—')}"
            )
        key_points.append("⚠️ Verify dosage with KVK before chemical application")

        return _build_response(
            intent="fertilizer", lang=lang, spoken=spoken,
            title=f"{fert_name} Guide — {crop.title()}",
            category="Nutrient Management",
            key_points=key_points,
            action_pill={"label": "View Farm Analysis", "action": "navigate_analysis"},
            escalate=False,
        )
    else:
        spoken = {
            "en": f"Your farm in {loc} does not have a verified fertilizer dosage in active analysis. Please verify with your local agricultural extension officer or KVK before applying chemical fertilizers.",
            "te": f"{loc}లో మీ పొలానికి ధృవీకరించబడిన ఎరువుల మోతాదు అందుబాటులో లేదు. రసాయన ఎరువులు వేసే ముందు స్థానిక KVK లేదా వ్యవసాయ అధికారిని సంప్రదించండి.",
            "hi": f"{loc} में आपके खेत के लिए सत्यापित उर्वरक मात्रा उपलब्ध नहीं है। रासायनिक खाद डालने से पहले अपने स्थानीय कृषि विस्तार अधिकारी या KVK से सलाह लें।",
        }.get(lang, f"Your farm in {loc} does not have a verified fertilizer dosage in active analysis. Please consult local KVK.")

        key_points = [
            f"Target crop: {crop}",
            "No verified field dosage in active analysis",
            "Soil testing at local KVK recommended before application",
        ]
        return _build_response(
            intent="fertilizer", lang=lang, spoken=spoken,
            title="Nutrient Dosage Advisory",
            category="Nutrient Management",
            key_points=key_points,
            action_pill={"label": "Run Farm Analyzer", "action": "navigate_analysis"},
            escalate=True,
            suggested_q=f"What is the recommended NPK dosage for {crop} based on local soil conditions?",
        )


def _respond_crop(ctx, lang, loc, crop, season):
    crop_sec = ctx.get("crop", {})
    crop_data = crop_sec.get("data") or {}
    trust = crop_sec.get("trust_level", "unavailable")

    top_3 = crop_data.get("top_3") or []
    best = (crop_data.get("best_crop") or top_3[0] if top_3 else {})

    if best and best.get("crop"):
        best_crop_name = best["crop"]
        conf = best.get("confidence", 0)
        others = [c["crop"] for c in (top_3[1:3] if len(top_3) > 1 else []) if isinstance(c, dict) and c.get("crop")]
        others_str = ", ".join(c.title() for c in others)

        spoken = {
            "en": (
                f"For {season} season in {loc}, AGRIFY recommends {best_crop_name.title()} as the top crop"
                + (f" with {conf:.0f}% model confidence" if conf > 10 else "")
                + (f". Alternatives: {others_str}." if others_str else ".")
                + " Verify with your local KVK for certified high-yield varieties."
            ),
            "te": (
                f"{loc}లో {season} సీజన్‌కు AGRIFY {best_crop_name.title()} పంట సిఫారసు చేస్తోంది"
                + (f" ({conf:.0f}% నమూనా నమ్మకం)" if conf > 10 else "")
                + (f". ప్రత్యామ్నాయాలు: {others_str}." if others_str else ".")
                + " అత్యధిక దిగుబడి రకాల కోసం KVK సంప్రదించండి."
            ),
            "hi": (
                f"{loc} में {season} मौसम के लिए AGRIFY {best_crop_name.title()} की सिफारिश करता है"
                + (f" ({conf:.0f}% मॉडल विश्वास)" if conf > 10 else "")
                + (f"। विकल्प: {others_str}।" if others_str else "।")
                + " उच्च उपज वाली किस्मों के लिए KVK से संपर्क करें।"
            ),
        }.get(lang, f"Recommended crop for {season} in {loc}: {best_crop_name.title()}.")

        key_points = [f"🌱 Top pick: {best_crop_name.title()}"]
        if conf > 10:
            key_points.append(f"📊 Model confidence: {conf:.0f}%")
        if others:
            key_points.append(f"🔄 Alternatives: {others_str}")
        key_points.append(f"📅 Season: {season} | Region: {loc}")

    else:
        season_crops = {"Kharif": "Rice, Cotton, Maize", "Rabi": "Wheat, Chickpea, Mustard", "Zaid": "Maize, Mungbean"}
        spoken = {
            "en": f"For {season} season in {loc}, common crops include {season_crops.get(season, 'Rice, Wheat, Maize')}. Run Farm Analyzer with your GPS for a personalized recommendation.",
            "te": f"{loc}లో {season} సీజన్‌కు సాధారణ పంటలు: {season_crops.get(season, 'వరి, గోధుమ, మొక్కజొన్న')}. వ్యక్తిగత సలహా కోసం GPS తో ఫార్మ్ అనాలైజర్ నడిపించండి.",
            "hi": f"{loc} में {season} के लिए सामान्य फसलें: {season_crops.get(season, 'धान, गेहूं, मक्का')}। व्यक्तिगत सुझाव के लिए Farm Analyzer चलाएं।",
        }.get(lang, f"Common {season} crops: {season_crops.get(season, 'Rice, Wheat, Maize')}.")

        key_points = [
            f"Season: {season}",
            f"Common picks: {season_crops.get(season, 'Rice, Wheat, Maize')}",
            "Run Farm Analyzer for soil + GPS based recommendation",
        ]

    return _build_response(
        intent="crop", lang=lang, spoken=spoken,
        title=f"Crop Suitability — {season} Season",
        category="Crop Advisory",
        key_points=key_points,
        action_pill={"label": "Full Crop Analysis", "action": "navigate_analysis"},
        escalate=False,
        trust_note=_t(lang, "source_note_ml") if trust == "ml_model" else "",
    )


def _respond_alerts(ctx, lang, loc, crop, season):
    active = get_active_alerts(ctx, ("danger", "warning", "info"))
    danger = [a for a in active if a.get("severity") == "danger"]
    warnings = [a for a in active if a.get("severity") == "warning"]
    tips = [a for a in active if a.get("severity") in ("info", "tip")]

    if danger:
        top = danger[0]
        spoken = {
            "en": f"⚠️ URGENT alert for {loc}: {top['title']} — {top.get('message', '')} Check your alert dashboard immediately.",
            "te": f"⚠️ {loc}లో అత్యవసర హెచ్చరిక: {top['title']} — {top.get('message', '')} వెంటనే హెచ్చరిక డాష్‌బోర్డ్ చూడండి.",
            "hi": f"⚠️ {loc} के लिए अत्यावश्यक चेतावनी: {top['title']} — {top.get('message', '')} तुरंत अलर्ट डैशबोर्ड देखें।",
        }.get(lang, f"URGENT: {top['title']} — {top.get('message', '')}")
    elif warnings:
        top = warnings[0]
        spoken = {
            "en": f"Farm alert for {loc}: {top['title']} — {top.get('message', '')}",
            "te": f"{loc}లో పొలం హెచ్చరిక: {top['title']} — {top.get('message', '')}",
            "hi": f"{loc} के लिए खेत चेतावनी: {top['title']} — {top.get('message', '')}",
        }.get(lang, f"Alert: {top['title']} — {top.get('message', '')}")
    elif tips:
        top = tips[0]
        spoken = {
            "en": f"Farm conditions look normal for {loc}. Tip: {top.get('message', 'Regular farming schedule recommended.')}",
            "te": f"{loc}లో పొలం పరిస్థితులు సాధారణంగా ఉన్నాయి. చిట్కా: {top.get('message', '')}",
            "hi": f"{loc} में खेत की स्थिति सामान्य है। सुझाव: {top.get('message', '')}",
        }.get(lang, f"Normal conditions. {top.get('message', '')}")
    else:
        err = (ctx.get("alerts") or {}).get("error", "")
        if err or not ctx.get("lat"):
            spoken_msg = _t(lang, "no_location") if not ctx.get("lat") else f"Alert data unavailable: {err}"
        else:
            spoken_msg = {
                "en": f"No severe alerts active for {crop} in {loc}. Environmental conditions appear normal.",
                "te": f"{loc}లో {crop} పంటకు తీవ్రమైన హెచ్చరికలు లేవు. పరిస్థితులు సాధారణంగా ఉన్నాయి.",
                "hi": f"{loc} में {crop} के लिए कोई गंभीर चेतावनी नहीं है। स्थिति सामान्य लग रही है।",
            }.get(lang, f"No severe alerts for {crop} in {loc}.")
        spoken = spoken_msg

    key_points = []
    for a in (danger + warnings)[:3]:
        icon = "🚨" if a["severity"] == "danger" else "⚠️"
        key_points.append(f"{icon} {a['title']}: {(a.get('message') or '')[:90]}")
    for tip in tips[:2]:
        key_points.append(f"✅ {tip['title']}: {(tip.get('message') or '')[:80]}")
    if not key_points:
        key_points = ["No active danger or warning alerts", f"All parameters normal for {crop}"]

    return _build_response(
        intent="alerts", lang=lang, spoken=spoken,
        title="Active Farm Alerts",
        category="Farm Protection",
        key_points=key_points,
        action_pill={"label": "Open Alert Center", "action": "navigate_alerts"},
        escalate=bool(danger),
        suggested_q=f"What protective actions should I take for {crop} against the current weather risk?" if danger else None,
    )


def _respond_plant_health(ctx, lang, loc, crop, season):
    weather = get_trusted_weather(ctx)
    humidity_risk = weather and weather.get("humidity", 0) > 80

    humidity_note = ""
    if humidity_risk:
        humidity_note = {
            "en": f" Current humidity is {weather['humidity']}% — elevated fungal risk. Pre-emptive fungicide spray may be warranted.",
            "te": f" ప్రస్తుత తేమ {weather['humidity']}% — శిలీంద్ర వ్యాధి ప్రమాదం ఉంది. నివారణ మందు చల్లండి.",
            "hi": f" वर्तमान आर्द्रता {weather['humidity']}% — फंगल रोग का खतरा। रोकथाम के लिए फफूंदनाशी का छिड़काव करें।",
        }.get(lang, "")

    spoken = {
        "en": f"The symptoms you described on {crop} may be consistent with early stress, foliar blight, or nutrient deficiency.{humidity_note} Upload a clear leaf photo in Crop Doctor for AI visual analysis. Physical confirmation by your local agriculture officer is recommended before any treatment.",
        "te": f"{crop} పంటపై మీరు వివరించిన లక్షణాలు తెగులు లేదా పోషక లోపానికి సంబంధించినవి కావచ్చు.{humidity_note} ఆకు ఫోటో క్రాప్ డాక్టర్‌లో అప్‌లోడ్ చేయండి. నిర్ధారణ కోసం వ్యవసాయ అధికారి సంప్రదించండి.",
        "hi": f"{crop} पर बताए गए लक्षण तनाव, फंगस या पोषण की कमी से हो सकते हैं।{humidity_note} Crop Doctor में पत्ती की स्पष्ट फोटो अपलोड करें। उपचार से पहले कृषि अधिकारी से पुष्टि कराएं।",
    }.get(lang, f"Symptoms on {crop} need physical confirmation. Use Crop Doctor for AI diagnosis.")

    return _build_response(
        intent="plant_health", lang=lang, spoken=spoken,
        title=f"{crop.title()} Plant Health Advisory",
        category="Plant Health",
        key_points=[
            "Symptoms need physical confirmation before any treatment",
            "Upload leaf photo in Crop Doctor for AI visual analysis",
            "Do NOT apply pesticide without confirmed diagnosis",
            f"{'⚠️ High humidity — elevated fungal risk' if humidity_risk else 'Monitor plants daily for disease progression'}",
        ],
        action_pill={"label": "Open Crop Doctor", "action": "navigate_cropDoctor"},
        escalate=True,
        suggested_q=f"What are the early symptoms of leaf blight vs nutrient deficiency in {crop}?",
    )


def _respond_farm_analysis(ctx, lang, loc, crop, season):
    weather = get_trusted_weather(ctx)
    soil = get_trusted_soil(ctx)
    fert_data = (ctx.get("fertilizer") or {}).get("data") or {}
    crop_data = (ctx.get("crop") or {}).get("data") or {}
    alerts = get_active_alerts(ctx, ("danger", "warning"))

    summary_parts = [f"Farm analysis for {crop.title()} in {loc} ({season} season)."]
    if weather:
        summary_parts.append(f"Weather: {weather.get('temperature')}°C, {weather.get('description', '')}.")
    if soil:
        summary_parts.append(f"Soil: N={soil.get('N','—')}, P={soil.get('P','—')}, K={soil.get('K','—')}, pH={soil.get('ph','—')}.")
    if fert_data.get("fertilizer"):
        summary_parts.append(f"Recommended fertilizer: {fert_data['fertilizer']}.")
    if alerts:
        summary_parts.append(f"{len(alerts)} active alert(s).")

    spoken = " ".join(summary_parts)
    if lang == "te":
        spoken = {
            "en": spoken,
            "te": f"{loc}లో {crop.title()} పంట ఫార్మ్ విశ్లేషణ సిద్ధంగా ఉంది. " + (f"వాతావరణం: {weather.get('temperature')}°C. " if weather else "") + (f"నేల: N={soil.get('N','—')}, pH={soil.get('ph','—')}." if soil else ""),
        }.get("te", spoken)
    elif lang == "hi":
        spoken = f"{loc} में {crop.title()} फसल का फार्म विश्लेषण तैयार है। " + (f"मौसम: {weather.get('temperature')}°C। " if weather else "") + (f"मिट्टी: N={soil.get('N','—')}, pH={soil.get('ph','—')}।" if soil else "")

    key_points = []
    if weather:
        key_points.append(f"🌡️ {weather.get('temperature')}°C | {weather.get('humidity')}% humidity | {weather.get('description','')}")
    if soil:
        key_points.append(f"🌱 Soil N={soil.get('N','—')}, P={soil.get('P','—')}, K={soil.get('K','—')}, pH={soil.get('ph','—')}")
    if fert_data.get("fertilizer"):
        key_points.append(f"💊 Fertilizer: {fert_data['fertilizer']} ({fert_data.get('npk','N/A')})")
    for a in alerts[:2]:
        key_points.append(f"⚠️ {a['title']}")

    return _build_response(
        intent="farm_analysis", lang=lang, spoken=spoken,
        title=f"Farm Analysis — {crop.title()} | {loc}",
        category="Farm Intelligence",
        key_points=key_points[:4],
        action_pill={"label": "Full Farm Report", "action": "navigate_analysis"},
        escalate=False,
    )


def _respond_action_plan(ctx, lang, loc, crop, season):
    client_ap = (ctx.get("client") or {}).get("action_plan") or {}
    immediate_actions = client_ap.get("immediate_actions") or []
    top_act = None
    if immediate_actions and isinstance(immediate_actions, list) and isinstance(immediate_actions[0], dict):
        top_act = immediate_actions[0].get("title")

    if top_act:
        spoken = {
            "en": f"A 7-day action plan is active for {crop}. Your top priority is: {top_act}.",
            "te": f"{crop} కోసం 7 రోజుల కార్యాచరణ ప్రణాళిక సిద్ధంగా ఉంది. మొదటి ప్రాధాన్యత: {top_act}.",
            "hi": f"{crop} के लिए 7-दिवसीय कार्य योजना सक्रिय है। आपकी मुख्य प्राथमिकता: {top_act} है।",
        }.get(lang, f"7-day action plan for {crop}. Priority: {top_act}.")
        key_points = [
            f"Immediate focus: {top_act}",
            f"Season: {season}",
            f"Location: {loc}",
        ]
    else:
        result = _respond_farm_analysis(ctx, lang, loc, crop, season)
        spoken = result["spoken_response"] + " Visit your Action Plan in the Farm Analyzer for a day-by-day task schedule."
        key_points = result["display_card"]["key_points"]

    return _build_response(
        intent="action_plan", lang=lang, spoken=spoken,
        title=f"7-Day Plan for {crop.title()}",
        category="Action Plan",
        key_points=key_points,
        action_pill={"label": "View 7-Day Plan", "action": "navigate_analysis"},
        escalate=False,
    )


def _respond_unknown(ctx, lang, loc, crop, season):
    spoken = {
        "en": "I did not quite understand. You can ask about crops, fertilizers, irrigation, weather, or mandi prices.",
        "te": "మీరు చెప్పింది నాకు అర్థం కాలేదు. పంటలు, ఎరువులు, నీటిపారుదల, వాతావరణం లేదా మార్కెట్ ధరల గురించి అడగండి.",
        "hi": "मैं आपकी बात पूरी तरह समझ नहीं पाया। आप फसल, खाद, सिंचाई, मौसम या मंडी भाव से संबंधित सवाल पूछ सकते हैं।",
    }.get(lang, "I did not understand. Ask about crops, fertilizers, irrigation, weather, or market prices.")

    return _build_response(
        intent="unknown", lang=lang, spoken=spoken,
        title="AGRIFY Copilot",
        category="Farmer Copilot",
        key_points=[
            "Ask about crops, fertilizers, irrigation, weather, or mandi prices",
            "Available in English, Telugu, and Hindi",
        ],
        action_pill={"label": "Open Farm Analyzer", "action": "navigate_analysis"},
        escalate=False,
    )


def _respond_general(ctx, lang, loc, crop, season):
    spoken = {
        "en": "I am AGRIFY Voice Copilot. I can assist with live weather, mandi prices, crop suitability, fertilizer guidance, irrigation scheduling, and farm alerts. Ask me a specific farming question!",
        "te": "నేను AGRIFY వాయిస్ సహాయకుడిని. వాతావరణం, మండి ధరలు, పంట సలహాలు, ఎరువులు, నీటిపారుదల మరియు హెచ్చరికలపై సహాయం చేస్తాను.",
        "hi": "मैं AGRIFY Voice Copilot सहायक हूँ। मैं लाइव मौसम, मंडी भाव, फसल सुझाव, उर्वरक, सिंचाई और कृषि चेतावनियों में मदद कर सकता हूँ।",
    }.get(lang, "I am AGRIFY Voice Copilot. Ask about crops, fertilizers, weather, irrigation, or market prices.")

    return _build_response(
        intent="general_agriculture", lang=lang, spoken=spoken,
        title="AGRIFY Farmer Copilot",
        category="Farmer Copilot",
        key_points=[
            "🌤️ Live weather & 5-day forecast",
            "📊 Real mandi prices from Agmarknet",
            "🌱 ML crop & fertilizer recommendations",
            "🚨 Farm alerts & irrigation guidance",
        ],
        action_pill={"label": "Open Farm Analyzer", "action": "navigate_analysis"},
        escalate=False,
    )


# ============================================================
# RESPONSE BUILDER (shared structure — matches existing contract)
# ============================================================
def _build_response(
    intent: str, lang: str,
    spoken: str, title: str, category: str,
    key_points: list, action_pill: Optional[dict],
    escalate: bool = False,
    suggested_q: Optional[str] = None,
    trust_note: str = "",
) -> dict:
    disclaimer = _t(lang, "disclaimer")
    if trust_note:
        disclaimer = f"{trust_note} {disclaimer}"

    return {
        "status": "success",
        "source": "rule_based_engine",
        "language": lang,
        "intent": intent,
        "spoken_response": spoken,
        "display_card": {
            "title": title,
            "category": category,
            "key_points": [str(p) for p in key_points[:4]],
            "action_pill": action_pill,
        },
        "expert_escalation": {
            "recommended": escalate,
            "suggested_question": suggested_q,
        },
        "disclaimer": disclaimer,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# LEGACY GEMINI LAYER — REPLACED BY ModelGateway in Phase 3F-1
# ============================================================
# _gemini_response() is retained as a reference stub only.
# It is no longer called by generate_response().
# ModelGateway (agent/gateway.py) now handles all AI provider calls.
# This stub is kept to avoid breaking any external callers that may
# reference _gemini_response() during transition, and will be removed
# in Phase 3F-2 cleanup.
def _gemini_response(plan, ctx: dict, gemini_key: str) -> Optional[dict]:
    """
    DEPRECATED — superseded by ModelGateway in Phase 3F-1.
    Kept as a reference stub only. Not called by generate_response().
    """
    # Delegate to gateway for backward compatibility if somehow called
    try:
        from .gateway import ModelGateway, AIRequest, AGRIFY_AGENT_SYSTEM_PROMPT
        lang = ctx.get("language", "en")
        intent = ctx.get("intent", "general_agriculture")
        facts = _build_gemini_facts(ctx)
        request = AIRequest(
            system_prompt=AGRIFY_AGENT_SYSTEM_PROMPT,
            user_content=f"Farmer query: {ctx.get('query', '')}\nDetected intent: {intent}",
            verified_facts=facts,
            intent=intent,
            language=lang,
        )
        result = ModelGateway().query(request)
        if result:
            return _ai_result_to_response(result, ctx)
    except Exception:
        pass
    return None


def _build_gemini_facts(ctx: dict) -> dict:
    """Extract a minimal, verified facts snapshot for the Gemini prompt."""
    facts: dict = {
        "intent": ctx.get("intent"),
        "crop": ctx.get("active_crop"),
        "location": ctx.get("location_str"),
        "season": ctx.get("season"),
    }

    weather = get_trusted_weather(ctx)
    if weather:
        facts["weather"] = {
            "temperature_c": weather.get("temperature"),
            "humidity_pct": weather.get("humidity"),
            "description": weather.get("description"),
            "rainfall_mm": weather.get("rainfall"),
            "wind_speed_ms": weather.get("wind_speed"),
            "trust": ctx.get("current_weather", {}).get("trust_level"),
        }

    fc = (ctx.get("forecast") or {}).get("data") or {}
    if fc.get("forecast"):
        days = fc["forecast"]
        facts["forecast_5day"] = {
            "total_rainfall_mm": round(sum(d.get("rainfall_total", 0) for d in days), 1),
            "max_temp_c": max((d.get("temp_max", 0) for d in days), default=None),
            "days": [{"date": d["date"], "day": d["day"], "rain_mm": d.get("rainfall_total", 0), "desc": d.get("description", "")} for d in days[:5]],
            "advisories": fc.get("advisory", []),
        }

    soil = get_trusted_soil(ctx)
    if soil:
        facts["soil"] = {
            "N": soil.get("N"),
            "P": soil.get("P"),
            "K": soil.get("K"),
            "ph": soil.get("ph"),
            "moisture_pct": soil.get("moisture_pct"),
            "trust": ctx.get("soil", {}).get("trust_level"),
        }

    market_sec = get_trusted_market(ctx)
    if market_sec and market_sec.get("data"):
        md = market_sec["data"]
        if md.get("is_reference"):
            facts["market"] = {
                "reference_price_per_kg": md.get("reference_price"),
                "note": "Reference estimate — not live Agmarknet data",
                "trust": "reference_estimate",
            }
        else:
            facts["market"] = {
                "avg_price_per_kg": md.get("avg_price_per_kg"),
                "min_price_per_kg": md.get("min_price_per_kg"),
                "max_price_per_kg": md.get("max_price_per_kg"),
                "best_market": md.get("best_market"),
                "total_markets": md.get("total_markets_reporting"),
                "trust": market_sec.get("trust_level"),
            }

    fert_data = (ctx.get("fertilizer") or {}).get("data") or {}
    if fert_data.get("fertilizer"):
        facts["fertilizer"] = {
            "name": fert_data["fertilizer"],
            "npk": fert_data.get("npk"),
            "qty_per_ha": fert_data.get("qty_per_ha"),
            "trust": ctx.get("fertilizer", {}).get("trust_level"),
            "safety_note": "Never state qty_per_ha if trust is client_supplemental",
        }

    crop_data = (ctx.get("crop") or {}).get("data") or {}
    if crop_data.get("top_3"):
        top3 = crop_data["top_3"]
        facts["crop_recommendation"] = {
            "top_pick": (top3[0] if top3 else {}).get("crop"),
            "confidence": (top3[0] if top3 else {}).get("confidence"),
            "alternatives": [c.get("crop") for c in top3[1:3] if isinstance(c, dict)],
            "trust": ctx.get("crop", {}).get("trust_level"),
        }

    alerts = get_active_alerts(ctx, ("danger", "warning"))
    if alerts:
        facts["alerts"] = [
            {"severity": a["severity"], "title": a["title"], "message": a.get("message", "")[:120]}
            for a in alerts[:3]
        ]

    return facts
