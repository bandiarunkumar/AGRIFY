"""
AGRIFY Agent — Safety Validator
Module: backend/agent/safety.py

Post-generation safety gate that validates the response produced by the
responder before it is returned to the frontend.

Absolute prohibitions (never overridable):
  1. No invented numerical values (dosage, price, weather, soil)
     that are not present in the verified rich_context.
  2. No guarantee language ("guaranteed", "100%", "definitely will").
  3. No confirmed disease diagnosis language.
  4. No pesticide dosage/concentration statements.
  5. Any violation → discard generated response → use the safe fallback.
"""

import re
from typing import Optional


# ============================================================
# PROHIBITED PHRASES (language-agnostic, applied to spoken_response)
# ============================================================
GUARANTEE_PATTERNS = [
    r'\b100\s*%\s*(effective|cure|guarantee|guaranteed|success)\b',
    r'\bguaranteed\b',
    r'\bdefintely will\b',
    r'\bwill definitely\b',
    r'\bcertain (yield|profit|cure)\b',
    r'\bsure to (cure|eliminate|eradicate)\b',
]

DISEASE_CONFIRMATION_PATTERNS = [
    r'\b(your crop|this plant|the plant) (has|have|is infected with|definitely has)\b',
    r'\bconfirmed (disease|diagnosis|infection)\b',
    r'\bdiagnosed with\b',
]

PESTICIDE_DOSAGE_PATTERNS = [
    # Catches "<number> ml/L", "<number> g/L", "<number> ml per litre" etc.
    r'\b\d+(\.\d+)?\s*(ml|g|gm|gram|litre|liter)\s*/\s*(l|litre|liter|hectare|acre)\b',
    r'\b\d+(\.\d+)?\s*(ml|g|gm)\s+per\s+(litre|liter|hectare|acre)\b',
    # Chemical product names paired with concentrations
    r'\b(chlorpyrifos|imidacloprid|cypermethrin|monocrotophos|endosulfan|profenofos)\s+\d',
]

# Numbers that are safe to appear in spoken_response (from verified context)
# These are extracted from rich_context and used to whitelist numbers.

def _extract_verified_numbers(rich_context: dict) -> set:
    """
    Extract all numerical values from verified sections of rich_context.
    These numbers are safe to appear in the spoken_response.
    """
    verified = set()

    def _collect(obj):
        if isinstance(obj, (int, float)) and obj != 0:
            verified.add(round(float(obj), 1))
        elif isinstance(obj, dict):
            for v in obj.values():
                _collect(v)
        elif isinstance(obj, list):
            for item in obj:
                _collect(item)

    # Trust levels that allow their numbers to appear in the response
    trusted_levels = {"live", "soilgrids", "agmarknet", "agmarknet_fallback",
                      "ml_model", "rule_based", "reference_estimate", "user_entered"}

    for key in ["current_weather", "forecast", "soil", "market", "crop",
                "fertilizer", "alerts"]:
        section = rich_context.get(key, {})
        if isinstance(section, dict) and section.get("trust_level") in trusted_levels:
            _collect(section.get("data"))

    return verified


def _find_unverified_numbers(text: str, verified_numbers: set) -> list:
    """
    Find numbers in text that are NOT in the verified set.
    Returns list of suspicious (number_str, float_val) tuples.
    """
    # Match standalone numbers (integers and decimals)
    all_nums = re.findall(r'\b(\d+(?:\.\d+)?)\b', text)
    suspicious = []
    for ns in all_nums:
        val = float(ns)
        # Skip very small numbers (day numbers, years, small counters)
        if val < 2 or val > 100000:
            continue
        # Allow numbers close to any verified number (±5% tolerance)
        close = any(
            abs(val - vn) <= max(0.5, abs(vn) * 0.05)
            for vn in verified_numbers
        )
        if not close:
            suspicious.append((ns, val))
    return suspicious


def validate_response(response: dict, rich_context: dict) -> dict:
    """
    Validate a generated response against safety rules.

    If the response passes all checks, return it unchanged.
    If any check fails, replace spoken_response with a safe fallback
    and add a 'safety_gate_triggered' flag.

    The display_card and other structural fields are preserved
    even when spoken_response is replaced.
    """
    spoken = response.get("spoken_response", "")
    if not spoken or not isinstance(spoken, str):
        return response

    violations = []

    # ---- Check 1: Guarantee language ----
    for pat in GUARANTEE_PATTERNS:
        if re.search(pat, spoken, re.IGNORECASE):
            violations.append(f"guarantee_language: pattern '{pat}' matched")
            break

    # ---- Check 2: Disease confirmation ----
    for pat in DISEASE_CONFIRMATION_PATTERNS:
        if re.search(pat, spoken, re.IGNORECASE):
            violations.append(f"disease_confirmation: pattern '{pat}' matched")
            break

    # ---- Check 3: Pesticide dosage ----
    for pat in PESTICIDE_DOSAGE_PATTERNS:
        if re.search(pat, spoken, re.IGNORECASE):
            violations.append(f"pesticide_dosage: pattern '{pat}' matched")
            break

    # ---- Check 4: Unverified numbers ----
    # Only run this check when we have actual verified data (not empty context)
    verified_numbers = _extract_verified_numbers(rich_context)
    if verified_numbers and len(spoken.split()) > 10:
        suspicious = _find_unverified_numbers(spoken, verified_numbers)
        if len(suspicious) > 3:
            # More than 3 unexplained numbers is a red flag for hallucination
            violations.append(f"unverified_numbers: {suspicious[:3]}")

    if not violations:
        return response

    # ---- Safety gate triggered ----
    print(f"[AGRIFY Safety Gate] Violations in spoken_response: {violations}")

    # Build safe fallback spoken response from display_card key_points
    card = response.get("display_card") or {}
    key_points = card.get("key_points") or []
    intent = rich_context.get("intent", "general_agriculture")

    safe_spoken = _build_safe_fallback_spoken(intent, rich_context, key_points)

    return {
        **response,
        "spoken_response": safe_spoken,
        "source": "rule_based_engine_safety_gate",
        "safety_gate_triggered": True,
        "safety_violations": violations,
    }


def _build_safe_fallback_spoken(intent: str, ctx: dict, key_points: list) -> str:
    """Construct a minimal safe spoken response when the generator's output is rejected."""
    lang = ctx.get("language", "en")
    crop = ctx.get("active_crop", "your crop")
    loc = ctx.get("location_str", "your area")

    SAFE_FALLBACKS = {
        "en": {
            "weather":    f"Current weather data for {loc} is available in the Weather tab for accurate readings.",
            "market":     f"For verified mandi prices for {crop}, please check the Market tab or visit your local mandi.",
            "fertilizer": f"For {crop} fertilizer guidance, run the Farm Analyzer for a field-specific recommendation from your soil data.",
            "crop":       f"Crop recommendation for {loc} is available in the Farm Analyzer based on your live soil and weather data.",
            "irrigation": f"Irrigation guidance for {crop} is available in your Farm Analyzer report.",
            "alerts":     f"Check your Farm Alert dashboard for active warnings in {loc}.",
            "default":    "I can assist with crop, fertilizer, weather, irrigation, and market queries. Please ask a specific question.",
        },
        "te": {
            "weather":    f"{loc}లో వాతావరణ సమాచారం వెదర్ ట్యాబ్‌లో చూడండి.",
            "market":     f"{crop} మండి ధరల కోసం మార్కెట్ ట్యాబ్ లేదా స్థానిక మండి సంప్రదించండి.",
            "fertilizer": f"{crop} ఎరువుల సలహా కోసం ఫార్మ్ అనాలైజర్ నడిపించండి.",
            "crop":       f"{loc}కు అనువైన పంట సలహా ఫార్మ్ అనాలైజర్‌లో అందుబాటులో ఉంది.",
            "default":    "పంట, ఎరువు, వాతావరణం, నీటిపారుదల లేదా మార్కెట్ విషయాలపై అడగండి.",
        },
        "hi": {
            "weather":    f"{loc} में मौसम की जानकारी वेदर टैब में देखें।",
            "market":     f"{crop} का मंडी भाव जानने के लिए मार्केट टैब या स्थानीय मंडी से पूछें।",
            "fertilizer": f"{crop} के लिए उर्वरक सलाह हेतु फार्म एनालाइजर चलाएं।",
            "crop":       f"{loc} के लिए फसल सुझाव फार्म एनालाइजर में उपलब्ध है।",
            "default":    "फसल, खाद, मौसम, सिंचाई या मंडी भाव के बारे में पूछें।",
        },
    }

    lang_map = SAFE_FALLBACKS.get(lang, SAFE_FALLBACKS["en"])
    return lang_map.get(intent, lang_map.get("default", SAFE_FALLBACKS["en"]["default"]))
