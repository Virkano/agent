import type { Ref } from 'vue'

import { get, post } from '@/request'
import type { Result } from '@/request/Result'
import useStore from '@/stores'
import type { ResourcePool } from '@/api/resource-coordination'

export type EventSourceType = 'WEBHOOK' | 'SCHEDULED' | 'USER' | 'SYSTEM'
export type FlowVersionStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
export type FlowRunStatus = 'PENDING' | 'RUNNING' | 'WAITING' | 'SUCCEEDED' | 'FAILED' | 'CANCELLED'
export type FlowNodeRunStatus = 'PENDING' | 'READY' | 'WAITING_RESOURCE' | 'RUNNING' | 'WAITING_MANUAL' | 'SUCCEEDED' | 'FAILED' | 'SKIPPED' | 'CANCELLED'
export type FlowNodeType = 'DATA_QUERY' | 'AGENT' | 'REPORT' | 'NOTIFICATION' | 'TOOL' | 'MANUAL'
export type NodeDependencyMode = 'ALL_SUCCESS' | 'ANY_SUCCESS' | 'ALL_TERMINAL'
export type NodeActivationMode = 'NORMAL' | 'FALLBACK_ONLY'
export type NodeFailureStrategy = 'FAIL_RUN' | 'FALLBACK' | 'CONTINUE'

export interface FlowNodeDefinition {
  code: string
  name: string
  node_type: FlowNodeType
  dependencies: string[]
  resource_pool_id?: string | null
  priority?: number
  required_units?: number
  mutex_keys?: string[]
  dependency_mode?: NodeDependencyMode
  activation_mode?: NodeActivationMode
  condition?: Record<string, unknown>
  max_retries?: number
  timeout_seconds?: number
  failure_strategy?: NodeFailureStrategy
  fallback_node_code?: string
  recovery_action?: string
}

export interface EventFlow {
  id: string
  code: string
  name: string
  description: string
  version_no: number
  status: FlowVersionStatus
  status_label: string
  event_type: string
  source_types: EventSourceType[]
  node_count: number
  published_at: string | null
  create_time: string
  event_schema?: Record<string, unknown>
  nodes?: FlowNodeDefinition[]
}

export interface EventFlowNodeRun {
  id: string
  node_code: string
  node_name: string
  node_type: FlowNodeType
  node_type_label: string
  sequence_no: number
  dependencies: string[]
  dependency_mode: NodeDependencyMode
  activation_mode: NodeActivationMode
  condition: Record<string, unknown>
  max_retries: number
  timeout_seconds: number
  failure_strategy: NodeFailureStrategy
  fallback_node_code: string
  recovery_action: string
  active_attempt_no: number
  failure_handled: boolean
  fallback_activated: boolean
  span_id: string
  resource_pool_id: string | null
  priority: number
  required_units: number
  mutex_keys: string[]
  status: FlowNodeRunStatus
  status_label: string
  dispatch_task: null | {
    id: string
    code: string
    status: string
    status_label: string
    queue_reason: string
  }
  input_snapshot: Record<string, unknown>
  output_snapshot: Record<string, unknown>
  started_at: string | null
  finished_at: string | null
}

export interface EventFlowRunEvent {
  id: string
  sequence_no: number
  event_type: string
  event_type_label: string
  node_code: string
  detail: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface EventFlowNodeAttempt {
  id: string
  node_code: string
  attempt_no: number
  status: 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'TIMED_OUT'
  status_label: string
  dispatch_task_id: string | null
  trace_id: string
  span_id: string
  timeout_seconds: number
  output_snapshot: Record<string, unknown>
  error_snapshot: Record<string, unknown>
  recovery_action: string
  started_at: string | null
  finished_at: string | null
}

export interface EventFlowRun {
  id: string
  code: string
  flow_id: string
  flow_code: string
  flow_name: string
  flow_version: number
  event_id: string
  event_type: string
  subject: string
  source_type: EventSourceType
  status: FlowRunStatus
  status_label: string
  trace_id: string
  replay_of_id: string | null
  replay_sequence: number
  node_count: number
  completed_node_count: number
  succeeded_node_count: number
  started_at: string | null
  finished_at: string | null
  create_time: string
  context_snapshot?: Record<string, unknown>
  result_summary?: Record<string, unknown>
  nodes?: EventFlowNodeRun[]
  events?: EventFlowRunEvent[]
  attempts?: EventFlowNodeAttempt[]
}

export interface EventOrchestrationDashboard {
  summary: {
    published_flow_count: number
    event_count: number
    running_count: number
    waiting_count: number
    succeeded_count: number
    failed_count: number
    manual_waiting_count: number
    resource_waiting_count: number
    retried_node_count: number
    fallback_count: number
    skipped_node_count: number
  }
  flows: EventFlow[]
  runs: EventFlowRun[]
}

export interface EventFlowCreateForm {
  code: string
  name: string
  description: string
  event_type: string
  source_types: EventSourceType[]
  event_schema: Record<string, unknown>
  nodes: FlowNodeDefinition[]
  publish: boolean
}

export interface StandardEventCreateForm {
  event_id: string
  idempotency_key: string
  source_type: EventSourceType
  event_type: string
  subject: string
  payload: Record<string, unknown>
  metadata: Record<string, unknown>
}

const prefix = () => {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/event-orchestration`
}

export const getEventOrchestrationDashboard = (
  loading?: Ref<boolean>,
): Promise<Result<EventOrchestrationDashboard>> => get(`${prefix()}/dashboard`, undefined, loading)

export const createEventFlow = (
  data: EventFlowCreateForm,
  loading?: Ref<boolean>,
): Promise<Result<EventFlow>> => post(`${prefix()}/flow`, data, undefined, loading)

export const publishEventFlow = (
  flowId: string,
  loading?: Ref<boolean>,
): Promise<Result<EventFlow>> => post(`${prefix()}/flow/${flowId}/publish`, {}, undefined, loading)

export const receiveStandardEvent = (
  data: StandardEventCreateForm,
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; event: Record<string, unknown>; runs: EventFlowRun[] }>> =>
  post(`${prefix()}/event`, data, undefined, loading)

export const getEventFlowRun = (
  runId: string,
  loading?: Ref<boolean>,
): Promise<Result<EventFlowRun>> => get(`${prefix()}/run/${runId}`, undefined, loading)

export const advanceEventFlowRun = (
  runId: string,
  loading?: Ref<boolean>,
): Promise<Result<EventFlowRun>> => post(`${prefix()}/run/${runId}/advance`, {}, undefined, loading)

export const replayEventFlowRun = (
  runId: string,
  idempotencyKey: string,
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; event: Record<string, unknown>; runs: EventFlowRun[] }>> =>
  post(`${prefix()}/run/${runId}/replay`, { idempotency_key: idempotencyKey }, undefined, loading)

export const operateEventFlowNode = (
  runId: string,
  nodeId: string,
  data: { action: 'SUCCEED' | 'FAIL' | 'APPROVE' | 'REJECT'; note?: string; output?: Record<string, unknown> },
  loading?: Ref<boolean>,
): Promise<Result<EventFlowRun>> =>
  post(`${prefix()}/run/${runId}/node/${nodeId}/operate`, data, undefined, loading)

export type EventOrchestrationResourcePool = ResourcePool
