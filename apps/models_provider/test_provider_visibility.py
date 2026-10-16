import json
from types import SimpleNamespace

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from models_provider.constants.model_provider_constants import (
    PRIVATE_MODEL_PROVIDER_KEYS,
    PUBLIC_MODEL_PROVIDER_KEYS,
    VISIBLE_MODEL_PROVIDER_KEYS,
    ModelProvideConstants,
    get_visible_model_provider_keys,
)
from models_provider.views.provide import Provide


class ModelProviderVisibilityTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def get_provider_catalog(self, model_type=''):
        request = self.factory.get('/admin/api/provider', {'model_type': model_type})
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))
        response = Provide.as_view()(request)
        return json.loads(response.content)['data']

    def test_visible_catalog_only_contains_supported_public_and_private_providers(self):
        self.assertEqual(
            get_visible_model_provider_keys(),
            PUBLIC_MODEL_PROVIDER_KEYS + PRIVATE_MODEL_PROVIDER_KEYS,
        )
        self.assertEqual(VISIBLE_MODEL_PROVIDER_KEYS, get_visible_model_provider_keys())
        self.assertTrue(set(VISIBLE_MODEL_PROVIDER_KEYS).issubset(ModelProvideConstants.__members__))

    def test_private_catalog_only_exposes_docker_ai_and_ollama(self):
        self.assertEqual(
            PRIVATE_MODEL_PROVIDER_KEYS,
            ('model_docker_ai_provider', 'model_ollama_provider'),
        )
        self.assertNotIn('model_local_provider', VISIBLE_MODEL_PROVIDER_KEYS)
        self.assertNotIn('model_xinference_provider', VISIBLE_MODEL_PROVIDER_KEYS)
        self.assertNotIn('model_vllm_provider', VISIBLE_MODEL_PROVIDER_KEYS)

    def test_overseas_public_providers_are_hidden_from_catalog(self):
        for provider in (
            'model_openai_provider',
            'model_azure_provider',
            'model_anthropic_provider',
            'model_gemini_provider',
            'model_aws_bedrock_provider',
            'model_regolo_provider',
        ):
            self.assertNotIn(provider, VISIBLE_MODEL_PROVIDER_KEYS)

    def test_other_domestic_providers_are_hidden_from_catalog(self):
        for provider in (
            'model_wenxin_provider',
            'model_tencent_cloud_provider',
            'model_siliconCloud_provider',
            'model_minimax_provider',
        ):
            self.assertNotIn(provider, VISIBLE_MODEL_PROVIDER_KEYS)

    def test_provider_endpoint_returns_only_visible_catalog(self):
        provider_keys = tuple(item['provider'] for item in self.get_provider_catalog())
        self.assertEqual(provider_keys, VISIBLE_MODEL_PROVIDER_KEYS)

    def test_model_type_filter_cannot_restore_hidden_providers(self):
        provider_keys = {item['provider'] for item in self.get_provider_catalog('LLM')}
        self.assertTrue(provider_keys)
        self.assertTrue(provider_keys.issubset(VISIBLE_MODEL_PROVIDER_KEYS))
        self.assertNotIn('model_openai_provider', provider_keys)
