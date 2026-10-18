"""
AGRIFY — AI Model Gateway
Module: backend/agent/gateway.py

Provider-agnostic AI abstraction layer for the AGRIFY Agent Core.
Allows the Agent Core responder to use Gemini or OpenAI without coupling
business logic to a specific provider.

ARCHITECTURE:
    AIRequest → ModelGateway → GeminiProvider | OpenAIProvider → AIResult | None
    On None → caller falls back to deterministic rule engine.

SAFETY:
    - Credentials are read from env vars; NEVER logged, NEVER returned in output.
    - Providers receive only the verified facts snapshot from _build_gemini_facts().
    - Safety validation (agent/safety.py) runs AFTER this gateway returns.
    - Providers cannot bypass the existing AGRIFY safety gate.

TIMEOUT STRATEGY:
    SDK/HTTP timeout: native per-provider mechanism.
        Gemini: request_options={"timeout": timeout_s}
        OpenAI: openai.OpenAI(timeout=timeout_s)
    Provider calls remain synchronous so timeouts do not leave abandoned
    worker threads running after a request has been rejected.

PROVIDER SELECTION (configuration-driven, NOT language-driven):
    AI_PROVIDER_PRIMARY=gemini   -> Gemini primary, OpenAI secondary
    AI_PROVIDER_PRIMARY=openai   -> OpenAI primary, Gemini secondary
    AI_PROVIDER_PRIMARY=auto     -> first available (Gemini if both keys present)

ENVIRONMENT VARIABLES:
    AI_PROVIDER_PRIMARY         gemini | openai | auto  (default: gemini)
    AI_PROVIDER_TIMEOUT_SECONDS integer                 (default: 12)
    GEMINI_API_KEY              secret — never logged
    GEMINI_MODEL                model name              (default: gemini-2.5-flash)
    OPENAI_API_KEY              secret — never logged
    OPENAI_MODEL                model name              (default: gpt-4o-mini)
"""

import os
import re
import json
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class AIRequest:
    """
    Provider-agnostic AI request.
    Contains only data derived from the verified AGRIFY context.
    Raw user input is included for conversational phrasing only —
    providers are explicitly prohibited from inventing facts.
    """
    system_prompt: str        # AGRIFY safety-constrained system instructions
    user_content: str         # e.g. "Farmer query: X\nDetected intent: Y"
    verified_facts: dict      # Minimal trusted facts from _build_gemini_facts()
    intent: str               # Classified intent
    language: str             # en | te | hi
    temperature: float = 0.15
    response_mime_type: str = "application/json"


@dataclass
class AIResult:
    """
    Normalized, validated provider response.
    Only produced after structural validation — never a raw provider dict.
    """
    spoken_response: str       # TTS-safe, no markdown
    display_card: dict         # {title, category, key_points, action_pill}
    expert_escalation: dict    # {recommended, suggested_question}
    disclaimer: str
    source: str                # "gemini_ai_agent" | "openai_ai_agent"
    model_used: str            # e.g. "gemini-2.5-flash", "gpt-4o-mini"
    intent: str = ""
    language: str = "en"


# ============================================================
# BASE PROVIDER INTERFACE
# ============================================================

class BaseProvider(ABC):
    """Abstract provider interface. All providers must implement call()."""

    @abstractmethod
    def call(self, request: AIRequest, timeout_s: int) -> Optional[AIResult]:
        """
        Execute the AI request and return a validated AIResult, or None on failure.
        Must enforce timeout_s as an actual SDK/HTTP timeout.
        Must return None (not raise) on any failure.
        Must NEVER log API keys or authorization headers.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    def _parse_and_validate(
        self, raw_text: str, source: str, lang: str, intent: str
    ) -> Optional[AIResult]:
        """
        Shared JSON parse + structural validation.
        Returns AIResult on success, None on any failure.
        Never logs raw response text (may contain sensitive context data).
        """
        try:
            clean = re.sub(r"^```json\s*", "", raw_text.strip())
            clean = re.sub(r"\s*```$", "", clean)
            data = json.loads(clean)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("[Gateway] %s — JSON parse failure: %s", source, type(exc).__name__)
            return None

        # Structural validation of required fields
        spoken = data.get("spoken_response")
        card = data.get("display_card")
        if not isinstance(spoken, str) or not spoken.strip():
            logger.warning("[Gateway] %s — missing or empty spoken_response", source)
            return None
        if not isinstance(card, dict):
            logger.warning("[Gateway] %s — missing or malformed display_card", source)
            return None

        # Sanitize spoken response: strip markdown symbols (TTS-unsafe)
        spoken = spoken.replace("**", "").replace("*", "").replace("#", "").strip()

        esc = data.get("expert_escalation")
        if not isinstance(esc, dict):
            esc = {"recommended": False, "suggested_question": None}

        disclaimer = data.get("disclaimer") or ""

        return AIResult(
            spoken_response=spoken,
            display_card={
                "title": card.get("title", "AGRIFY Copilot Advisory"),
                "category": card.get("category", "General Advisory"),
                "key_points": (card.get("key_points") or [])[:4],
                "action_pill": card.get("action_pill"),
            },
            expert_escalation={
                "recommended": bool(esc.get("recommended")),
                "suggested_question": esc.get("suggested_question"),
            },
            disclaimer=disclaimer,
            source=source,
            model_used=self.model_name,
            intent=intent,
            language=lang,
        )


# ============================================================
# GEMINI PROVIDER
# ============================================================

class GeminiProvider(BaseProvider):
    """
    Wraps Google Generative AI (google-generativeai SDK).
    Timeout: SDK request_options.
    """

    def __init__(self, api_key: str, model_name: str):
        if not api_key:
            raise ValueError("GeminiProvider: api_key must not be empty")
        self._api_key = api_key       # Never logged
        self._model_name = model_name

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def call(self, request: AIRequest, timeout_s: int) -> Optional[AIResult]:
        try:
            import google.generativeai as genai
        except ImportError:
            logger.warning("[Gateway] Gemini — google-generativeai not installed")
            return None

        wall_budget = timeout_s + 3
        t0 = time.monotonic()
        try:
            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(self._model_name)
            full_prompt = (
                f"{request.system_prompt}\n\n"
                f"VERIFIED_FACTS: {json.dumps(request.verified_facts, ensure_ascii=False)}\n\n"
                f"{request.user_content}"
            )
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": request.temperature,
                    "response_mime_type": request.response_mime_type,
                },
                request_options={"timeout": timeout_s},
            )
            raw_text = response.text
            if not raw_text or not raw_text.strip():
                logger.warning("[Gateway] Gemini — empty response text")
                return None
        except Exception as exc:
            logger.warning("[Gateway] Gemini — SDK error: %s", type(exc).__name__)
            return None

        elapsed = round(time.monotonic() - t0, 1)
        logger.info("[Gateway] Gemini — response received in %ss", elapsed)
        return self._parse_and_validate(
            raw_text, "gemini_ai_agent", request.language, request.intent
        )


# ============================================================
# OPENAI PROVIDER
# ============================================================

class OpenAIProvider(BaseProvider):
    """
    Wraps the OpenAI Python SDK.
    Timeout: native HTTP timeout on the openai.OpenAI client.
    Gracefully unavailable if the openai package is not installed.
    """

    def __init__(self, api_key: str, model_name: str):
        if not api_key:
            raise ValueError("OpenAIProvider: api_key must not be empty")
        self._api_key = api_key       # Never logged
        self._model_name = model_name

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    def call(self, request: AIRequest, timeout_s: int) -> Optional[AIResult]:
        try:
            import openai
        except ImportError:
            logger.warning("[Gateway] OpenAI — openai package not installed; skipping")
            return None

        t0 = time.monotonic()
        try:
            client = openai.OpenAI(
                api_key=self._api_key,
                timeout=float(timeout_s),
                max_retries=0,
            )
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"{request.system_prompt}\n\n"
                        f"VERIFIED_FACTS: {json.dumps(request.verified_facts, ensure_ascii=False)}"
                    ),
                },
                {"role": "user", "content": request.user_content},
            ]
            completion = client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                temperature=request.temperature,
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            choice = completion.choices[0] if completion.choices else None
            if not choice:
                logger.warning("[Gateway] OpenAI — no choices in response")
                return None
            raw_text = choice.message.content
            if not raw_text or not raw_text.strip():
                logger.warning("[Gateway] OpenAI — empty content in choice")
                return None
        except Exception as exc:
            logger.warning("[Gateway] OpenAI — SDK error: %s", type(exc).__name__)
            return None

        elapsed = round(time.monotonic() - t0, 1)
        logger.info("[Gateway] OpenAI — response received in %ss", elapsed)
        return self._parse_and_validate(
            raw_text, "openai_ai_agent", request.language, request.intent
        )


# ============================================================
# MODEL GATEWAY — ORCHESTRATOR
# ============================================================

class ModelGateway:
    """
    Orchestrates provider selection and the primary -> secondary -> None fallback chain.

    Provider selection is ALWAYS configuration-driven (env vars).
    It is NEVER based on query language, user agent, or any runtime request property.

    Usage:
        gateway = ModelGateway()
        result: Optional[AIResult] = gateway.query(request)
        # None -> caller should use rule-based fallback
    """

    def __init__(self):
        self._primary_name = os.getenv("AI_PROVIDER_PRIMARY", "gemini").lower().strip()
        self._timeout_s = int(os.getenv("AI_PROVIDER_TIMEOUT_SECONDS", "12"))
        self._gemini_key = os.getenv("GEMINI_API_KEY", "")
        self._openai_key = os.getenv("OPENAI_API_KEY", "")
        self._gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _build_provider(self, name: str) -> Optional[BaseProvider]:
        """Instantiate a provider by name. Returns None if key is missing."""
        if name == "gemini":
            if not self._gemini_key:
                logger.debug("[Gateway] Gemini key not configured — skipping")
                return None
            return GeminiProvider(self._gemini_key, self._gemini_model)
        elif name == "openai":
            if not self._openai_key:
                logger.debug("[Gateway] OpenAI key not configured — skipping")
                return None
            return OpenAIProvider(self._openai_key, self._openai_model)
        else:
            logger.warning("[Gateway] Unknown provider name: %s", name)
            return None

    def _resolve_order(self) -> list:
        """
        Determine provider order from configuration.
        Returns a list of provider names in priority order.
        This function is deterministic and language-independent.
        """
        primary = self._primary_name
        if primary == "auto":
            # auto: first available provider wins; prefer Gemini
            order = []
            if self._gemini_key:
                order.append("gemini")
            if self._openai_key:
                order.append("openai")
            return order
        elif primary == "gemini":
            return ["gemini", "openai"]
        elif primary == "openai":
            return ["openai", "gemini"]
        else:
            logger.warning(
                "[Gateway] Unknown AI_PROVIDER_PRIMARY='%s'; defaulting to gemini",
                primary,
            )
            return ["gemini", "openai"]

    def query(self, request: AIRequest) -> Optional[AIResult]:
        """
        Execute the AI request against configured providers.
        Returns AIResult on success, or None if all providers fail.
        None signals the caller to use the deterministic rule engine.

        Safety contract:
          - This method never raises exceptions; all failures return None.
          - API keys are never included in log output.
          - Provider order is config-driven, not language-driven.
        """
        provider_order = self._resolve_order()

        for provider_name in provider_order:
            provider = self._build_provider(provider_name)
            if provider is None:
                continue  # Key not configured for this provider

            logger.info(
                "[Gateway] Trying provider=%s model=%s timeout=%ss",
                provider.name,
                provider.model_name,
                self._timeout_s,
            )
            t0 = time.monotonic()
            try:
                result = provider.call(request, self._timeout_s)
            except Exception as exc:
                # Defensive catch — call() should never raise, but guard here
                elapsed = round(time.monotonic() - t0, 1)
                logger.warning(
                    "[Gateway] Provider %s raised unexpectedly after %ss: %s",
                    provider_name,
                    elapsed,
                    type(exc).__name__,
                )
                result = None

            if result is not None:
                logger.info(
                    "[Gateway] Provider %s succeeded (source=%s)",
                    provider_name,
                    result.source,
                )
                return result

            elapsed = round(time.monotonic() - t0, 1)
            logger.info(
                "[Gateway] Provider %s failed after %ss — trying next",
                provider_name,
                elapsed,
            )

        logger.info("[Gateway] All providers exhausted — returning None for rule engine")
        return None


# ============================================================
# AGRIFY SAFETY SYSTEM PROMPT (shared across providers)
# ============================================================
# This prompt is equivalent to the existing _gemini_response() prompt in responder.py.
# Centralising it here ensures both providers receive identical safety constraints.
# The safety gate (agent/safety.py validate_response) remains the PRIMARY safety boundary.
# This prompt is a secondary prompt-level constraint only.

AGRIFY_AGENT_SYSTEM_PROMPT = (
    "You are AGRIFY Voice Copilot — an intelligent agricultural voice assistant for Indian farmers.\n"
    "Answer ONLY based on the VERIFIED_FACTS provided. Do NOT invent any numbers or facts.\n\n"
    "CRITICAL SAFETY RULES:\n"
    "1. NEVER invent, calculate, or hallucinate ANY fertilizer dosage, pesticide dosage, chemical "
    "application rate, market price, weather reading, soil value, or crop yield.\n"
    "2. If fertilizer quantity is asked and has_trusted_fertilizer_dosage is False (or absent), "
    "explicitly state AGRIFY does not have a verified quantity for this field and advise consulting KVK.\n"
    "3. For plant diseases: NEVER state a confirmed diagnosis. Use cautious advisory wording "
    "('symptoms may be consistent with...') and recommend expert confirmation.\n"
    "4. Do NOT promise guaranteed yields, guaranteed profits, or 100% cure rates.\n"
    "5. For market prices: only restate prices from VERIFIED_FACTS. Never invent a price.\n"
    "6. For soil values: only restate values from VERIFIED_FACTS. Never invent N/P/K or pH.\n"
    "7. For weather data: only restate values from VERIFIED_FACTS. Never fabricate temperature or rainfall.\n"
    "8. Respond in the language specified by the 'language' field in VERIFIED_FACTS. "
    "If language is 'te', respond in Telugu. If 'hi', respond in Hindi. Otherwise English.\n"
    "9. spoken_response MUST be concise, conversational (2-4 short sentences), suitable for TTS. "
    "NO markdown, NO asterisks, NO bullet points, NO headers in spoken_response.\n"
    "10. Output MUST BE strictly a single valid JSON object with NO markdown fence.\n\n"
    "JSON Schema:\n"
    "{\n"
    '  "spoken_response": "2-4 natural spoken sentences without markdown",\n'
    '  "display_card": {\n'
    '    "title": "Short title",\n'
    '    "category": "Category name",\n'
    '    "key_points": ["bullet 1", "bullet 2", "bullet 3"],\n'
    '    "action_pill": {"label": "Button label", "action": "navigate_analysis"}\n'
    "  },\n"
    '  "expert_escalation": {\n'
    '    "recommended": true or false,\n'
    '    "suggested_question": "question for agronomist or null"\n'
    "  },\n"
    '  "disclaimer": "Brief advisory disclaimer"\n'
    "}"
)
