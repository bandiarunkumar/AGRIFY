"""
AGRIFY Agent — Tool Executor
Module: backend/agent/tools.py

Wraps existing ETL/ML functions into isolated, timeout-safe tool slots.
Tools are called directly (same process) — no HTTP round-trips.

Execution strategy:
  Wave 1 (parallel): tool_weather, tool_soil, tool_market
  Wave 2 (parallel): tool_crop, tool_fertilizer, tool_alerts
    (Wave 2 uses Wave 1 results where available)

Each tool returns a ToolResult with a trust_level label.
Tool failures are non-fatal — the agent continues with what it has.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError

# ---- Tool timeouts (seconds) ----
TIMEOUT_WEATHER  = 8
TIMEOUT_SOIL     = 12
TIMEOUT_MARKET   = 10
TIMEOUT_ALERTS   = 5   # usually uses pre-fetched weather, so fast
TIMEOUT_CROP     = 3   # in-process ML
TIMEOUT_FERT     = 3   # in-process ML

# Wave structure
WAVE_1_TOOLS = {"tool_weather", "tool_soil", "tool_market"}
WAVE_2_TOOLS = {"tool_crop", "tool_fertilizer", "tool_alerts"}


# ============================================================
# RESULT DATACLASS
# ============================================================
@dataclass
class ToolResult:
    tool: str
    data: Optional[Dict[str, Any]]   # None on error
    trust_level: str                  # live | soilgrids | agmarknet | agmarknet_fallback
                                      # ml_model | rule_based | reference_estimate | unavailable
    error: Optional[str]              # human-readable error string or None
    fetch_ms: int                     # wall-clock milliseconds


def _timed(fn, *args, **kwargs) -> tuple:
    """Run fn(*args, **kwargs), return (result, elapsed_ms)."""
    t0 = time.monotonic()
    result = fn(*args, **kwargs)
    return result, int((time.monotonic() - t0) * 1000)


# ============================================================
# TOOL 1 — WEATHER
# ============================================================
def tool_weather(entities: dict, _prev: dict = None) -> ToolResult:
    """
    Fetch live current weather + 5-day forecast by GPS coordinates.
    Falls back gracefully if no lat/lon or API key missing.
    """
    lat = entities.get("lat")
    lon = entities.get("lon")

    if lat is None or lon is None:
        return ToolResult(
            tool="tool_weather", data=None,
            trust_level="unavailable",
            error="No GPS coordinates available. Run Farm Analyzer or allow location access.",
            fetch_ms=0,
        )

    try:
        from etl.weather_etl import get_weather_by_coords, get_forecast_by_coords

        (current, ms1) = _timed(get_weather_by_coords, lat, lon)
        (forecast, ms2) = _timed(get_forecast_by_coords, lat, lon)

        if "error" in current:
            return ToolResult(
                tool="tool_weather", data=None,
                trust_level="unavailable",
                error=current["error"],
                fetch_ms=ms1,
            )

        return ToolResult(
            tool="tool_weather",
            data={"current": current, "forecast": forecast},
            trust_level="live",
            error=None,
            fetch_ms=ms1 + ms2,
        )
    except Exception as e:
        return ToolResult(
            tool="tool_weather", data=None,
            trust_level="unavailable",
            error=f"Weather fetch failed: {str(e)}",
            fetch_ms=0,
        )


# ============================================================
# TOOL 2 — SOIL
# ============================================================
def tool_soil(entities: dict, _prev: dict = None) -> ToolResult:
    """
    Fetch real soil data from SoilGrids (ISRIC) by GPS coordinates.
    Falls back to regional heuristic if coordinates unavailable.
    """
    lat = entities.get("lat")
    lon = entities.get("lon")

    if lat is None or lon is None:
        # Try heuristic from client-supplied state
        return _soil_heuristic_fallback(entities.get("state", ""))

    try:
        from etl.soil_etl import get_soil_by_coords

        (soil, ms) = _timed(get_soil_by_coords, lat, lon)

        if "error" in soil or not soil.get("ok"):
            return _soil_heuristic_fallback(entities.get("state", ""))

        return ToolResult(
            tool="tool_soil",
            data=soil,
            trust_level="soilgrids",
            error=None,
            fetch_ms=ms,
        )
    except Exception as e:
        return _soil_heuristic_fallback(entities.get("state", ""), error_note=str(e))


def _soil_heuristic_fallback(state: str = "", error_note: str = "") -> ToolResult:
    """Return a clearly-labeled regional heuristic soil profile."""
    try:
        from predictions import REGION_SOIL_PROFILES
        state_key = state.lower() if state else "default"
        profile = REGION_SOIL_PROFILES.get(state_key, REGION_SOIL_PROFILES["default"])
        data = {
            "ok": True,
            "N": profile["N"],
            "P": profile["P"],
            "K": profile["K"],
            "ph": profile["ph"],
            "moisture_pct": profile.get("moisture", 45),
            "organic_carbon": profile.get("organic_carbon", 0.8),
            "soil_type": profile.get("soil_type", "Loamy"),
            "source_name": "regional_heuristic",
            "data_quality": "estimated",
        }
    except Exception:
        data = {
            "ok": True,
            "N": 50, "P": 40, "K": 30, "ph": 6.8,
            "moisture_pct": 45, "organic_carbon": 0.8, "soil_type": "Loamy",
            "source_name": "default_heuristic",
            "data_quality": "estimated",
        }
    return ToolResult(
        tool="tool_soil",
        data=data,
        trust_level="reference_estimate",
        error=error_note or None,
        fetch_ms=0,
    )


# ============================================================
# TOOL 3 — MARKET
# ============================================================
def tool_market(entities: dict, _prev: dict = None) -> ToolResult:
    """
    Fetch real mandi prices from Agmarknet (data.gov.in).
    Falls back to config CROP_PRICES reference estimate.
    """
    crop = entities.get("active_crop", "rice")
    state = entities.get("state") or entities.get("district")
    district = entities.get("district")

    try:
        from etl.market_etl import fetch_market_prices

        (result, ms) = _timed(fetch_market_prices, crop, state, district, 20)

        if not result.get("ok"):
            return _market_reference_fallback(crop, result.get("error", ""))

        # Market data successfully fetched
        trust = "agmarknet_fallback" if result.get("fallback") else "agmarknet"
        return ToolResult(
            tool="tool_market",
            data=result,
            trust_level=trust,
            error=None,
            fetch_ms=ms,
        )
    except Exception as e:
        return _market_reference_fallback(crop, str(e))


def _market_reference_fallback(crop: str, error_note: str = "") -> ToolResult:
    """Return config reference price clearly labeled as estimate."""
    try:
        from config import CROP_PRICES
        price = CROP_PRICES.get(crop.lower(), 25)
    except Exception:
        price = 25
    return ToolResult(
        tool="tool_market",
        data={"reference_price": price, "crop": crop, "is_reference": True},
        trust_level="reference_estimate",
        error=error_note or None,
        fetch_ms=0,
    )


# ============================================================
# TOOL 4 — ALERTS
# ============================================================
def tool_alerts(entities: dict, prev: dict = None) -> ToolResult:
    """
    Generate farm alerts using weather + soil + crop context.
    Uses pre-fetched weather from tool_weather if available (avoids duplicate API call).
    """
    lat = entities.get("lat")
    lon = entities.get("lon")

    if lat is None or lon is None:
        return ToolResult(
            tool="tool_alerts", data=[],
            trust_level="unavailable",
            error="No GPS coordinates — alerts require location.",
            fetch_ms=0,
        )

    try:
        from alerts.alert_engine import generate_farm_alerts

        # Re-use weather from wave 1 if available
        current_weather = None
        forecast = None
        soil = None

        if prev:
            weather_res = prev.get("tool_weather")
            if weather_res and weather_res.data:
                current_weather = weather_res.data.get("current")
                forecast = weather_res.data.get("forecast")
            soil_res = prev.get("tool_soil")
            if soil_res and soil_res.data:
                soil = soil_res.data

        t0 = time.monotonic()
        alerts = generate_farm_alerts(
            lat=lat, lon=lon,
            current_weather=current_weather,
            forecast=forecast,
            soil=soil,
            active_crop=entities.get("active_crop", "rice"),
            season=entities.get("season", "Kharif"),
        )
        ms = int((time.monotonic() - t0) * 1000)

        return ToolResult(
            tool="tool_alerts",
            data=alerts,
            trust_level="rule_based",
            error=None,
            fetch_ms=ms,
        )
    except Exception as e:
        return ToolResult(
            tool="tool_alerts", data=[],
            trust_level="unavailable",
            error=f"Alert engine error: {str(e)}",
            fetch_ms=0,
        )


# ============================================================
# TOOL 5 — CROP RECOMMENDATION
# ============================================================
def tool_crop(entities: dict, prev: dict = None) -> ToolResult:
    """
    Run ML crop prediction using soil + weather data from wave 1.
    Falls back to rule-based feasibility filter.
    """
    # Extract inputs from wave 1 results
    soil_data = {}
    weather_data = {}
    if prev:
        sr = prev.get("tool_soil")
        if sr and sr.data:
            soil_data = sr.data
        wr = prev.get("tool_weather")
        if wr and wr.data:
            weather_data = wr.data.get("current", {})

    N = soil_data.get("N", 50)
    P = soil_data.get("P", 40)
    K = soil_data.get("K", 30)
    ph = soil_data.get("ph", 6.8)
    moisture = soil_data.get("moisture_pct", 45)
    temp = weather_data.get("temperature", 28)
    humidity = weather_data.get("humidity", 65)
    rainfall = max(moisture * 5, 100)
    season = entities.get("season", "Kharif")
    region = entities.get("region", "South")

    try:
        from predictions import predict_crop

        (result, ms) = _timed(predict_crop, N, P, K, temp, humidity, ph, rainfall)

        if "error" in result:
            raise ValueError(result["error"])

        return ToolResult(
            tool="tool_crop",
            data={
                "best_crop": result["best_crop"],
                "top_3": [result["best_crop"]] + result.get("alternatives", [])[:2],
                "inputs": result.get("input_summary", {}),
            },
            trust_level="ml_model",
            error=None,
            fetch_ms=ms,
        )
    except Exception as e:
        # Rule-based fallback: return crop based on season
        crop_by_season = {
            "Kharif": "rice", "Rabi": "wheat", "Zaid": "maize",
        }
        fallback_crop = crop_by_season.get(season, "rice")
        return ToolResult(
            tool="tool_crop",
            data={
                "best_crop": {"crop": fallback_crop, "confidence": 0},
                "top_3": [{"crop": fallback_crop, "confidence": 0}],
                "inputs": {},
            },
            trust_level="rule_based",
            error=str(e),
            fetch_ms=0,
        )


# ============================================================
# TOOL 6 — FERTILIZER
# ============================================================
def tool_fertilizer(entities: dict, prev: dict = None) -> ToolResult:
    """
    Run ML fertilizer prediction using soil data from wave 1.
    Falls back to rule-based N/P/K deficiency check.
    """
    soil_data = {}
    weather_data = {}
    if prev:
        sr = prev.get("tool_soil")
        if sr and sr.data:
            soil_data = sr.data
        wr = prev.get("tool_weather")
        if wr and wr.data:
            weather_data = wr.data.get("current", {})

    if not soil_data:
        return ToolResult(
            tool="tool_fertilizer",
            data=None,
            trust_level="unavailable",
            error="No verified soil data available for fertilizer recommendation",
            fetch_ms=0,
        )

    N = soil_data.get("N", 50)
    P = soil_data.get("P", 40)
    K = soil_data.get("K", 30)
    ph = soil_data.get("ph", 6.8)
    moisture = soil_data.get("moisture_pct", 45)
    organic_carbon = soil_data.get("organic_carbon", 0.8)
    soil_type = soil_data.get("soil_type", "Loamy")
    temp = weather_data.get("temperature", 28)
    humidity = weather_data.get("humidity", 65)
    rainfall = max(moisture * 5, 100)
    crop = entities.get("active_crop", "rice")
    season = entities.get("season", "Kharif")
    region = entities.get("region", "South")

    # Normalize organic_carbon: SoilGrids gives cg/kg (centimol), need fraction
    if organic_carbon > 5:
        organic_carbon = organic_carbon / 100.0

    try:
        from predictions import predict_fertilizer
        from config import FERTILIZER_STAGE_GUIDE, FERTILIZER_INFO

        (result, ms) = _timed(predict_fertilizer,
            soil_type=soil_type, soil_ph=ph, soil_moisture=moisture,
            organic_carbon=organic_carbon, electrical_conductivity=0.5,
            N=N, P=P, K=K, temperature=temp, humidity=humidity, rainfall=rainfall,
            crop_type=crop, growth_stage="Vegetative",
            season=season, irrigation="Drip", previous_crop="Unknown",
            region=region, fertilizer_usage="Urea", yield_last=3000,
        )

        if "error" in result:
            raise ValueError(result["error"])

        best = result["best_fertilizer"]
        fert_name = best["fertilizer"]
        stage_guide = FERTILIZER_STAGE_GUIDE.get(crop.lower(),
                      FERTILIZER_STAGE_GUIDE.get("rice", []))
        fert_info = FERTILIZER_INFO.get(fert_name, {})

        return ToolResult(
            tool="tool_fertilizer",
            data={
                "fertilizer": fert_name,
                "confidence": best.get("confidence", 0),
                "npk": fert_info.get("npk", "N/A"),
                "qty_per_ha": fert_info.get("qty_per_ha", 50),
                "cost_per_kg": fert_info.get("cost_per_kg", 20),
                "stage_guide": stage_guide,
                "alternatives": result.get("alternatives", []),
                "soil_N": N, "soil_P": P, "soil_K": K, "soil_ph": ph,
            },
            trust_level="ml_model",
            error=None,
            fetch_ms=ms,
        )
    except Exception as e:
        # Rule-based N/P/K deficiency fallback
        fert_name = _rule_fertilizer(N, P, K)
        try:
            from config import FERTILIZER_INFO, FERTILIZER_STAGE_GUIDE
            fert_info = FERTILIZER_INFO.get(fert_name, {})
            stage_guide = FERTILIZER_STAGE_GUIDE.get(crop.lower(),
                          FERTILIZER_STAGE_GUIDE.get("rice", []))
        except Exception:
            fert_info = {}
            stage_guide = []

        return ToolResult(
            tool="tool_fertilizer",
            data={
                "fertilizer": fert_name,
                "confidence": 0,
                "npk": fert_info.get("npk", "N/A"),
                "qty_per_ha": fert_info.get("qty_per_ha", 50),
                "cost_per_kg": fert_info.get("cost_per_kg", 20),
                "stage_guide": stage_guide,
                "soil_N": N, "soil_P": P, "soil_K": K, "soil_ph": ph,
            },
            trust_level="rule_based",
            error=str(e),
            fetch_ms=0,
        )


def _rule_fertilizer(N: float, P: float, K: float) -> str:
    """Simple rule-based fertilizer recommendation from soil NPK."""
    n_def = N < 35
    p_def = P < 25
    k_def = K < 25
    if n_def and p_def and k_def:
        return "NPK"
    if n_def and p_def:
        return "DAP"
    if n_def:
        return "Urea"
    if p_def:
        return "SSP"
    if k_def:
        return "MOP"
    return "Compost"


# ============================================================
# PARALLEL EXECUTOR — Two-Wave Strategy
# ============================================================
TOOL_FN_MAP = {
    "tool_weather":    tool_weather,
    "tool_soil":       tool_soil,
    "tool_market":     tool_market,
    "tool_alerts":     tool_alerts,
    "tool_crop":       tool_crop,
    "tool_fertilizer": tool_fertilizer,
}

TOOL_TIMEOUT_MAP = {
    "tool_weather":    TIMEOUT_WEATHER,
    "tool_soil":       TIMEOUT_SOIL,
    "tool_market":     TIMEOUT_MARKET,
    "tool_alerts":     TIMEOUT_ALERTS,
    "tool_crop":       TIMEOUT_CROP,
    "tool_fertilizer": TIMEOUT_FERT,
}


def execute_tools(plan) -> Dict[str, ToolResult]:
    """
    Execute all required tools for an AgentPlan.

    Wave 1: tool_weather, tool_soil, tool_market (independent, parallel)
    Wave 2: tool_crop, tool_fertilizer, tool_alerts (use Wave 1 results, parallel)

    All failures are isolated — a timeout or exception in one tool
    does NOT prevent other tools from returning results.
    """
    required = set(plan.required_tools)
    results: Dict[str, ToolResult] = {}

    wave_1 = [t for t in ["tool_weather", "tool_soil", "tool_market"] if t in required]
    wave_2 = [t for t in ["tool_crop", "tool_fertilizer", "tool_alerts"] if t in required]

    def _run(tool_name: str, prev: dict) -> ToolResult:
        fn = TOOL_FN_MAP[tool_name]
        timeout = TOOL_TIMEOUT_MAP[tool_name]
        try:
            return fn(plan.entities, prev)
        except Exception as e:
            return ToolResult(
                tool=tool_name, data=None,
                trust_level="unavailable",
                error=f"Unhandled error in {tool_name}: {str(e)}",
                fetch_ms=0,
            )

    # ---- Wave 1 ----
    if wave_1:
        with ThreadPoolExecutor(max_workers=min(len(wave_1), 3)) as executor:
            futures = {executor.submit(_run, t, {}): t for t in wave_1}
            max_timeout = max(TOOL_TIMEOUT_MAP[t] for t in wave_1) + 2
            for fut in as_completed(futures, timeout=max_timeout):
                tool_name = futures[fut]
                try:
                    results[tool_name] = fut.result()
                except Exception as e:
                    results[tool_name] = ToolResult(
                        tool=tool_name, data=None, trust_level="unavailable",
                        error=str(e), fetch_ms=0,
                    )

    # ---- Wave 2 (passes Wave 1 results) ----
    if wave_2:
        with ThreadPoolExecutor(max_workers=min(len(wave_2), 3)) as executor:
            futures = {executor.submit(_run, t, results): t for t in wave_2}
            max_timeout = max(TOOL_TIMEOUT_MAP[t] for t in wave_2) + 2
            for fut in as_completed(futures, timeout=max_timeout):
                tool_name = futures[fut]
                try:
                    results[tool_name] = fut.result()
                except Exception as e:
                    results[tool_name] = ToolResult(
                        tool=tool_name, data=None, trust_level="unavailable",
                        error=str(e), fetch_ms=0,
                    )

    return results
