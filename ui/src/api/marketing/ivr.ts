import type { Ref } from 'vue'

import { exportFile, get, post } from '@/request'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type IvrTransport = 'HTTP' | 'WEBSOCKET_REPLAY'
export type IvrSessionStatus =
  | 'CREATED'
  | 'ACTIVE'
  | 'BROADCASTING'
  | 'TRANSFERRED'
  | 'ENDED'
  | 'FAILED'
export type IvrEventDirection = 'INBOUND' | 'OUTBOUND' | 'SYSTEM'
export type IvrEventType =
  | 'SESSION_STARTED'
  | 'AUDIO_CHUNK_RECEIVED'
  | 'STT_COMPLETED'
  | 'RESPONSE_CREATED'
  | 'BROADCAST_STARTED'
  | 'BROADCAST_ENDED'
  | 'TRANSFERRED'
  | 'SESSION_ENDED'
  | 'FAILED'

export interface IvrEvent {
  id: string
  sequence: number
  event_type: IvrEventType
  event_type_label: string
  direction: IvrEventDirection
  direction_label: string
  request_id: string
  payload: Record<string, any>
  occurred_at: string
  create_time: string
}

export interface IvrSession {
  id: string
  external_session_id: string
  transport: IvrTransport
  transport_label: string
  caller_masked: string
  caller_label: string
  language: string
  status: IvrSessionStatus
  status_label: string
  current_sequence: number
  latest_transcript: string
  latest_response: string
  metadata: Record<string, any>
  started_at: string | null
  ended_at: string | null
  create_time: string
  update_time: string
  redis_state: Record<string, any> | null
  events?: IvrEvent[]
}

export interface IvrProtocol {
  version: string
  mode: 'LOCAL_PROTOCOL_REPLAY'
  external_integration_status: 'PENDING'
  http: Record<string, string>
  websocket: {
    status: 'CONTRACT_REPLAY'
    future_endpoint: string
    note: string
  }
  message_types: Array<{ type: IvrEventType; label: string }>
  response_commands: Array<'PLAY_TEXT' | 'TRANSFER_TO_AGENT' | 'END_SESSION'>
}

export interface IvrDashboard {
  summary: {
    session_count: number
    active_session_count: number
    event_count: number
    websocket_replay_count: number
  }
  status_counts: Record<IvrSessionStatus, number>
  protocol: IvrProtocol
  sessions: IvrSession[]
}

export interface IvrInstruction {
  command: 'PLAY_TEXT' | 'TRANSFER_TO_AGENT' | 'END_SESSION'
  tts_text: string
  reason: string
  final: boolean
}

export type ChangeOperationType =
  | 'PLAN_CHANGE'
  | 'CONFIG_CHANGE'
  | 'DATA_MIGRATION'
  | 'NETWORK_CUTOVER'
  | 'OTHER'
export type ChangeOperationStatus =
  | 'DRAFT'
  | 'RISK_EVALUATED'
  | 'CONFIRMATION_PENDING'
  | 'APPROVED'
  | 'REJECTED'
export type ChangeRiskLevel = 'GREEN' | 'YELLOW' | 'RED'
export type ChangeConfirmationStatus = 'NOT_REQUIRED' | 'PENDING' | 'APPROVED' | 'REJECTED'
export type ChangeConfirmationDecision = 'APPROVE' | 'REJECT'
export type ChangeControlStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'ABORTED'
export type ChangeControlAction = 'START' | 'COMPLETE' | 'ABORT'
export type ChangeCommunicationKind = 'CONTROL_REMINDER' | 'CUTOVER_NOTICE'
export type ChangeCommunicationPhase = 'BEFORE' | 'DURING' | 'AFTER'
export type ChangeCommunicationAudience = 'OPERATOR' | 'CUSTOMER'
export type ChangeCommunicationChannel = 'IN_APP' | 'IVR' | 'SMS' | 'MANUAL'
export type ChangeCommunicationStatus = 'PENDING' | 'SENT' | 'ACKNOWLEDGED' | 'FAILED'

export interface ChangeRiskReason {
  factor: string
  label: string
  severity: 'PASS' | 'NOTICE' | 'WARNING' | 'CRITICAL'
  points: number
  message: string
}

export interface ChangeRiskInput {
  instruction_complete: boolean
  business_logic_passed: boolean
  consistency_passed: boolean
  affected_customer_count: number
  cross_system_change: boolean
  rollback_plan_ready: boolean
  emergency_change: boolean
  customer_notice_ready: boolean
}

export interface ChangeRiskAssessment {
  id: string
  revision: number
  risk_level: ChangeRiskLevel
  risk_level_label: string
  risk_score: number
  input_snapshot: ChangeRiskInput
  reasons: ChangeRiskReason[]
  evaluator_name: string
  create_time: string
}

export interface ChangeConfirmation {
  id: string
  assessment_id: string
  request_id: string
  decision: ChangeConfirmationDecision
  decision_label: string
  comment: string
  risk_level: ChangeRiskLevel
  risk_score: number
  confirmer_name: string
  create_time: string
}

export interface ChangeOperation {
  id: string
  code: string
  name: string
  operation_type: ChangeOperationType
  operation_type_label: string
  description: string
  planned_start_at: string | null
  ivr_session_id: string | null
  ivr_session_external_id: string
  status: ChangeOperationStatus
  status_label: string
  risk_level: ChangeRiskLevel
  risk_level_label: string
  risk_score: number
  risk_revision: number
  risk_snapshot: Partial<ChangeRiskInput>
  risk_reasons: ChangeRiskReason[]
  confirmation_status: ChangeConfirmationStatus
  confirmation_status_label: string
  evaluated_at: string | null
  decided_at: string | null
  creator_name: string
  create_time: string
  update_time: string
  assessments?: ChangeRiskAssessment[]
  confirmations?: ChangeConfirmation[]
}

export interface ChangeOperationDashboard {
  summary: {
    operation_count: number
    red_count: number
    pending_confirmation_count: number
    approved_count: number
  }
  risk_counts: Record<ChangeRiskLevel, number>
  operations: ChangeOperation[]
  risk_rules: Record<'red' | 'yellow' | 'green' | 'confirmation', string>
}

export interface ChangeOperationCommunication {
  id: string
  operation_id: string
  request_id: string
  kind: ChangeCommunicationKind
  kind_label: string
  phase: ChangeCommunicationPhase
  phase_label: string
  audience: ChangeCommunicationAudience
  audience_label: string
  channel: ChangeCommunicationChannel
  channel_label: string
  subject: string
  content: string
  status: ChangeCommunicationStatus
  status_label: string
  scheduled_at: string | null
  sent_at: string | null
  acknowledged_at: string | null
  failure_reason: string
  operator_name: string
  create_time: string
  update_time: string
}

export interface ChangeControlActionRecord {
  id: string
  revision: number
  action: ChangeControlAction
  action_label: string
  previous_status: ChangeControlStatus
  previous_status_label: string
  current_status: ChangeControlStatus
  current_status_label: string
  note: string
  operator_name: string
  create_time: string
}

export interface ChangeControlOperation extends ChangeOperation {
  control_status: ChangeControlStatus
  control_status_label: string
  actual_start_at: string | null
  completed_at: string | null
  communication_count: number
  pending_communication_count: number
  communications?: ChangeOperationCommunication[]
  control_actions?: ChangeControlActionRecord[]
}

export interface ChangeQualityMetrics {
  operation_count: number
  evaluated_count: number
  green_count: number
  yellow_count: number
  red_count: number
  approved_count: number
  rejected_count: number
  pending_confirmation_count: number
  in_progress_count: number
  completed_count: number
  aborted_count: number
  communication_count: number
  sent_communication_count: number
  acknowledged_communication_count: number
  failed_communication_count: number
  communication_coverage_rate: number
  control_completion_rate: number
  average_confirmation_seconds: number
}

export interface ChangeQualityTrendItem {
  date: string
  operation_count: number
  red_count: number
  communication_count: number
  completed_count: number
}

export interface ChangeQualityOperationSnapshot {
  id: string
  date: string
  code: string
  name: string
  risk_level: ChangeRiskLevel
  risk_level_label: string
  risk_score: number
  status: ChangeOperationStatus
  status_label: string
  control_status: ChangeControlStatus
  control_status_label: string
  communication_count: number
  actual_start_at: string | null
  completed_at: string | null
}

export interface ChangeQualityReport {
  id: string
  title: string
  period_start: string
  period_end: string
  metrics: ChangeQualityMetrics
  generated_at: string
  generator_name: string
  daily_trend?: ChangeQualityTrendItem[]
  operations?: ChangeQualityOperationSnapshot[]
}

export interface ChangeControlDashboard {
  summary: {
    operation_count: number
    not_started_count: number
    in_progress_count: number
    completed_count: number
    aborted_count: number
    pending_communication_count: number
    failed_communication_count: number
    report_count: number
  }
  communication_counts: Record<ChangeCommunicationStatus, number>
  operations: ChangeControlOperation[]
  reports: ChangeQualityReport[]
}

const prefix = () => {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/marketing/ivr`
}

export const getIvrDashboard = (loading?: Ref<boolean>): Promise<Result<IvrDashboard>> =>
  get(`${prefix()}/dashboard`, {}, loading)

export const getIvrProtocol = (loading?: Ref<boolean>): Promise<Result<IvrProtocol>> =>
  get(`${prefix()}/protocol`, {}, loading)

export const getIvrSession = (
  sessionId: string,
  loading?: Ref<boolean>,
): Promise<Result<IvrSession>> => get(`${prefix()}/session/${sessionId}`, {}, loading)

export const createIvrSession = (
  data: {
    external_session_id?: string
    transport: IvrTransport
    caller_number?: string
    caller_label?: string
    language: string
  },
  loading?: Ref<boolean>,
): Promise<
  Result<{ created: boolean; cache_synced: boolean; session: IvrSession; protocol: IvrProtocol }>
> => post(`${prefix()}/session`, data, {}, loading)

export const sendIvrAudioChunk = (
  sessionId: string,
  data: {
    request_id: string
    chunk_index: number
    duration_ms: number
    transcript_hint: string
    is_final: boolean
  },
  loading?: Ref<boolean>,
): Promise<
  Result<{
    created: boolean
    cache_synced: boolean
    session: IvrSession
    events: IvrEvent[]
    instruction: IvrInstruction
  }>
> => post(`${prefix()}/session/${sessionId}/audio`, data, {}, loading)

export const sendIvrStateEvent = (
  sessionId: string,
  data: { request_id: string; event_type: IvrEventType; payload?: Record<string, any> },
  loading?: Ref<boolean>,
): Promise<
  Result<{ created: boolean; cache_synced: boolean; session: IvrSession; event: IvrEvent }>
> => post(`${prefix()}/session/${sessionId}/event`, data, {}, loading)

export const getChangeOperationDashboard = (
  loading?: Ref<boolean>,
): Promise<Result<ChangeOperationDashboard>> => get(`${prefix()}/change/dashboard`, {}, loading)

export const getChangeOperation = (
  operationId: string,
  loading?: Ref<boolean>,
): Promise<Result<ChangeOperation>> =>
  get(`${prefix()}/change/operation/${operationId}`, {}, loading)

export const createChangeOperation = (
  data: {
    code?: string
    name: string
    operation_type: ChangeOperationType
    description?: string
    planned_start_at?: string | null
    ivr_session_id?: string | null
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; operation: ChangeOperation }>> =>
  post(`${prefix()}/change/operation`, data, {}, loading)

export const evaluateChangeOperation = (
  operationId: string,
  data: ChangeRiskInput,
  loading?: Ref<boolean>,
): Promise<
  Result<{
    operation: ChangeOperation
    assessment: ChangeRiskAssessment
    requires_confirmation: boolean
  }>
> => post(`${prefix()}/change/operation/${operationId}/evaluate`, data, {}, loading)

export const confirmChangeOperation = (
  operationId: string,
  data: { request_id: string; decision: ChangeConfirmationDecision; comment: string },
  loading?: Ref<boolean>,
): Promise<
  Result<{ created: boolean; operation: ChangeOperation; confirmation: ChangeConfirmation }>
> => post(`${prefix()}/change/operation/${operationId}/confirm`, data, {}, loading)

export const getChangeControlDashboard = (
  loading?: Ref<boolean>,
): Promise<Result<ChangeControlDashboard>> =>
  get(`${prefix()}/change/control/dashboard`, {}, loading)

export const getChangeControlOperation = (
  operationId: string,
  loading?: Ref<boolean>,
): Promise<Result<ChangeControlOperation>> =>
  get(`${prefix()}/change/control/operation/${operationId}`, {}, loading)

export const createChangeCommunication = (
  operationId: string,
  data: {
    request_id?: string
    kind: ChangeCommunicationKind
    phase: ChangeCommunicationPhase
    audience: ChangeCommunicationAudience
    channel: ChangeCommunicationChannel
    subject: string
    content: string
    scheduled_at?: string | null
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; communication: ChangeOperationCommunication }>> =>
  post(`${prefix()}/change/operation/${operationId}/communication`, data, {}, loading)

export const updateChangeCommunicationStatus = (
  communicationId: string,
  data: { status: 'SENT' | 'ACKNOWLEDGED' | 'FAILED'; failure_reason?: string },
  loading?: Ref<boolean>,
): Promise<
  Result<{
    changed: boolean
    notification_count: number
    communication: ChangeOperationCommunication
  }>
> => post(`${prefix()}/change/communication/${communicationId}/status`, data, {}, loading)

export const controlChangeOperation = (
  operationId: string,
  data: { action: ChangeControlAction; note?: string },
  loading?: Ref<boolean>,
): Promise<
  Result<{ operation: ChangeControlOperation; action_record: ChangeControlActionRecord }>
> => post(`${prefix()}/change/operation/${operationId}/control`, data, {}, loading)

export const generateChangeQualityReport = (
  data: { title?: string; period_start: string; period_end: string },
  loading?: Ref<boolean>,
): Promise<Result<ChangeQualityReport>> =>
  post(`${prefix()}/change/quality/report`, data, {}, loading)

export const getChangeQualityReport = (
  reportId: string,
  loading?: Ref<boolean>,
): Promise<Result<ChangeQualityReport>> =>
  get(`${prefix()}/change/quality/report/${reportId}`, {}, loading)

export const getChangeQualityDrilldown = (
  reportId: string,
  date: string,
  loading?: Ref<boolean>,
): Promise<
  Result<{
    date: string
    summary: ChangeQualityTrendItem
    operations: ChangeQualityOperationSnapshot[]
  }>
> => get(`${prefix()}/change/quality/report/${reportId}/drilldown`, { date }, loading)

export const downloadChangeQualityReport = (
  reportId: string,
  format: 'csv' | 'pdf',
  loading?: Ref<boolean>,
) =>
  exportFile(
    `change-quality-report.${format}`,
    `${prefix()}/change/quality/report/${reportId}/export/${format}`,
    {},
    loading,
  )
