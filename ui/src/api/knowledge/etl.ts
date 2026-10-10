import type { Ref } from 'vue'

import { get, post } from '@/request/index'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type KnowledgeEtlRunStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'WAITING_RELEASE'
  | 'SUCCESS'
  | 'FAILED'
export type KnowledgeEtlStageStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'SKIPPED'
export type KnowledgeIndexVersionStatus = 'CANDIDATE' | 'PUBLISHED' | 'ARCHIVED'

export interface KnowledgeEtlQualityCheck {
  key: string
  label: string
  actual: number
  threshold: number
  passed: boolean
}

export interface KnowledgeEtlQualityResult {
  passed?: boolean
  score?: number
  checks?: KnowledgeEtlQualityCheck[]
  source_paragraph_count?: number
  nonempty_paragraph_count?: number
  empty_paragraph_count?: number
  embedding_count?: number
  embedded_paragraph_count?: number
  missing_paragraph_count?: number
}

export interface KnowledgeEtlStage {
  id: string
  stage: string
  stage_label: string
  sequence: number
  status: KnowledgeEtlStageStatus
  status_label: string
  input_snapshot: Record<string, unknown>
  output_snapshot: Record<string, unknown>
  error_message: string
  started_at?: string | null
  finished_at?: string | null
}

export interface KnowledgeIndexVersion {
  id: string
  version: number
  version_label: string
  status: KnowledgeIndexVersionStatus
  status_label: string
  source_run_id: string
  source_run_number: number
  document_ids: string[]
  document_count: number
  paragraph_count: number
  embedding_count: number
  embedding_model_id?: string | null
  embedding_model_name: string
  content_digest: string
  quality_result: KnowledgeEtlQualityResult
  published_at?: string | null
  create_time: string
}

export interface KnowledgeEtlRun {
  id: string
  run_number: number
  trigger: 'MANUAL' | 'RETRY'
  trigger_label: string
  status: KnowledgeEtlRunStatus
  status_label: string
  current_stage: string
  current_stage_label: string
  document_ids: string[]
  config_snapshot: {
    min_paragraph_count: number
    min_embedding_coverage: number
  }
  quality_result: KnowledgeEtlQualityResult
  error_message: string
  retry_of_id?: string | null
  operator_name: string
  started_at?: string | null
  finished_at?: string | null
  create_time: string
  index_version?: KnowledgeIndexVersion | null
  stages?: KnowledgeEtlStage[]
}

export interface KnowledgeIndexRelease {
  id: string
  action: 'PUBLISH' | 'ROLLBACK'
  action_label: string
  from_version_id?: string | null
  from_version_label: string
  target_version_id: string
  target_version_label: string
  reason: string
  operator_name: string
  create_time: string
}

export interface KnowledgeEtlDocument {
  id: string
  name: string
  char_length: number
  status: string
  paragraph_count: number
  embedding_count: number
}

export interface KnowledgeEtlDashboard {
  knowledge: { id: string; name: string }
  summary: {
    document_count: number
    run_count: number
    failed_run_count: number
    candidate_count: number
    published_version: string
  }
  documents: KnowledgeEtlDocument[]
  runs: KnowledgeEtlRun[]
  versions: KnowledgeIndexVersion[]
  releases: KnowledgeIndexRelease[]
}

export interface KnowledgeEtlRunPayload {
  document_ids?: string[]
  min_paragraph_count: number
  min_embedding_coverage: number
}

function prefix(knowledgeId: string) {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/knowledge/${knowledgeId}/etl`
}

function getDashboard(
  knowledgeId: string,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEtlDashboard>> {
  return get(prefix(knowledgeId), undefined, loading)
}

function startRun(
  knowledgeId: string,
  data: KnowledgeEtlRunPayload,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEtlRun>> {
  return post(`${prefix(knowledgeId)}/run`, data, undefined, loading, 1000 * 60 * 10)
}

function getRun(
  knowledgeId: string,
  runId: string,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEtlRun>> {
  return get(`${prefix(knowledgeId)}/run/${runId}`, undefined, loading)
}

function retryRun(
  knowledgeId: string,
  runId: string,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEtlRun>> {
  return post(`${prefix(knowledgeId)}/run/${runId}/retry`, {}, undefined, loading, 1000 * 60 * 10)
}

function publishRun(
  knowledgeId: string,
  runId: string,
  reason: string,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEtlRun>> {
  return post(`${prefix(knowledgeId)}/run/${runId}/publish`, { reason }, undefined, loading)
}

function rollbackVersion(
  knowledgeId: string,
  versionId: string,
  reason: string,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeIndexVersion>> {
  return post(`${prefix(knowledgeId)}/version/${versionId}/rollback`, { reason }, undefined, loading)
}

export default {
  getDashboard,
  startRun,
  getRun,
  retryRun,
  publishRun,
  rollbackVersion,
}
