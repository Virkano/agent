import type { Ref } from 'vue'

import { get, post, put } from '@/request'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type MetricWorkOrderStatus = 'NEW' | 'ASSIGNED' | 'CLAIMED' | 'PROCESSING' | 'RESOLVED' | 'CLOSED'

export interface MetricFoundationSummary {
  definition_count: number
  theme_count: number
  batch_count: number
  baseline_count: number
  rule_count: number
  active_incident_count: number
  open_order_count: number
}

export interface MetricThemeSummary {
  theme: string
  theme_label: string
  metric_count: number
}

export interface MetricDefinitionCatalog {
  id: string
  metric_key: string
  name: string
  theme: string
  theme_label: string
  unit: string
  description: string
  dimensions_schema: string[]
  enabled: boolean
}

export interface MetricDefinitionOverview extends MetricDefinitionCatalog {
  latest_value: number | null
  latest_dimensions: Record<string, string>
  observed_at: string | null
}

export interface MetricAnalyticsPoint {
  id: string
  value: number
  dimensions: Record<string, string>
  observed_at: string
  batch_no: string
  baseline_mean: number | null
  baseline_standard_deviation: number | null
  warning_threshold: number | null
  critical_threshold: number | null
  alert: null | {
    id: string
    severity: 'WARNING' | 'CRITICAL'
    status: string
    threshold_value: number
    rule_name: string
    config_version: number
  }
}

export interface MetricAnalytics {
  filters: {
    theme: string
    definition_id: string | null
    device: string
    network_element: string
    time_slot: string
  }
  dimension_options: {
    device: string[]
    network_element: string[]
    time_slot: string[]
  }
  definitions: MetricDefinitionCatalog[]
  selected_definition: MetricDefinitionCatalog | null
  theme_stats: Array<MetricThemeSummary & {
    observation_count: number
    average_value: number | null
    minimum_value: number | null
    maximum_value: number | null
    latest_value: number | null
    latest_unit: string
    latest_observed_at: string | null
    alert_count: number
  }>
  summary: {
    observation_count: number
    average_value: number | null
    minimum_value: number | null
    maximum_value: number | null
    alert_count: number
  }
  points: MetricAnalyticsPoint[]
}

export interface MetricObservationDetail {
  observation: {
    id: string
    definition: MetricDefinitionCatalog
    value: number
    dimensions: Record<string, string>
    dimension_key: string
    observed_at: string
    raw_snapshot: Record<string, unknown>
  }
  batch: {
    id: string
    batch_no: string
    status: string
    source_name: string
    total_rows: number
    accepted_rows: number
    rejected_rows: number
    collected_at: string
    operator_name: string
  }
  baselines: Array<{
    id: string
    version: number
    algorithm: string
    window_size: number
    sample_count: number
    mean_value: number
    standard_deviation: number
    snapshot: Record<string, unknown>
    calculated_at: string
  }>
  incidents: Array<{
    id: string
    title: string
    message: string
    severity: 'WARNING' | 'CRITICAL'
    status: string
    observed_value: number
    threshold_value: number
    config_version: number
    config_snapshot: Record<string, unknown>
    rule_name: string
    first_triggered_at: string
    last_triggered_at: string
    orders: Array<MetricDispatchOrder & { events: MetricOrderEvent[] }>
  }>
}

export interface MetricDataSource {
  id: string
  source_key: string
  name: string
  source_type: 'MANUAL' | 'API' | 'DATABASE'
  source_type_label: string
  config_snapshot: Record<string, unknown>
  enabled: boolean
  update_time: string
}

export interface MetricRuleOverview {
  id: string
  definition_id: string
  theme: string
  metric_name: string
  theme_label: string
  name: string
  mode: 'STATIC' | 'DYNAMIC'
  mode_label: string
  direction_label: string
  direction: 'ABOVE' | 'BELOW'
  warning_threshold: number | null
  critical_threshold: number | null
  warning_deviation: number
  critical_deviation: number
  baseline_window: number
  dimension_filter: Record<string, string>
  active_windows: Array<{ start: string; end: string }>
  config_version: number
  compliance_status: 'PASSED' | 'FAILED'
  compliance_issues: string[]
  enabled: boolean
}

export interface MetricAssignee {
  id: string
  name: string
  username: string
}

export interface MetricDutyShift {
  id: string
  name: string
  starts_at: string
  ends_at: string
  assignee_id: string
  assignee_name: string
  contact_snapshot: Record<string, unknown>
  enabled: boolean
}

export interface MetricOrderEvent {
  id: string
  action: string
  action_label: string
  from_status: string
  to_status: string
  note: string
  snapshot: Record<string, unknown>
  operator_id: string | null
  operator_name: string
  occurred_at: string
}

export interface MetricDispatchOrder {
  id: string
  incident_id: string
  title: string
  status: MetricWorkOrderStatus
  status_label: string
  severity: 'WARNING' | 'CRITICAL'
  metric_name: string
  theme_label: string
  observed_value: number
  threshold_value: number
  assignee_id: string | null
  assignee_name: string
  assignment_snapshot: Record<string, unknown>
  create_time: string
  claimed_at: string | null
  resolved_at: string | null
  closed_at: string | null
}

export interface MetricCollectionBatchOverview {
  id: string
  batch_no: string
  status: 'IMPORTED' | 'PARTIAL' | 'FAILED'
  accepted_rows: number
  rejected_rows: number
  collected_at: string
}

export interface MetricFoundationOverview {
  summary: MetricFoundationSummary
  themes: MetricThemeSummary[]
  definitions: MetricDefinitionOverview[]
  sources: MetricDataSource[]
  rules: MetricRuleOverview[]
  duty_shifts: MetricDutyShift[]
  assignees: MetricAssignee[]
  orders: MetricDispatchOrder[]
  recent_batches: MetricCollectionBatchOverview[]
}

const prefix = () => {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/metric-foundation`
}

export const getMetricFoundationOverview = (
  loading?: Ref<boolean>,
): Promise<Result<MetricFoundationOverview>> => get(`${prefix()}/overview`, {}, loading)

export const getMetricAnalytics = (
  params: Record<string, unknown> = {},
  loading?: Ref<boolean>,
): Promise<Result<MetricAnalytics>> => get(`${prefix()}/analytics`, params, loading)

export const getMetricObservationDetail = (
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<MetricObservationDetail>> => get(`${prefix()}/observation/${id}`, {}, loading)

export const bootstrapMetricFoundation = (
  loading?: Ref<boolean>,
): Promise<Result<{ overview: MetricFoundationOverview }>> => post(`${prefix()}/bootstrap`, {}, {}, loading)

export const operateMetricDispatchOrder = (
  id: string,
  data: {
    action: 'ASSIGN' | 'TRANSFER' | 'CLAIM' | 'START' | 'COMMENT' | 'RESOLVE' | 'CLOSE'
    assignee_id?: string
    note?: string
  },
  loading?: Ref<boolean>,
): Promise<Result<MetricDispatchOrder>> => post(`${prefix()}/order/${id}/operate`, data, {}, loading)

export const saveMetricDefinition = (
  data: Record<string, unknown>,
  id?: string,
  loading?: Ref<boolean>,
): Promise<Result<MetricDefinitionOverview>> => id
  ? put(`${prefix()}/definition/${id}`, data, {}, loading)
  : post(`${prefix()}/definition`, data, {}, loading)

export const saveMetricSource = (
  data: Record<string, unknown>,
  id?: string,
  loading?: Ref<boolean>,
): Promise<Result<MetricDataSource>> => id
  ? put(`${prefix()}/source/${id}`, data, {}, loading)
  : post(`${prefix()}/source`, data, {}, loading)

export const saveMetricRule = (
  data: Record<string, unknown>,
  id?: string,
  loading?: Ref<boolean>,
): Promise<Result<MetricRuleOverview>> => id
  ? put(`${prefix()}/rule/${id}`, data, {}, loading)
  : post(`${prefix()}/rule`, data, {}, loading)

export const saveMetricDutyShift = (
  data: Record<string, unknown>,
  id?: string,
  loading?: Ref<boolean>,
): Promise<Result<MetricDutyShift>> => id
  ? put(`${prefix()}/duty-shift/${id}`, data, {}, loading)
  : post(`${prefix()}/duty-shift`, data, {}, loading)

export const getMetricOrderEvents = (
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<MetricOrderEvent[]>> => get(`${prefix()}/order/${id}/events`, {}, loading)
