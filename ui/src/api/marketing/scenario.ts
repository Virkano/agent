import { get, post, put, del } from '@/request/index'
import type { Result } from '@/request/Result'
import type { pageRequest } from '@/api/type/common'
import type { Ref } from 'vue'
import useStore from '@/stores'

const prefix: any = { _value: '/workspace/' }
Object.defineProperty(prefix, 'value', {
  get: function () {
    const { user } = useStore()
    return `${this._value}${user.getWorkspaceId()}/marketing/scenario`
  },
})

export interface MarketingScenario {
  id?: string
  name: string
  target_audience?: string
  objective?: string
  channel?: string
  status?: 'DRAFT' | 'ACTIVE' | 'PAUSED'
  application_id?: string | null
  application_name?: string
  knowledge_id?: string | null
  knowledge_name?: string
  config?: Record<string, any>
  description?: string
  create_user?: string
  create_time?: string
  update_time?: string
}

export interface MarketingRecommendationOffer {
  id?: string
  name: string
  benefit: string
  plan_keywords: string[]
  provinces: string[]
  min_data_usage_gb?: number
  min_call_usage_minutes?: number
  fee_note: string
  contract_note: string
  priority?: number
  exclusive_group?: string
  effective_start?: string
  effective_end?: string
}

export interface MarketingRecommendationPolicy {
  enabled: boolean
  offers: MarketingRecommendationOffer[]
}

const getScenarioPage: (
  page: pageRequest,
  param?: any,
  loading?: Ref<boolean>,
) => Promise<Result<any>> = (page, param, loading) => {
  return get(`${prefix.value}/${page.current_page}/${page.page_size}`, param, loading)
}

const getScenarioList: (param?: any, loading?: Ref<boolean>) => Promise<Result<MarketingScenario[]>> = (
  param,
  loading,
) => {
  return get(prefix.value, param, loading)
}

const createScenario: (
  data: MarketingScenario,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingScenario>> = (data, loading) => {
  return post(prefix.value, data, undefined, loading)
}

const updateScenario: (
  scenarioId: string,
  data: MarketingScenario,
  loading?: Ref<boolean>,
) => Promise<Result<MarketingScenario>> = (scenarioId, data, loading) => {
  return put(`${prefix.value}/${scenarioId}`, data, undefined, loading)
}

const deleteScenario: (scenarioId: string, loading?: Ref<boolean>) => Promise<Result<boolean>> = (
  scenarioId,
  loading,
) => {
  return del(`${prefix.value}/${scenarioId}`, undefined, {}, loading)
}

const simulateRecommendation: (
  scenarioId: string,
  data: Record<string, string>,
  loading?: Ref<boolean>,
) => Promise<Result<any>> = (scenarioId, data, loading) => {
  return post(`${prefix.value}/${scenarioId}/recommendation/simulate`, data, undefined, loading)
}

export default {
  getScenarioPage,
  getScenarioList,
  createScenario,
  updateScenario,
  simulateRecommendation,
  deleteScenario,
}
