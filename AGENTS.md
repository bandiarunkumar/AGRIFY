# AGRIFY — AI Agents, Voice Copilot & Orchestration (AGENTS.md)

**Status:** Current Implementation Audit & Agent Verification Baseline
**Version:** 3.0-production
**Updated:** October 2026

---

## 1. Overview & Agentic Philosophy

The AGRIFY AI Agent subsystem is designed to act as a **Voice Copilot & Agronomic Decision Support System** for farmers. Unlike open-ended conversational models that may hallucinate chemical dosages or speculative numbers, the AGRIFY agent architecture enforces **Strict Agronomic Grounding**:
- The model never invents pesticide dosages, fertilizer formulations, weather measurements, or mandi market rates.
- AI models are used strictly for linguistic translation, empathetic communication, entity extraction, and explanation.
- Factual grounding is guaranteed by querying verified ETL modules and deterministic rule engines.

---

## 2. Core Modules & Agent Pipeline (`backend/agent/` & `voice_assistant.py`)

The agent processing pipeline follows a 6-stage lifecycle (**VERIFIED via Unit Test Suite: 59 passed, 1 skipped**):

```
[User Audio / Text]
       │
       ▼
1. INTENT & ENTITY EXTRACTION (`planner.py`, `voice_assistant.py`)
       │
       ▼
2. TOOL EXECUTION (`tools.py`)
       │ (Parallel retrieval of Weather, Soil, Mandi Prices, Alerts)
       ▼
3. CONTEXT CONSOLIDATION (`context.py`)
       │ (Merges client state with backend verified telemetry)
       ▼
4. MULTI-PROVIDER AI GATEWAY (`gateway.py`)
       │ (Gemini 2.5 Flash ──[fail/timeout]──> OpenAI GPT-4o-mini)
       ▼
5. SAFETY VALIDATION (`safety.py`)
       │ (Validates against hallucinated chemical dosages or unverified claims)
       ▼
6. MULTIMODAL RESPONSE DISPATCH (`responder.py`)
       ├─► Spoken Response (Clean natural text for TTS; no markdown/symbols)
       └─► Display Card (Visual UI card with key points and route redirection)
```

### Module Responsibilities

1. **`planner.py` (VERIFIED):**
   - Maps natural queries in English, Telugu, or Hindi into 11 distinct intent categories:
     - `action_plan`, `plant_health`, `fertilizer`, `irrigation`, `weather`, `market`, `alerts`, `farm_analysis`, `crop`, `general_agriculture`, `unknown`.
   - Extracts agricultural entities (crop name, region, soil type, crop stage).
2. **`tools.py` (VERIFIED):**
   - Dispatches parallel non-blocking calls to backend ETL pipelines using `ThreadPoolExecutor`.
   - Enforces 4-second timeout guards per tool to prevent hanging requests.
3. **`context.py` (VERIFIED):**
   - Filters client-supplied telemetry, removing contradictory or unverified inputs.
4. **`gateway.py` (VERIFIED with mocks; UNVERIFIED with live paid API keys):**
   - Dispatches structured prompts to the primary AI model configured in `AI_PROVIDER_PRIMARY`.
   - Catches connection timeouts (`AI_PROVIDER_TIMEOUT_SECONDS`), quota exhaustion, and malformed JSON, instantly delegating to the secondary provider or rule engine.
5. **`safety.py` (VERIFIED):**
   - Inspects generated text before delivery. If an external model proposes hazardous chemical advice or ungrounded quantities, the safety layer substitutes deterministic extension guidance.
6. **`responder.py` (VERIFIED):**
   - Formats localized responses conforming to the AGRIFY multimodal contract:
     - `spoken_response`: 1–3 short sentences without asterisks, markdown, or brackets for clean Web Speech API reading.
     - `display_card`: Structured JSON with `title`, `key_points`, and `action_route` to seamlessly deep-link the user to specific app tabs (`/weather`, `/market`, `/analysis`, `/experts`).

---

## 3. Strict Safety Guardrails & Rules

| Guardrail Rule | System Behavior | Status |
| :--- | :--- | :--- |
| **No Chemical Hallucination** | If specific fertilizer/pesticide dosage is not found in verified database, the agent refuses to fabricate grams/liters and outputs: *"AGRIFY does not have a verified fertilizer dosage for this specific field. Please check your Farm Analyzer report or consult your local KVK officer."* | **VERIFIED** (`test_voice_assistant.py`) |
| **No Diagnosis Overreach** | Crop health questions explicitly state that symptom matching is advisory and directs the farmer to local agricultural extension officers for physical inspection. | **VERIFIED** (`test_voice_assistant.py`) |
| **Audio-Safe Synthesis** | All audio output strings are stripped of Markdown formatting (`**`, `*`, `#`, `[]`), ensuring text-to-speech engines pronounce natural phrasing without reading punctuation code. | **VERIFIED** (`test_voice_tts.js`) |
| **Zero Key Exposure** | AI credentials and provider metadata are strictly filtered from public response objects. Gateway public attributes contain no API secret references. | **VERIFIED** (`test_gateway_3f1.py`) |

---

## 4. Multi-Provider Fallback Matrix

```
                +---------------------------------------+
                |        Incoming Query & Context       |
                +-------------------+-------------------+
                                    |
                    +---------------+---------------+
                    |                               |
       [AI Keys Configured]            [No API Keys Configured]
                    |                               |
                    v                               v
    +-------------------------------+   +-------------------------------+
    | Primary: Google Gemini Flash  |   |   Deterministic Rule Engine   |
    +---------------+---------------+   |    (`LOCALIZED_TEMPLATES`)    |
                    |                   +---------------+---------------+
        [Failure / Timeout]                             |
                    v                                   |
    +-------------------------------+                   |
    | Secondary: OpenAI GPT-4o-mini |                   |
    +---------------+---------------+                   |
                    |                                   |
        [Failure / Timeout]                             |
                    v                                   |
    +-------------------------------+                   |
    |   Deterministic Rule Engine   |                   |
    |    (`LOCALIZED_TEMPLATES`)    |<------------------+
    +---------------+---------------+
                    |
                    v
    +-------------------------------+
    | Multi-Lingual Speech/Card UI  |
    +-------------------------------+
```

*Verification Note:* The provider fallback cascade (Gemini ➔ OpenAI ➔ Rule Engine) has been verified using mocked failure scenarios in `backend/test_gateway_3f1.py`. Live provider fallback using real external credentials and network connections is **UNVERIFIED / UNTESTED** in this offline audit.
