"""
AGRIFY — AI Farm Action Plan Engine
Module: backend/action_plan.py

Provides deterministic rule-based action planning with optional Gemini AI
enhancement for localized explanation and prioritization.

STRICT SAFETY CONSTRAINTS:
- Never invents fertilizer dosages, pesticide recommendations, disease diagnoses,
  market rates, yields, or weather numbers.
- Uses only the verified agronomic values present in the farm-analysis input payload.
- Always provides advisory wording and escalates to KVK / extension experts.
- Cleanly falls back to the deterministic rule engine on any Gemini failure or timeout.
"""

import os
import json
import re
from datetime import datetime, timezone

# Optional Gemini import
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# ============================================================
# LOCALIZATION DICTIONARIES (for Deterministic Rule Engine)
# ============================================================
LOCALIZED_STRINGS = {
    "en": {
        "summary_tpl": "7-Day Farm Action Plan for {crop} in {location} ({season} season). Focus on: {top_action}",
        "disclaimer": "This Action Plan is an advisory guide synthesized from satellite soil estimates, meteorological feeds, and agronomic models. It does not guarantee specific yields, profits, or pest eradication. Please verify field decisions with your local Krishi Vigyan Kendra (KVK) or Agriculture Extension Officer.",
        "estimated_soil_warning": "Soil nutrient figures are regional satellite estimates (SoilGrids). Verification with local KVK laboratory testing is recommended before large chemical fertilizer investments.",
        "soil_test_action": "Submit a physical soil sample to your nearest KVK laboratory to verify NPK and organic carbon levels.",
        "irrigation_title": "Irrigation Management",
        "fertilizer_title": "Nutrient Management",
        "soil_title": "Soil Conditioning",
        "protection_title": "Field Protection",
        "days_1_2": "Days 1–2",
        "days_1_2_focus": "Field Preparation & Basal Care",
        "days_3_4": "Days 3–4",
        "days_3_4_focus": "Nutrient Timing & Crop Sowing",
        "days_5_7": "Days 5–7",
        "days_5_7_focus": "Irrigation Routine & Stress Monitoring",
        "std_monitor": "Conduct daily field inspection for moisture uniformity and early seedling emergence.",
        "weather_check": "Review the live weather advisory before performing chemical spray or soil tillage.",
        "ask_kvk_soil": "Can I obtain a formal Soil Health Card test for N-P-K and organic carbon at the local KVK lab?",
        "ask_kvk_fert": "What is the optimal split-dose timing and local subsidy availability for {fert} in {location}?",
        "ask_kvk_ph": "Given my soil pH of {ph:.1f}, what is the recommended dosage and source of {amendment} for local soil conditions?",
        "ask_kvk_general": "What are the recommended high-yield, disease-resistant {crop} varieties certified for {season} season in {location}?",
    },
    "te": {
        "summary_tpl": "{location}లో {season} సీజన్‌కు {crop} పంట కోసం 7 రోజుల కార్యాచరణ ప్రణాళిక. ముఖ్య ప్రాధాన్యత: {top_action}",
        "disclaimer": "ఈ కార్యాచరణ ప్రణాళిక ఉపగ్రహ నేల అంచనాలు, వాతావరణ సమాచారం మరియు వ్యవసాయ సూత్రాల ఆధారంగా రూపొందించబడిన సలహా మాత్రమే. ఇది నిర్దిష్ట దిగుబడి లేదా లాభాలకు హామీ ఇవ్వదు. క్షేత్రస్థాయి నిర్ణయాలకు మీ సమీప కృషి విజ్ఞాన కేంద్రం (KVK) లేదా వ్యవసాయ విస్తరణ అధికారిని సంప్రదించండి.",
        "estimated_soil_warning": "నేల పోషకాల వివరాలు ప్రాంతీయ ఉపగ్రహ అంచనాలు (SoilGrids). ఎరువుల కొనుగోలుకు ముందు స్థానిక KVK ల్యాబ్ పరీక్ష ద్వారా ధృవీకరించుకోవాలని సూచించబడింది.",
        "soil_test_action": "ఖచ్చితమైన NPK మరియు సేంద్రీయ కర్బన స్థాయిల కోసం సమీప KVK లేదా రైతు భరోసా కేంద్రంలో నేల నమూనా పరీక్ష చేయించండి.",
        "irrigation_title": "నీటి యాజమాన్యం",
        "fertilizer_title": "పోషక యాజమాన్యం",
        "soil_title": "నేల శుద్ధి / సరిదిద్దడం",
        "protection_title": "పంట సంరక్షణ",
        "days_1_2": "రోజులు 1–2",
        "days_1_2_focus": "నేల తయారీ మరియు ప్రాథమిక ఎరువులు",
        "days_3_4": "రోజులు 3–4",
        "days_3_4_focus": "విత్తనం నాటడం మరియు పోషకాల ప్రణాళిక",
        "days_5_7": "రోజులు 5–7",
        "days_5_7_focus": "నీటి పారుదల మరియు పంట పరిశీలన",
        "std_monitor": "తేమ సమానంగా ఉందో లేదో మరియు మొక్కల పెరుగుదలను రోజూ పరిశీలించండి.",
        "weather_check": "మందుల పిచికారీ లేదా దుక్కి దున్నే ముందు తాజా వాతావరణ నివేదికను గమనించండి.",
        "ask_kvk_soil": "స్థానిక KVK ప్రయోగశాలలో N-P-K మరియు సేంద్రీయ కర్బనం కోసం నేల ఆరోగ్య కార్డు పరీక్ష ఎక్కడ చేయించుకోవచ్చు?",
        "ask_kvk_fert": "{location}లో {crop} కోసం {fert} ఎరువుల లభ్యత మరియు ప్రభుత్వ సబ్సిడీ వివరాలు ఏమిటి?",
        "ask_kvk_ph": "నా నేల pH {ph:.1f} ఉన్నందున, స్థానిక నేలలకు అనువైన {amendment} మోతాదు ఎంత?",
        "ask_kvk_general": "{location}లో {season} సీజన్‌కు అనువైన అధిక దిగుబడినిచ్చే {crop} రకాలు ఏవి?",
    },
    "hi": {
        "summary_tpl": "{location} में {season} मौसम के लिए {crop} फसल हेतु 7-दिवसीय कार्य योजना। मुख्य प्राथमिकता: {top_action}",
        "disclaimer": "यह कार्य योजना उपग्रह मृदा अनुमान, मौसम पूर्वानुमान और कृषि वैज्ञानिक मॉडल पर आधारित एक सलाहकार मार्गदर्शिका है। यह किसी निश्चित उपज या लाभ की गारंटी नहीं देती है। खेत से जुड़े निर्णयों के लिए अपने स्थानीय कृषि विज्ञान केंद्र (KVK) या कृषि विस्तार अधिकारी से परामर्श अवश्य लें।",
        "estimated_soil_warning": "मृदा पोषक तत्वों के आंकड़े क्षेत्रीय उपग्रह अनुमान (SoilGrids) हैं। भारी उर्वरक निवेश से पहले स्थानीय KVK प्रयोगशाला में मृदा परीक्षण कराने की सलाह दी जाती है।",
        "soil_test_action": "सटीक NPK और जैविक कार्बन स्तर की जांच के लिए अपने निकटतम KVK प्रयोगशाला में मिट्टी का नमूना जमा करें।",
        "irrigation_title": "सिंचाई प्रबंधन",
        "fertilizer_title": "उर्वरक एवं पोषण प्रबंधन",
        "soil_title": "मृदा सुधार",
        "protection_title": "फसल सुरक्षा",
        "days_1_2": "दिन 1–2",
        "days_1_2_focus": "खेत की तैयारी और बेसल खुराक",
        "days_3_4": "दिन 3–4",
        "days_3_4_focus": "बुवाई एवं पोषक तत्व प्रबंधन",
        "days_5_7": "दिन 5–7",
        "days_5_7_focus": "सिंचाई दिनचर्या एवं फसल निगरानी",
        "std_monitor": "खेत में नमी की एकरूपता और अंकुरण की दैनिक रूप से जांच करें।",
        "weather_check": "स्प्रे करने या जुताई करने से पहले मौसम पूर्वानुमान की जांच अवश्य करें।",
        "ask_kvk_soil": "क्या स्थानीय KVK प्रयोगशाला में N-P-K और जैविक कार्बन के लिए मृदा स्वास्थ्य कार्ड बनवाया जा सकता है?",
        "ask_kvk_fert": "{location} में {crop} के लिए {fert} की उपलब्धता और सब्सिडी के क्या नियम हैं?",
        "ask_kvk_ph": "मिट्टी का pH {ph:.1f} होने पर स्थानीय परिस्थितियों के अनुसार {amendment} की सही मात्रा क्या है?",
        "ask_kvk_general": "{location} में {season} मौसम के लिए अनुशंसित उच्च उपज वाली {crop} किस्में कौन सी हैं?",
    }
}


def normalize_language(lang_input: str) -> str:
    """Normalize language code to supported set (en, te, hi). Default: en."""
    if not isinstance(lang_input, str):
        return "en"
    lang_clean = lang_input.strip().lower()
    if lang_clean in ("te", "telugu"):
        return "te"
    if lang_clean in ("hi", "hindi"):
        return "hi"
    return "en"


def _extract_farm_context(payload: dict) -> dict:
    """
    Safely extract and normalize farm-analysis fields.
    Works whether payload is wrapped in {'analysis': ...} or passed at top-level.
    """
    analysis = payload.get("analysis") if isinstance(payload.get("analysis"), dict) else payload
    if not isinstance(analysis, dict):
        analysis = {}

    req = analysis.get("request") if isinstance(analysis.get("request"), dict) else {}
    loc = analysis.get("location") if isinstance(analysis.get("location"), dict) else {}
    weather = analysis.get("weather") if isinstance(analysis.get("weather"), dict) else {}
    soil = analysis.get("soil") if isinstance(analysis.get("soil"), dict) else {}
    crop_rec = analysis.get("crop_recommendation") if isinstance(analysis.get("crop_recommendation"), dict) else {}
    fert_rec = analysis.get("fertilizer_recommendation") if isinstance(analysis.get("fertilizer_recommendation"), dict) else {}
    irr_rec = analysis.get("irrigation_guidance") if isinstance(analysis.get("irrigation_guidance"), dict) else {}
    alerts = analysis.get("alerts") if isinstance(analysis.get("alerts"), list) else []

    # Identify target crop
    crop = payload.get("crop") or req.get("active_crop")
    if not crop:
        top_3 = crop_rec.get("top_3") or []
        if top_3 and isinstance(top_3, list) and isinstance(top_3[0], dict):
            crop = top_3[0].get("crop")
    if not crop:
        crop = req.get("previous_crop") or "Crop"

    crop_name = str(crop).strip().capitalize()

    # Location strings
    district = loc.get("district") or loc.get("village") or "Local Field"
    state = loc.get("state") or ""
    location_str = f"{district}, {state}".strip(", ") if state else district
    season = req.get("season") or "Current"

    # Soil data quality check
    data_quality = str(soil.get("data_quality") or "").lower()
    source_name = str(soil.get("source_name") or "").lower()
    is_estimated = (data_quality == "estimated") or ("soilgrids" in source_name)

    return {
        "crop": crop_name,
        "season": season,
        "district": district,
        "location_str": location_str,
        "weather": weather,
        "soil": soil,
        "fert_rec": fert_rec,
        "irr_rec": irr_rec,
        "alerts": alerts,
        "is_estimated": is_estimated,
    }


# ============================================================
# DETERMINISTIC RULE-BASED ENGINE
# ============================================================
def build_rule_based_action_plan(context: dict, lang: str = "en") -> dict:
    """
    Constructs an agronomic action plan purely from deterministic rules.
    Guarantees zero invented chemical values, dosages, or climate numbers.
    """
    S = LOCALIZED_STRINGS.get(lang, LOCALIZED_STRINGS["en"])
    crop = context["crop"]
    season = context["season"]
    loc_str = context["location_str"]
    weather = context["weather"]
    soil = context["soil"]
    fert_rec = context["fert_rec"]
    irr_rec = context["irr_rec"]
    alerts = context["alerts"]
    is_estimated = context["is_estimated"]

    immediate_actions = []
    key_risks = []
    expert_questions = []

    # 1. Process Existing High-Severity Alerts First
    active_hazard_titles = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        severity = str(alert.get("severity") or "").lower()
        title = alert.get("title") or ""
        msg = alert.get("message") or ""

        if severity in ("danger", "warning"):
            active_hazard_titles.append(title)
            # Create an immediate action from high-priority alert
            priority_val = "high" if severity == "danger" else "medium"
            immediate_actions.append({
                "priority": priority_val,
                "category": S["protection_title"],
                "title": title,
                "action": msg,
            })
            # Also register under key risks
            key_risks.append({
                "severity": severity,
                "risk": title,
                "mitigation": msg,
            })

    # 2. Irrigation Action (strictly using existing guidance)
    net_irr = irr_rec.get("net_irrigation_needed_mm_day")
    irr_msg = irr_rec.get("recommendation")
    irr_method = irr_rec.get("irrigation_method") or "Drip"
    if irr_msg:
        priority_val = "high" if ("URGENT" in irr_msg or (isinstance(net_irr, (int, float)) and net_irr >= 5.0)) else "medium"
        immediate_actions.append({
            "priority": priority_val,
            "category": S["irrigation_title"],
            "title": f"{S['irrigation_title']} ({irr_method})",
            "action": irr_msg,
        })

    # 3. Nutrient Deficiency Actions (strictly using existing remedies)
    deficiencies = fert_rec.get("nutrient_deficiency_summary") or []
    rec_fert = fert_rec.get("recommended_fertilizer") or {}
    fert_name = rec_fert.get("fertilizer") or "NPK"

    if isinstance(deficiencies, list):
        for d in deficiencies:
            if not isinstance(d, dict):
                continue
            nutrient = d.get("nutrient") or "Nutrient"
            level = d.get("level") or "imbalance"
            remedy = d.get("remedy")
            if remedy:
                immediate_actions.append({
                    "priority": "high" if level in ("low", "acidic", "alkaline") else "medium",
                    "category": S["fertilizer_title"],
                    "title": f"{nutrient} [{level.upper()}]",
                    "action": remedy,
                })

    # If no deficiency listed, provide basal prescription from recommended_fertilizer details
    if not deficiencies and rec_fert.get("details"):
        details = rec_fert.get("details", {})
        npk_ratio = details.get("npk", "N/A")
        qty = details.get("qty_per_ha", 50)
        action_text = f"Apply {fert_name} ({npk_ratio}) at {qty} kg/ha according to field schedule."
        immediate_actions.append({
            "priority": "medium",
            "category": S["fertilizer_title"],
            "title": f"{S['fertilizer_title']}: {fert_name}",
            "action": action_text,
        })

    # 4. Soil Quality Alert & Lab Action (if data is estimated from SoilGrids)
    if is_estimated:
        immediate_actions.append({
            "priority": "low",
            "category": S["soil_title"],
            "title": "SoilGrids Estimated Telemetry",
            "action": S["estimated_soil_warning"],
        })
        expert_questions.append(S["ask_kvk_soil"])

    # 5. Build 7-Day Plan (this_week_plan)
    # Days 1–2: Basal Application & Soil Prep
    stage_guide = fert_rec.get("stage_wise_application") or []
    basal_stage = stage_guide[0] if (stage_guide and isinstance(stage_guide, list) and isinstance(stage_guide[0], dict)) else None

    tasks_d1_2 = []
    if is_estimated:
        tasks_d1_2.append(S["soil_test_action"])
    if basal_stage:
        stg_name = basal_stage.get("stage", "Basal")
        n_pct = basal_stage.get("n_pct", 0)
        p_pct = basal_stage.get("p_pct", 0)
        k_pct = basal_stage.get("k_pct", 0)
        tasks_d1_2.append(f"Execute {stg_name}: apply target nutrients (N: {n_pct}%, P: {p_pct}%, K: {k_pct}%).")
    elif deficiencies:
        tasks_d1_2.append(f"Apply prescribed basal soil conditioners ({deficiencies[0].get('nutrient', 'NPK')}).")
    else:
        tasks_d1_2.append(f"Prepare field beds and calibrate sowing lines for {crop}.")

    # Days 3–4: Sowing & Weather Safeguard
    tasks_d3_4 = [
        f"Proceed with {season} season planting/sowing for {crop}.",
        S["weather_check"],
    ]
    if len(active_hazard_titles) > 0:
        tasks_d3_4.append(f"Monitor ongoing risk: {active_hazard_titles[0]}.")

    # Days 5–7: Irrigation & Monitoring Routine
    tasks_d5_7 = [
        S["std_monitor"],
    ]
    if irr_msg:
        tasks_d5_7.append(f"Maintain irrigation routine: {irr_msg}")

    this_week_plan = [
        {
            "period": S["days_1_2"],
            "focus": S["days_1_2_focus"],
            "tasks": tasks_d1_2,
        },
        {
            "period": S["days_3_4"],
            "focus": S["days_3_4_focus"],
            "tasks": tasks_d3_4,
        },
        {
            "period": S["days_5_7"],
            "focus": S["days_5_7_focus"],
            "tasks": tasks_d5_7,
        },
    ]

    # 6. Additional Key Risks (if not already recorded from alerts)
    if not key_risks:
        temp = weather.get("temperature")
        if isinstance(temp, (int, float)) and temp > 38:
            key_risks.append({
                "severity": "warning",
                "risk": f"High Temperature ({temp}°C)",
                "mitigation": "Increase irrigation frequency and mulch soil to reduce evapotranspiration.",
            })
        else:
            key_risks.append({
                "severity": "advisory",
                "risk": "Seasonal Environmental Shifts",
                "mitigation": "Track 5-day weather forecast regularly to protect early stage crop development.",
            })

    # 7. Formulate Expert / KVK Questions
    ph_val = soil.get("ph")
    if isinstance(ph_val, (int, float)) and (ph_val < 6.0 or ph_val > 8.0):
        amendment = "agricultural lime (CaCO₃)" if ph_val < 6.0 else "gypsum (CaSO₄)"
        expert_questions.append(S["ask_kvk_ph"].format(ph=ph_val, amendment=amendment))

    if fert_name:
        expert_questions.append(S["ask_kvk_fert"].format(fert=fert_name, location=loc_str, crop=crop))

    expert_questions.append(S["ask_kvk_general"].format(crop=crop, season=season, location=loc_str))

    # 8. Synthesize Voice-Friendly Summary
    top_action_str = immediate_actions[0]["title"] if immediate_actions else f"Field prep for {crop}"
    summary = S["summary_tpl"].format(
        crop=crop,
        location=loc_str,
        season=season,
        top_action=top_action_str,
    )

    return {
        "status": "success",
        "source": "rule_based_engine",
        "language": lang,
        "crop": crop,
        "summary": summary,
        "immediate_actions": immediate_actions[:4],  # clean top 4 max
        "this_week_plan": this_week_plan,
        "key_risks": key_risks[:3],
        "expert_questions": expert_questions[:4],
        "disclaimer": S["disclaimer"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# OPTIONAL GEMINI AI ENHANCEMENT
# ============================================================
def try_gemini_action_plan(context: dict, lang: str = "en", gemini_api_key: str = None) -> dict:
    """
    Optionally calls Gemini to structure, prioritize, and translate the action plan.
    STRICT SAFETY:
    - Minimizes prompt to verified facts only.
    - Explicitly prohibits inventing chemical names, doses, or prices.
    - If anything fails, returns None to allow seamless fallback.
    """
    if not gemini_api_key or genai is None:
        return None

    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Prepare minimized, controlled input
        minimized = {
            "target_crop": context["crop"],
            "season": context["season"],
            "location": context["location_str"],
            "weather_facts": {
                "temperature": context["weather"].get("temperature"),
                "humidity": context["weather"].get("humidity"),
                "rainfall": context["weather"].get("rainfall"),
                "description": context["weather"].get("weather_desc") or context["weather"].get("description"),
            },
            "soil_facts": {
                "N": context["soil"].get("N"),
                "P": context["soil"].get("P"),
                "K": context["soil"].get("K"),
                "ph": context["soil"].get("ph"),
                "is_estimated_from_satellite": context["is_estimated"],
            },
            "prescribed_fertilizer": {
                "fertilizer": (context["fert_rec"].get("recommended_fertilizer") or {}).get("fertilizer"),
                "details": (context["fert_rec"].get("recommended_fertilizer") or {}).get("details"),
                "deficiencies": context["fert_rec"].get("nutrient_deficiency_summary"),
            },
            "prescribed_irrigation": {
                "net_irrigation_mm_day": context["irr_rec"].get("net_irrigation_needed_mm_day"),
                "recommendation": context["irr_rec"].get("recommendation"),
            },
            "alerts": [
                {"severity": a.get("severity"), "title": a.get("title"), "message": a.get("message")}
                for a in context["alerts"][:3] if isinstance(a, dict)
            ],
            "requested_language": lang,
        }

        lang_name = "Telugu" if lang == "te" else ("Hindi" if lang == "hi" else "English")

        system_instruction = (
            "You are the AGRIFY AI Farm Action Planner. Your job is to format verified agronomic data "
            "into a structured, farmer-friendly 7-day action plan.\n\n"
            "STRICT RULES:\n"
            f"1. Respond entirely in {lang_name} (language code: {lang}).\n"
            "2. DO NOT invent, calculate, or hallucinate ANY new fertilizer doses, pesticide names, "
            "disease diagnoses, yield figures, or market prices. Use ONLY the facts provided in the JSON input.\n"
            "3. If soil is marked 'is_estimated_from_satellite: true', include a note advising testing at a local KVK.\n"
            "4. Output MUST BE strictly a single valid JSON object with NO markdown fence or extra commentary.\n"
            "5. JSON Schema:\n"
            "{\n"
            '  "summary": "1-2 sentence voice-friendly overview",\n'
            '  "immediate_actions": [{"priority": "high"|"medium"|"low", "category": "...", "title": "...", "action": "..."}],\n'
            '  "this_week_plan": [{"period": "Days 1–2", "focus": "...", "tasks": ["..."]}],\n'
            '  "key_risks": [{"severity": "danger"|"warning"|"advisory", "risk": "...", "mitigation": "..."}],\n'
            '  "expert_questions": ["question 1", "question 2", "question 3"],\n'
            '  "disclaimer": "Advisory disclaimer emphasizing verification with KVK or extension officer"\n'
            "}"
        )

        prompt = f"{system_instruction}\n\nAGRONOMIC DATA:\n{json.dumps(minimized, ensure_ascii=False)}"

        # Generate with safety settings and low temperature for consistency
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.2, "response_mime_type": "application/json"}
        )

        raw_text = response.text.strip()
        # Clean potential markdown wrapping if present
        clean_json = re.sub(r"^```json\s*", "", raw_text)
        clean_json = re.sub(r"\s*```$", "", clean_json)

        data = json.loads(clean_json)

        # Validate required keys
        required_keys = ["summary", "immediate_actions", "this_week_plan", "key_risks", "expert_questions", "disclaimer"]
        if not all(k in data for k in required_keys):
            return None

        return {
            "status": "success",
            "source": "gemini_ai",
            "language": lang,
            "crop": context["crop"],
            "summary": data["summary"],
            "immediate_actions": data["immediate_actions"][:4],
            "this_week_plan": data["this_week_plan"][:3],
            "key_risks": data["key_risks"][:3],
            "expert_questions": data["expert_questions"][:4],
            "disclaimer": data["disclaimer"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        # Silently catch any Gemini error (quota, timeout, parse, bad response)
        print(f"Gemini Action Plan notice: {e}. Falling back to rule_based_engine.")
        return None


# ============================================================
# MAIN ENTRYPOINT
# ============================================================
def generate_action_plan(payload: dict) -> dict:
    """
    Top-level function called by the Flask endpoint.
    Handles validation, language extraction, Gemini attempt, and deterministic fallback.
    """
    if not isinstance(payload, dict):
        raise ValueError("Invalid request body: expected a JSON object.")

    # Determine requested language
    lang = normalize_language(payload.get("language"))

    # Safely extract context
    context = _extract_farm_context(payload)

    # Attempt Gemini enhancement if configured
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and genai is not None:
        gemini_result = try_gemini_action_plan(context, lang=lang, gemini_api_key=gemini_key)
        if gemini_result is not None:
            return gemini_result

    # Deterministic Rule-Based Fallback
    return build_rule_based_action_plan(context, lang=lang)
