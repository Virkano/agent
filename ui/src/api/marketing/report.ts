import type { Ref } from 'vue'

import { del, exportFile, get, post, put } from '@/request/index'
import type { Result } from '@/request/Result'
import type { PageList } from '@/api/type/common'
import useStore from '@/stores'

export type MarketingReportStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED'
export type MarketingAttributionMethod = 'LAST_TOUCH' | 'LINEAR'
export type MarketingReportSubscriptionFrequency = 'DAILY' | 'WEEKLY' | 'MONTHLY'

export interface MarketingReportTemplate {
  id: string
  name: string
  description: string
  title_template: string
  narrative_prompt: string
  config: Record<string, unknown>
  active: boolean
  version: number
  create_time: string
  update_time: string
}

export interface MarketingReportMetrics {
  task_count: number
  customer_count: number
  batch_count: number
  exposure_count: number
  touch_count: number
  reached_customer_count: number
  touch_rate: number
  conversion_count: number
  converted_customer_count: number
  conversion_rate: number
  attributed_revenue: number
  marketing_cost: number
  variable_cost: number
  marginal_contribution: number
  roi: number
  attribution_method: MarketingAttributionMethod
  attribution_method_label: string
  attribution_touch_count: number
  attribution_distribution: Array<{
    channel: string
    weight: number
    attributed_revenue: number
    revenue_share: number
  }>
  channel_distribution: Array<{
    channel: string
    task_count: number
    target_count: number
  }>
}

export interface MarketingAnalysisReport {
  id: string
  title: string
  period_start: string
  period_end: string
  status: MarketingReportStatus
  attribution_method: MarketingAttributionMethod
  attribution_method_label: string
  template_id?: string | null
  template_name: string
  task_id?: string | null
  task_name: string
  model_id?: string | null
  model_name: string
  metrics: Partial<MarketingReportMetrics>
  narrative: string
  html_content?: string
  input_snapshot?: MarketingReportGeneratePayload
  error_message: string
  retry_count: number
  generated_at?: string | null
  create_user: string
  create_time: string
  update_time: string
  runs?: Array<{
    id: string
    attempt: number
    status: MarketingReportStatus
    error_message: string
    started_at?: string | null
    finished_at?: string | null
  }>
}

export interface MarketingReportMetadata {
  templates: MarketingReportTemplate[]
  tasks: Array<{ id: string; name: string; channel: string; status: string }>
  models: Array<{ id: string; name: string; provider: string; model_name: string }>
}

export interface MarketingReportGeneratePayload {
  template_id?: string | null
  task_id?: string | null
  model_id?: string | null
  title?: string
  period_start: string
  period_end: string
  attribution_method?: MarketingAttributionMethod
  attributed_revenue?: string | number
  marketing_cost?: string | number
  variable_cost?: string | number
  use_llm?: boolean
}

export interface MarketingReportSubscription {
  id: string
  name: string
  template_id: string
  template_name: string
  task_id?: string | null
  task_name: string
  model_id?: string | null
  model_name: string
  frequency: MarketingReportSubscriptionFrequency
  run_time: string
  weekday: number
  month_day: number
  period_days: number
  attribution_method: MarketingAttributionMethod
  use_llm: boolean
  email_enabled: boolean
  recipient_emails: string[]
  enabled: boolean
  next_run_at?: string | null
  last_run_at?: string | null
  last_status: string
  last_error: string
  last_report_id?: string | null
}

export type MarketingReportSubscriptionPayload = Omit<
  MarketingReportSubscription,
  | 'id'
  | 'template_name'
  | 'task_name'
  | 'model_name'
  | 'next_run_at'
  | 'last_run_at'
  | 'last_status'
  | 'last_error'
  | 'last_report_id'
>

export type MarketingReportTemplatePayload = Pick<
  MarketingReportTemplate,
  'name' | 'description' | 'title_template' | 'narrative_prompt' | 'active'
>

function prefix() {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/marketing/report`
}

export function getReportMetadata(loading?: Ref<boolean>): Promise<Result<MarketingReportMetadata>> {
  return get(`${prefix()}/metadata`, undefined, loading)
}

export function getReportPage(
  page: { current_page: number; page_size: number },
  params?: { keyword?: string; status?: MarketingReportStatus | ''; task_id?: string },
  loading?: Ref<boolean>,
): Promise<Result<PageList<MarketingAnalysisReport[]>>> {
  return get(`${prefix()}/${page.current_page}/${page.page_size}`, params, loading)
}

export function getReportDetail(
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<MarketingAnalysisReport>> {
  return get(`${prefix()}/${id}`, undefined, loading)
}

export function generateReport(
  data: MarketingReportGeneratePayload,
  loading?: Ref<boolean>,
): Promise<Result<MarketingAnalysisReport>> {
  return post(`${prefix()}/generate`, data, undefined, loading)
}

export function retryReport(
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<MarketingAnalysisReport>> {
  return post(`${prefix()}/${id}/retry`, undefined, undefined, loading)
}

export function createReportTemplate(
  data: MarketingReportTemplatePayload,
  loading?: Ref<boolean>,
): Promise<Result<MarketingReportTemplate>> {
  return post(`${prefix()}/template`, data, undefined, loading)
}

export function updateReportTemplate(
  id: string,
  data: Partial<MarketingReportTemplatePayload>,
  loading?: Ref<boolean>,
): Promise<Result<MarketingReportTemplate>> {
  return put(`${prefix()}/template/${id}`, data, undefined, loading)
}

export function deleteReportTemplate(id: string): Promise<Result<boolean>> {
  return del(`${prefix()}/template/${id}`)
}

export function downloadReport(id: string, format: 'html' | 'pdf' | 'docx', loading?: Ref<boolean>) {
  return exportFile(`marketing-report.${format}`, `${prefix()}/${id}/download/${format}`, {}, loading)
}

function subscriptionPrefix() {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/marketing/report-subscription`
}

export function getReportSubscriptions(
  loading?: Ref<boolean>,
): Promise<Result<MarketingReportSubscription[]>> {
  return get(subscriptionPrefix(), undefined, loading)
}

export function createReportSubscription(
  data: MarketingReportSubscriptionPayload,
  loading?: Ref<boolean>,
): Promise<Result<MarketingReportSubscription>> {
  return post(subscriptionPrefix(), data, undefined, loading)
}

export function updateReportSubscription(
  id: string,
  data: MarketingReportSubscriptionPayload,
  loading?: Ref<boolean>,
): Promise<Result<MarketingReportSubscription>> {
  return put(`${subscriptionPrefix()}/${id}`, data, undefined, loading)
}

export function deleteReportSubscription(id: string): Promise<Result<boolean>> {
  return del(`${subscriptionPrefix()}/${id}`)
}

export function runReportSubscription(
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<{ report_id: string; report_status: MarketingReportStatus }>> {
  return post(`${subscriptionPrefix()}/${id}/run`, {}, undefined, loading)
}
