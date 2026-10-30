"""
AGRIFY Agent — Trust Consolidator
Module: backend/agent/context.py

Merges backend-fetched tool results with client-supplied context.
Labels every value with its trust_level so the responder and
safety validator know what can be stated as fact vs advisory.

Trust hierarchy (highest → lowest):
  live           → OpenWeatherMap real-time fetch
  soilgrids      → ISRIC SoilGrids GPS satellite data
  agmarknet      → Agmarknet real mandi record
  agmarknet_fallback → Built-in Telangana mandi database
  ml_model       → RandomForest crop/fertilizer prediction
  rule_based     → Deterministic agronomic rule engine
  user_entered   → Farmer typed values in Farm Analyzer form
  reference_estimate → Config constant (CROP_PRICES, etc.)
  client_supplemental → Frontend window globals (stale, unverified)
  unavailable    → Tool failed; data absent
  invented       → BLOCKED — never generated
"""

from typing import Dict, Any, Optional


def consolidate_context(
    tool_results: dict,
    client_context: dict,
    entities: dict,
    intent: str,
    language: str = "en",
    query: str = "",
) -> dict:
    """
    Build a rich, trust-labeled context dict consumed by the responder and safety validator.

    Structure of returned dict:
    {
        "intent":          str,
        "query":           str,
        "language":        str,
        "active_crop":     str,
        "location_str":    str,
        "season":          str,
        "lat":             float | None,
        "lon":             float | None,

        # Tool results — each has: trust_level, data, error
        "current_weather": { trust_level, data: {temperature, humidity, ...} }
        "forecast":        { trust_level, data: {forecast: [...], advisory: [...]} }
        "soil":            { trust_level, data: {N, P, K, ph, moisture_pct, ...} }
        "market":          { trust_level, data: {avg_price_per_kg, markets, ...} }
        "crop":            { trust_level, data: {best_crop, top_3, ...} }
        "fertilizer":      { trust_level, data: {fertilizer, npk, qty_per_ha, ...} }
        "alerts":          { trust_level, data: [...list of alert dicts...] }

        # Supplemental client data (labeled, lower trust)
        "client":          { original context snapshot }
    }
    """
    ctx: Dict[str, Any] = {
        "intent": intent,
        "query": query,
        "language": language,
        "active_crop": entities.get("active_crop", "rice"),
        "season": entities.get("season", "Kharif"),
        "lat": entities.get("lat"),
        "lon": entities.get("lon"),
        "location_str": _build_location_str(entities, client_context, tool_results),
        "client": client_context,
    }

    # ---- Weather ----
    weather_res = tool_results.get("tool_weather")
    if weather_res and weather_res.data:
        ctx["current_weather"] = {
            "trust_level": weather_res.trust_level,
            "data": weather_res.data.get("current", {}),
            "error": weather_res.error,
        }
        ctx["forecast"] = {
            "trust_level": weather_res.trust_level,
            "data": weather_res.data.get("forecast", {}),
            "error": None,
        }
    else:
        # Try supplemental from client context
        client_weather = client_context.get("weather") or {}
        if client_weather.get("temperature"):
            ctx["current_weather"] = {
                "trust_level": "client_supplemental",
                "data": client_weather,
                "error": weather_res.error if weather_res else "No weather data fetched",
            }
            ctx["forecast"] = {
                "trust_level": "unavailable",
                "data": {},
                "error": None,
            }
        else:
            ctx["current_weather"] = {
                "trust_level": "unavailable",
                "data": {},
                "error": weather_res.error if weather_res else "Weather not requested",
            }
            ctx["forecast"] = {"trust_level": "unavailable", "data": {}, "error": None}

    # ---- Soil ----
    soil_res = tool_results.get("tool_soil")
    if soil_res and soil_res.data:
        ctx["soil"] = {
            "trust_level": soil_res.trust_level,
            "data": soil_res.data,
            "error": soil_res.error,
        }
    else:
        client_soil = client_context.get("soil") or {}
        if client_soil:
            ctx["soil"] = {
                "trust_level": "client_supplemental",
                "data": client_soil,
                "error": soil_res.error if soil_res else None,
            }
        else:
            ctx["soil"] = {
                "trust_level": "unavailable", "data": {}, "error": None,
            }

    # ---- Market ----
    market_res = tool_results.get("tool_market")
    if market_res and market_res.data:
        ctx["market"] = {
            "trust_level": market_res.trust_level,
            "data": market_res.data,
            "error": market_res.error,
        }
    else:
        ctx["market"] = {"trust_level": "unavailable", "data": {}, "error": None}

    # ---- Crop Recommendation ----
    crop_res = tool_results.get("tool_crop")
    if crop_res and crop_res.data:
        ctx["crop"] = {
            "trust_level": crop_res.trust_level,
            "data": crop_res.data,
            "error": crop_res.error,
        }
        # Update active_crop with ML best guess if not already from context
        if entities.get("active_crop") == "rice" and not entities.get("crop_query"):
            best = (crop_res.data.get("best_crop") or {}).get("crop")
            if best:
                ctx["active_crop"] = best
    else:
        # Supplement from client context crop recommendation
        client_crop = client_context.get("crop_recommendation") or {}
        if client_crop:
            ctx["crop"] = {
                "trust_level": "client_supplemental",
                "data": client_crop,
                "error": None,
            }
        else:
            ctx["crop"] = {"trust_level": "unavailable", "data": {}, "error": None}

    # ---- Fertilizer ----
    fert_res = tool_results.get("tool_fertilizer")
    if fert_res and fert_res.data:
        ctx["fertilizer"] = {
            "trust_level": fert_res.trust_level,
            "data": fert_res.data,
            "error": fert_res.error,
        }
    else:
        client_fert = client_context.get("fertilizer_recommendation") or {}
        if client_fert:
            ctx["fertilizer"] = {
                "trust_level": "client_supplemental",
                "data": client_fert,
                "error": None,
            }
        else:
            ctx["fertilizer"] = {"trust_level": "unavailable", "data": {}, "error": None}

    # ---- Alerts ----
    alert_res = tool_results.get("tool_alerts")
    if alert_res is not None:
        ctx["alerts"] = {
            "trust_level": alert_res.trust_level,
            "data": alert_res.data or [],
            "error": alert_res.error,
        }
    else:
        client_alerts = client_context.get("alerts") or []
        ctx["alerts"] = {
            "trust_level": "client_supplemental" if client_alerts else "unavailable",
            "data": client_alerts,
            "error": None,
        }

    return ctx


def _build_location_str(entities: dict, client_context: dict, tool_results: dict) -> str:
    """Build a human-readable location string from best available data."""
    # 1. Try live weather city name
    weather_res = tool_results.get("tool_weather")
    if weather_res and weather_res.data:
        current = weather_res.data.get("current", {})
        city = current.get("city_name", "")
        if city:
            return city

    # 2. Try client context location metadata
    loc = client_context.get("location") or {}
    if isinstance(loc, dict):
        district = loc.get("district") or loc.get("village", "")
        state = loc.get("state", "")
        if district and state:
            return f"{district}, {state}"
        if district:
            return district

    # 3. Fall back to entities
    city = entities.get("city", "")
    state = entities.get("state", "")
    district = entities.get("district", "")
    if city:
        return city.title()
    if district and state:
        return f"{district}, {state}"
    if district:
        return district
    if state:
        return state

    return "Your Field"


# ============================================================
# HELPER: Extract safe typed values from context sections
# ============================================================
def get_trusted_weather(ctx: dict) -> Optional[dict]:
    """Return weather data only if trust_level is live or client_supplemental."""
    cw = ctx.get("current_weather", {})
    if cw.get("trust_level") in ("live", "client_supplemental") and cw.get("data"):
        return cw["data"]
    return None


def get_trusted_soil(ctx: dict) -> Optional[dict]:
    """Return soil data only if trust_level is soilgrids, reference_estimate, or supplemental."""
    soil = ctx.get("soil", {})
    if soil.get("trust_level") in ("soilgrids", "reference_estimate", "client_supplemental", "user_entered") and soil.get("data"):
        return soil["data"]
    return None


def get_trusted_market(ctx: dict) -> Optional[dict]:
    """Return market data with trust level, or None."""
    market = ctx.get("market", {})
    if market.get("data"):
        return market
    return None


def get_active_alerts(ctx: dict, severity: tuple = ("danger", "warning")) -> list:
    """Return active alerts filtered by severity."""
    alerts_sec = ctx.get("alerts", {})
    alerts = alerts_sec.get("data") or []
    if isinstance(alerts, list):
        return [a for a in alerts if isinstance(a, dict) and a.get("severity") in severity]
    return []
