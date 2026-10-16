import type {Provider} from '@/api/type/model'

export const PUBLIC_MODEL_PROVIDER_KEYS = [
  'model_kimi_provider',
  'model_zhipu_provider',
  'model_xf_provider',
  'model_deepseek_provider',
  'model_volcanic_engine_provider',
  'model_tencent_provider',
  'aliyun_bai_lian_model_provider',
] as const

export const PRIVATE_MODEL_PROVIDER_KEYS = [
  'model_docker_ai_provider',
  'model_ollama_provider',
] as const

const visibleModelProviderKeys = new Set<string>([
  ...PUBLIC_MODEL_PROVIDER_KEYS,
  ...PRIVATE_MODEL_PROVIDER_KEYS,
])
const privateModelProviderKeys = new Set<string>(PRIVATE_MODEL_PROVIDER_KEYS)

export const isVisibleModelProvider = (provider: string) =>
  visibleModelProviderKeys.has(provider)

export const isPrivateModelProvider = (provider: string) =>
  privateModelProviderKeys.has(provider)

export const filterVisibleModelProviders = (providers: Array<Provider>) =>
  providers.filter((item) => isVisibleModelProvider(item.provider))
