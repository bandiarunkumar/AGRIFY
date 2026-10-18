"""
CORS and origin allowlist security test suite.
Verifies allowed origins, rejected origins, preflight requests, and existing API routes.
"""
import os
import unittest
import api


class TestCORSConfiguration(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()

    def test_allowed_origin_receives_cors_header(self):
        """Allowed origin (http://localhost:5173) receives matching Access-Control-Allow-Origin header."""
        response = self.client.get(
            "/api/health",
            headers={"Origin": "http://localhost:5173"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")
        # Ensure wildcard is NOT returned
        self.assertNotEqual(response.headers.get("Access-Control-Allow-Origin"), "*")

    def test_local_127_origin_receives_cors_header(self):
        """Allowed local IP origin (http://127.0.0.1:5173) receives matching header."""
        response = self.client.get(
            "/api/health",
            headers={"Origin": "http://127.0.0.1:5173"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://127.0.0.1:5173")

    def test_rejected_origin_does_not_receive_allow_header(self):
        """Untrusted origin (http://untrusted-malicious-site.com) does NOT receive allow-origin header."""
        response = self.client.get(
            "/api/health",
            headers={"Origin": "http://untrusted-malicious-site.com"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))

    def test_preflight_options_request_allowed(self):
        """Preflight OPTIONS request from allowed origin returns 200 and allowed methods."""
        response = self.client.options(
            "/api/assistant/query",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")
        allow_methods = response.headers.get("Access-Control-Allow-Methods", "")
        self.assertIn("POST", allow_methods)

    def test_preflight_options_request_rejected(self):
        """Preflight OPTIONS request from untrusted origin does NOT return allow-origin header."""
        response = self.client.options(
            "/api/assistant/query",
            headers={
                "Origin": "http://attacker.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )
        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))

    def test_cors_resolution_logic_custom_environment(self):
        """Test get_allowed_origins parses ALLOWED_ORIGINS and FRONTEND_URL cleanly."""
        original_allowed = os.environ.get("ALLOWED_ORIGINS")
        original_frontend = os.environ.get("FRONTEND_URL")
        original_env = os.environ.get("FLASK_ENV")
        try:
            os.environ["ALLOWED_ORIGINS"] = "https://app.agrify.org, https://admin.agrify.org"
            os.environ["FRONTEND_URL"] = "https://portal.agrify.org"
            os.environ["FLASK_ENV"] = "production"

            origins = api.get_allowed_origins()
            self.assertIn("https://app.agrify.org", origins)
            self.assertIn("https://admin.agrify.org", origins)
            self.assertIn("https://portal.agrify.org", origins)
            self.assertNotIn("*", origins)
        finally:
            if original_allowed is not None:
                os.environ["ALLOWED_ORIGINS"] = original_allowed
            else:
                os.environ.pop("ALLOWED_ORIGINS", None)

            if original_frontend is not None:
                os.environ["FRONTEND_URL"] = original_frontend
            else:
                os.environ.pop("FRONTEND_URL", None)

            if original_env is not None:
                os.environ["FLASK_ENV"] = original_env
            else:
                os.environ.pop("FLASK_ENV", None)


if __name__ == "__main__":
    unittest.main()
