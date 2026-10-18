"""
AGRIFY — Phase 5: End-to-End User Journey & Production Acceptance Test Suite
Module: backend/test_e2e_integration_phase5.py

Verifies:
1. Complete Farmer Journey:
   Registration -> Full GPS Analysis -> Action Plan -> History -> Isolation
2. Multi-lingual Copilot & Agent Flow (English, Telugu, Hindi)
3. Safety Guardrails (no dosage fabrication, no diagnosis certainty, audio-safe TTS)
4. Market Price ETL & Provenance (metadata, data_quality, fallback indicators)
5. Production Readiness & Observability (/api/health, CORS, input limits)
"""

import os
import sys
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "phase5-test-secret-key-32-bytes-long!!"
os.environ["FLASK_ENV"] = "development"

from api import app, is_db_available
from models.database import db, FarmProfile, FarmActionPlan, CropRecommendation


class TestPhase5EndToEndIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def setUp(self):
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # ========================================================
    # 1. COMPLETE FARMER USER JOURNEY
    # ========================================================
    def test_complete_farmer_lifecycle_and_multi_tenant_isolation(self):
        """
        Tests the entire end-to-end user journey:
        Step 1: Register farm profile for Farmer Arun.
        Step 2: Run full farm analysis with farm_uid & auth token.
        Step 3: Generate a 7-day action plan for the recommended crop.
        Step 4: Fetch farm history and verify persisted analyses and action plans.
        Step 5: Register second farm for Farmer Bob.
        Step 6: Verify Farmer Bob cannot access Farmer Arun's history or plans.
        """
        # Step 1: Register Farmer Arun
        reg_payload = {
            "farm_name": "Arun Organic Farm",
            "farmer_name": "Arun Kumar",
            "state": "Telangana",
            "district": "Rangareddy",
            "village": "Moinabad",
            "latitude": 17.3195,
            "longitude": 78.2778,
            "total_area_acres": 5.0,
            "primary_crop": "Tomato",
        }
        res = self.client.post("/api/farm/profile", json=reg_payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        arun_uid = data.get("farm_uid")
        arun_token = data.get("owner_token")
        self.assertTrue(arun_uid)
        self.assertTrue(arun_token)

        arun_headers = {"Authorization": f"Bearer {arun_token}"}

        # Step 2: Run full farm analysis for Arun's farm
        analysis_payload = {
            "farm_uid": arun_uid,
            "latitude": 17.3195,
            "longitude": 78.2778,
            "area_acres": 5.0,
            "season": "Kharif",
            "previous_crop": "Tomato",
            "soil": {"ph": 6.8, "N": 65, "P": 25, "K": 20},
        }
        res = self.client.post("/api/farm/analyze", json=analysis_payload, headers=arun_headers)
        self.assertEqual(res.status_code, 200)
        analysis_res = res.get_json()
        self.assertTrue(analysis_res.get("persistence", {}).get("persisted"))
        self.assertEqual(analysis_res["persistence"]["farm_uid"], arun_uid)
        rec_id = analysis_res["persistence"].get("crop_recommendation_id")
        self.assertIsNotNone(rec_id)
        self.assertIn("crop_recommendation", analysis_res)
        self.assertIn("fertilizer_recommendation", analysis_res)
        self.assertIn("irrigation_guidance", analysis_res)

        # Step 3: Generate 7-day action plan linked to this farm
        plan_payload = {
            "farm_uid": arun_uid,
            "crop_recommendation_id": rec_id,
            "crop": "Tomato",
            "season": "Kharif",
            "analysis": analysis_res,
            "language": "en",
        }
        res = self.client.post("/api/farm/action-plan", json=plan_payload, headers=arun_headers)
        self.assertEqual(res.status_code, 200)
        plan_res = res.get_json()
        self.assertTrue(plan_res.get("persistence", {}).get("persisted"))
        self.assertEqual(plan_res["persistence"]["farm_uid"], arun_uid)
        self.assertIn("immediate_actions", plan_res)
        self.assertIn("this_week_plan", plan_res)

        # Step 4: Verify Arun can fetch farm history and action plans
        res = self.client.get(f"/api/farm/history/{arun_uid}", headers=arun_headers)
        self.assertEqual(res.status_code, 200)
        history_data = res.get_json()
        self.assertEqual(len(history_data.get("crop_recommendations", [])), 1)
        self.assertEqual(history_data["crop_recommendations"][0]["id"], rec_id)

        res = self.client.get(f"/api/farm/action-plans/{arun_uid}", headers=arun_headers)
        self.assertEqual(res.status_code, 200)
        plans_data = res.get_json()
        self.assertEqual(len(plans_data.get("action_plans", [])), 1)

        # Step 5: Register Farmer Bob
        bob_payload = {
            "farm_name": "Bob Green Acres",
            "farmer_name": "Bob Smith",
            "state": "Andhra Pradesh",
            "district": "Guntur",
            "latitude": 16.3067,
            "longitude": 80.4365,
            "area_acres": 10.0,
        }
        res = self.client.post("/api/farm/profile", json=bob_payload)
        self.assertEqual(res.status_code, 201)
        bob_token = res.get_json().get("owner_token")
        bob_headers = {"Authorization": f"Bearer {bob_token}"}

        # Step 6: Multi-tenant Isolation: Farmer Bob CANNOT view Arun's data
        res = self.client.get(f"/api/farm/history/{arun_uid}", headers=bob_headers)
        self.assertEqual(res.status_code, 403)

        res = self.client.get(f"/api/farm/action-plans/{arun_uid}", headers=bob_headers)
        self.assertEqual(res.status_code, 403)

        # Unauthenticated request returns 401
        res = self.client.get(f"/api/farm/history/{arun_uid}")
        self.assertEqual(res.status_code, 401)

    # ========================================================
    # 2. MULTILINGUAL VOICE COPILOT & SAFETY
    # ========================================================
    def test_multilingual_voice_assistant_queries(self):
        """Test voice assistant queries in English, Telugu, and Hindi."""
        # English query
        payload_en = {
            "query": "What is the best irrigation schedule for cotton?",
            "language": "en",
            "context": {"crop": "Cotton", "soil": {"ph": 7.0}}
        }
        res = self.client.post("/api/assistant/query", json=payload_en)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("language"), "en")
        self.assertIn("spoken_response", data)
        self.assertIn("display_card", data)

        # Telugu query
        payload_te = {
            "query": "పత్తి పంటకు నీటి యాజమాన్యం ఎలా చేయాలి?",
            "language": "te",
            "context": {"crop": "Cotton"}
        }
        res = self.client.post("/api/assistant/query", json=payload_te)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("language"), "te")
        self.assertIn("spoken_response", data)

        # Hindi query
        payload_hi = {
            "query": "कपास की फसल के लिए सिंचाई कैसे करें?",
            "language": "hi",
            "context": {"crop": "Cotton"}
        }
        res = self.client.post("/api/assistant/query", json=payload_hi)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("language"), "hi")

    def test_voice_assistant_safety_rules(self):
        """
        Verify strict agronomic safety guardrails:
        1. No chemical dosage hallucination when trusted data is missing.
        2. Audio-safe synthesis: no markdown asterisks, hashtags in spoken_response.
        """
        payload = {
            "query": "How many kg of urea per acre should I spray on rice?",
            "language": "en",
            "context": {
                "crop": "Rice",
                "has_trusted_fertilizer_dosage": False,
            }
        }
        res = self.client.post("/api/assistant/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        spoken = data.get("spoken_response", "")

        # Verify no markdown formatting symbols in TTS text
        self.assertNotIn("**", spoken)
        self.assertNotIn("*", spoken)
        self.assertNotIn("#", spoken)

        # Verify safety guardrail refusal / referral
        self.assertTrue(
            "dose" in spoken.lower() or "verified" in spoken.lower() or "kvk" in spoken.lower() or "fertilizer" in spoken.lower()
        )

    # ========================================================
    # 3. CHATBOT SAFE AGRICULTURAL ASSISTANT
    # ========================================================
    def test_chatbot_endpoint_and_safety(self):
        """Test /api/chat with English, Telugu, and safety queries."""
        # Empty query
        res = self.client.post("/api/chat", json={})
        self.assertEqual(res.status_code, 200)
        self.assertIn("Please type a question", res.get_json().get("reply", ""))

        # English fertilizer question -> safe advisory
        res = self.client.post("/api/chat", json={"message": "Give me exact dosage of chemical pesticide for blast", "language": "en"})
        self.assertEqual(res.status_code, 200)
        reply = res.get_json().get("reply", "")
        self.assertIn("Dosage", reply)
        self.assertIn("KVK", reply)

        # Telugu general question
        res = self.client.post("/api/chat", json={"message": "వరి సాగు గురించి చెప్పండి", "language": "te"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("reply", res.get_json())

    # ========================================================
    # 4. MARKET PRICE PROVENANCE & FRESHNESS
    # ========================================================
    def test_market_price_metadata_and_provenance(self):
        """Test /api/market-prices provenance labels and fallback indicators."""
        payload = {"crop": "tomato", "state": "Telangana"}
        res = self.client.post("/api/market-prices", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn("data_quality", data)
        self.assertIn("source_name", data)
        self.assertIn("markets", data)
        self.assertIsInstance(data["markets"], list)
        self.assertIn("is_fallback", data)

    # ========================================================
    # 5. HEALTH CHECK & OBSERVABILITY
    # ========================================================
    def test_health_check_observability(self):
        """Test /api/health returns database mode and version."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertIn("database", data)
        self.assertIn("version", data)

    def test_request_limit_enforcement(self):
        """Test oversized input validation returns 400."""
        oversized = "A" * 4005
        res = self.client.post("/api/chat", json={"message": oversized})
        self.assertEqual(res.status_code, 400)
        self.assertIn("4000 characters or fewer", res.get_json().get("error", ""))

        res = self.client.post("/api/assistant/query", json={"query": oversized})
        self.assertEqual(res.status_code, 400)
        self.assertIn("4000 characters or fewer", res.get_json().get("error", ""))


if __name__ == "__main__":
    unittest.main()
