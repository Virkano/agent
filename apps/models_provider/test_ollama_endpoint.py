from unittest.mock import patch

from django.test import SimpleTestCase

from models_provider.impl.ollama_model_provider.endpoint import resolve_ollama_base_url


class OllamaEndpointTests(SimpleTestCase):
    def test_uses_saved_endpoint_without_override(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                resolve_ollama_base_url("http://127.0.0.1:11434/"),
                "http://127.0.0.1:11434",
            )

    def test_container_override_wins_without_persisting_it(self):
        with patch.dict(
            "os.environ",
            {"JB_OLLAMA_BASE_URL": "http://host.docker.internal:11434/"},
            clear=True,
        ):
            self.assertEqual(
                resolve_ollama_base_url("http://127.0.0.1:11434"),
                "http://host.docker.internal:11434",
            )
