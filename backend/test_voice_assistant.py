"""
Phase 3D-3 Comprehensive Verification Suite
Tests:
A. English general agriculture
B. Telugu general agriculture
C. Hindi general agriculture
D. fertilizer with trusted dosage
E. fertilizer without trusted dosage
F. irrigation with trusted irrigation data
G. weather with weather context
H. market with market context
I. action-plan context
J. plant-health uncertainty
K. missing Gemini key
L. Gemini failure
M. malformed Gemini JSON
N. malformed request
O. missing optional context
P. unsupported language
Q. no hallucinated dosage
R. no hallucinated weather
S. no disease certainty
T. existing /api/chat unchanged
U. existing /api/farm/analyze unchanged
V. existing /api/farm/action-plan unchanged
W. Python syntax/import checks
"""

import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Set path to backend
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from voice_assistant import (
    normalize_language,
    classify_intent,
    filter_context_by_intent,
    synthesize_rule_based_response,
    synthesize_gemini_response,
    query_voice_assistant,
)
from api import app


class TestVoiceAssistant(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # These route tests cover the deterministic responder and must never
        # make paid or network-dependent provider calls.
        self.gateway_patch = patch("agent.gateway.ModelGateway.query", return_value=None)
        self.gateway_patch.start()

    def tearDown(self):
        self.gateway_patch.stop()

    # Test W: Python syntax & imports
    def test_W_imports(self):
        import voice_assistant
        self.assertTrue(hasattr(voice_assistant, "query_voice_assistant"))
        self.assertTrue(hasattr(voice_assistant, "classify_intent"))

    # Test A: English general agriculture
    def test_A_english_general_agriculture(self):
        res = self.app.post("/api/assistant/query", json={
            "query": "How can you help my farming?",
            "language": "en",
            "context": {}
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["language"], "en")
        self.assertIn("spoken_response", data)
        self.assertIsInstance(data["display_card"]["key_points"], list)
        self.assertIn("timestamp", data)

    # Test B: Telugu general agriculture
    def test_B_telugu_general_agriculture(self):
        res = self.app.post("/api/assistant/query", json={
            "query": "మీరు నాకు ఎలా సహాయపడగలరు?",
            "language": "te",
            "context": {}
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["language"], "te")
        self.assertIn("AGRIFY", data["spoken_response"])

    # Test C: Hindi general agriculture
    def test_C_hindi_general_agriculture(self):
        res = self.app.post("/api/assistant/query", json={
            "query": "आप मेरी खेती में कैसे मदद कर सकते हैं?",
            "language": "hi",
            "context": {}
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["language"], "hi")
        self.assertIn("सहायक", data["spoken_response"])

    # Test D: Fertilizer with trusted dosage
    def test_D_fertilizer_with_trusted_dosage(self):
        payload = {
            "query": "What fertilizer dose should I use for rice?",
            "language": "en",
            "context": {
                "request": {"active_crop": "Rice", "season": "Kharif"},
                "fertilizer_recommendation": {
                    "recommended_fertilizer": {
                        "fertilizer": "DAP",
                        "details": {"npk": "18-46-0", "qty_per_ha": 50}
                    },
                    "stage_wise_application": [{"stage": "Basal", "n_pct": 50}]
                }
            }
        }
        res = self.app.post("/api/assistant/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], "fertilizer")
        self.assertIn("50", data["spoken_response"])
        self.assertIn("DAP", data["spoken_response"])
        self.assertFalse(data["expert_escalation"]["recommended"])

    # Test E: Fertilizer without trusted dosage
    def test_E_fertilizer_without_trusted_dosage(self):
        payload = {
            "query": "How much DAP dosage should I apply?",
            "language": "en",
            "context": {
                "request": {"active_crop": "Rice"},
                # No fertilizer_recommendation provided
            }
        }
        res = self.app.post("/api/assistant/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], "fertilizer")
        self.assertIn("does not have a verified fertilizer dosage", data["spoken_response"])
        self.assertTrue(data["expert_escalation"]["recommended"])

    # Test F: Irrigation with trusted irrigation data
    def test_F_irrigation_trusted_data(self):
        payload = {
            "query": "When and how much should I water my cotton field?",
            "language": "en",
            "context": {
                "request": {"active_crop": "Cotton"},
                "irrigation_guidance": {
                    "recommendation": "Irrigate tomorrow morning.",
                    "net_irrigation_needed_mm_day": 4.5,
                    "irrigation_method": "Drip"
                }
            }
        }
        res = self.app.post("/api/assistant/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], "irrigation")
        self.assertIn("4.5", data["spoken_response"])
        self.assertIn("Drip", data["spoken_response"])

    # Test G: Weather with weather context
    def test_G_weather_context(self):
        payload = {
            "query": "What is the weather forecast today?",
            "language": "en",
            "context": {
                "location": {"district": "Warangal", "state": "Telangana"},
                "weather": {
                    "temperature": 31.5,
                    "humidity": 65,
                    "weather_desc": "scattered clouds"
                }
            }
        }
        res = self.app.post("/api/assistant/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], "weather")
        self.assertIn("31.5", data["spoken_response"])
        self.assertIn("Warangal", data["spoken_response"])

    # Test H: Market with market context
    def test_H_market_context(self):
        payload = {
            "query": "What is the mandi price for Maize?",
            "language": "en",
            "context": {
                "crop": "Maize",
                "location": {"district": "Khammam"}
            }
        }
        res = self.app.post("/api/assistant/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], "market")
        self.assertIn("Maize", data["spoken_response"])
        self.assertIn("₹", data["spoken_response"])

    # Test I: Action-plan context
    def test_I_action_plan_context(self):
        payload = {
            "query": "What is my 7-day action plan for this week?",
            "language": "en",
            "context": {
                "request": {"active_crop": "Chilli"},
                "action_plan": {
                    "immediate_actions": [{"title": "Spray neem oil for thrips prevention"}]
                }
            }
        }
        res = self.app.post("/api/assistant/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], "action_plan")
        self.assertIn("Spray neem oil", data["spoken_response"])

    # Test J: Plant-health uncertainty & non-definitive language
    def test_J_plant_health_uncertainty(self):
        payload = {
            "query": "My tomato leaves have black spots and yellowing, is it blight disease?",
            "language": "en",
            "context": {"request": {"active_crop": "Tomato"}}
        }
        res = self.app.post("/api/assistant/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["intent"], "plant_health")
        self.assertIn("may be consistent with", data["spoken_response"])
        self.assertTrue(data["expert_escalation"]["recommended"])

    # Test K: Missing Gemini Key fallback
    def test_K_missing_gemini_key(self):
        with patch.dict(os.environ, {}, clear=True):
            res = self.app.post("/api/assistant/query", json={"query": "What is rice crop?", "language": "en"})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["source"], "rule_based_engine")

    # Test L: Gemini API exception / failure fallback
    def test_L_gemini_failure_fallback(self):
        with patch("voice_assistant.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = Exception("API rate limit exceeded")
            mock_genai.GenerativeModel.return_value = mock_model
            with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
                res = self.app.post("/api/assistant/query", json={"query": "Tell me about weather", "language": "en"})
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertEqual(data["source"], "rule_based_engine")

    # Test M: Malformed Gemini JSON fallback
    def test_M_malformed_gemini_json_fallback(self):
        with patch("voice_assistant.genai") as mock_genai:
            mock_model = MagicMock()
            mock_resp = MagicMock()
            mock_resp.text = "NOT JSON TEXT AT ALL {broken"
            mock_model.generate_content.return_value = mock_resp
            mock_genai.GenerativeModel.return_value = mock_model
            with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
                res = self.app.post("/api/assistant/query", json={"query": "Check weather", "language": "en"})
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertEqual(data["source"], "rule_based_engine")

    # Test N: Malformed requests (null body, non-dict, missing query)
    def test_N_malformed_requests(self):
        # Empty POST
        res1 = self.app.post("/api/assistant/query", data="", content_type="application/json")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.get_json()["intent"], "unknown")

        # Missing query key
        res2 = self.app.post("/api/assistant/query", json={"language": "en"})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.get_json()["intent"], "unknown")

        # Extra oversized / unexpected fields
        res3 = self.app.post("/api/assistant/query", json={"query": "Hello", "random_junk": "x" * 5000})
        self.assertEqual(res3.status_code, 200)

    # Test O: Missing optional context fields
    def test_O_missing_optional_context(self):
        res = self.app.post("/api/assistant/query", json={"query": "How to irrigate?", "context": {}})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("spoken_response", data)

    # Test P: Unsupported language falls back to 'en'
    def test_P_unsupported_language_fallback(self):
        res = self.app.post("/api/assistant/query", json={"query": "Hello", "language": "french_fr"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["language"], "en")

    # Test Q: Guardrail against hallucinated dosage
    def test_Q_no_hallucinated_dosage(self):
        payload = {
            "query": "Give me exact dosage of urea for cotton",
            "language": "en",
            "context": {}
        }
        res = self.app.post("/api/assistant/query", json=payload)
        data = res.get_json()
        self.assertTrue(data["expert_escalation"]["recommended"])
        self.assertIn("does not have a verified fertilizer dosage", data["spoken_response"])

    # Test R: Guardrail against hallucinated weather
    def test_R_no_hallucinated_weather(self):
        payload = {
            "query": "What is the temperature in my farm right now?",
            "language": "en",
            "context": {} # No weather provided
        }
        res = self.app.post("/api/assistant/query", json=payload)
        data = res.get_json()
        # Should not invent a fake number like 42°C
        self.assertNotIn("°C", data["spoken_response"])
        self.assertIn("Weather tab", data["spoken_response"])

    # Test S: Guardrail against disease certainty
    def test_S_no_disease_certainty(self):
        payload = {
            "query": "Is my crop 100% infected with bacterial blight?",
            "language": "en",
            "context": {}
        }
        res = self.app.post("/api/assistant/query", json=payload)
        data = res.get_json()
        self.assertNotIn("100% confirmed", data["spoken_response"].lower())
        self.assertIn("may be consistent with", data["spoken_response"])

    # Test T: Existing /api/chat unchanged
    def test_T_existing_chat_unchanged(self):
        res = self.app.post("/api/chat", json={"message": "What is urea?", "lang": "en"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("reply", data)

    # Test U: Existing /api/farm/analyze unchanged
    @patch("api.get_weather_by_coords")
    @patch("api.reverse_geocode")
    @patch("api.get_soil_by_coords")
    def test_U_existing_analyze_unchanged(self, mock_soil, mock_geo, mock_weather):
        mock_weather.return_value = {"ok": True, "temperature": 28, "humidity": 60, "weather_desc": "Clear"}
        mock_geo.return_value = {"district": "Hyderabad", "state": "Telangana"}
        mock_soil.return_value = {"ok": True, "N": 90, "P": 42, "K": 43, "ph": 6.5, "moisture_pct": 55, "soil_type": "Loamy"}

        payload = {
            "latitude": 17.3850,
            "longitude": 78.4867,
            "crop": "rice",
            "season": "Kharif",
            "N": 90, "P": 42, "K": 43, "ph": 6.5
        }
        res = self.app.post("/api/farm/analyze", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("crop_recommendation", data)
        self.assertIn("fertilizer_recommendation", data)
        self.assertIn("irrigation_guidance", data)
        self.assertIn("location", data)

    # Test V: Existing /api/farm/action-plan unchanged
    def test_V_existing_action_plan_unchanged(self):
        payload = {
            "farm_analysis": {
                "request": {"active_crop": "rice", "season": "Kharif"},
                "alerts": [],
                "crop_recommendation": {"top_3": [{"crop": "rice", "suitability_score": 95}]},
                "fertilizer_recommendation": {"recommended_fertilizer": {"fertilizer": "Urea", "details": {"qty_per_ha": 40}}},
                "irrigation_guidance": {"recommendation": "Irrigate tomorrow", "net_irrigation_needed_mm_day": 3.2}
            },
            "language": "en"
        }
        res = self.app.post("/api/farm/action-plan", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("immediate_actions", data)
        self.assertIn("this_week_plan", data)


if __name__ == "__main__":
    unittest.main()
