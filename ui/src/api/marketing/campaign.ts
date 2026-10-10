import { del, exportFile, get, post, put } from '@/request/index'
import type { Result } from '@/request/Result'
import type { pageRequest } from '@/api/type/common'
import type { Ref } from 'vue'
import useStore from '@/stores'

const prefix: any = { _value: '/workspace/' }
Object.defineProperty(prefix, 'value', {
  get() {
    return `${this._value}${useStore().user.getWorkspaceId()}/marketing/campaign`
  },
})

export interface MarketingCampaign {
  id?: string
  name: string
  code: string
  status?: 'DRAFT' | 'ACTIVE' | 'PAUSED' | 'ARCHIVED'
  approval_status?: 'DRAFT' | 'PENDING' | 'APPROVED' | 'REJECTED'
  approval_note?: string
  approver_name?: string
  approved_at?: string | null
  can_submit?: boolean
  can_approve?: boolean
  version?: number
  priority?: number
  exclusive_group?: string
  benefit: string
  fee_note?: string
  contract_note?: string
  plan_keywords?: string[]
  provinces?: string[]
  min_data_usage_gb?: number
  min_call_usage_minutes?: number
  effective_start?: string | null
  effective_end?: string | null
  description?: string
  create_time?: string
  update_time?: string
}

export interface MarketingCampaignVersion {
  id: string
  campaign_id: string
  version: number
  snapshot: MarketingCampaign
  change_type: 'BASELINE' | 'CREATE' | 'UPDATE' | 'RESTORE' | 'ARCHIVE'
  source_version?: number | null
  approval_status: 'DRAFT' | 'PENDING' | 'APPROVED' | 'REJECTED'
  approval_note?: string
  approver_name?: string
  approved_at?: string | null
  operator_name?: string
  changed_fields: string[]
  can_restore: boolean
  create_time?: string
}

export interface MarketingCampaignEffectSegment {
  name: string
  customer_count: number
  intent_count: number
  converted_count: number
  manual_count: number
  no_intent_count: number
  intent_rate: number
  conversion_rate: number
}

export interface MarketingCampaignEffect {
  campaign: MarketingCampaign
  scope: string
  metrics: {
    task_count: number
    chat_count: number
    customer_count: number
    intent_count: number
    manual_count: number
    converted_count: number
    no_intent_count: number
    intent_rate: number
    manual_rate: number
  }
  recommendation: {
    action: 'CONTINUE_GRAY' | 'EXPAND' | 'PAUSE'
    reason: string
    suggested_next_batch_size: number
  }
  eligible_tasks: Array<{ id: string; name: string }>
  breakdowns: {
    province: MarketingCampaignEffectSegment[]
    current_plan: MarketingCampaignEffectSegment[]
  }
}
const page = (page: pageRequest, params?: any, loading?: Ref<boolean>) =>
  get(`${prefix.value}/${page.current_page}/${page.page_size}`, params, loading)
const list = (params?: any, loading?: Ref<boolean>): Promise<Result<MarketingCampaign[]>> =>
  get(prefix.value, params, loading)
const create = (data: MarketingCampaign, loading?: Ref<boolean>) =>
  post(prefix.value, data, undefined, loading)
const update = (id: string, data: MarketingCampaign, loading?: Ref<boolean>) =>
  put(`${prefix.value}/${id}`, data, undefined, loading)
const remove = (id: string, loading?: Ref<boolean>) =>
  del(`${prefix.value}/${id}`, undefined, {}, loading)
const submit = (id: string, loading?: Ref<boolean>) =>
  post(`${prefix.value}/${id}/submit`, {}, undefined, loading)
const approve = (
  id: string,
  approval_status: 'APPROVED' | 'REJECTED',
  approval_note = '',
  loading?: Ref<boolean>,
) => post(`${prefix.value}/${id}/approval`, { approval_status, approval_note }, undefined, loading)
const effect = (id: string, loading?: Ref<boolean>): Promise<Result<MarketingCampaignEffect>> =>
  get(`${prefix.value}/${id}/effect`, undefined, loading)
const exportEffect = (id: string, fileName: string, loading?: Ref<boolean>) =>
  exportFile(fileName, `${prefix.value}/${id}/effect/export`, {}, loading)
const action = (
  id: string,
  data: { action: 'EXPAND' | 'PAUSE'; task_id?: string },
  loading?: Ref<boolean>,
) => post(`${prefix.value}/${id}/recommendation-action`, data, undefined, loading)
const versions = (id: string, loading?: Ref<boolean>) =>
  get(`${prefix.value}/${id}/versions`, undefined, loading)
const restore = (id: string, version: number, loading?: Ref<boolean>) =>
  post(`${prefix.value}/${id}/versions/${version}/restore`, {}, undefined, loading)
export default {
  page,
  list,
  create,
  update,
  remove,
  submit,
  approve,
  effect,
  exportEffect,
  action,
  versions,
  restore,
}
