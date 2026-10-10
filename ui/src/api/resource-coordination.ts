import type { Ref } from 'vue'

import { get, post } from '@/request'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type ResourcePoolType = 'AGENT' | 'MODEL' | 'TOOL' | 'WORKER'
export type DispatchTaskSource = 'WEBHOOK' | 'SCHEDULED' | 'USER' | 'SYSTEM'
export type DispatchTaskStatus = 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELLED'
export type DispatchTaskAction = 'SUCCEED' | 'FAIL' | 'CANCEL'

export interface ResourcePool {
  id: string
  code: string
  name: string
  resource_type: ResourcePoolType
  resource_type_label: string
  capacity: number
  used_units: number
  available_units: number
  utilization_percent: number
  max_units_per_task: number
  lease_timeout_seconds: number
  enabled: boolean
  description: string
  metadata: Record<string, unknown>
  active_lease_count: number
  queued_task_count: number
  create_time: string
}

export interface ResourceLease {
  id: string
  status: 'ACTIVE' | 'RELEASED' | 'EXPIRED'
  status_label: string
  units: number
  expires_at: string
  released_at: string | null
  release_reason: string
}

export interface DispatchTaskEvent {
  id: string
  sequence_no: number
  event_type: string
  event_type_label: string
  previous_status: string
  current_status: DispatchTaskStatus
  current_status_label: string
  detail: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface DispatchTask {
  id: string
  pool_id: string
  pool_code: string
  pool_name: string
  code: string
  name: string
  source: DispatchTaskSource
  source_label: string
  source_reference: string
  priority: number
  required_units: number
  mutex_keys: string[]
  status: DispatchTaskStatus
  status_label: string
  queue_reason: string
  queued_at: string
  started_at: string | null
  finished_at: string | null
  lease: ResourceLease | null
  payload_snapshot?: Record<string, unknown>
  result_summary?: Record<string, unknown>
  events?: DispatchTaskEvent[]
  create_time: string
}

export interface ResourceCoordinationDashboard {
  summary: {
    pool_count: number
    enabled_pool_count: number
    queued_task_count: number
    running_task_count: number
    succeeded_task_count: number
    failed_task_count: number
    active_lease_count: number
    allocated_units: number
    mutex_conflict_count: number
  }
  pools: ResourcePool[]
  tasks: DispatchTask[]
}

export interface ResourcePoolCreateForm {
  code: string
  name: string
  resource_type: ResourcePoolType
  capacity: number
  max_units_per_task: number
  lease_timeout_seconds: number
  description: string
}

export interface DispatchTaskCreateForm {
  request_id: string
  idempotency_key: string
  name: string
  source: DispatchTaskSource
  source_reference: string
  priority: number
  required_units: number
  mutex_keys: string[]
  payload: Record<string, unknown>
}

const prefix = () => {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/resource-coordination`
}

export const getResourceCoordinationDashboard = (
  loading?: Ref<boolean>,
): Promise<Result<ResourceCoordinationDashboard>> => get(`${prefix()}/dashboard`, undefined, loading)

export const createResourcePool = (
  data: ResourcePoolCreateForm,
  loading?: Ref<boolean>,
): Promise<Result<ResourcePool>> => post(`${prefix()}/pool`, data, undefined, loading)

export const createDispatchTask = (
  poolId: string,
  data: DispatchTaskCreateForm,
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; task: DispatchTask }>> =>
  post(`${prefix()}/pool/${poolId}/task`, data, undefined, loading)

export const getDispatchTask = (
  taskId: string,
  loading?: Ref<boolean>,
): Promise<Result<DispatchTask>> => get(`${prefix()}/task/${taskId}`, undefined, loading)

export const operateDispatchTask = (
  taskId: string,
  data: { action: DispatchTaskAction; note?: string; result_summary?: Record<string, unknown> },
  loading?: Ref<boolean>,
): Promise<Result<{ task: DispatchTask; allocated_task_ids: string[] }>> =>
  post(`${prefix()}/task/${taskId}/operate`, data, undefined, loading)

export const reclaimResourcePool = (
  poolId: string,
  loading?: Ref<boolean>,
): Promise<Result<{ expired_lease_ids: string[]; allocated_task_ids: string[] }>> =>
  post(`${prefix()}/pool/${poolId}/reclaim`, {}, undefined, loading)
