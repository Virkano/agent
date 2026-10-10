import type { Ref } from 'vue'

import { get, post, put } from '@/request'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type MonitoringScope = 'MODEL' | 'DATA' | 'KNOWLEDGE' | 'RESOURCE'
export type MonitoringStatus = 'HEALTHY' | 'WARNING' | 'CRITICAL' | 'UNKNOWN'
export type MonitoringAlertStatus = 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED'
export type MonitoringOperator = 'GT' | 'GTE' | 'LT' | 'LTE'
export type MonitoringAutoAction = 'NONE' | 'RETRY_FAILED_RUN' | 'CREATE_ROLLBACK_TASK'

export interface MonitoringMetric {
  id: string
  scope: MonitoringScope
  scope_label: string
  metric_key: string
  metric_name: string
  value: number
  unit: string
  status: MonitoringStatus
  status_label: string
  details: Record<string, unknown>
  collected_at: string
}

export interface MonitoringScopeGroup {
  scope: MonitoringScope
  scope_label: string
  metrics: MonitoringMetric[]
}

export interface MonitoringDashboard {
  latest_run: null | {
    id: string
    status: string
    summary: Record<string, number | Record<string, number>>
    error_message: string
    finished_at: string
  }
  scopes: MonitoringScopeGroup[]
  trends: Record<string, Array<{ value: number; collected_at: string }>>
  summary: {
    metric_count: number
    active_alert_count: number
    critical_alert_count: number
    rule_count: number
  }
}

export interface MonitoringRule {
  id: string
  name: string
  scope: MonitoringScope
  scope_label: string
  metric_key: string
  metric_name: string
  operator: MonitoringOperator
  operator_label: string
  warning_threshold: number | null
  critical_threshold: number | null
  enabled: boolean
  auto_action: MonitoringAutoAction
  auto_action_label: string
  cooldown_minutes: number
  description: string
  update_time: string
}

export interface MonitoringRuleWriteRequest {
  name: string
  metric_key: string
  operator: MonitoringOperator
  warning_threshold: number | null
  critical_threshold: number | null
  enabled: boolean
  auto_action: MonitoringAutoAction
  cooldown_minutes: number
  description: string
}

export interface MonitoringAlert {
  id: string
  scope: MonitoringScope
  scope_label: string
  metric_key: string
  metric_name: string
  title: string
  message: string
  severity: MonitoringStatus
  status: MonitoringAlertStatus
  status_label: string
  observed_value: number
  threshold_value: number
  auto_action: MonitoringAutoAction
  response_status: string
  response_detail: Record<string, unknown>
  first_triggered_at: string
  last_triggered_at: string
  acknowledged_at?: string | null
  resolved_at?: string | null
}

const prefix = () => {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/platform-monitoring`
}

export const getMonitoringDashboard = (loading?: Ref<boolean>): Promise<Result<MonitoringDashboard>> =>
  get(`${prefix()}/dashboard`, {}, loading)

export const collectMonitoringMetrics = (loading?: Ref<boolean>): Promise<Result<MonitoringDashboard>> =>
  post(`${prefix()}/collect`, {}, {}, loading)

export const getMonitoringRules = (loading?: Ref<boolean>): Promise<Result<MonitoringRule[]>> =>
  get(`${prefix()}/rule`, {}, loading)

export const createMonitoringRule = (
  data: MonitoringRuleWriteRequest,
  loading?: Ref<boolean>,
): Promise<Result<MonitoringRule>> => post(`${prefix()}/rule`, data, {}, loading)

export const updateMonitoringRule = (
  id: string,
  data: Partial<MonitoringRuleWriteRequest>,
  loading?: Ref<boolean>,
): Promise<Result<MonitoringRule>> => put(`${prefix()}/rule/${id}`, data, {}, loading)

export const getMonitoringAlerts = (
  status = '',
  loading?: Ref<boolean>,
): Promise<Result<MonitoringAlert[]>> => get(`${prefix()}/alert`, { status }, loading)

export const operateMonitoringAlert = (
  id: string,
  action: 'ACKNOWLEDGE' | 'RESOLVE' | 'RETRY_RESPONSE',
  loading?: Ref<boolean>,
): Promise<Result<MonitoringAlert>> => post(`${prefix()}/alert/${id}/operate`, { action }, {}, loading)

