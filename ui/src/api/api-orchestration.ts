import type { Ref } from 'vue'

import { get, post, put } from '@/request'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type ApiAuthScheme = 'NONE' | 'API_KEY' | 'JWT' | 'OAUTH2' | 'SIGNATURE'
export type ApiEnvironment = 'TEST' | 'GRAY' | 'PRODUCTION'
export type ApiVersionStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
export type ApiInvocationStatus =
  | 'SUCCESS'
  | 'AUTH_FAILED'
  | 'SCHEMA_FAILED'
  | 'RESPONSE_FAILED'
  | 'TIMEOUT'
  | 'RETRY_EXHAUSTED'
  | 'CIRCUIT_OPEN'
export type ApiAdapterMode = 'MOCK' | 'GATEWAY'
export type ApiCircuitState = 'CLOSED' | 'OPEN'

export type ApiParameterSource = 'REQUEST' | 'CONTEXT' | 'CONSTANT' | 'PREVIOUS_OUTPUT'

export interface ApiParameterBinding {
  target: string
  source_type: ApiParameterSource
  source_path?: string
  source_value?: unknown
  required?: boolean
  depends_on?: string[]
}

export interface ApiOrchestrationVersion {
  id: string
  version_no: number
  status: ApiVersionStatus
  status_label: string
  environment: ApiEnvironment
  environment_label: string
  protocol: string
  method: string
  endpoint_path: string
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
  request_mapping: Record<string, unknown>
  response_mapping: Record<string, unknown>
  openapi_snapshot: Record<string, unknown>
  parameter_bindings: ApiParameterBinding[]
  adapter_mode: ApiAdapterMode
  adapter_mode_label: string
  gateway_base_url: string
  required_scopes: string[]
  timeout_ms: number
  max_retries: number
  circuit_failure_threshold: number
  circuit_recovery_seconds: number
  mock_response: Record<string, unknown>
  published_at: string | null
  create_time: string
}

export interface ApiOrchestrationAsset {
  id: string
  asset_key: string
  name: string
  description: string
  icon: string
  auth_scheme: ApiAuthScheme
  auth_scheme_label: string
  auth_reference: string
  ip_allowlist: string[]
  enabled: boolean
  published_version_no: number | null
  circuit_state: ApiCircuitState
  circuit_state_label: string
  consecutive_failures: number
  circuit_opened_at: string | null
  version_count: number
  update_time: string
  versions?: ApiOrchestrationVersion[]
  governance_events?: ApiGovernanceEvent[]
  draft_version?: ApiOrchestrationVersion
}

export interface ApiGovernanceEvent {
  id: string
  event_type: string
  version_no: number | null
  event_snapshot: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface ApiInvocationAudit {
  id: string
  asset_id: string
  asset_name: string
  version_no: number
  request_id: string
  status: ApiInvocationStatus
  status_label: string
  auth_scheme: ApiAuthScheme
  auth_result: boolean
  schema_result: boolean
  request_snapshot: Record<string, unknown>
  response_snapshot: Record<string, unknown>
  error_message: string
  duration_ms: number
  operator_name: string
  create_time: string
}

export interface ApiOrchestrationDashboard {
  summary: {
    asset_count: number
    published_count: number
    version_count: number
    invocation_count: number
    success_count: number
    failure_count: number
    circuit_open_count: number
  }
  assets: ApiOrchestrationAsset[]
  recent_audits: ApiInvocationAudit[]
}

export interface ApiAssetForm {
  asset_key: string
  name: string
  description: string
  icon: string
  auth_scheme: ApiAuthScheme
  auth_reference: string
  ip_allowlist: string[]
  environment: ApiEnvironment
  method: string
  endpoint_path: string
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
  request_mapping: Record<string, unknown>
  response_mapping: Record<string, unknown>
  openapi_snapshot: Record<string, unknown>
  parameter_bindings: ApiParameterBinding[]
  adapter_mode: ApiAdapterMode
  gateway_base_url: string
  required_scopes: string[]
  timeout_ms: number
  max_retries: number
  circuit_failure_threshold: number
  circuit_recovery_seconds: number
  mock_response: Record<string, unknown>
}

export interface OpenApiImportResult {
  method: string
  endpoint_path: string
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
  parameter_bindings: ApiParameterBinding[]
  openapi_snapshot: Record<string, unknown>
  summary: { title: string; version: string; operation_id: string }
}

export interface ApiSchemaDiff {
  added: string[]
  removed: string[]
  type_changed: { field: string; from?: string; to?: string }[]
  required_added: string[]
  required_removed: string[]
}

export interface ApiVersionComparison {
  base_version: ApiOrchestrationVersion
  target_version: ApiOrchestrationVersion
  changed_fields: string[]
  input_schema_diff: ApiSchemaDiff
  output_schema_diff: ApiSchemaDiff
  breaking_changes: string[]
  breaking_count: number
  compatible: boolean
}

const prefix = () => {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/api-orchestration`
}

export const getApiOrchestrationDashboard = (
  loading?: Ref<boolean>,
): Promise<Result<ApiOrchestrationDashboard>> => get(`${prefix()}/dashboard`, undefined, loading)

export const bootstrapApiOrchestration = (
  loading?: Ref<boolean>,
): Promise<Result<ApiOrchestrationDashboard>> => post(`${prefix()}/bootstrap`, {}, undefined, loading)

export const saveApiAsset = (
  data: ApiAssetForm,
  assetId?: string,
  loading?: Ref<boolean>,
): Promise<Result<ApiOrchestrationAsset>> =>
  assetId
    ? put(`${prefix()}/asset/${assetId}`, data, undefined, loading)
    : post(`${prefix()}/asset`, data, undefined, loading)

export const getApiAsset = (
  assetId: string,
  loading?: Ref<boolean>,
): Promise<Result<ApiOrchestrationAsset>> => get(`${prefix()}/asset/${assetId}`, undefined, loading)

export const importOpenApi = (
  document: Record<string, unknown>,
  loading?: Ref<boolean>,
): Promise<Result<OpenApiImportResult>> =>
  post(`${prefix()}/openapi/import`, { document }, undefined, loading)

export const compareApiVersions = (
  assetId: string,
  baseVersionId: string,
  targetVersionId: string,
  loading?: Ref<boolean>,
): Promise<Result<ApiVersionComparison>> =>
  get(
    `${prefix()}/asset/${assetId}/version/${baseVersionId}/compare?target_version_id=${encodeURIComponent(targetVersionId)}`,
    undefined,
    loading,
  )

export const publishApiVersion = (
  assetId: string,
  versionId: string,
  data: { breaking_change_confirmed?: boolean; change_ticket?: string } = {},
  loading?: Ref<boolean>,
): Promise<Result<ApiOrchestrationAsset>> =>
  post(`${prefix()}/asset/${assetId}/version/${versionId}/publish`, data, undefined, loading)

export const setApiAssetEnabled = (
  assetId: string,
  data: { enabled: boolean; reason?: string },
  loading?: Ref<boolean>,
): Promise<Result<ApiOrchestrationAsset>> =>
  post(`${prefix()}/asset/${assetId}/enabled`, data, undefined, loading)

export const rollbackApiVersion = (
  assetId: string,
  versionId: string,
  loading?: Ref<boolean>,
): Promise<Result<ApiOrchestrationAsset>> =>
  post(`${prefix()}/asset/${assetId}/version/${versionId}/rollback`, {}, undefined, loading)

export const invokeApiMock = (
  assetId: string,
  data: {
    request_id?: string
    payload: Record<string, unknown>
    auth_context: Record<string, unknown>
    source_context?: Record<string, unknown>
    simulated_failures?: number
    simulated_latency_ms?: number
  },
  loading?: Ref<boolean>,
): Promise<Result<ApiInvocationAudit>> =>
  post(`${prefix()}/asset/${assetId}/mock-invoke`, data, undefined, loading)
