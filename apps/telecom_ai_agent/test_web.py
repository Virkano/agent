from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase


class HealthCheckTests(SimpleTestCase):
    @patch("telecom_ai_agent.urls.web.get_env", return_value="false")
    @patch("telecom_ai_agent.urls.web.cache")
    @patch("telecom_ai_agent.urls.web.connection")
    def test_healthz_checks_database_and_cache(self, connection, cache, _get_env):
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cache.get.return_value = "ok"

        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        cursor.execute.assert_called_once_with("SELECT 1")
        cache.set.assert_called_once_with("deployment:healthz", "ok", timeout=10)

    @patch("telecom_ai_agent.urls.web.get_env", return_value="false")
    @patch("telecom_ai_agent.urls.web.connection")
    def test_healthz_returns_503_without_error_details(self, connection, _get_env):
        connection.cursor.side_effect = RuntimeError("sensitive connection detail")

        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})

    @patch("telecom_ai_agent.urls.web.socket.create_connection")
    @patch("telecom_ai_agent.urls.web.get_env", return_value="true")
    @patch("telecom_ai_agent.urls.web.cache")
    @patch("telecom_ai_agent.urls.web.connection")
    def test_healthz_checks_embedded_vector_service(self, connection, cache, _get_env, create_connection):
        connection.cursor.return_value.__enter__.return_value = MagicMock()
        cache.get.return_value = "ok"
        create_connection.return_value.__enter__.return_value = MagicMock()

        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        create_connection.assert_called_once_with(("127.0.0.1", 11636), timeout=2)


class SpaRouteTests(SimpleTestCase):
    def test_admin_user_deep_link_returns_spa(self):
        response = self.client.get("/admin/system/user")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])
        self.assertIn('/admin/assets/', response.content.decode())

    @patch("telecom_ai_agent.urls.web.os.path.isfile", return_value=False)
    def test_root_locale_index_returns_empty_list_when_missing(self, _isfile):
        response = self.client.get("/locales/index.json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"locales": []})

    @patch("telecom_ai_agent.urls.web.os.path.isfile", return_value=False)
    def test_admin_locale_index_returns_empty_list_when_missing(self, _isfile):
        response = self.client.get("/admin/locales/index.json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"locales": []})

    def test_admin_api_profile_requires_authentication(self):
        response = self.client.get("/admin/api/user/profile")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], 1003)

    def test_admin_api_profile_rejects_invalid_token(self):
        response = self.client.get("/admin/api/user/profile", HTTP_AUTHORIZATION="Bearer invalid-token")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], 1002)

    def test_admin_api_user_manage_requires_authentication(self):
        response = self.client.get("/admin/api/user_manage/1/20")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], 1003)
