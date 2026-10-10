import { get, post, put, del } from '@/request/index'
import type { Result } from '@/request/Result'
import type { pageRequest } from '@/api/type/common'
import type { Ref } from 'vue'
import useStore from '@/stores'

const prefix: any = { _value: '/workspace/' }
Object.defineProperty(prefix, 'value', {
  get: function () {
    const { user } = useStore()
    return `${this._value}${user.getWorkspaceId()}/marketing/task`
  },
})

export interface MarketingTask {
  id?: string
  workspace_id?: string
  name: string
  scenario_id?: string
  scenario_name?: string
  target_audience?: string
  objective?: string
  channel?: string
  status?: 'DRAFT' | 'RUNNING' | 'PAUSED' | 'FINISHED'
  application_id?: string | null
  application_name?: string
  knowledge_id?: string | null
  knowledge_name?: string
  target_count?: number
  chat_count?: number
  chat_url?: string
  config: Record<string, any>
  campaign_ids?: string[]
  campaign_names?: string[]
  description?: string
  create_user?: string
  create_time?: string
  update_time?: string
}

export interface MarketingCustomer {
  id?: string
  task_id?: string
  name?: string
  phone?: string
  phone_masked?: string
  province?: string
  current_plan?: string
  monthly_data_usage?: string
  monthly_call_usage?: string
  status?: 'PENDING' | 'TOUCHED' | 'CONSULTED' | 'INTENT' | 'NO_INTENT' | 'MANUAL' | 'CONVERTED'
  intent?: string
  remark?: string
  chat_count?: number
  chat_url?: string
  config?: Record<string, any>
  latest_conversion?: MarketingConversionRecord | null
  create_time?: string
  update_time?: string
}

export interface MarketingConversionRecord {
  id?: string
  task_id?: string
  customer_id?: string
  customer_name?: string
  batch_id?: string | null
  batch_name?: string
  outcome: 'CONVERTED' | 'LOST'
  product_name?: string
  note: string
  operator_name?: string
  create_time?: string
}

export interface MarketingConversionRecordWrite {
  outcome: MarketingConversionRecord['outcome']
  product_name?: string
  note: string
  batch_id?: string | null
}

export interface MarketingCustomerFollowUp {
  status: NonNullable<MarketingCustomer['status']>
  intent?: string
  note: string
}

export interface MarketingCustomerImportRow {
  row_number: number
  data: Record<string, string>
  phone_masked: string
  status: 'READY' | 'SKIPPED' | 'ERROR'
  reason: string
}

export interface MarketingCustomerImportPreview {
  file_name: string
  headers: string[]
  mapping: Record<string, string>
  rows: MarketingCustomerImportRow[]
  summary: { total_count: number; ready_count: number; skipped_count: number; error_count: number }
}

export interface MarketingCustomerImportBatch {
  id: string
  file_name: string
  total_count: number
  valid_count: number
  imported_count: number
  skipped_count: number
  error_count: number
  mapping: Record<string, string>
  error_rows: MarketingCustomerImportRow[]
  operator_name: string
  create_time: string
}

export interface MarketingTouchBatch {
  id?: string
  task_id?: string
  name: string
  status: 'READY' | 'RUNNING' | 'CLOSED'
  owner_name?: string
  deadline?: string | null
  approval_status?: 'PENDING' | 'APPROVED' | 'REJECTED'
  approval_note?: string
  approver_name?: string
  approved_at?: string | null
  approval_due_at?: string | null
  is_approval_overdue?: boolean
  creator_name?: string
  can_approve?: boolean
  can_resubmit?: boolean
  filter_config?: Record<string, any>
  selected_count?: number
  excluded_count?: number
  customer_snapshot?: Array<Record<string, any>>
  excluded_snapshot?: Array<Record<string, any>>
  create_time?: string
  update_time?: string
}

export interface MarketingTouchBatchDetail {
  batch: MarketingTouchBatch
  metrics: MarketingTouchBatchMetrics
  executions: MarketingTouchExecution[]
  conversions?: MarketingConversionRecord[]
  approval_records?: MarketingTouchBatchApprovalRecord[]
}

export interface MarketingTouchBatchApprovalRecord {
  id?: string
  action: 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'RESUBMITTED'
  note?: string
  operator_name?: string
  create_time?: string
}

export interface MarketingTouchBatchMetrics {
  selected_count: number
  executed_count: number
  waiting_count: number
  contacted_count: number
  no_answer_count: number
  rejected_count: number
  intent_count: number
  manual_count: number
  converted_count: number
  lost_count: number
  conversion_rate: number
}

export interface MarketingTouchExecution {
  id?: string
  batch_id?: string
  customer_id: string
  customer_name?: string
  phone_masked?: string
  result: 'CONTACTED' | 'NO_ANSWER' | 'REJECTED' | 'INTENT' | 'MANUAL'
  note: string
  next_follow_up_at?: string | null
  operator_name?: string
  create_time?: string
}

export interface MarketingTaskDashboard {
  task: MarketingTask
  funnel: Record<string, number>
  batch_summary: Record<string, number>
  batches: Array<MarketingTouchBatch & { executed_count: number; is_overdue: boolean }>
  priority_customers: MarketingCustomer[]
}

export interface MarketingApprovalQueue {
  summary: { pending_count: number; overdue_count: number }
  records: Array<MarketingTouchBatch & { task_name: string; approval_sla_hours: number }>
  generated_at?: string
}

export interface MarketingTouchBatchCreate {
  name: string
  plan_keyword?: string
  province?: string
  min_data_usage_gb?: number
  min_call_usage_minutes?: number
  statuses?: Array<NonNullable<MarketingCustomer['status']>>
  cooldown_days?: number
  max_customers?: number
}

export interface MarketingTouchBatchApproval {
  approval_status: 'APPROVED' | 'REJECTED'
  approval_note?: string
}

export interface MarketingTouchBatchResubmit extends MarketingTouchBatchCreate {
  resubmit_note: string
}

export type MarketingQualityStatus = 'PASS' | 'REVIEW' | 'HIGH_RISK'
export type MarketingManualReviewStatus =
  | 'PENDING'
  | 'CONFIRMED_PASS'
  | 'CONFIRMED_ISSUE'
  | 'REVISED'
export type MarketingManualReviewAction = 'CONFIRM_PASS' | 'CONFIRM_ISSUE' | 'REVISE'

export interface MarketingQualityReviewActionRecord {
  id: string
  action: MarketingManualReviewAction
  previous_status: MarketingManualReviewStatus
  current_status: MarketingManualReviewStatus
  reviewer_name: string
  note: string
  original_answer: string
  revised_answer: string
  revision: number
  create_time: string
}

export interface MarketingQualityReview {
  id: string
  task_id: string
  task_name: string
  customer_id?: string | null
  customer_name: string
  record_id: string
  problem_text: string
  original_answer: string
  record_create_time: string
  status: MarketingQualityStatus
  score: number
  risk_types: string[]
  reasons: string[]
  suggestion: string
  evidence: Record<string, any>
  rule_version: string
  manual_status: MarketingManualReviewStatus
  reviewer_name: string
  reviewed_at?: string | null
  review_note: string
  revised_answer: string
  manual_revision: number
  manual_actions: MarketingQualityReviewActionRecord[]
}

export interface MarketingQualityReviewSummary {
  total_count: number
  pending_count: number
  reviewed_count: number
  revised_count: number
  high_risk_count: number
}

export interface MarketingQualityReviewPage {
  total: number
  records: MarketingQualityReview[]
  current: number
  size: number
  summary: MarketingQualityReviewSummary
}

export interface MarketingQualityReviewHandle {
  action: MarketingManualReviewAction
  note: string
  revised_answer?: string
}

export type MarketingQualityPolicyMode = 'OFF' | 'SHADOW' | 'INTERCEPT'
export type MarketingPreflightAction =
  | 'OBSERVED'
  | 'SAFEGUARD_REWRITTEN'
  | 'INTERCEPTED'
  | 'BYPASSED'

export interface MarketingQualityPolicy {
  mode: MarketingQualityPolicyMode
  rule_version: string
  updated_by_name: string
  update_time?: string | null
  available_modes: Array<{ value: MarketingQualityPolicyMode; label: string }>
  interception_available: boolean
  intercept_rule_types: string[]
  eligible_rule_options: Array<{ value: string; label: string }>
  interception_guard: string
}

export interface MarketingPreflightRecord {
  id: string
  task_id: string
  task_name: string
  customer_id?: string | null
  customer_name: string
  record_id: string
  problem_text: string
  policy_mode: MarketingQualityPolicyMode
  action: MarketingPreflightAction
  generated_answer: string
  final_answer: string
  status: MarketingQualityStatus
  score: number
  risk_types: string[]
  reasons: string[]
  suggestion: string
  evidence: Record<string, any>
  rule_version: string
  evaluation_ms: number
  create_time: string
}

export interface MarketingPreflightSummary {
  total_count: number
  pass_count: number
  review_count: number
  high_risk_count: number
  safeguard_rewritten_count: number
  intercepted_count: number
  bypassed_count: number
}

export interface MarketingPreflightPage {
  total: number
  records: MarketingPreflightRecord[]
  current: number
  size: number
  summary: MarketingPreflightSummary
}

export interface MarketingQualityRuleEffectBlocker {
  code: string
  message: string
}

export interface MarketingQualityRuleEffectItem {
  risk_type: string
  label: string
  is_high_risk: boolean
  reason: string
  suggestion: string
  hit_count: number
  shadow_hit_count: number
  pending_count: number
  reviewed_count: number
  confirmed_issue_count: number
  false_positive_count: number
  revised_count: number
  manual_review_rate: number | null
  issue_confirmation_rate: number | null
  false_positive_rate: number | null
  eligible: boolean
  gate_status: string
  gate_label: string
  blockers: MarketingQualityRuleEffectBlocker[]
  latest_hit_at?: string | null
}

export interface MarketingQualityRuleEffect {
  summary: {
    hit_record_count: number
    pending_record_count: number
    manually_reviewed_record_count: number
    preflight_record_count: number
    preflight_risk_record_count: number
    eligible_rule_count: number
    displayed_rule_count: number
  }
  thresholds: {
    min_reviewed_samples: number
    min_issue_confirmation_rate: number
    max_false_positive_rate: number
    high_risk_only: boolean
  }
  risk_type_options: Array<{ value: string; label: string }>
  rules: MarketingQualityRuleEffectItem[]
  generated_at: string
}

const getTaskPage: (
  page: pageRequest,
  param?: any,
  loading?: Ref<boolean>,
) => Promise<Result<any>> = (page, param, loading) => {
  return get(`${prefix.value}/${page.current_page}/${page.page_size}`, param, loading)
}

const getTaskList: (param?: any, loading?: Ref<boolean>) => Promise<Result<MarketingTask[]>> = (
  param,
  loading,
) => {
  return get(prefix.value, param, loading)
}

const createTask: (
  data: MarketingTask,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingTask>> = (data, loading) => {
  return post(prefix.value, data, undefined, loading)
}

const updateTask: (
  taskId: string,
  data: MarketingTask,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingTask>> = (taskId, data, loading) => {
  return put(`${prefix.value}/${taskId}`, data, undefined, loading)
}

const deleteTask: (taskId: string, loading?: Ref<boolean>) => Promise<Result<boolean>> = (
  taskId,
  loading,
) => {
  return del(`${prefix.value}/${taskId}`, undefined, {}, loading)
}

const getTaskEffect: (
  taskId: string,
  page: pageRequest,
  loading?: Ref<boolean>,
) => Promise<Result<any>> = (taskId, page, loading) => {
  return get(
    `${prefix.value}/${taskId}/effect/${page.current_page}/${page.page_size}`,
    undefined,
    loading,
  )
}

const getQualityReviewPage: (
  page: pageRequest,
  param?: Record<string, any>,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingQualityReviewPage>> = (page, param, loading) => {
  return get(
    `${prefix.value.replace('/marketing/task', '/marketing/quality-review')}/${page.current_page}/${page.page_size}`,
    param,
    loading,
  )
}

const handleQualityReview: (
  reviewId: string,
  data: MarketingQualityReviewHandle,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingQualityReview>> = (reviewId, data, loading) => {
  return post(
    `${prefix.value.replace('/marketing/task', '/marketing/quality-review')}/${reviewId}/handle`,
    data,
    undefined,
    loading,
  )
}

const getQualityPolicy: (loading?: Ref<boolean>) => Promise<Result<MarketingQualityPolicy>> = (
  loading,
) => {
  return get(
    `${prefix.value.replace('/marketing/task', '/marketing/quality-policy')}`,
    undefined,
    loading,
  )
}

const updateQualityPolicy: (
  data: Pick<MarketingQualityPolicy, 'mode' | 'intercept_rule_types'>,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingQualityPolicy>> = (data, loading) => {
  return put(
    `${prefix.value.replace('/marketing/task', '/marketing/quality-policy')}`,
    data,
    undefined,
    loading,
  )
}

const getPreflightLogPage: (
  page: pageRequest,
  param?: Record<string, any>,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingPreflightPage>> = (page, param, loading) => {
  return get(
    `${prefix.value.replace('/marketing/task', '/marketing/preflight-log')}/${page.current_page}/${page.page_size}`,
    param,
    loading,
  )
}

const getQualityRuleEffect: (
  param?: Record<string, any>,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingQualityRuleEffect>> = (param, loading) => {
  return get(
    `${prefix.value.replace('/marketing/task', '/marketing/quality-rule-effect')}`,
    param,
    loading,
  )
}

const getTaskDashboard: (
  taskId: string,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingTaskDashboard>> = (taskId, loading) => {
  return get(`${prefix.value}/${taskId}/dashboard`, undefined, loading)
}

const getApprovalQueue: (loading?: Ref<boolean>) => Promise<Result<MarketingApprovalQueue>> = (
  loading,
) => {
  return get(
    `${prefix.value.replace('/marketing/task', '/marketing/approval-queue')}`,
    undefined,
    loading,
  )
}

const getCustomerPage: (
  taskId: string,
  page: pageRequest,
  param?: any,
  loading?: Ref<boolean>,
) => Promise<Result<any>> = (taskId, page, param, loading) => {
  return get(
    `${prefix.value}/${taskId}/customer/${page.current_page}/${page.page_size}`,
    param,
    loading,
  )
}

const createCustomer: (
  taskId: string,
  data: MarketingCustomer,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingCustomer>> = (taskId, data, loading) => {
  return post(`${prefix.value}/${taskId}/customer`, data, undefined, loading)
}

const updateCustomer: (
  taskId: string,
  customerId: string,
  data: MarketingCustomer,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingCustomer>> = (taskId, customerId, data, loading) => {
  return put(`${prefix.value}/${taskId}/customer/${customerId}`, data, undefined, loading)
}

const followUpCustomer: (
  taskId: string,
  customerId: string,
  data: MarketingCustomerFollowUp,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingCustomer>> = (taskId, customerId, data, loading) => {
  return post(
    `${prefix.value}/${taskId}/customer/${customerId}/follow-up`,
    data,
    undefined,
    loading,
  )
}

const recordCustomerConversion: (
  taskId: string,
  customerId: string,
  data: MarketingConversionRecordWrite,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingConversionRecord>> = (taskId, customerId, data, loading) => {
  return post(
    `${prefix.value}/${taskId}/customer/${customerId}/conversion`,
    data,
    undefined,
    loading,
  )
}

const getTouchBatches: (
  taskId: string,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingTouchBatch[]>> = (taskId, loading) => {
  return get(`${prefix.value}/${taskId}/touch-batch`, undefined, loading)
}

const createTouchBatch: (
  taskId: string,
  data: MarketingTouchBatchCreate,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingTouchBatch>> = (taskId, data, loading) => {
  return post(`${prefix.value}/${taskId}/touch-batch`, data, undefined, loading)
}

const getTouchBatchDetail: (
  taskId: string,
  batchId: string,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingTouchBatchDetail>> = (taskId, batchId, loading) => {
  return get(`${prefix.value}/${taskId}/touch-batch/${batchId}`, undefined, loading)
}

const updateTouchBatch: (
  taskId: string,
  batchId: string,
  data: Partial<MarketingTouchBatch>,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingTouchBatch>> = (taskId, batchId, data, loading) => {
  return put(`${prefix.value}/${taskId}/touch-batch/${batchId}`, data, undefined, loading)
}

const approveTouchBatch: (
  taskId: string,
  batchId: string,
  data: MarketingTouchBatchApproval,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingTouchBatch>> = (taskId, batchId, data, loading) => {
  return post(`${prefix.value}/${taskId}/touch-batch/${batchId}/approval`, data, undefined, loading)
}

const resubmitTouchBatch: (
  taskId: string,
  batchId: string,
  data: MarketingTouchBatchResubmit,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingTouchBatch>> = (taskId, batchId, data, loading) => {
  return post(`${prefix.value}/${taskId}/touch-batch/${batchId}/resubmit`, data, undefined, loading)
}

const createTouchExecution: (
  taskId: string,
  batchId: string,
  data: Omit<
    MarketingTouchExecution,
    'id' | 'batch_id' | 'customer_name' | 'phone_masked' | 'operator_name' | 'create_time'
  >,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingTouchExecution>> = (taskId, batchId, data, loading) => {
  return post(
    `${prefix.value}/${taskId}/touch-batch/${batchId}/execution`,
    data,
    undefined,
    loading,
  )
}

const getFollowUpQueue: (taskId: string, loading?: Ref<boolean>) => Promise<Result<any[]>> = (
  taskId,
  loading,
) => {
  return get(`${prefix.value}/${taskId}/follow-up-queue`, undefined, loading)
}

const deleteCustomer: (
  taskId: string,
  customerId: string,
  loading?: Ref<boolean>,
) => Promise<Result<boolean>> = (taskId, customerId, loading) => {
  return del(`${prefix.value}/${taskId}/customer/${customerId}`, undefined, {}, loading)
}

const previewCustomerImport: (
  taskId: string,
  data: FormData,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingCustomerImportPreview>> = (taskId, data, loading) => {
  return post(`${prefix.value}/${taskId}/customer/import/preview`, data, undefined, loading)
}

const confirmCustomerImport: (
  taskId: string,
  data: Pick<MarketingCustomerImportPreview, 'file_name' | 'mapping' | 'rows'>,
  loading?: Ref<boolean>,
) => Promise<
  Result<{ batch: MarketingCustomerImportBatch; rows: MarketingCustomerImportRow[] }>
> = (taskId, data, loading) => {
  return post(`${prefix.value}/${taskId}/customer/import`, data, undefined, loading)
}

const getCustomerImportHistory: (
  taskId: string,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingCustomerImportBatch[]>> = (taskId, loading) => {
  return get(`${prefix.value}/${taskId}/customer/import-history`, undefined, loading)
}

export default {
  getTaskPage,
  getTaskList,
  createTask,
  updateTask,
  deleteTask,
  getTaskEffect,
  getQualityReviewPage,
  handleQualityReview,
  getQualityPolicy,
  updateQualityPolicy,
  getPreflightLogPage,
  getQualityRuleEffect,
  getTaskDashboard,
  getApprovalQueue,
  getCustomerPage,
  createCustomer,
  updateCustomer,
  followUpCustomer,
  recordCustomerConversion,
  getTouchBatches,
  createTouchBatch,
  getTouchBatchDetail,
  updateTouchBatch,
  approveTouchBatch,
  resubmitTouchBatch,
  createTouchExecution,
  getFollowUpQueue,
  deleteCustomer,
  previewCustomerImport,
  confirmCustomerImport,
  getCustomerImportHistory,
}
