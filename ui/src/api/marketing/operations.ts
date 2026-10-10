import type { Ref } from 'vue'

import { exportFile, get, post, put } from '@/request/index'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type MarketingOperationsHealthStatus = 'HEALTHY' | 'WARNING' | 'CRITICAL'
export type MarketingOperationsIssueSeverity = 'INFO' | 'WARNING' | 'CRITICAL'
export type MarketingTaskHealthStatus = 'HEALTHY' | 'ATTENTION' | 'ERROR'
export type MarketingAlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL'
export type MarketingAlertStatus = 'OPEN' | 'CLAIMED' | 'PROCESSING' | 'CLOSED'
export type MarketingAlertHandleAction = 'CLAIM' | 'START' | 'CLOSE' | 'REOPEN'
export type MarketingAlertCollaborateAction = 'ASSIGN' | 'TRANSFER' | 'COMMENT'
export type MarketingAlertRootCause =
  | 'MODEL'
  | 'DATA'
  | 'KNOWLEDGE'
  | 'SYSTEM'
  | 'PROCESS'
  | 'OTHER'
export type MarketingAlertResolutionType =
  | 'CONFIG_CHANGE'
  | 'DATA_FIX'
  | 'KNOWLEDGE_UPDATE'
  | 'RETRY_RECOVERY'
  | 'MANUAL_INTERVENTION'
  | 'FALSE_POSITIVE'
  | 'OTHER'

export interface MarketingOperationsMetrics {
  active_task_count: number
  task_count: number
  customer_count: number
  conversation_count: number
  conversation_success_rate: number
  avg_response_seconds: number
  slow_conversation_count: number
  total_tokens: number
  quality_review_count: number
  quality_pass_rate: number
  quality_issue_count: number
  pending_review_count: number
  preflight_count: number
  intercepted_count: number
  bypassed_count: number
  runtime_error_count: number
  overdue_batch_count: number
  converted_customer_count: number
  conversion_count: number
  conversion_rate: number
}

export interface MarketingOperationsTrendItem {
  date: string
  conversation_count: number
  quality_issue_count: number
  runtime_error_count: number
  intercepted_count: number
  bypassed_count: number
  conversion_count: number
}

export interface MarketingOperationsIssue {
  type: string
  severity: MarketingOperationsIssueSeverity
  title: string
  description: string
  count: number
  route: string
}

export interface MarketingTaskHealth {
  task_id: string
  task_name: string
  task_status: 'DRAFT' | 'RUNNING' | 'PAUSED' | 'FINISHED'
  health_status: MarketingTaskHealthStatus
  customer_count: number
  conversation_count: number
  avg_response_seconds: number
  quality_issue_count: number
  pending_review_count: number
  runtime_error_count: number
  converted_customer_count: number
  conversion_count: number
  conversion_rate: number
  last_activity_at?: string | null
}

export interface MarketingOperationsOverview {
  range: {
    days: 7 | 30 | 90
    start_date: string
    end_date: string
    task_id?: string | null
  }
  health: {
    status: MarketingOperationsHealthStatus
    label: string
    summary: string
    critical_count: number
    warning_count: number
  }
  metrics: MarketingOperationsMetrics
  trend: MarketingOperationsTrendItem[]
  issues: MarketingOperationsIssue[]
  task_health: MarketingTaskHealth[]
  generated_at: string
}

export interface MarketingAlertActionRecord {
  id: string
  action:
    | 'CREATED'
    | 'REFRESHED'
    | 'CLAIMED'
    | 'STARTED'
    | 'CLOSED'
    | 'REOPENED'
    | 'RESPONSE_OVERDUE'
    | 'RESOLUTION_OVERDUE'
    | 'ASSIGNED'
    | 'TRANSFERRED'
    | 'COMMENTED'
    | 'SUBSCRIBED'
    | 'UNSUBSCRIBED'
    | 'ATTACHED'
  previous_status: MarketingAlertStatus | ''
  current_status: MarketingAlertStatus
  operator_name: string
  note: string
  snapshot: {
    count?: number
    source_active?: boolean
    severity?: MarketingAlertSeverity
    previous_assignee_id?: string | null
    previous_assignee_name?: string
    assignee_id?: string
    assignee_name?: string
    subscriber_user_id?: string
    subscriber_user_name?: string
    file_id?: string
    file_name?: string
    file_size?: number
  }
  revision: number
  create_time: string
}

export interface MarketingAlertHandlingRound {
  id: string
  sequence: number
  assignee_id?: string | null
  assignee_name: string
  assigned_by_name: string
  assigned_at: string
  response_due_at?: string | null
  resolution_due_at?: string | null
  first_responded_at?: string | null
  ended_at?: string | null
  end_reason: '' | 'TRANSFERRED' | 'CLOSED' | 'REOPENED'
  end_note: string
}

export interface MarketingAlertSubscriber {
  id: string
  user_id: string
  user_name: string
  subscribed_by_name: string
  create_time: string
}

export interface MarketingAlertAttachment {
  id: string
  file_name: string
  content_type: string
  file_size: number
  uploader_name: string
  expires_at?: string | null
  create_time: string
  download_url: string
}

export interface MarketingAlert {
  id: string
  alert_type: string
  title: string
  description: string
  severity: MarketingAlertSeverity
  status: MarketingAlertStatus
  current_count: number
  source_active: boolean
  target_route: string
  assignee_id?: string | null
  assignee_name: string
  first_triggered_at: string
  last_triggered_at: string
  sla_started_at?: string | null
  response_due_at?: string | null
  resolution_due_at?: string | null
  first_responded_at?: string | null
  response_escalated_at?: string | null
  resolution_escalated_at?: string | null
  response_overdue: boolean
  resolution_overdue: boolean
  escalation_user_id?: string | null
  escalation_user_name: string
  resolved_at?: string | null
  closed_at?: string | null
  close_note: string
  root_cause_category: MarketingAlertRootCause | ''
  root_cause_label: string
  resolution_type: MarketingAlertResolutionType | ''
  resolution_type_label: string
  impact_scope: string
  revision: number
  actions: MarketingAlertActionRecord[]
  handling_rounds: MarketingAlertHandlingRound[]
  subscribers: MarketingAlertSubscriber[]
  attachments: MarketingAlertAttachment[]
  capabilities: {
    can_assign: boolean
    can_transfer: boolean
    can_comment: boolean
    can_subscribe: boolean
    can_attach: boolean
  }
  related_experiences: MarketingAlertExperience[]
}

export interface MarketingAlertExperience {
  id: string
  title: string
  alert_type?: string
  root_cause_category: MarketingAlertRootCause
  root_cause_label: string
  resolution_type: MarketingAlertResolutionType
  resolution_type_label: string
  impact_scope: string
  close_note: string
  assignee_name: string
  closed_at: string
}

export interface MarketingAlertSummary {
  total_count: number
  active_count: number
  open_count: number
  claimed_count: number
  processing_count: number
  closed_count: number
  critical_count: number
  sla_overdue_count: number
}

export interface MarketingAlertPage {
  total: number
  records: MarketingAlert[]
  current: number
  size: number
  summary: MarketingAlertSummary
}

export interface MarketingAlertRule {
  id: string
  alert_type: string
  name: string
  severity: MarketingAlertSeverity
  enabled: boolean
  threshold: number
  response_sla_minutes: number
  resolution_sla_minutes: number
  escalation_user_id?: string | null
  escalation_user_name: string
  description: string
  updated_by_name: string
  update_time: string
}

export interface MarketingAlertRuleChange {
  id: string
  version: number
  change_type: 'UPDATED' | 'ROLLED_BACK'
  change_type_label: string
  snapshot: {
    enabled: boolean
    threshold: number
    severity: MarketingAlertSeverity
    response_sla_minutes: number
    resolution_sla_minutes: number
    escalation_user_id?: string | null
    escalation_user_name: string
  }
  reason: string
  operator_name: string
  create_time: string
}

export interface MarketingAlertRuleEffectItem {
  rule: MarketingAlertRule
  metrics: {
    signal_event_count: number
    refresh_count: number
    reopen_count: number
    repeat_rate: number
    closed_count: number
    false_positive_count: number
    false_positive_rate: number
    avg_resolution_seconds: number
  }
  recommendation: {
    threshold: number
    changed: boolean
    reason: string
    confidence: 'LOW' | 'MEDIUM' | 'HIGH'
    sample_count: number
  }
  simulations: Array<{
    threshold: number
    estimated_trigger_count: number
    estimated_reduction_rate: number
    recommended: boolean
  }>
  history: MarketingAlertRuleChange[]
}

export interface MarketingAlertRuleEffect {
  range: { days: 7 | 30 | 90; start_at: string; end_at: string }
  summary: {
    rule_count: number
    enabled_rule_count: number
    optimization_count: number
    signal_event_count: number
    false_positive_count: number
  }
  rules: MarketingAlertRuleEffectItem[]
  simulation_note: string
}

export interface MarketingAlertMember {
  id: string
  name: string
  username: string
}

export interface MarketingAlertPerformanceMetrics {
  total_count: number
  active_count: number
  closed_count: number
  overdue_count: number
  avg_response_seconds: number
  avg_resolution_seconds: number
  response_total: number
  response_met_count: number
  response_sla_rate: number
  resolution_total: number
  resolution_met_count: number
  resolution_sla_rate: number
  sla_milestone_total: number
  sla_milestone_met_count: number
  sla_attainment_rate: number
}

export interface MarketingAlertOwnerPerformance extends MarketingAlertPerformanceMetrics {
  assignee_id?: string | null
  assignee_name: string
}

export interface MarketingAlertPerformance {
  range: {
    days: 7 | 30 | 90
    start_at: string
    end_at: string
  }
  summary: MarketingAlertPerformanceMetrics & { unassigned_count: number }
  workload: MarketingAlertOwnerPerformance[]
}

export interface MarketingAlertDistributionItem {
  value: string
  label: string
  count: number
  percentage: number
}

export interface MarketingAlertRetrospective {
  range: { days: 7 | 30 | 90; start_at: string; end_at: string }
  summary: {
    closed_count: number
    classified_count: number
    recurrence_count: number
    avg_resolution_seconds: number
  }
  root_causes: MarketingAlertDistributionItem[]
  resolution_types: MarketingAlertDistributionItem[]
  recurring_alerts: Array<{
    id: string
    title: string
    alert_type: string
    recurrence_count: number
    status: MarketingAlertStatus
    last_triggered_at: string
  }>
  experiences: MarketingAlertExperience[]
}

export interface MarketingAlertNoiseItem {
  id: string
  title: string
  alert_type: string
  severity: MarketingAlertSeverity
  status: MarketingAlertStatus
  current_count: number
  refresh_count: number
  reopen_count: number
  repeat_count: number
  noise_score: number
  noise_level: 'LOW' | 'MEDIUM' | 'HIGH'
  noise_label: string
  recommendation: string
  suggested_root_cause_category: MarketingAlertRootCause | ''
  suggested_root_cause_label: string
  suggested_resolution_type: MarketingAlertResolutionType | ''
  suggested_resolution_type_label: string
  suggested_note: string
  last_triggered_at: string
}

export interface MarketingAlertMergeSuggestion {
  group_key: string
  primary_alert_id: string
  primary_alert_title: string
  alert_count: number
  total_current_count: number
  reason: string
  recommendation: string
  candidates: Array<{
    id: string
    title: string
    alert_type: string
    severity: MarketingAlertSeverity
    status: MarketingAlertStatus
    current_count: number
  }>
}

export interface MarketingAlertNoiseAnalysis {
  range: { days: 7 | 30 | 90; start_at: string; end_at: string }
  summary: {
    monitored_alert_count: number
    repeated_alert_count: number
    high_noise_count: number
    deduplicated_event_count: number
    merge_suggestion_count: number
  }
  noise_alerts: MarketingAlertNoiseItem[]
  merge_suggestions: MarketingAlertMergeSuggestion[]
}

function getOperationsOverview(
  params: { days: 7 | 30 | 90; task_id?: string },
  loading?: Ref<boolean>,
): Promise<Result<MarketingOperationsOverview>> {
  const { user } = useStore()
  return get(`/workspace/${user.getWorkspaceId()}/marketing/operations-overview`, params, loading)
}

function getAlertPage(
  page: { current_page: number; page_size: number },
  params?: {
    status?: MarketingAlertStatus | ''
    severity?: MarketingAlertSeverity | ''
    keyword?: string
    assignee_id?: string
    unassigned?: boolean
    active_only?: boolean
    sla_overdue?: boolean
  },
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlertPage>> {
  const { user } = useStore()
  return get(
    `/workspace/${user.getWorkspaceId()}/marketing/alert/${page.current_page}/${page.page_size}`,
    params,
    loading,
  )
}

function syncAlerts(
  days: 7 | 30 | 90,
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlertSummary>> {
  const { user } = useStore()
  return post(
    `/workspace/${user.getWorkspaceId()}/marketing/alert/sync`,
    { days },
    undefined,
    loading,
  )
}

function handleAlert(
  id: string,
  data: {
    action: MarketingAlertHandleAction
    note?: string
    root_cause_category?: MarketingAlertRootCause
    resolution_type?: MarketingAlertResolutionType
    impact_scope?: string
  },
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlert>> {
  const { user } = useStore()
  return post(
    `/workspace/${user.getWorkspaceId()}/marketing/alert/${id}/handle`,
    data,
    undefined,
    loading,
  )
}

function getAlertRetrospective(
  days: 7 | 30 | 90,
  rootCauseCategory: MarketingAlertRootCause | '' = '',
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlertRetrospective>> {
  const { user } = useStore()
  return get(
    `/workspace/${user.getWorkspaceId()}/marketing/alert-retrospective`,
    { days, root_cause_category: rootCauseCategory },
    loading,
  )
}

function getAlertNoiseAnalysis(
  days: 7 | 30 | 90,
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlertNoiseAnalysis>> {
  const { user } = useStore()
  return get(
    `/workspace/${user.getWorkspaceId()}/marketing/alert-noise-analysis`,
    { days },
    loading,
  )
}

function exportAlertRetrospective(
  days: 7 | 30 | 90,
  rootCauseCategory: MarketingAlertRootCause | '' = '',
  loading?: Ref<boolean>,
) {
  const { user } = useStore()
  return exportFile(
    '营销告警复盘.csv',
    `/workspace/${user.getWorkspaceId()}/marketing/alert-retrospective/export`,
    { days, root_cause_category: rootCauseCategory },
    loading,
  )
}

function collaborateAlert(
  id: string,
  data: { action: MarketingAlertCollaborateAction; assignee_id?: string; note?: string },
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlert>> {
  const { user } = useStore()
  return post(
    `/workspace/${user.getWorkspaceId()}/marketing/alert/${id}/collaborate`,
    data,
    undefined,
    loading,
  )
}

function updateAlertSubscriber(
  id: string,
  data: { action: 'ADD' | 'REMOVE'; user_id: string },
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlert>> {
  const { user } = useStore()
  return post(
    `/workspace/${user.getWorkspaceId()}/marketing/alert/${id}/subscriber`,
    data,
    undefined,
    loading,
  )
}

function uploadAlertAttachment(
  id: string,
  file: File,
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlert>> {
  const { user } = useStore()
  const data = new FormData()
  data.append('file', file)
  return post(
    `/workspace/${user.getWorkspaceId()}/marketing/alert/${id}/attachment`,
    data,
    undefined,
    loading,
  )
}

function getAlert(id: string, loading?: Ref<boolean>): Promise<Result<MarketingAlert>> {
  const { user } = useStore()
  return get(`/workspace/${user.getWorkspaceId()}/marketing/alert/${id}`, undefined, loading)
}

function getAlertRules(loading?: Ref<boolean>): Promise<Result<MarketingAlertRule[]>> {
  const { user } = useStore()
  return get(`/workspace/${user.getWorkspaceId()}/marketing/alert-rule`, undefined, loading)
}

function getAlertRuleEffect(
  days: 7 | 30 | 90,
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlertRuleEffect>> {
  const { user } = useStore()
  return get(`/workspace/${user.getWorkspaceId()}/marketing/alert-rule-effect`, { days }, loading)
}

function getAlertMembers(loading?: Ref<boolean>): Promise<Result<MarketingAlertMember[]>> {
  const { user } = useStore()
  return get(`/workspace/${user.getWorkspaceId()}/marketing/alert-members`, undefined, loading)
}

function getAlertPerformance(
  days: 7 | 30 | 90,
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlertPerformance>> {
  const { user } = useStore()
  return get(`/workspace/${user.getWorkspaceId()}/marketing/alert-performance`, { days }, loading)
}

function updateAlertRule(
  id: string,
  data: Pick<
    MarketingAlertRule,
    | 'enabled'
    | 'threshold'
    | 'severity'
    | 'response_sla_minutes'
    | 'resolution_sla_minutes'
    | 'escalation_user_id'
  > & { change_reason?: string },
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlertRule>> {
  const { user } = useStore()
  return put(
    `/workspace/${user.getWorkspaceId()}/marketing/alert-rule/${id}`,
    data,
    undefined,
    loading,
  )
}

function rollbackAlertRule(
  id: string,
  changeId: string,
  loading?: Ref<boolean>,
): Promise<Result<MarketingAlertRule>> {
  const { user } = useStore()
  return post(
    `/workspace/${user.getWorkspaceId()}/marketing/alert-rule/${id}/rollback`,
    { change_id: changeId },
    undefined,
    loading,
  )
}

export default {
  getOperationsOverview,
  getAlertPage,
  syncAlerts,
  handleAlert,
  getAlertNoiseAnalysis,
  getAlertRetrospective,
  exportAlertRetrospective,
  collaborateAlert,
  updateAlertSubscriber,
  uploadAlertAttachment,
  getAlert,
  getAlertRules,
  getAlertRuleEffect,
  getAlertMembers,
  getAlertPerformance,
  updateAlertRule,
  rollbackAlertRule,
}
