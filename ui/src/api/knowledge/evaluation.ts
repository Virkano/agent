import type { Ref } from 'vue'

import { del, exportFile, get, post, put } from '@/request/index'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type KnowledgeEvaluationMode = 'embedding' | 'keywords' | 'blend' | 'reranker'
export type KnowledgeEvaluationRunStatus = 'RUNNING' | 'SUCCESS' | 'PARTIAL' | 'FAILED'
export type KnowledgeDependencyStatus = 'HEALTHY' | 'WARNING' | 'ERROR' | 'NOT_CONFIGURED'

export interface KnowledgeEvaluationCase {
  id: string
  question: string
  expected_document_id?: string | null
  expected_document_name: string
  expected_paragraph_id?: string | null
  expected_paragraph_title: string
  expected_paragraph_content: string
  expected_answer: string
  enabled: boolean
  update_time: string
}

export interface KnowledgeEvaluationMatch {
  paragraph_id: string
  paragraph_title: string
  content: string
  document_id: string
  document_name: string
  vector_score: number
  comprehensive_score: number
  reranker_score?: number | null
}

export interface KnowledgeEvaluationModeMetrics {
  mode: KnowledgeEvaluationMode
  mode_label: string
  case_count: number
  hit_count: number
  hit_rate: number
  recall_at_k: number
  mrr: number
  no_answer_count: number
  no_answer_rate: number
  failed_count: number
  avg_latency_ms: number
}

export interface KnowledgeEvaluationSummary {
  case_count: number
  mode_count: number
  result_count: number
  error_count: number
  best_mode: KnowledgeEvaluationMode | ''
  best_mode_label: string
  best_hit_rate: number
  mode_metrics: KnowledgeEvaluationModeMetrics[]
}

export interface KnowledgeEvaluationResult {
  id: string
  case_id?: string | null
  mode: KnowledgeEvaluationMode
  mode_label: string
  question: string
  expected_document_id: string
  expected_document_name: string
  expected_paragraph_id: string
  expected_answer: string
  hit: boolean
  expected_rank?: number | null
  latency_ms: number
  top_score: number
  matches: KnowledgeEvaluationMatch[]
  error_message: string
}

export interface KnowledgeEvaluationRun {
  id: string
  status: KnowledgeEvaluationRunStatus
  status_label: string
  search_modes: KnowledgeEvaluationMode[]
  top_number: number
  similarity: number
  reranker_model_id?: string | null
  reranker_model_name: string
  summary: KnowledgeEvaluationSummary
  error_message: string
  started_at?: string | null
  finished_at?: string | null
  user_name: string
  create_time: string
  results?: KnowledgeEvaluationResult[]
}

export interface KnowledgeEvaluationDashboard {
  knowledge: { id: string; name: string; description: string }
  case_summary: {
    total_count: number
    enabled_count: number
    document_target_count: number
    paragraph_target_count: number
    answer_target_count: number
  }
  cases: KnowledgeEvaluationCase[]
  runs: KnowledgeEvaluationRun[]
  latest_run?: KnowledgeEvaluationRun | null
  documents: Array<{ id: string; name: string }>
  reranker_models: Array<{ id: string; name: string; model_name: string; provider: string }>
  dependency_health: Array<{
    key: string
    name: string
    status: KnowledgeDependencyStatus
    detail: string
  }>
  mode_labels: Record<KnowledgeEvaluationMode, string>
}

export interface KnowledgeEvaluationCasePayload {
  question: string
  expected_document_id?: string | null
  expected_paragraph_id?: string | null
  expected_answer?: string
  enabled?: boolean
}

export interface KnowledgeEvaluationRunPayload {
  search_modes: KnowledgeEvaluationMode[]
  top_number: number
  similarity: number
  reranker_model_id?: string | null
}

export interface KnowledgeEvaluationCaseImportResult {
  total_count: number
  imported_count: number
  skipped_count: number
  cases: KnowledgeEvaluationCase[]
}

function prefix(knowledgeId: string) {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/knowledge/${knowledgeId}/evaluation`
}

function getDashboard(
  knowledgeId: string,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEvaluationDashboard>> {
  return get(prefix(knowledgeId), undefined, loading)
}

function getOptions(
  knowledgeId: string,
  documentId?: string,
  loading?: Ref<boolean>,
): Promise<
  Result<{
    documents: Array<{ id: string; name: string }>
    paragraphs: Array<{ id: string; title: string; content: string }>
  }>
> {
  return get(`${prefix(knowledgeId)}/options`, { document_id: documentId }, loading)
}

function createCase(
  knowledgeId: string,
  data: KnowledgeEvaluationCasePayload,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEvaluationCase>> {
  return post(`${prefix(knowledgeId)}/case`, data, undefined, loading)
}

function updateCase(
  knowledgeId: string,
  caseId: string,
  data: Partial<KnowledgeEvaluationCasePayload>,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEvaluationCase>> {
  return put(`${prefix(knowledgeId)}/case/${caseId}`, data, undefined, loading)
}

function deleteCase(
  knowledgeId: string,
  caseId: string,
  loading?: Ref<boolean>,
): Promise<Result<boolean>> {
  return del(`${prefix(knowledgeId)}/case/${caseId}`, undefined, {}, loading)
}

function downloadCaseTemplate(knowledgeId: string, loading?: Ref<boolean>) {
  return exportFile(
    '知识库检索评估样本模板.csv',
    `${prefix(knowledgeId)}/case/template`,
    undefined,
    loading,
  )
}

function importCases(
  knowledgeId: string,
  file: File,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEvaluationCaseImportResult>> {
  const data = new FormData()
  data.append('file', file, file.name)
  return post(`${prefix(knowledgeId)}/case/import`, data, undefined, loading)
}

function exportCases(knowledgeId: string, loading?: Ref<boolean>) {
  return exportFile(
    '知识库检索评估样本.csv',
    `${prefix(knowledgeId)}/case/export`,
    undefined,
    loading,
  )
}

function runEvaluation(
  knowledgeId: string,
  data: KnowledgeEvaluationRunPayload,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEvaluationRun>> {
  return post(`${prefix(knowledgeId)}/run`, data, undefined, loading, 1000 * 60 * 10)
}

function getRun(
  knowledgeId: string,
  runId: string,
  loading?: Ref<boolean>,
): Promise<Result<KnowledgeEvaluationRun>> {
  return get(`${prefix(knowledgeId)}/run/${runId}`, undefined, loading)
}

function exportRun(knowledgeId: string, runId: string, loading?: Ref<boolean>) {
  return exportFile(
    '知识库检索评估结果.csv',
    `${prefix(knowledgeId)}/run/${runId}/export`,
    undefined,
    loading,
  )
}

export default {
  getDashboard,
  getOptions,
  createCase,
  updateCase,
  deleteCase,
  downloadCaseTemplate,
  importCases,
  exportCases,
  runEvaluation,
  getRun,
  exportRun,
}
