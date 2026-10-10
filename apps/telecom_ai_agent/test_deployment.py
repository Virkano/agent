import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured

from common.management.commands.services.command import Services
from telecom_ai_agent.deployment import deployment_settings


class DeploymentSettingsTests(unittest.TestCase):
    def setUp(self):
        self.production = {
            "JB_DEPLOYMENT_MODE": "production",
            "JB_SECRET_KEY": "production-key-unique-value-with-at-least-32-characters",
            "JB_DB_PASSWORD": "custom-database-password",
            "JB_REDIS_PASSWORD": "custom-redis-password",
            "JB_DEFAULT_PASSWORD": "custom-admin-password",
            "JB_ALLOWED_HOSTS": "agent.example.com,api.example.com",
            "JB_DEBUG": "false",
        }

    def test_local_mode_retains_development_defaults(self):
        values = deployment_settings({"DEBUG": "true"}, {})
        self.assertTrue(values["DEBUG"])
        self.assertEqual(values["ALLOWED_HOSTS"], ["*"])

    def test_production_requires_explicit_secrets(self):
        with self.assertRaisesRegex(ImproperlyConfigured, "JB_SECRET_KEY"):
            deployment_settings({}, {"JB_DEPLOYMENT_MODE": "production"})

    def test_production_rejects_insecure_defaults_and_wildcard(self):
        env = {**self.production, "JB_DEFAULT_PASSWORD": "TelecomAI@123.."}
        with self.assertRaisesRegex(ImproperlyConfigured, "bundled development default"):
            deployment_settings({}, env)
        env = {**self.production, "JB_ALLOWED_HOSTS": "*"}
        with self.assertRaisesRegex(ImproperlyConfigured, "explicit non-local hosts"):
            deployment_settings({}, env)
        env = {**self.production, "JB_DEBUG": "true"}
        with self.assertRaisesRegex(ImproperlyConfigured, "JB_DEBUG must be false"):
            deployment_settings({}, env)

    def test_production_enables_https_and_cookie_protection(self):
        values = deployment_settings({}, self.production)
        self.assertFalse(values["DEBUG"])
        self.assertEqual(values["ALLOWED_HOSTS"], ["agent.example.com", "api.example.com"])
        self.assertTrue(values["SESSION_COOKIE_SECURE"])
        self.assertTrue(values["CSRF_COOKIE_SECURE"])
        self.assertTrue(values["SECURE_SSL_REDIRECT"])
        self.assertGreater(values["SECURE_HSTS_SECONDS"], 0)

    def test_preflight_cli_passes_without_echoing_secrets(self):
        script = Path(__file__).resolve().parents[2] / "scripts" / "check-deployment-security.py"
        result = subprocess.run(
            [sys.executable, str(script), "--production"],
            env={**os.environ, **self.production},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(self.production["JB_SECRET_KEY"], result.stdout + result.stderr)
        self.assertNotIn(self.production["JB_DB_PASSWORD"], result.stdout + result.stderr)

    def test_web_does_not_start_local_model_without_explicit_setting(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(Services.web_services(), [Services.gunicorn])

    def test_local_model_can_be_explicitly_enabled(self):
        with patch.dict(os.environ, {"JB_START_LOCAL_MODEL": "true"}, clear=True):
            self.assertEqual(Services.web_services(), [Services.gunicorn, Services.local_model])

    def test_business_image_enables_internal_vector_service(self):
        dockerfile = Path(__file__).resolve().parents[2] / "docker" / "Dockerfile.app"
        source = dockerfile.read_text(encoding="utf-8")

        self.assertIn("JB_START_LOCAL_MODEL=true", source)
        self.assertIn("JB_LOCAL_MODEL_HOST=127.0.0.1", source)
        self.assertIn("EXPOSE 8080", source)
        self.assertNotIn("EXPOSE 11636", source)


if __name__ == "__main__":
    unittest.main()
