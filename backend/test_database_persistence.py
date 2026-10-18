"""
AGRIFY — Persistent Farm Intelligence & Ownership Test Suite
Module: backend/test_database_persistence.py

Verifies:
1. Database URL normalization and engine options.
2. Token generation, HMAC-SHA256 hashing, and verification.
3. Farm profile CRUD with token-based access control.
4. Multi-tenant isolation (Owner A cannot read/mutate Owner B's records).
5. Unauthorized requests (missing token -> 401, invalid token -> 403).
6. Atomic persistence of multi-table farm analyses and action plans.
7. Transactional integrity and rollback on simulated failure.
8. Stateless mode fallback when database is disabled/unconfigured.
"""

import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import json
import unittest
from unittest.mock import patch, MagicMock

# Set an isolated in-memory SQLite database before importing Flask app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from api import app, is_db_available

import database_config
import auth
from models.database import (
    db,
    FarmProfile,
    WeatherSnapshot,
    SoilSummary,
    CropRecommendation,
    FarmActionPlan,
)


class TestDatabaseConfiguration(unittest.TestCase):
    """Test database URL parsing, normalization, and engine options."""

    def test_postgres_url_normalization(self):
        raw = "postgres://user:pass@ep-cool-db.us-east-1.postgres.render.com/agrify"
        normalized = database_config.normalize_database_url(raw)
        self.assertTrue(normalized.startswith("postgresql://"))
        self.assertNotIn("postgres://", normalized)

    def test_postgresql_url_preservation(self):
        raw = "postgresql://user:pass@localhost:5432/agrify"
        normalized = database_config.normalize_database_url(raw)
        self.assertEqual(normalized, raw)

    def test_empty_database_url(self):
        self.assertEqual(database_config.normalize_database_url(""), "")
        self.assertEqual(database_config.normalize_database_url(None), "")

    def test_engine_options_sqlite(self):
        options = database_config.get_sqlalchemy_engine_options("sqlite:///:memory:")
        self.assertTrue(options.get("pool_pre_ping"))
        self.assertNotIn("pool_recycle", options)

    def test_engine_options_postgres(self):
        options = database_config.get_sqlalchemy_engine_options("postgresql://localhost/db")
        self.assertTrue(options.get("pool_pre_ping"))
        self.assertEqual(options.get("pool_recycle"), 1800)
        self.assertEqual(options.get("pool_timeout"), 30)


class TestAuthAndOwnership(unittest.TestCase):
    """Test cryptographic token generation and verification."""

    def test_token_format_and_entropy(self):
        token = auth.generate_owner_token()
        self.assertTrue(token.startswith("agf_"))
        self.assertGreaterEqual(len(token), 32)
        token2 = auth.generate_owner_token()
        self.assertNotEqual(token, token2)

    def test_token_hashing_and_verification(self):
        token = auth.generate_owner_token()
        token_hash = auth.hash_owner_token(token)
        self.assertNotEqual(token, token_hash)
        self.assertEqual(len(token_hash), 64)  # SHA-256 hex length

        # Valid verification
        self.assertTrue(auth.verify_owner_token(token_hash, token))

        # Invalid token rejection
        self.assertFalse(auth.verify_owner_token(token_hash, "wrong-token"))
        self.assertFalse(auth.verify_owner_token(token_hash, ""))


class TestFarmPersistenceAndIsolation(unittest.TestCase):
    """Test full database persistence, ownership verification, and tenant isolation."""

    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = app.test_client()

        with app.app_context():
            db.create_all()



    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_farm_profile_success(self):
        payload = {
            "farmer_name": "Ramesh Rao",
            "latitude": 17.3850,
            "longitude": 78.4867,
            "area_acres": 3.5,
            "village": "Gachibowli",
            "district": "Rangareddy",
            "state": "Telangana",
            "pincode": "500032",
        }
        resp = self.client.post("/api/farm/profile", json=payload)
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()

        self.assertIn("farm_uid", data)
        self.assertIn("owner_token", data)
        self.assertTrue(data["owner_token"].startswith("agf_"))

        # Verify plain-text token is NOT stored in the database
        with app.app_context():
            farm = FarmProfile.query.filter_by(farm_uid=data["farm_uid"]).first()
            self.assertIsNotNone(farm)
            self.assertNotEqual(farm.owner_token_hash, data["owner_token"])
            self.assertTrue(auth.verify_owner_token(farm.owner_token_hash, data["owner_token"]))

    def test_unauthorized_profile_access(self):
        # Create a farm profile
        create_resp = self.client.post("/api/farm/profile", json={
            "farmer_name": "Sita Devi",
            "latitude": 16.5062,
            "longitude": 80.6480,
            "area_acres": 2.0,
        })
        farm_uid = create_resp.get_json()["farm_uid"]

        # Missing token -> 401
        resp_no_token = self.client.get(f"/api/farm/profile/{farm_uid}")
        self.assertEqual(resp_no_token.status_code, 401)

        # Invalid token -> 403
        resp_bad_token = self.client.get(
            f"/api/farm/profile/{farm_uid}",
            headers={"X-Farm-Token": "agf_invalid_token_12345"},
        )
        self.assertEqual(resp_bad_token.status_code, 403)

    def test_multi_tenant_isolation(self):
        """Owner A must not be able to read or mutate Owner B's farm profile or history."""
        # Create Farm A
        resp_a = self.client.post("/api/farm/profile", json={
            "farmer_name": "Farmer A",
            "latitude": 17.1,
            "longitude": 78.1,
            "area_acres": 2.0,
        })
        farm_a = resp_a.get_json()

        # Create Farm B
        resp_b = self.client.post("/api/farm/profile", json={
            "farmer_name": "Farmer B",
            "latitude": 17.2,
            "longitude": 78.2,
            "area_acres": 4.0,
        })
        farm_b = resp_b.get_json()

        # Owner A accessing Farm A with header -> 200
        auth_resp_a = self.client.get(
            f"/api/farm/profile/{farm_a['farm_uid']}",
            headers={"X-Farm-Token": farm_a["owner_token"]},
        )
        self.assertEqual(auth_resp_a.status_code, 200)
        self.assertEqual(auth_resp_a.get_json()["farmer_name"], "Farmer A")

        # Owner A attempting to access Farm B using Token A -> 403 Forbidden
        attack_resp = self.client.get(
            f"/api/farm/profile/{farm_b['farm_uid']}",
            headers={"X-Farm-Token": farm_a["owner_token"]},
        )
        self.assertEqual(attack_resp.status_code, 403)

        # Owner A attempting to access Farm B's history using Bearer token -> 403 Forbidden
        history_attack_resp = self.client.get(
            f"/api/farm/history/{farm_b['farm_uid']}",
            headers={"Authorization": f"Bearer {farm_a['owner_token']}"},
        )
        self.assertEqual(history_attack_resp.status_code, 403)

    def test_farm_analysis_atomic_persistence(self):
        """Analyze farm with farm_uid and valid token; verify multi-table persistence."""
        create_resp = self.client.post("/api/farm/profile", json={
            "farmer_name": "Gopal Reddy",
            "latitude": 17.3850,
            "longitude": 78.4867,
            "area_acres": 3.0,
        })
        farm_data = create_resp.get_json()
        farm_uid = farm_data["farm_uid"]
        owner_token = farm_data["owner_token"]

        analysis_payload = {
            "latitude": 17.3850,
            "longitude": 78.4867,
            "area_acres": 3.0,
            "season": "Kharif",
            "farm_uid": farm_uid,
            "owner_token": owner_token,
        }

        # Mock external APIs to ensure deterministic offline execution
        with patch("api.get_weather_by_coords", return_value={"ok": True, "temperature": 29.0, "humidity": 65.0}), \
             patch("api.get_soil_by_coords", return_value={"ok": True, "N": 60, "P": 45, "K": 35, "ph": 6.8, "moisture_pct": 35, "organic_carbon": 55}), \
             patch("api.reverse_geocode", return_value={"district": "Hyderabad", "state": "Telangana"}):

            resp = self.client.post("/api/farm/analyze", json=analysis_payload)
            self.assertEqual(resp.status_code, 200)
            res_data = resp.get_json()

            self.assertTrue(res_data.get("persistence", {}).get("persisted"))
            rec_id = res_data["persistence"]["crop_recommendation_id"]
            self.assertIsNotNone(rec_id)

        # Verify records exist in database
        with app.app_context():
            rec = db.session.get(CropRecommendation, rec_id)
            self.assertIsNotNone(rec)

            self.assertEqual(rec.season, "Kharif")
            self.assertEqual(rec.district, "Hyderabad")

            weather_snaps = WeatherSnapshot.query.filter_by(farm_id=rec.farm_id).all()
            self.assertGreaterEqual(len(weather_snaps), 1)

            soil_sums = SoilSummary.query.filter_by(farm_id=rec.farm_id).all()
            self.assertGreaterEqual(len(soil_sums), 1)

        # Test action plan persistence
        action_payload = {
            "farm_uid": farm_uid,
            "owner_token": owner_token,
            "crop_recommendation_id": rec_id,
            "crop": "cotton",
            "crop_recommendation": res_data["crop_recommendation"],
            "weather": {"temperature": 29.0, "humidity": 65.0, "forecast_daily": []},
            "soil": {"N": 60, "P": 45, "K": 35, "ph": 6.8},
            "alerts": [],
        }

        action_resp = self.client.post("/api/farm/action-plan", json=action_payload)
        self.assertEqual(action_resp.status_code, 200)
        action_data = action_resp.get_json()
        self.assertTrue(action_data.get("persistence", {}).get("persisted"))

        # Verify History endpoint returns everything cleanly
        history_resp = self.client.get(
            f"/api/farm/history/{farm_uid}",
            headers={"X-Farm-Token": owner_token},
        )
        self.assertEqual(history_resp.status_code, 200)
        hist = history_resp.get_json()
        self.assertEqual(len(hist["crop_recommendations"]), 1)
        self.assertEqual(len(hist["action_plans"]), 1)
        self.assertEqual(len(hist["weather_snapshots"]), 1)
        self.assertEqual(len(hist["soil_summaries"]), 1)

    def test_transaction_rollback_on_failure(self):
        """Simulate a failure during persistence to ensure atomic rollback."""
        create_resp = self.client.post("/api/farm/profile", json={
            "farmer_name": "Anand Rao",
            "latitude": 18.0,
            "longitude": 79.0,
            "area_acres": 2.0,
        })
        farm_data = create_resp.get_json()
        farm_uid = farm_data["farm_uid"]
        owner_token = farm_data["owner_token"]

        analysis_payload = {
            "latitude": 18.0,
            "longitude": 79.0,
            "area_acres": 2.0,
            "season": "Kharif",
            "farm_uid": farm_uid,
            "owner_token": owner_token,
        }

        # Mock external APIs and inject an exception into db.session.commit
        with patch("api.get_weather_by_coords", return_value={"ok": True, "temperature": 30.0, "humidity": 60.0}), \
             patch("api.get_soil_by_coords", return_value={"ok": True, "N": 50, "P": 40, "K": 30, "ph": 7.0}), \
             patch("api.reverse_geocode", return_value={"district": "Warangal", "state": "Telangana"}), \
             patch.object(db.session, "commit", side_effect=Exception("Simulated disk error")):

            resp = self.client.post("/api/farm/analyze", json=analysis_payload)
            self.assertEqual(resp.status_code, 500)
            self.assertIn("error", resp.get_json())

        # Verify no orphaned recommendations, snapshots, or soil entries were committed
        with app.app_context():
            farm = FarmProfile.query.filter_by(farm_uid=farm_uid).first()
            self.assertEqual(len(farm.crop_recommendations), 0)
            self.assertEqual(len(farm.weather_snapshots), 0)
            self.assertEqual(len(farm.soil_summaries), 0)

    def test_stateless_fallback_when_db_disabled(self):
        """When database is not active, endpoints must not crash with 500."""
        # Temporarily mock is_db_available to return False
        with patch("api.is_db_available", return_value=False):
            # 1. Profile registration returns stateless response
            prof_resp = self.client.post("/api/farm/profile", json={
                "farmer_name": "Stateless Farmer",
                "latitude": 15.0,
                "longitude": 77.0,
                "area_acres": 1.5,
            })
            self.assertEqual(prof_resp.status_code, 200)
            data = prof_resp.get_json()
            self.assertTrue(data.get("stateless"))
            self.assertIsNone(data.get("owner_token"))

            # 2. Farm analysis operates statelessly
            with patch("api.get_weather_by_coords", return_value={"ok": True, "temperature": 28.0, "humidity": 60.0}), \
                 patch("api.get_soil_by_coords", return_value={"ok": True, "N": 50, "P": 40, "K": 30, "ph": 7.0}), \
                 patch("api.reverse_geocode", return_value={"district": "Kurnool", "state": "Andhra Pradesh"}):
                analyze_resp = self.client.post("/api/farm/analyze", json={
                    "latitude": 15.0,
                    "longitude": 77.0,
                    "area_acres": 1.5,
                    "season": "Kharif",
                })
                self.assertEqual(analyze_resp.status_code, 200)
                self.assertFalse(analyze_resp.get_json().get("persistence", {}).get("persisted"))

    def test_token_rotation_success_and_invalidation(self):
        """Rotating owner token must succeed with valid token and immediately invalidate old token."""
        create_resp = self.client.post("/api/farm/profile", json={
            "farmer_name": "Kavitha Reddy",
            "latitude": 17.5,
            "longitude": 78.5,
            "area_acres": 2.5,
        })
        farm_data = create_resp.get_json()
        farm_uid = farm_data["farm_uid"]
        old_token = farm_data["owner_token"]

        # 1. Rotate token
        rotate_resp = self.client.post(
            f"/api/farm/profile/{farm_uid}/rotate-token",
            headers={"X-Farm-Token": old_token},
        )
        self.assertEqual(rotate_resp.status_code, 200)
        new_token = rotate_resp.get_json()["owner_token"]
        self.assertNotEqual(old_token, new_token)
        self.assertTrue(new_token.startswith("agf_"))

        # 2. Old token is now rejected with 403
        old_token_resp = self.client.get(
            f"/api/farm/profile/{farm_uid}",
            headers={"X-Farm-Token": old_token},
        )
        self.assertEqual(old_token_resp.status_code, 403)

        # 3. New token succeeds with 200
        new_token_resp = self.client.get(
            f"/api/farm/profile/{farm_uid}",
            headers={"X-Farm-Token": new_token},
        )
        self.assertEqual(new_token_resp.status_code, 200)
        self.assertEqual(new_token_resp.get_json()["farmer_name"], "Kavitha Reddy")

    def test_token_rotation_unauthorized(self):
        create_resp = self.client.post("/api/farm/profile", json={
            "farmer_name": "Sunil Kumar",
            "latitude": 17.6,
            "longitude": 78.6,
            "area_acres": 1.0,
        })
        farm_uid = create_resp.get_json()["farm_uid"]

        # Missing token -> 401
        self.assertEqual(
            self.client.post(f"/api/farm/profile/{farm_uid}/rotate-token").status_code,
            401
        )
        # Invalid token -> 403
        self.assertEqual(
            self.client.post(
                f"/api/farm/profile/{farm_uid}/rotate-token",
                headers={"X-Farm-Token": "agf_invalid_token"}
            ).status_code,
            403
        )

    def test_delete_farm_profile_and_cascade(self):
        """Deleting a farm profile must delete the profile and all linked records cleanly."""
        create_resp = self.client.post("/api/farm/profile", json={
            "farmer_name": "Balram Das",
            "latitude": 17.3850,
            "longitude": 78.4867,
            "area_acres": 3.0,
        })
        farm_data = create_resp.get_json()
        farm_uid = farm_data["farm_uid"]
        owner_token = farm_data["owner_token"]

        # Add records to the farm
        with patch("api.get_weather_by_coords", return_value={"ok": True, "temperature": 29.0, "humidity": 65.0}), \
             patch("api.get_soil_by_coords", return_value={"ok": True, "N": 60, "P": 45, "K": 35, "ph": 6.8}), \
             patch("api.reverse_geocode", return_value={"district": "Hyderabad", "state": "Telangana"}):
            self.client.post("/api/farm/analyze", json={
                "latitude": 17.3850,
                "longitude": 78.4867,
                "area_acres": 3.0,
                "season": "Kharif",
                "farm_uid": farm_uid,
                "owner_token": owner_token,
            })

        # Verify child records exist in database
        with app.app_context():
            farm = FarmProfile.query.filter_by(farm_uid=farm_uid).first()
            farm_id = farm.id
            self.assertEqual(len(farm.crop_recommendations), 1)
            self.assertEqual(len(farm.weather_snapshots), 1)
            self.assertEqual(len(farm.soil_summaries), 1)

        # Delete farm profile
        del_resp = self.client.delete(
            f"/api/farm/profile/{farm_uid}",
            headers={"X-Farm-Token": owner_token},
        )
        self.assertEqual(del_resp.status_code, 200)

        # Verify farm profile AND children are all removed
        with app.app_context():
            self.assertIsNone(FarmProfile.query.filter_by(farm_uid=farm_uid).first())
            self.assertEqual(WeatherSnapshot.query.filter_by(farm_id=farm_id).count(), 0)
            self.assertEqual(SoilSummary.query.filter_by(farm_id=farm_id).count(), 0)
            self.assertEqual(CropRecommendation.query.filter_by(farm_id=farm_id).count(), 0)

    def test_farm_analyze_upfront_auth_rejection_prevents_api_calls(self):
        """Unauthorized analyze requests must be rejected upfront without calling external APIs."""
        create_resp = self.client.post("/api/farm/profile", json={
            "farmer_name": "Target Farmer",
            "latitude": 17.0,
            "longitude": 78.0,
            "area_acres": 2.0,
        })
        farm_uid = create_resp.get_json()["farm_uid"]

        mock_weather = MagicMock()
        mock_soil = MagicMock()
        with patch("api.get_weather_by_coords", mock_weather), \
             patch("api.get_soil_by_coords", mock_soil):

            # Attempt analyze with bad token
            resp = self.client.post("/api/farm/analyze", json={
                "latitude": 17.0,
                "longitude": 78.0,
                "area_acres": 2.0,
                "season": "Kharif",
                "farm_uid": farm_uid,
                "owner_token": "agf_fraudulent_token",
            })
            self.assertEqual(resp.status_code, 403)

            # Assert external APIs were never contacted
            mock_weather.assert_not_called()
            mock_soil.assert_not_called()


class TestProductionConfigurationValidation(unittest.TestCase):
    """Test validate_production_configuration for secret enforcement and database safety."""

    def test_development_mode_skips_validation(self):
        """In development/testing mode, no errors are raised even with weak config."""
        env = {"FLASK_ENV": "development", "SECRET_KEY": "weak"}
        result = database_config.validate_production_configuration(environ=env)
        self.assertFalse(result["is_production"])
        self.assertEqual(result["status"], "development_or_testing")

    def test_production_rejects_missing_secret_key(self):
        """Production mode must fail when SECRET_KEY is absent."""
        env = {"FLASK_ENV": "production"}
        with self.assertRaises(ValueError) as ctx:
            database_config.validate_production_configuration(environ=env)
        self.assertIn("SECRET_KEY", str(ctx.exception))

    def test_production_rejects_default_secret_key(self):
        """Production mode must fail with the default development placeholder key."""
        env = {"FLASK_ENV": "production", "SECRET_KEY": "agrify-default-secret-salt-key"}
        with self.assertRaises(ValueError) as ctx:
            database_config.validate_production_configuration(environ=env)
        self.assertIn("SECRET_KEY", str(ctx.exception))

    def test_production_rejects_short_secret_key(self):
        """Production mode must fail when SECRET_KEY is shorter than 16 characters."""
        env = {"FLASK_ENV": "production", "SECRET_KEY": "short123"}
        with self.assertRaises(ValueError) as ctx:
            database_config.validate_production_configuration(environ=env)
        self.assertIn("minimum 16 characters", str(ctx.exception))

    def test_production_rejects_common_insecure_keys(self):
        """Common insecure placeholder keys must be rejected in production."""
        insecure = ["secret", "changeme", "development-key", "12345678"]
        for key in insecure:
            env = {"FLASK_ENV": "production", "SECRET_KEY": key}
            with self.assertRaises(ValueError, msg=f"Should reject key: {key}"):
                database_config.validate_production_configuration(environ=env)

    def test_production_rejects_sqlite_database(self):
        """SQLite must not be allowed as a production database."""
        env = {
            "FLASK_ENV": "production",
            "SECRET_KEY": "a-very-long-and-random-production-key-that-is-secure",
            "DATABASE_URL": "sqlite:///data.db",
        }
        with self.assertRaises(ValueError) as ctx:
            database_config.validate_production_configuration(environ=env)
        self.assertIn("SQLite", str(ctx.exception))

    def test_production_accepts_valid_configuration(self):
        """Valid production configuration with strong secret and PostgreSQL must succeed."""
        env = {
            "FLASK_ENV": "production",
            "SECRET_KEY": "a-very-long-and-random-production-key-that-is-secure",
            "DATABASE_URL": "postgresql://user:pass@db.render.com:5432/agrify",
        }
        result = database_config.validate_production_configuration(environ=env)
        self.assertTrue(result["is_production"])
        self.assertEqual(result["status"], "production_validated")
        self.assertTrue(result["database_configured"])
        self.assertEqual(result["persistence_mode"], "persistent")

    def test_production_stateless_without_database_url(self):
        """Production without DATABASE_URL is allowed but marked stateless."""
        env = {
            "FLASK_ENV": "production",
            "SECRET_KEY": "a-very-long-and-random-production-key-that-is-secure",
        }
        result = database_config.validate_production_configuration(environ=env)
        self.assertTrue(result["is_production"])
        self.assertFalse(result["database_configured"])
        self.assertEqual(result["persistence_mode"], "stateless")

    def test_environment_variable_also_triggers_production(self):
        """ENVIRONMENT=production must trigger production validation."""
        env = {"ENVIRONMENT": "production", "SECRET_KEY": "short"}
        with self.assertRaises(ValueError):
            database_config.validate_production_configuration(environ=env)


class TestPersistenceMode(unittest.TestCase):
    """Test get_persistence_mode detection."""

    def test_stateless_when_no_database(self):
        """When DATABASE_URL is empty, persistence mode must be 'stateless'."""
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            mode = database_config.get_persistence_mode()
            self.assertEqual(mode, "stateless")

    def test_persistent_when_database_configured(self):
        """When DATABASE_URL is set, persistence mode must be 'persistent'."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/agrify"}, clear=False):
            mode = database_config.get_persistence_mode()
            self.assertEqual(mode, "persistent")

    def test_in_memory_test_mode(self):
        """Under testing with in-memory SQLite, mode must be 'in_memory_test'."""
        mode = database_config.get_persistence_mode(
            is_testing=True,
            current_uri="sqlite:///:memory:"
        )
        self.assertEqual(mode, "in_memory_test")

    def test_database_enabled_flag(self):
        """is_database_enabled must reflect DATABASE_URL presence."""
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            self.assertFalse(database_config.is_database_enabled())
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/db"}, clear=False):
            self.assertTrue(database_config.is_database_enabled())


if __name__ == "__main__":
    unittest.main()
