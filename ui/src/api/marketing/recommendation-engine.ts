import type { Ref } from 'vue'

import { get, post, put } from '@/request'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type RecommendationTrainingStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED'
export type RecommendationModelStatus = 'TRAINED' | 'PUBLISHED' | 'ARCHIVED'

export interface RecommendationTrainingRun {
  id: string
  name: string
  snapshot_version: number
  status: RecommendationTrainingStatus
  status_label: string
  input_dim: number
  embedding_dim: number
  epochs: number
  learning_rate: number
  user_count: number
  item_count: number
  sample_count: number
  positive_count: number
  initial_loss: number | null
  final_loss: number | null
  metrics: Record<string, number>
  error_message: string
  started_at: string | null
  finished_at: string | null
  create_time: string
}

export interface RecommendationModelVersion {
  id: string
  version: number
  name: string
  status: RecommendationModelStatus
  status_label: string
  training_run_id: string
  snapshot_version: number
  embedding_dim: number
  metrics: Record<string, number>
  published_at: string | null
  item_embedding_count: number
  create_time: string
}

export interface RecommendationItemEmbedding {
  id: string
  campaign_id: string
  campaign_name: string
  dimension: number
  vector_norm: number
  update_time: string
}

export interface RecommendationCustomerOption {
  id: string
  name: string
  phone: string
  province: string
  current_plan: string
}

export interface RecommendationDashboard {
  summary: {
    snapshot_version: number | null
    user_feature_count: number
    item_feature_count: number
    successful_run_count: number
    model_version_count: number
    published_version: number | null
    inference_count: number
  }
  training_runs: RecommendationTrainingRun[]
  model_versions: RecommendationModelVersion[]
  item_embeddings: RecommendationItemEmbedding[]
  customers: RecommendationCustomerOption[]
}

export interface RecommendationCandidate {
  campaign_id: string
  campaign_name: string
  campaign_code: string
  score: number
  similarity: number
  benefit: string
  reasons: string[]
}

export interface RecommendationInferenceResult {
  inference_id: string
  model_version: number
  customer: { id: string; name: string; phone: string }
  top_k: number
  latency_ms: number
  candidates: RecommendationCandidate[]
}

export type RecommendationRecallChannel =
  | 'TWO_TOWER'
  | 'RULE'
  | 'COLLABORATIVE'
  | 'CONTENT'
  | 'HOT'
  | 'REGION'

export interface RecommendationFusionConfig {
  weights: Record<RecommendationRecallChannel, number>
  enabled_channels: RecommendationRecallChannel[]
  candidate_pool_size: number
  channels: Array<{ value: RecommendationRecallChannel; label: string }>
  update_time: string
}

export interface RecommendationFusionSource {
  channel: RecommendationRecallChannel
  channel_label: string
  score: number
  weight: number
  contribution: number
  reason: string
}

export interface RecommendationFusionCandidate {
  campaign_id: string
  campaign_name: string
  campaign_code: string
  benefit: string
  score: number
  source_count: number
  source_details: RecommendationFusionSource[]
}

export interface RecommendationFusionResult {
  fusion_run_id: string
  model_version: number | null
  customer: { id: string; name: string; phone: string }
  top_k: number
  latency_ms: number
  channel_counts: Record<RecommendationRecallChannel, number>
  candidates: RecommendationFusionCandidate[]
}

export interface RecommendationFusionRun {
  id: string
  customer: { id: string | null; name: string }
  model_version: number | null
  top_k: number
  latency_ms: number
  config_snapshot: Pick<RecommendationFusionConfig, 'weights' | 'enabled_channels' | 'candidate_pool_size'>
  fused_candidates: RecommendationFusionCandidate[]
  create_time: string
}

export interface RecommendationFusionDashboard {
  config: RecommendationFusionConfig
  summary: {
    fusion_run_count: number
    active_channel_count: number
    latest_latency_ms: number | null
  }
  recent_runs: RecommendationFusionRun[]
}

export type RecommendationRankingStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
export type RecommendationRankingFeature =
  | 'RECALL_SCORE'
  | 'BUSINESS_MATCH'
  | 'REGION_FIT'
  | 'PLAN_FIT'
  | 'USAGE_FIT'
  | 'CHANNEL_COVERAGE'
  | 'PRIORITY_SCORE'

export interface RecommendationRankingFeatureDetail {
  feature: RecommendationRankingFeature
  label: string
  value: number
  weight: number
  contribution: number
  reason: string
}

export interface RecommendationRankingCandidate extends RecommendationFusionCandidate {
  rank: number
  recall_score: number
  rank_score: number
  feature_details: RecommendationRankingFeatureDetail[]
}

export interface RecommendationRankingVersion {
  id: string
  version: number
  name: string
  status: RecommendationRankingStatus
  status_label: string
  feature_weights: Record<RecommendationRankingFeature, number>
  feature_schema: Array<{ value: RecommendationRankingFeature; label: string }>
  metrics: Record<string, number | string>
  published_at: string | null
  create_time: string
}

export interface RecommendationRankingRun {
  id: string
  customer: { id: string | null; name: string }
  fusion_run_id: string | null
  ranking_version: number | null
  top_n: number
  candidate_count: number
  latency_ms: number
  config_snapshot: Pick<RecommendationRankingVersion, 'name' | 'feature_weights' | 'feature_schema'> & { version: number }
  ranked_candidates: RecommendationRankingCandidate[]
  create_time: string
}

export interface RecommendationRankingResult {
  ranking_run_id: string
  fusion_run_id: string
  ranking_version: number
  ranking_version_name: string
  customer: { id: string; name: string; phone: string }
  top_n: number
  candidate_count: number
  fusion_latency_ms: number
  ranking_latency_ms: number
  candidates: RecommendationRankingCandidate[]
}

export interface RecommendationRankingDashboard {
  summary: {
    ranking_version_count: number
    published_version: number | null
    ranking_run_count: number
    latest_latency_ms: number | null
  }
  feature_schema: Array<{ value: RecommendationRankingFeature; label: string }>
  versions: RecommendationRankingVersion[]
  recent_runs: RecommendationRankingRun[]
}

export type RecommendationFeedbackType = 'EXPOSED' | 'CLICKED' | 'CONVERTED' | 'NEGATIVE'
export type RecommendationIncrementalStatus = 'RUNNING' | 'SUCCESS' | 'FAILED'

export interface RecommendationFeedbackEvent {
  id: string
  customer: { id: string | null; name: string }
  campaign: { id: string | null; name: string }
  ranking_run_id: string | null
  event_type: RecommendationFeedbackType
  event_type_label: string
  label: number
  source_type: string
  source_id: string
  feature_snapshot: Partial<Record<RecommendationRankingFeature, number>>
  metadata: Record<string, unknown>
  occurred_at: string
}

export interface RecommendationIncrementalRun {
  id: string
  name: string
  status: RecommendationIncrementalStatus
  status_label: string
  base_ranking_version: number | null
  generated_ranking_version: number | null
  generated_status: RecommendationRankingStatus | null
  learning_rate: number
  sample_count: number
  positive_count: number
  negative_count: number
  weight_delta: Partial<Record<RecommendationRankingFeature, number>>
  metrics: Record<string, number | string | boolean | Record<string, number>>
  error_message: string
  started_at: string | null
  finished_at: string | null
  create_time: string
}

export interface RecommendationIncrementalDashboard {
  summary: {
    feedback_count: number
    labeled_sample_count: number
    positive_count: number
    negative_count: number
    incremental_run_count: number
    latest_generated_version: number | null
  }
  feedback_by_type: Record<RecommendationFeedbackType, number>
  event_types: Array<{ value: RecommendationFeedbackType; label: string; training_label: number }>
  recent_events: RecommendationFeedbackEvent[]
  recent_runs: RecommendationIncrementalRun[]
}

export interface RecommendationIncrementalTrainRequest {
  name: string
  base_ranking_version_id?: string
  learning_rate: number
  minimum_samples: number
  auto_publish: boolean
}

export interface RecommendationEffectDashboard {
  period: { days: 7 | 30 | 90; start_at: string; end_at: string }
  summary: {
    exposure_count: number
    click_count: number
    conversion_count: number
    negative_count: number
    ctr: number
    cvr: number
    negative_rate: number
    coverage_rate: number
    diversity_score: number
    unique_customer_count: number
    active_campaign_count: number
    ranking_run_count: number
  }
  latency: {
    ranking_avg_ms: number
    fusion_avg_ms: number
    total_avg_ms: number
    p95_total_ms: number
  }
  funnel: Array<{ stage: RecommendationFeedbackType; label: string; count: number }>
  daily_trend: Array<{
    date: string
    exposure_count: number
    click_count: number
    conversion_count: number
    negative_count: number
    ctr: number
    cvr: number
  }>
  version_performance: Array<{
    version: number | null
    name: string
    status: RecommendationRankingStatus | null
    is_published: boolean
    run_count: number
    exposure_count: number
    click_count: number
    conversion_count: number
    negative_count: number
    ctr: number
    cvr: number
    negative_rate: number
    coverage_rate: number
    diversity_score: number
    ranking_avg_ms: number
    total_avg_ms: number
  }>
  campaign_performance: Array<{
    campaign_id: string
    campaign_name: string
    exposure_count: number
    click_count: number
    conversion_count: number
    negative_count: number
    ctr: number
    cvr: number
  }>
}

export interface RecommendationTrainRequest {
  name: string
  snapshot_version?: number
  embedding_dim: number
  epochs: number
  learning_rate: number
  auto_publish: boolean
}

const prefix = () => {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/marketing/recommendation`
}

export const getRecommendationDashboard = (loading?: Ref<boolean>): Promise<Result<RecommendationDashboard>> =>
  get(`${prefix()}/dashboard`, {}, loading)

export const buildRecommendationFeatureSnapshot = (
  inputDim = 64,
  loading?: Ref<boolean>,
): Promise<Result<{ snapshot_version: number; input_dim: number; user_count: number; item_count: number }>> =>
  post(`${prefix()}/feature-snapshot`, { input_dim: inputDim }, {}, loading)

export const trainRecommendationModel = (
  data: RecommendationTrainRequest,
  loading?: Ref<boolean>,
): Promise<Result<{ training_run: RecommendationTrainingRun; model_version: RecommendationModelVersion }>> =>
  post(`${prefix()}/train`, data, {}, loading)

export const publishRecommendationModel = (
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<RecommendationModelVersion>> => post(`${prefix()}/model/${id}/publish`, {}, {}, loading)

export const inferRecommendation = (
  data: { customer_id: string; top_k: number; model_version_id?: string },
  loading?: Ref<boolean>,
): Promise<Result<RecommendationInferenceResult>> => post(`${prefix()}/infer`, data, {}, loading)

export const getRecommendationFusionDashboard = (
  loading?: Ref<boolean>,
): Promise<Result<RecommendationFusionDashboard>> => get(`${prefix()}/fusion-dashboard`, {}, loading)

export const saveRecommendationFusionConfig = (
  data: Pick<RecommendationFusionConfig, 'weights' | 'enabled_channels' | 'candidate_pool_size'>,
  loading?: Ref<boolean>,
): Promise<Result<RecommendationFusionConfig>> => put(`${prefix()}/fusion-config`, data, {}, loading)

export const inferRecommendationFusion = (
  data: { customer_id: string; top_k: number; model_version_id?: string },
  loading?: Ref<boolean>,
): Promise<Result<RecommendationFusionResult>> => post(`${prefix()}/fusion-infer`, data, {}, loading)

export const getRecommendationRankingDashboard = (
  loading?: Ref<boolean>,
): Promise<Result<RecommendationRankingDashboard>> => get(`${prefix()}/ranking-dashboard`, {}, loading)

export const createRecommendationRankingVersion = (
  data: { name: string; feature_weights: Record<RecommendationRankingFeature, number>; auto_publish: boolean },
  loading?: Ref<boolean>,
): Promise<Result<RecommendationRankingVersion>> => post(`${prefix()}/ranking-version`, data, {}, loading)

export const publishRecommendationRankingVersion = (
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<RecommendationRankingVersion>> => post(`${prefix()}/ranking-version/${id}/publish`, {}, {}, loading)

export const inferRecommendationRanking = (
  data: { customer_id: string; top_n: number; candidate_pool_size: number; ranking_version_id?: string },
  loading?: Ref<boolean>,
): Promise<Result<RecommendationRankingResult>> => post(`${prefix()}/ranking-infer`, data, {}, loading)

export const getRecommendationIncrementalDashboard = (
  loading?: Ref<boolean>,
): Promise<Result<RecommendationIncrementalDashboard>> => get(`${prefix()}/incremental-dashboard`, {}, loading)

export const recordRecommendationFeedback = (
  data: {
    ranking_run_id: string
    campaign_id: string
    event_type: Exclude<RecommendationFeedbackType, 'EXPOSED'>
    event_key?: string
    metadata?: Record<string, unknown>
  },
  loading?: Ref<boolean>,
): Promise<Result<RecommendationFeedbackEvent & { created: boolean }>> => post(`${prefix()}/feedback`, data, {}, loading)

export const syncRecommendationFeedback = (
  loading?: Ref<boolean>,
): Promise<
  Result<{
    created_count: number
    created_by_type: Record<RecommendationFeedbackType, number>
    total_event_count: number
  }>
> => post(`${prefix()}/incremental-sync`, {}, {}, loading)

export const trainRecommendationIncremental = (
  data: RecommendationIncrementalTrainRequest,
  loading?: Ref<boolean>,
): Promise<Result<{ run: RecommendationIncrementalRun; generated_version: RecommendationRankingVersion }>> =>
  post(`${prefix()}/incremental-train`, data, {}, loading)

export const getRecommendationEffectDashboard = (
  days: 7 | 30 | 90,
  loading?: Ref<boolean>,
): Promise<Result<RecommendationEffectDashboard>> => get(`${prefix()}/effect-dashboard`, { days }, loading)
