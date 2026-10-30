"""
Google GenAI client (google-genai) with safe fallback
"""
import os
import logging

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except Exception:
    genai = None
    types = None
    HAS_GENAI = False


class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}")
                self.client = None
    
    def generate_agricultural_response(self, message, lang="en", system_prompt=None):
        if not self.client:
            return None, "unavailable"
        try:
            concise_instruction = "Keep the response extremely direct, crisp, and under 150 words. Use bullet points for key actions."
            
            if system_prompt:
                prompt = f"{system_prompt}\n{concise_instruction}\n\nRequested language: {lang}\nUser question: {message}"
            else:
                prompt = f"{concise_instruction}\nLanguage: {lang}\nQuestion: {message}"

            resp = self.client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=350
                ) if types else None,
            )
            text = getattr(resp, "text", None)
            if isinstance(text, str) and text.strip():
                return text.strip(), "gemini_ai"
        except Exception as e:
            logger.warning(f"Gemini API error: {e}")
            return None, "error"
        return None, "no_response"


gemini_client = GeminiClient()
