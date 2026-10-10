import type { Ref } from 'vue'

import { exportFile, get, post } from '@/request'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type CustomerType = 'PUBLIC' | 'ENTERPRISE' | 'MIXED'
export type InstanceStatus = 'DRAFT' | 'READY' | 'RUNNING' | 'COMPLETED' | 'CANCELLED' | 'FAILED'
export type InstanceAction = 'PREPARE' | 'START' | 'COMPLETE' | 'CANCEL'
export type ComplaintSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type ValidationStatus = 'VALID' | 'INVALID'
export type ComplaintSource = 'GENERATED' | 'IMPORTED'
export type ProcessRunStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'BLOCKED'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'FAILED'
export type ProcessStepStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'BLOCKED'
  | 'COMPLETED'
  | 'SKIPPED'
  | 'FAILED'
export type ProcessRunAction =
  | 'START'
  | 'COMPLETE_STEP'
  | 'AUTO_ADVANCE'
  | 'BLOCK'
  | 'RESUME'
  | 'SKIP'
  | 'FAIL'
  | 'CANCEL'
export type DataSimulationKind = 'METRIC' | 'SENTIMENT'
export type DataSimulationStatus = 'READY' | 'FAILED'
export type DataDistribution = 'LINEAR' | 'WAVE' | 'RANDOM' | 'STEP'
export type SceneRunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'CANCELLED' | 'FAILED'
export type SceneStepStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'SKIPPED' | 'FAILED'
export type SceneRunAction = 'START' | 'COMPLETE_STEP' | 'SKIP_STEP' | 'FAIL' | 'CANCEL'
export type SceneLibraryStatus = 'DRAFT' | 'READY' | 'ARCHIVED'
export type SceneLibraryVisibility = 'WORKSPACE' | 'PRIVATE'
export type SceneLibraryAction = 'PUBLISHED' | 'ARCHIVED'
export type WorkOrderPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type WorkOrderStatus = 'OPEN' | 'PROCESSING' | 'RESOLVED' | 'CLOSED'
export type WorkOrderAction = 'ACCEPT' | 'RESOLVE' | 'CLOSE' | 'REOPEN'
export type AlertSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type AlertStatus = 'PENDING' | 'ACTIVE' | 'ACKNOWLEDGED' | 'RECOVERED'
export type AlertAction = 'REPORT' | 'ACKNOWLEDGE' | 'RECOVER'
export type TimelineKind =
  | 'COMPLAINT'
  | 'METRIC'
  | 'SENTIMENT'
  | 'PROCESS'
  | 'SCENE'
  | 'ALERT'
  | 'WORK_ORDER'
export type DataModelBuildStrategy = 'FULL_INSTANCE' | 'SCENE_LINKED' | 'FAULT_CHAIN'
export type DataModelQualityStatus = 'PASS' | 'WARN' | 'FAIL'
export type DataModelLoadStatus = 'LOADED' | 'PARTIAL' | 'FAILED'
export type TracebackScope = 'FULL_INSTANCE' | 'INCIDENT_WINDOW' | 'CUSTOM'
export type TracebackStatus = 'READY' | 'EMPTY' | 'ARCHIVED'
export type CapabilityMockKind = 'API' | 'ATOMIC'
export type CapabilityCallStatus = 'SUCCEEDED' | 'FAILED' | 'TIMEOUT'
export type FaultConfigurationStatus = 'DRAFT' | 'READY' | 'ARCHIVED'
export type FaultConfigurationAction = 'CREATED' | 'VALIDATED' | 'CLONED' | 'APPLIED' | 'ARCHIVED'
export type SceneReplayStatus = 'READY' | 'EMPTY'
export type FaultReportLevel = 'LEVEL_1' | 'LEVEL_2' | 'LEVEL_3' | 'LEVEL_4'
export type FaultReportStatus = 'DRAFT' | 'REPORTED' | 'PROCESSING' | 'RECOVERED' | 'CLOSED'
export type FaultReportAction =
  | 'SUBMITTED'
  | 'ACCEPTED'
  | 'STAGE_ADVANCED'
  | 'ESCALATED'
  | 'ATTACHMENT_ADDED'
  | 'RECOVERED'
  | 'CLOSED'
export type AuxiliarySimulationStatus = 'COMPLETED' | 'ATTENTION'
export type RandomFactorCategory = 'NETWORK' | 'FAULT' | 'TRAFFIC'
export type RandomFactorDistribution = 'UNIFORM' | 'NORMAL'
export type AuxiliaryReportFormat = 'pdf' | 'xlsx' | 'json'
export type AuxiliaryReportLevel = 'summary' | 'full'
export type SimulationRecordKind =
  | 'INSTANCE'
  | 'COMPLAINT_BATCH'
  | 'DATA_BATCH'
  | 'PROCESS_RUN'
  | 'SCENE_RUN'
  | 'ALERT'
  | 'TRACEBACK'
  | 'CAPABILITY_CALL'
  | 'FAULT_REPORT'
  | 'AUXILIARY_SIMULATION'
export type SimulationRecordState = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'ATTENTION' | 'FAILED'

export interface RehearsalScenario {
  id: string
  code: string
  name: string
  description: string
  customer_scope: CustomerType
  customer_scope_label: string
  version: number
  status: string
  status_label: string
  configuration: Record<string, unknown>
  create_time: string
  update_time: string
}

export interface ComplaintTemplate {
  id: string
  code: string
  name: string
  customer_type: Exclude<CustomerType, 'MIXED'>
  customer_type_label: string
  version: number
  enabled: boolean
  profile_schema: Record<string, unknown>
  complaint_schema: Record<string, unknown>
  categories: string[]
  content_patterns: string[]
  update_time: string
}

export interface ComplaintBatch {
  id: string
  instance_id: string
  template_id: string | null
  template_name: string
  request_id: string
  source: ComplaintSource
  source_label: string
  status: 'READY' | 'PARTIAL' | 'FAILED'
  status_label: string
  version: number
  filename: string
  total_count: number
  valid_count: number
  invalid_count: number
  time_start: string | null
  time_end: string | null
  error_summary: Record<string, number>
  create_time: string
}

export interface RehearsalEvent {
  id: string
  sequence_no: number
  event_type: string
  event_type_label: string
  previous_status: InstanceStatus
  previous_status_label: string
  current_status: InstanceStatus
  current_status_label: string
  detail: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface RehearsalInstance {
  id: string
  scenario_id: string
  scenario_name: string
  request_id: string
  code: string
  name: string
  status: InstanceStatus
  status_label: string
  planned_start_at: string | null
  started_at: string | null
  completed_at: string | null
  fault_configuration_id: string | null
  fault_configuration_name: string
  fault_configuration_version: number | null
  fault_configuration_snapshot: Record<string, unknown>
  parameters: Record<string, unknown>
  summary: Record<string, number>
  complaint_count: number
  invalid_count: number
  batch_count: number
  data_batch_count: number
  data_model_count: number
  traceback_count: number
  scene_replay_count: number
  fault_report_count: number
  auxiliary_simulation_count: number
  scene_library_count: number
  scene_run_count: number
  alert_count: number
  create_time: string
  update_time: string
  batches?: ComplaintBatch[]
  events?: RehearsalEvent[]
  process_runs?: ProcessRun[]
  data_batches?: DataSimulationBatch[]
  data_models?: RehearsalDataModel[]
  tracebacks?: RehearsalTraceback[]
  scene_replays?: SceneReplay[]
  fault_reports?: FaultReport[]
  auxiliary_simulations?: AuxiliarySimulation[]
  scene_libraries?: SceneLibrary[]
  scene_runs?: SceneRun[]
  alerts?: RehearsalAlert[]
  fault_configuration?: FaultConfiguration | null
}

export interface DataSimulationRule {
  code: string
  name: string
  unit: string
  min_value: number
  max_value: number
  start_value: number
  end_value: number
  distribution: DataDistribution
  decimals: number
}

export interface DataSimulationTemplate {
  id: string
  code: string
  name: string
  description: string
  kind: DataSimulationKind
  kind_label: string
  version: number
  enabled: boolean
  default_rules: DataSimulationRule[]
  default_tags: string[]
  field_count: number
  update_time: string
}

export interface DataSimulationPoint {
  id: string
  batch_id: string
  sequence_no: number
  occurred_at: string
  values: Record<string, number>
  tags: string[]
  narrative: string
}

export interface DataFieldSummary {
  name: string
  unit: string
  minimum: number
  maximum: number
  average: number
  latest: number
  delta: number
  trend: 'UP' | 'DOWN' | 'FLAT'
  distribution: DataDistribution
}

export interface DataSimulationBatch {
  id: string
  instance_id: string
  instance_code: string
  instance_name: string
  template_id: string
  template_name: string
  template_version: number
  request_id: string
  code: string
  name: string
  kind: DataSimulationKind
  kind_label: string
  status: DataSimulationStatus
  status_label: string
  version: number
  point_count: number
  interval_minutes: number
  time_start: string
  time_end: string
  rules_snapshot: DataSimulationRule[]
  tags: string[]
  summary: {
    field_count: number
    fields: Record<string, DataFieldSummary>
  }
  create_time: string
  update_time: string
  points?: DataSimulationPoint[]
}

export interface SceneScriptStep {
  code: string
  name: string
  description: string
  expected_result: string
}

export interface SceneScript {
  id: string
  scenario_id: string
  scenario_name: string
  code: string
  name: string
  description: string
  version: number
  enabled: boolean
  steps: SceneScriptStep[]
  step_count: number
  create_time: string
  update_time: string
}

export interface SceneStep extends SceneScriptStep {
  id: string
  sequence_no: number
  status: SceneStepStatus
  status_label: string
  started_at: string | null
  completed_at: string | null
  duration_seconds: number
  note: string
  output_snapshot: Record<string, unknown>
}

export interface SceneEvent {
  id: string
  sequence_no: number
  action: string
  action_label: string
  step_id: string | null
  step_name: string
  previous_status: SceneRunStatus
  previous_status_label: string
  current_status: SceneRunStatus
  current_status_label: string
  detail: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface SceneLibraryEvent {
  id: string
  sequence_no: number
  action: string
  action_label: string
  previous_status: SceneLibraryStatus
  previous_status_label: string
  current_status: SceneLibraryStatus
  current_status_label: string
  detail: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface SceneLibrary {
  id: string
  scenario_id: string
  scenario_name: string
  script_id: string
  script_code: string
  script_name: string
  script_version: number
  default_instance_id: string | null
  default_instance_code: string
  default_instance_name: string
  process_template_id: string | null
  process_template_name: string
  data_model_id: string | null
  data_model_name: string
  source_library_id: string | null
  request_id: string
  code: string
  name: string
  description: string
  version: number
  status: SceneLibraryStatus
  status_label: string
  visibility: SceneLibraryVisibility
  visibility_label: string
  permission_roles: string[]
  linked_config: {
    script?: Record<string, unknown>
    default_instance?: Record<string, unknown> | null
    process_template?: Record<string, unknown> | null
    data_model?: Record<string, unknown> | null
    configuration?: Record<string, unknown>
  }
  run_count: number
  last_run_at: string | null
  event_count: number
  create_time: string
  update_time: string
  script?: SceneScript
  events?: SceneLibraryEvent[]
  scene_runs?: SceneRun[]
}

export interface SceneInjectedSnapshot {
  complaint_batches: Array<{
    id: string
    source: ComplaintSource
    status: string
    valid_count: number
    invalid_count: number
  }>
  data_batches: Array<{
    id: string
    code: string
    name: string
    kind: DataSimulationKind
    status: DataSimulationStatus
    point_count: number
  }>
  process_runs: Array<{
    id: string
    code: string
    name: string
    status: ProcessRunStatus
    progress_percent: number
  }>
  totals: Record<string, number>
}

export interface WorkOrderEvent {
  id: string
  sequence_no: number
  action: string
  action_label: string
  previous_status: WorkOrderStatus
  previous_status_label: string
  current_status: WorkOrderStatus
  current_status_label: string
  detail: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface WorkOrder {
  id: string
  scene_run_id: string
  scene_run_code: string
  scene_run_name: string
  request_id: string
  code: string
  title: string
  description: string
  priority: WorkOrderPriority
  priority_label: string
  status: WorkOrderStatus
  status_label: string
  assignee: string
  resolution: string
  accepted_at: string | null
  resolved_at: string | null
  closed_at: string | null
  create_time: string
  update_time: string
  events?: WorkOrderEvent[]
}

export interface SceneRun {
  id: string
  instance_id: string
  instance_code: string
  instance_name: string
  script_id: string
  script_name: string
  script_version: number
  library_id: string | null
  library_name: string
  library_version: number | null
  request_id: string
  code: string
  name: string
  status: SceneRunStatus
  status_label: string
  current_step_index: number
  current_step_code: string
  current_step_name: string
  total_steps: number
  completed_steps: number
  progress_percent: number
  script_snapshot: Record<string, unknown>
  injected_snapshot: SceneInjectedSnapshot
  started_at: string | null
  completed_at: string | null
  summary: Record<string, unknown>
  work_order_count: number
  alert_count: number
  create_time: string
  update_time: string
  steps?: SceneStep[]
  events?: SceneEvent[]
  work_orders?: WorkOrder[]
  alerts?: RehearsalAlert[]
}

export interface AlertRule {
  code: string
  name: string
  metric_code: string
  metric_name: string
  operator: 'GT' | 'GTE' | 'LT' | 'LTE' | 'EQ'
  threshold: number
  unit: string
  resource_type: string
}

export interface AlertTemplate {
  id: string
  scenario_id: string
  scenario_name: string
  code: string
  name: string
  description: string
  version: number
  enabled: boolean
  default_severity: AlertSeverity
  default_severity_label: string
  rules: AlertRule[]
  rule_count: number
  create_time: string
  update_time: string
}

export interface AlertEvent {
  id: string
  sequence_no: number
  action: string
  action_label: string
  previous_status: AlertStatus
  previous_status_label: string
  current_status: AlertStatus
  current_status_label: string
  occurred_at: string
  detail: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface RehearsalAlert {
  id: string
  instance_id: string
  instance_code: string
  instance_name: string
  template_id: string
  template_name: string
  template_version: number
  scene_run_id: string | null
  scene_run_name: string
  data_batch_id: string | null
  data_batch_name: string
  request_id: string
  code: string
  title: string
  description: string
  severity: AlertSeverity
  severity_label: string
  status: AlertStatus
  status_label: string
  source_system: string
  resource_type: string
  resource_id: string
  resource_name: string
  metric_code: string
  metric_name: string
  metric_value: number | null
  threshold: number | null
  occurred_at: string
  reported_at: string | null
  acknowledged_at: string | null
  recovered_at: string | null
  duration_seconds: number
  template_snapshot: Record<string, unknown>
  context: Record<string, unknown>
  event_count: number
  create_time: string
  update_time: string
  events?: AlertEvent[]
}

export interface TimelineItem {
  kind: TimelineKind
  kind_label: string
  occurred_at: string
  title: string
  subtitle: string
  status: string
  reference_id: string
  detail: Record<string, unknown>
}

export interface RehearsalTimeline {
  instance: { id: string; code: string; name: string }
  total: number
  kind_counts: Partial<Record<TimelineKind, number>>
  items: TimelineItem[]
}

export interface DataModelQualityCheck {
  code: string
  name: string
  passed: boolean
  severity: 'ERROR' | 'WARN'
  message: string
}

export interface DataModelLineageSource {
  source_type: string
  source_id: string
  code: string
  name: string
  count: number
}

export interface DataModelLineageRelation {
  from: string
  from_type: string
  to: string
  to_type: string
  relation: string
}

export interface DataModelVersion {
  id: string
  data_model_id: string
  version: number
  build_strategy: DataModelBuildStrategy
  build_strategy_label: string
  transformer_code: string
  source_counts: Record<string, number>
  entity_schema: Record<string, string[]>
  snapshot: Record<string, unknown>
  quality_report: {
    status: DataModelQualityStatus
    status_label: string
    score: number
    checks: DataModelQualityCheck[]
  }
  lineage: {
    sources?: DataModelLineageSource[]
    relations?: DataModelLineageRelation[]
  }
  checksum: string
  loaded_at: string
  create_time: string
  update_time: string
}

export interface DataModelLoad {
  id: string
  data_model_id: string
  version_id: string | null
  version: number
  request_id: string
  status: DataModelLoadStatus
  status_label: string
  source_counts: Record<string, number>
  note: string
  message: string
  started_at: string
  completed_at: string | null
  operator_name: string
  create_time: string
}

export interface RehearsalDataModel {
  id: string
  instance_id: string
  instance_code: string
  instance_name: string
  scenario_id: string
  scenario_name: string
  scene_run_id: string | null
  scene_run_name: string
  request_id: string
  code: string
  name: string
  description: string
  build_strategy: DataModelBuildStrategy
  build_strategy_label: string
  transformer_code: string
  version_count: number
  current_version: number
  quality_status: DataModelQualityStatus
  quality_status_label: string
  source_scope: Record<string, unknown>
  summary: {
    source_counts?: Record<string, number>
    quality_score?: number
    quality_status?: DataModelQualityStatus
    latest_checksum?: string
    loaded_at?: string
  }
  lineage: {
    sources?: DataModelLineageSource[]
    relations?: DataModelLineageRelation[]
  }
  version_total: number
  load_total: number
  create_time: string
  update_time: string
  versions?: DataModelVersion[]
  loads?: DataModelLoad[]
}

export interface TracebackNode {
  kind: TimelineKind
  kind_label: string
  count: number
  first_at: string
  last_at: string
  first_title: string
  last_title: string
  status_counts: Record<string, number>
}

export interface TracebackTransition {
  from_kind: TimelineKind
  from_label: string
  to_kind: TimelineKind
  to_label: string
  count: number
}

export interface TracebackDelta {
  field: string
  first_value: number
  last_value: number
  delta: number
  first_at: string
  last_at: string
}

export interface RehearsalTraceback {
  id: string
  instance_id: string
  instance_code: string
  instance_name: string
  scenario_id: string
  scenario_name: string
  scene_run_id: string | null
  scene_run_name: string
  data_model_id: string | null
  data_model_name: string
  request_id: string
  code: string
  name: string
  description: string
  scope: TracebackScope
  scope_label: string
  status: TracebackStatus
  status_label: string
  kind_scope: TimelineKind[]
  window_start: string | null
  window_end: string | null
  total_events: number
  kind_counts: Partial<Record<TimelineKind, number>>
  pivot_counts: {
    status_counts?: Record<string, number>
    node_counts?: Partial<Record<TimelineKind, number>>
  }
  summary: {
    instance_code?: string
    scope?: TracebackScope
    scope_label?: string
    kind_scope?: TimelineKind[]
    window_start?: string | null
    window_end?: string | null
    first_event_at?: string | null
    last_event_at?: string | null
    duration_minutes?: number
    dominant_kind?: TimelineKind | ''
    dominant_kind_label?: string
    root_signal?: string
    latest_signal?: string
    node_count?: number
    transition_count?: number
    delta_count?: number
  }
  checksum: string
  generated_at: string
  create_time: string
  update_time: string
  snapshot?: {
    instance?: { id: string; code: string; name: string }
    filters?: Record<string, unknown>
    items?: TimelineItem[]
    nodes?: TracebackNode[]
    transitions?: TracebackTransition[]
    deltas?: TracebackDelta[]
  }
  items?: TimelineItem[]
  nodes?: TracebackNode[]
  transitions?: TracebackTransition[]
  deltas?: TracebackDelta[]
}

export interface SimulationRecord {
  record_key: string
  kind: SimulationRecordKind
  kind_label: string
  resource_id: string
  instance_id: string
  instance_code: string
  instance_name: string
  code: string
  name: string
  status: string
  status_label: string
  state: SimulationRecordState
  state_label: string
  progress_percent: number
  occurrence_no: number
  result_summary: string
  event_count: number
  started_at: string | null
  completed_at: string | null
  duration_seconds: number
  create_time: string
  update_time: string
}

export interface SimulationRecordActivity {
  sequence_no: number
  label: string
  status_label: string
  occurred_at: string | null
  detail: Record<string, unknown>
}

export interface SimulationRecordDetail {
  record: SimulationRecord
  activity_count: number
  activity: SimulationRecordActivity[]
  detail: Record<string, unknown>
}

export interface CapabilityMock {
  id: string
  scenario_id: string
  scenario_name: string
  code: string
  name: string
  description: string
  kind: CapabilityMockKind
  kind_label: string
  version: number
  enabled: boolean
  method: string
  endpoint: string
  request_schema: Record<string, unknown>
  response_template: Record<string, unknown>
  failure_template: Record<string, unknown>
  default_status: CapabilityCallStatus
  default_status_label: string
  default_latency_ms: number
  create_time: string
  update_time: string
}

export interface CapabilityCall {
  id: string
  instance_id: string
  instance_code: string
  instance_name: string
  capability_id: string
  capability_code: string
  capability_name: string
  capability_kind: CapabilityMockKind
  capability_kind_label: string
  request_id: string
  call_no: number
  status: CapabilityCallStatus
  status_label: string
  source: 'SANDBOX' | 'REPLAY'
  warroom_group: string
  http_status: number
  latency_ms: number
  error_message: string
  started_at: string
  finished_at: string
  replay_of_id: string | null
  create_time: string
  update_time: string
  request_payload?: Record<string, unknown>
  response_payload?: Record<string, unknown>
  capability_snapshot?: Record<string, unknown>
  capability?: CapabilityMock
  replays?: CapabilityCall[]
}

export interface FaultAlertRule {
  code: string
  name: string
  severity: AlertSeverity
  metric_code: string
  operator: 'GT' | 'GTE' | 'LT' | 'LTE' | 'EQ'
  threshold: number
  unit?: string
}

export interface FaultTopologyNode {
  id: string
  name: string
  type: string
  zone?: string
  state?: string
}

export interface FaultTopologyLink {
  source: string
  target: string
  state?: string
}

export interface FaultPlanStep {
  code: string
  name: string
  owner_role?: string
  target_minutes?: number
}

export interface FaultConfigurationEvent {
  id: string
  sequence_no: number
  action: FaultConfigurationAction
  action_label: string
  instance_id: string | null
  instance_name: string
  previous_status: FaultConfigurationStatus
  previous_status_label: string
  current_status: FaultConfigurationStatus
  current_status_label: string
  detail: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface FaultConfiguration {
  id: string
  scenario_id: string
  scenario_name: string
  source_configuration_id: string | null
  request_id: string
  code: string
  name: string
  description: string
  version: number
  status: FaultConfigurationStatus
  status_label: string
  alert_rules: FaultAlertRule[]
  timeout_policy: {
    overall_seconds?: number
    step_seconds?: number
    on_timeout?: string
    retry_limit?: number
  }
  active_window: {
    timezone?: string
    weekdays?: number[]
    start?: string
    end?: string
  }
  topology_snapshot: {
    version?: string
    nodes?: FaultTopologyNode[]
    links?: FaultTopologyLink[]
  }
  emergency_plan: {
    code?: string
    name?: string
    owner?: string
    steps?: FaultPlanStep[]
  }
  validation_report: {
    status?: 'PENDING' | 'PASSED' | 'FAILED'
    passed?: boolean
    check_count?: number
    error_count?: number
    checks?: Array<{ code: string; name: string; passed: boolean; message: string }>
    errors?: string[]
  }
  validated_at: string | null
  published_at: string | null
  alert_rule_count: number
  topology_node_count: number
  topology_link_count: number
  plan_step_count: number
  bound_instance_count: number
  event_count: number
  create_time: string
  update_time: string
  events?: FaultConfigurationEvent[]
  bound_instances?: Array<{
    id: string
    code: string
    name: string
    status: InstanceStatus
    status_label: string
  }>
}

export interface ProcessTemplateStep {
  code: string
  name: string
  description: string
  owner_role: string
  planned_minutes: number
}

export interface ProcessTemplate {
  id: string
  code: string
  name: string
  description: string
  customer_scope: CustomerType
  customer_scope_label: string
  version: number
  enabled: boolean
  auto_advance: boolean
  steps: ProcessTemplateStep[]
  step_count: number
  update_time: string
}

export interface ProcessStep extends ProcessTemplateStep {
  id: string
  sequence_no: number
  status: ProcessStepStatus
  status_label: string
  started_at: string | null
  completed_at: string | null
  duration_seconds: number
  note: string
  output_snapshot: Record<string, unknown>
}

export interface ProcessEvent {
  id: string
  sequence_no: number
  action: string
  action_label: string
  step_id: string | null
  step_name: string
  previous_status: ProcessRunStatus
  previous_status_label: string
  current_status: ProcessRunStatus
  current_status_label: string
  detail: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface ProcessRun {
  id: string
  instance_id: string
  instance_code: string
  instance_name: string
  template_id: string
  template_name: string
  template_version: number
  request_id: string
  code: string
  name: string
  status: ProcessRunStatus
  status_label: string
  auto_advance: boolean
  current_step_index: number
  current_step_code: string
  current_step_name: string
  total_steps: number
  completed_steps: number
  progress_percent: number
  blocked_reason: string
  started_at: string | null
  completed_at: string | null
  template_snapshot: Record<string, unknown>
  summary: Record<string, unknown>
  create_time: string
  update_time: string
  steps?: ProcessStep[]
  events?: ProcessEvent[]
}

export interface Complaint {
  id: string
  instance_id: string
  batch_id: string
  sequence_no: number
  source: ComplaintSource
  source_label: string
  customer_type: Exclude<CustomerType, 'MIXED'>
  customer_type_label: string
  customer_ref: string
  customer_name: string
  contact_masked: string
  customer_segment: string
  occurred_at: string | null
  region: string
  channel: string
  category: string
  severity: ComplaintSeverity
  severity_label: string
  status: string
  status_label: string
  title: string
  content: string
  validation_status: ValidationStatus
  validation_status_label: string
  validation_errors: string[]
}

export interface RehearsalDashboard {
  summary: {
    scenario_count: number
    instance_count: number
    running_count: number
    ready_count: number
    complaint_count: number
    invalid_count: number
    batch_count: number
    process_run_count: number
    process_running_count: number
    process_blocked_count: number
    process_completed_count: number
    data_batch_count: number
    data_point_count: number
    metric_batch_count: number
    sentiment_batch_count: number
    data_model_count: number
    data_model_version_count: number
    data_model_warn_count: number
    traceback_count: number
    traceback_ready_count: number
    simulation_record_count: number
    capability_mock_count: number
    capability_call_count: number
    capability_call_succeeded_count: number
    capability_call_failed_count: number
    fault_configuration_count: number
    fault_configuration_ready_count: number
    fault_configuration_draft_count: number
    fault_configuration_bound_count: number
    scene_replay_count: number
    scene_replay_ready_count: number
    scene_replay_frame_count: number
    fault_report_template_count: number
    fault_report_count: number
    fault_report_active_count: number
    fault_report_overdue_count: number
    auxiliary_simulation_count: number
    auxiliary_simulation_attention_count: number
    scene_library_count: number
    scene_library_ready_count: number
    scene_run_count: number
    scene_running_count: number
    scene_completed_count: number
    work_order_count: number
    work_order_open_count: number
    alert_count: number
    alert_pending_count: number
    alert_active_count: number
    alert_recovered_count: number
  }
  customer_counts: Record<'PUBLIC' | 'ENTERPRISE', number>
  severity_counts: Record<ComplaintSeverity, number>
  scenarios: RehearsalScenario[]
  templates: ComplaintTemplate[]
  process_templates: ProcessTemplate[]
  process_runs: ProcessRun[]
  data_templates: DataSimulationTemplate[]
  data_batches: DataSimulationBatch[]
  data_tag_counts: Array<{ name: string; count: number }>
  data_models: RehearsalDataModel[]
  tracebacks: RehearsalTraceback[]
  scene_scripts: SceneScript[]
  scene_libraries: SceneLibrary[]
  scene_runs: SceneRun[]
  work_orders: WorkOrder[]
  alert_templates: AlertTemplate[]
  alerts: RehearsalAlert[]
  capability_mocks: CapabilityMock[]
  capability_calls: CapabilityCall[]
  fault_configurations: FaultConfiguration[]
  scene_replays: SceneReplay[]
  fault_report_templates: FaultReportTemplate[]
  fault_reports: FaultReport[]
  random_factor_catalog: RandomFactorDefinition[]
  auxiliary_simulations: AuxiliarySimulation[]
  instances: RehearsalInstance[]
  latest_complaints: Complaint[]
}

export interface ComplaintFilters {
  page?: number
  page_size?: number
  instance_id?: string
  customer_type?: '' | Exclude<CustomerType, 'MIXED'>
  severity?: '' | ComplaintSeverity
  validation_status?: '' | ValidationStatus
  source?: '' | ComplaintSource
  keyword?: string
  date_from?: string
  date_to?: string
}

export interface ComplaintPage {
  total: number
  page: number
  page_size: number
  items: Complaint[]
}

export interface ProcessRunFilters {
  page?: number
  page_size?: number
  instance_id?: string
  template_id?: string
  status?: '' | ProcessRunStatus
  auto_advance?: '' | 'true' | 'false'
  keyword?: string
}

export interface ProcessRunPage {
  total: number
  page: number
  page_size: number
  items: ProcessRun[]
}

export interface DataSimulationFilters {
  page?: number
  page_size?: number
  batch_id?: string
  instance_id?: string
  template_id?: string
  kind?: '' | DataSimulationKind
  status?: '' | DataSimulationStatus
  tag?: string
  keyword?: string
  date_from?: string
  date_to?: string
}

export interface DataSimulationPage {
  total: number
  page: number
  page_size: number
  items: DataSimulationBatch[]
}

export interface SceneRunFilters {
  page?: number
  page_size?: number
  instance_id?: string
  script_id?: string
  status?: '' | SceneRunStatus
  keyword?: string
}

export interface SceneRunPage {
  total: number
  page: number
  page_size: number
  items: SceneRun[]
}

export interface SceneLibraryFilters {
  page?: number
  page_size?: number
  scenario_id?: string
  script_id?: string
  status?: '' | SceneLibraryStatus
  visibility?: '' | SceneLibraryVisibility
  keyword?: string
}

export interface SceneLibraryPage {
  total: number
  page: number
  page_size: number
  items: SceneLibrary[]
}

export interface WorkOrderFilters {
  page?: number
  page_size?: number
  scene_run_id?: string
  status?: '' | WorkOrderStatus
  priority?: '' | WorkOrderPriority
  keyword?: string
}

export interface WorkOrderPage {
  total: number
  page: number
  page_size: number
  items: WorkOrder[]
}

export interface AlertFilters {
  page?: number
  page_size?: number
  instance_id?: string
  template_id?: string
  scene_run_id?: string
  status?: '' | AlertStatus
  severity?: '' | AlertSeverity
  keyword?: string
  date_from?: string
  date_to?: string
}

export interface DataModelFilters {
  page?: number
  page_size?: number
  instance_id?: string
  scenario_id?: string
  scene_run_id?: string
  build_strategy?: '' | DataModelBuildStrategy
  quality_status?: '' | DataModelQualityStatus
  keyword?: string
}

export interface DataModelPage {
  total: number
  page: number
  page_size: number
  items: RehearsalDataModel[]
}

export interface TracebackFilters {
  page?: number
  page_size?: number
  instance_id?: string
  scenario_id?: string
  scene_run_id?: string
  data_model_id?: string
  scope?: '' | TracebackScope
  status?: '' | TracebackStatus
  kind?: '' | TimelineKind
  keyword?: string
  date_from?: string
  date_to?: string
}

export interface TracebackPage {
  total: number
  page: number
  page_size: number
  items: RehearsalTraceback[]
}

export interface SimulationRecordFilters {
  page?: number
  page_size?: number
  instance_id?: string
  kind?: '' | SimulationRecordKind
  state?: '' | SimulationRecordState
  keyword?: string
  date_from?: string
  date_to?: string
}

export interface SimulationRecordPage {
  total: number
  page: number
  page_size: number
  summary: {
    total: number
    pending: number
    running: number
    succeeded: number
    attention: number
    failed: number
    average_duration_seconds: number
    kind_counts: Partial<Record<SimulationRecordKind, number>>
  }
  items: SimulationRecord[]
}

export interface CapabilityCallFilters {
  page?: number
  page_size?: number
  instance_id?: string
  capability_id?: string
  kind?: '' | CapabilityMockKind
  status?: '' | CapabilityCallStatus
  warroom_group?: string
  keyword?: string
  date_from?: string
  date_to?: string
}

export interface CapabilityCallPage {
  total: number
  page: number
  page_size: number
  summary: {
    total: number
    succeeded: number
    failed: number
    timeout: number
    average_latency_ms: number
  }
  warrooms: Array<{
    warroom_group: string
    total: number
    succeeded: number
    attention: number
  }>
  items: CapabilityCall[]
}

export interface FaultConfigurationFilters {
  page?: number
  page_size?: number
  scenario_id?: string
  status?: '' | FaultConfigurationStatus
  bound?: '' | 'true' | 'false'
  keyword?: string
}

export interface FaultConfigurationPage {
  total: number
  page: number
  page_size: number
  summary: {
    total: number
    ready: number
    draft: number
    archived: number
    bound_instances: number
  }
  items: FaultConfiguration[]
}

export interface SceneReplayFrame {
  sequence_no: number
  occurred_at: string
  channel: 'TRAFFIC' | 'ALERT' | 'CONTROL'
  channel_label: string
  source_node: string
  target_node: string
  protocol: string
  title: string
  status: string
  status_label: string
  latency_ms: number
  reference_id: string
  payload_summary: Record<string, unknown>
}

export interface SceneReplayNodeTrace {
  node_id: string
  node_name: string
  node_type: string
  before_state: string
  after_state: string
  changed: boolean
  traffic_count: number
  attention_count: number
  frames: SceneReplayFrame[]
}

export interface SceneReplay {
  id: string
  instance_id: string
  instance_code: string
  instance_name: string
  scene_run_id: string | null
  scene_run_name: string
  fault_configuration_id: string | null
  fault_configuration_name: string
  fault_configuration_version: number | null
  request_id: string
  code: string
  name: string
  description: string
  status: SceneReplayStatus
  status_label: string
  window_start: string | null
  window_end: string | null
  traffic_frame_count: number
  node_trace_count: number
  changed_node_count: number
  changed_link_count: number
  average_latency_ms: number
  summary: Record<string, number | string | null | Record<string, number>>
  checksum: string
  generated_at: string
  create_time: string
  update_time: string
  traffic_frames?: SceneReplayFrame[]
  topology_before?: { version?: string; nodes?: FaultTopologyNode[]; links?: FaultTopologyLink[] }
  topology_after?: { version?: string; nodes?: FaultTopologyNode[]; links?: FaultTopologyLink[] }
  node_traces?: SceneReplayNodeTrace[]
  mirror_comparison?: {
    node_deltas?: SceneReplayNodeTrace[]
    link_deltas?: Array<{ source: string; target: string; before_state: string; after_state: string }>
    before?: Record<string, number>
    after?: Record<string, number>
  }
}

export interface SceneReplayFilters {
  page?: number
  page_size?: number
  instance_id?: string
  scene_run_id?: string
  status?: '' | SceneReplayStatus
  node_id?: string
  keyword?: string
}

export interface SceneReplayPage {
  total: number
  page: number
  page_size: number
  summary: {
    total: number
    ready: number
    empty: number
    traffic_frames: number
    changed_nodes: number
    average_latency_ms: number
  }
  items: SceneReplay[]
}

export interface FaultReportStage {
  sequence_no?: number
  code: string
  name: string
  duration_minutes: number
  owner_role: string
  required_fields: string[]
}

export interface FaultReportAttachment {
  reference_id: string
  file_name: string
  content_type: string
  file_size: number
  note?: string
  added_at?: string
  added_by?: string
}

export interface FaultReportTemplate {
  id: string
  scenario_id: string | null
  scenario_name: string
  request_id: string
  code: string
  name: string
  description: string
  version: number
  status: 'READY' | 'ARCHIVED'
  status_label: string
  default_level: FaultReportLevel
  default_level_label: string
  stage_definitions: FaultReportStage[]
  stage_count: number
  required_fields: string[]
  report_count: number
  create_time: string
  update_time: string
}

export interface FaultReportEvent {
  id: string
  sequence_no: number
  action: string
  action_label: string
  previous_status: FaultReportStatus
  previous_status_label: string
  current_status: FaultReportStatus
  current_status_label: string
  previous_stage_code: string
  current_stage_code: string
  detail: Record<string, unknown>
  operator_name: string
  create_time: string
}

export interface FaultReport {
  id: string
  instance_id: string
  instance_code: string
  instance_name: string
  template_id: string | null
  template_name: string
  template_version: number | null
  scene_run_id: string | null
  scene_run_name: string
  request_id: string
  code: string
  title: string
  description: string
  impact_scope: string
  level: FaultReportLevel
  level_label: string
  status: FaultReportStatus
  status_label: string
  current_stage_code: string
  current_stage_name: string
  stage_index: number
  stage_count: number
  stage_owner_role: string
  progress_percent: number
  occurred_at: string
  reported_at: string | null
  accepted_at: string | null
  recovered_at: string | null
  closed_at: string | null
  stage_started_at: string
  stage_deadline_at: string
  remaining_seconds: number
  overdue_seconds: number
  is_overdue: boolean
  attachments: FaultReportAttachment[]
  attachment_count: number
  template_snapshot: {
    id?: string
    code?: string
    name?: string
    version?: number
    default_level?: FaultReportLevel
    stage_definitions?: FaultReportStage[]
    required_fields?: string[]
  }
  summary: Record<string, unknown>
  event_count: number
  allowed_actions: FaultReportAction[]
  create_time: string
  update_time: string
  events?: FaultReportEvent[]
}

export interface FaultReportFilters {
  page?: number
  page_size?: number
  instance_id?: string
  template_id?: string
  status?: '' | FaultReportStatus
  level?: '' | FaultReportLevel
  overdue?: '' | 'true'
  keyword?: string
}

export interface FaultReportPage {
  total: number
  page: number
  page_size: number
  summary: {
    total: number
    draft: number
    active: number
    recovered: number
    closed: number
    overdue: number
    attachments: number
  }
  items: FaultReport[]
}

export interface RandomFactorDefinition {
  code: string
  name: string
  category: RandomFactorCategory
  unit: string
  min_value: number
  max_value: number
  distribution: RandomFactorDistribution
  trigger_probability: number
  triggered?: boolean
  sampled_value?: number
  trigger_minute?: number | null
}

export interface AuxiliaryMetricStatistic {
  code: string
  name: string
  baseline: number
  mean: number
  peak: number
  variance: number
  delta_percent: number
}

export interface AuxiliarySimulationPoint {
  minute: number
  occurred_at: string
  latency_ms: number
  packet_loss_pct: number
  traffic_multiplier: number
  complaint_count: number
  ticket_backlog: number
  timeout_rate_pct: number
}

export interface AuxiliarySimulation {
  id: string
  instance_id: string
  instance_code: string
  instance_name: string
  scenario_name: string
  request_id: string
  code: string
  name: string
  seed: number
  duration_minutes: number
  status: AuxiliarySimulationStatus
  status_label: string
  factor_snapshot: RandomFactorDefinition[]
  factor_count: number
  triggered_factor_count: number
  anomaly_count: number
  summary: { point_count?: number; conclusion?: string; anomaly_count?: number }
  statistics: AuxiliaryMetricStatistic[]
  impact_analysis: string[]
  checksum: string
  started_at: string
  completed_at: string
  create_time: string
  update_time: string
  result_snapshot?: Record<string, unknown>
  points?: AuxiliarySimulationPoint[]
  anomalies?: Array<{ minute: number; occurred_at: string; reasons: string[] }>
  key_moments?: Array<{ minute: number; label: string; occurred_at: string }>
}

export interface AuxiliarySimulationFilters {
  page?: number
  page_size?: number
  instance_id?: string
  status?: '' | AuxiliarySimulationStatus
  seed?: number | string
  keyword?: string
}

export interface AuxiliarySimulationPage {
  total: number
  page: number
  page_size: number
  summary: {
    total: number
    attention: number
    factor_count: number
    triggered_factor_count: number
    anomaly_count: number
  }
  items: AuxiliarySimulation[]
}

export interface AlertPage {
  total: number
  page: number
  page_size: number
  items: RehearsalAlert[]
}

const prefix = () => {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/rehearsal`
}

function getDashboard(loading?: Ref<boolean>): Promise<Result<RehearsalDashboard>> {
  return get(`${prefix()}/dashboard`, undefined, loading)
}

function createInstance(
  data: {
    request_id: string
    scenario_id: string
    name: string
    code?: string
    planned_start_at?: string | null
    parameters?: Record<string, unknown>
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; instance: RehearsalInstance }>> {
  return post(`${prefix()}/instance`, data, undefined, loading)
}

function getInstance(id: string, loading?: Ref<boolean>): Promise<Result<RehearsalInstance>> {
  return get(`${prefix()}/instance/${id}`, undefined, loading)
}

function operateInstance(
  id: string,
  data: { action: InstanceAction; note?: string },
  loading?: Ref<boolean>,
): Promise<Result<{ instance: RehearsalInstance; event: RehearsalEvent }>> {
  return post(`${prefix()}/instance/${id}/operate`, data, undefined, loading)
}

function generateComplaints(
  id: string,
  data: {
    request_id: string
    template_id: string
    count: number
    start_at: string
    interval_minutes: number
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; batch: ComplaintBatch }>> {
  return post(`${prefix()}/instance/${id}/complaint/generate`, data, undefined, loading)
}

function importComplaints(
  id: string,
  requestId: string,
  file: File,
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; batch: ComplaintBatch }>> {
  const data = new FormData()
  data.append('request_id', requestId)
  data.append('file', file, file.name)
  return post(`${prefix()}/instance/${id}/complaint/import`, data, undefined, loading)
}

function getComplaints(
  params: ComplaintFilters,
  loading?: Ref<boolean>,
): Promise<Result<ComplaintPage>> {
  return get(`${prefix()}/complaint`, params, loading)
}

function exportComplaints(params: ComplaintFilters, loading?: Ref<boolean>) {
  return exportFile('预演申告数据.csv', `${prefix()}/complaint/export`, params, loading)
}

function downloadImportTemplate(loading?: Ref<boolean>) {
  return exportFile('预演申告导入模板.csv', `${prefix()}/complaint/import-template`, {}, loading)
}

function exportBatchValidation(batch: ComplaintBatch, loading?: Ref<boolean>) {
  return exportFile(
    `预演批次V${batch.version}校验报告.csv`,
    `${prefix()}/batch/${batch.id}/validation/export`,
    {},
    loading,
  )
}

function createProcessRun(
  instanceId: string,
  data: {
    request_id: string
    template_id: string
    name?: string
    auto_advance?: boolean | null
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; run: ProcessRun }>> {
  return post(`${prefix()}/instance/${instanceId}/process`, data, undefined, loading)
}

function getProcessRuns(
  params: ProcessRunFilters,
  loading?: Ref<boolean>,
): Promise<Result<ProcessRunPage>> {
  return get(`${prefix()}/process`, params, loading)
}

function getProcessRun(id: string, loading?: Ref<boolean>): Promise<Result<ProcessRun>> {
  return get(`${prefix()}/process/${id}`, undefined, loading)
}

function operateProcessRun(
  id: string,
  data: { action: ProcessRunAction; note?: string; reason?: string },
  loading?: Ref<boolean>,
): Promise<Result<{ run: ProcessRun; event: ProcessEvent }>> {
  return post(`${prefix()}/process/${id}/operate`, data, undefined, loading)
}

function exportProcessRuns(params: ProcessRunFilters, loading?: Ref<boolean>) {
  return exportFile('处置进度.csv', `${prefix()}/process/export`, params, loading)
}

function generateSimulationData(
  instanceId: string,
  data: {
    request_id: string
    template_id: string
    name?: string
    count: number
    start_at: string
    interval_minutes: number
    rules?: DataSimulationRule[]
    tags?: string[]
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; batch: DataSimulationBatch }>> {
  return post(`${prefix()}/instance/${instanceId}/data-simulation`, data, undefined, loading)
}

function getDataSimulations(
  params: DataSimulationFilters,
  loading?: Ref<boolean>,
): Promise<Result<DataSimulationPage>> {
  return get(`${prefix()}/data-simulation`, params, loading)
}

function getDataSimulation(
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<DataSimulationBatch>> {
  return get(`${prefix()}/data-simulation/${id}`, undefined, loading)
}

function exportDataSimulations(params: DataSimulationFilters, loading?: Ref<boolean>) {
  return exportFile('预演数据.csv', `${prefix()}/data-simulation/export`, params, loading)
}

function createDataModel(
  instanceId: string,
  data: {
    request_id: string
    name?: string
    description?: string
    build_strategy: DataModelBuildStrategy
    transformer_code?: string
    scene_run_id?: string | null
    source_scope?: Record<string, unknown>
  },
  loading?: Ref<boolean>,
): Promise<
  Result<{
    created: boolean
    data_model: RehearsalDataModel
    version: DataModelVersion
    load: DataModelLoad
  }>
> {
  return post(`${prefix()}/instance/${instanceId}/data-model`, data, undefined, loading)
}

function getDataModels(
  params: DataModelFilters,
  loading?: Ref<boolean>,
): Promise<Result<DataModelPage>> {
  return get(`${prefix()}/data-model`, params, loading)
}

function getDataModel(id: string, loading?: Ref<boolean>): Promise<Result<RehearsalDataModel>> {
  return get(`${prefix()}/data-model/${id}`, undefined, loading)
}

function loadDataModel(
  id: string,
  data: {
    request_id: string
    note?: string
    transformer_code?: string
    source_scope?: Record<string, unknown>
  },
  loading?: Ref<boolean>,
): Promise<
  Result<{
    created: boolean
    data_model: RehearsalDataModel
    version: DataModelVersion | null
    load: DataModelLoad
  }>
> {
  return post(`${prefix()}/data-model/${id}/load`, data, undefined, loading)
}

function createTraceback(
  instanceId: string,
  data: {
    request_id: string
    name?: string
    description?: string
    scope: TracebackScope
    scene_run_id?: string | null
    data_model_id?: string | null
    kind_scope?: TimelineKind[]
    window_start?: string | null
    window_end?: string | null
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; traceback: RehearsalTraceback }>> {
  return post(`${prefix()}/instance/${instanceId}/traceback`, data, undefined, loading)
}

function getTracebacks(
  params: TracebackFilters,
  loading?: Ref<boolean>,
): Promise<Result<TracebackPage>> {
  return get(`${prefix()}/traceback`, params, loading)
}

function getTraceback(id: string, loading?: Ref<boolean>): Promise<Result<RehearsalTraceback>> {
  return get(`${prefix()}/traceback/${id}`, undefined, loading)
}

function exportTracebacks(params: TracebackFilters, loading?: Ref<boolean>) {
  return exportFile('预演数据动态回溯.csv', `${prefix()}/traceback/export`, params, loading)
}

function getSimulationRecords(
  params: SimulationRecordFilters,
  loading?: Ref<boolean>,
): Promise<Result<SimulationRecordPage>> {
  return get(`${prefix()}/simulation-record`, params, loading)
}

function getSimulationRecord(
  kind: SimulationRecordKind,
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<SimulationRecordDetail>> {
  return get(`${prefix()}/simulation-record/${kind}/${id}`, undefined, loading)
}

function exportSimulationRecords(params: SimulationRecordFilters, loading?: Ref<boolean>) {
  return exportFile('预演记录.csv', `${prefix()}/simulation-record/export`, params, loading)
}

function getCapabilityMocks(
  params: { scenario_id?: string; kind?: '' | CapabilityMockKind; keyword?: string } = {},
  loading?: Ref<boolean>,
): Promise<Result<CapabilityMock[]>> {
  return get(`${prefix()}/capability-mock`, params, loading)
}

function createCapabilityMock(
  data: {
    scenario_id: string
    code: string
    name: string
    description?: string
    kind: CapabilityMockKind
    method: string
    endpoint: string
    request_schema?: Record<string, unknown>
    response_template?: Record<string, unknown>
    failure_template?: Record<string, unknown>
    default_status?: CapabilityCallStatus
    default_latency_ms?: number
  },
  loading?: Ref<boolean>,
): Promise<Result<CapabilityMock>> {
  return post(`${prefix()}/capability-mock`, data, undefined, loading)
}

function invokeCapability(
  instanceId: string,
  data: {
    request_id: string
    capability_id: string
    request_payload: Record<string, unknown>
    expected_status?: CapabilityCallStatus | null
    latency_ms?: number | null
    warroom_group?: string
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; call: CapabilityCall }>> {
  return post(`${prefix()}/instance/${instanceId}/capability-call`, data, undefined, loading)
}

function getCapabilityCalls(
  params: CapabilityCallFilters,
  loading?: Ref<boolean>,
): Promise<Result<CapabilityCallPage>> {
  return get(`${prefix()}/capability-call`, params, loading)
}

function getCapabilityCall(id: string, loading?: Ref<boolean>): Promise<Result<CapabilityCall>> {
  return get(`${prefix()}/capability-call/${id}`, undefined, loading)
}

function replayCapabilityCall(
  id: string,
  data: {
    request_id: string
    expected_status?: CapabilityCallStatus | null
    latency_ms?: number | null
    warroom_group?: string
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; call: CapabilityCall }>> {
  return post(`${prefix()}/capability-call/${id}/replay`, data, undefined, loading)
}

function getFaultConfigurations(
  params: FaultConfigurationFilters,
  loading?: Ref<boolean>,
): Promise<Result<FaultConfigurationPage>> {
  return get(`${prefix()}/fault-configuration`, params, loading)
}

function getFaultConfiguration(
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<FaultConfiguration>> {
  return get(`${prefix()}/fault-configuration/${id}`, undefined, loading)
}

function createFaultConfiguration(
  data: {
    request_id: string
    scenario_id: string
    code: string
    name: string
    description?: string
    alert_rules: FaultAlertRule[]
    timeout_policy: FaultConfiguration['timeout_policy']
    active_window: FaultConfiguration['active_window']
    topology_snapshot: FaultConfiguration['topology_snapshot']
    emergency_plan: FaultConfiguration['emergency_plan']
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; configuration: FaultConfiguration }>> {
  return post(`${prefix()}/fault-configuration`, data, undefined, loading)
}

function cloneFaultConfiguration(
  id: string,
  data: {
    request_id: string
    name?: string
    description?: string
    alert_rules?: FaultAlertRule[]
    timeout_policy?: FaultConfiguration['timeout_policy']
    active_window?: FaultConfiguration['active_window']
    topology_snapshot?: FaultConfiguration['topology_snapshot']
    emergency_plan?: FaultConfiguration['emergency_plan']
    note?: string
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; configuration: FaultConfiguration }>> {
  return post(`${prefix()}/fault-configuration/${id}/clone`, data, undefined, loading)
}

function validateFaultConfiguration(
  id: string,
  note = '',
  loading?: Ref<boolean>,
): Promise<Result<{ configuration: FaultConfiguration; event: FaultConfigurationEvent }>> {
  return post(`${prefix()}/fault-configuration/${id}/validate`, { note }, undefined, loading)
}

function archiveFaultConfiguration(
  id: string,
  note = '',
  loading?: Ref<boolean>,
): Promise<Result<{ configuration: FaultConfiguration; event: FaultConfigurationEvent }>> {
  return post(`${prefix()}/fault-configuration/${id}/archive`, { note }, undefined, loading)
}

function applyFaultConfiguration(
  instanceId: string,
  data: { request_id: string; configuration_id: string; note?: string },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; instance: RehearsalInstance }>> {
  return post(`${prefix()}/instance/${instanceId}/fault-configuration`, data, undefined, loading)
}

function createSceneReplay(
  instanceId: string,
  data: {
    request_id: string
    name?: string
    description?: string
    scene_run_id?: string | null
    window_start?: string | null
    window_end?: string | null
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; replay: SceneReplay }>> {
  return post(`${prefix()}/instance/${instanceId}/scene-replay`, data, undefined, loading)
}

function getSceneReplays(
  params: SceneReplayFilters,
  loading?: Ref<boolean>,
): Promise<Result<SceneReplayPage>> {
  return get(`${prefix()}/scene-replay`, params, loading)
}

function getSceneReplay(id: string, loading?: Ref<boolean>): Promise<Result<SceneReplay>> {
  return get(`${prefix()}/scene-replay/${id}`, undefined, loading)
}

function getFaultReportTemplates(
  params: { scenario_id?: string; status?: '' | 'READY' | 'ARCHIVED'; keyword?: string } = {},
  loading?: Ref<boolean>,
): Promise<Result<FaultReportTemplate[]>> {
  return get(`${prefix()}/fault-report-template`, params, loading)
}

function createFaultReportTemplate(
  data: {
    request_id: string
    scenario_id?: string | null
    code: string
    name: string
    description?: string
    default_level: FaultReportLevel
    stage_definitions: Array<Omit<FaultReportStage, 'sequence_no'>>
    required_fields?: string[]
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; template: FaultReportTemplate }>> {
  return post(`${prefix()}/fault-report-template`, data, undefined, loading)
}

function createFaultReport(
  instanceId: string,
  data: {
    request_id: string
    template_id: string
    scene_run_id?: string | null
    title: string
    description?: string
    impact_scope?: string
    level?: FaultReportLevel | null
    occurred_at?: string
    attachments?: FaultReportAttachment[]
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; report: FaultReport }>> {
  return post(`${prefix()}/instance/${instanceId}/fault-report`, data, undefined, loading)
}

function getFaultReports(
  params: FaultReportFilters,
  loading?: Ref<boolean>,
): Promise<Result<FaultReportPage>> {
  return get(`${prefix()}/fault-report`, params, loading)
}

function getFaultReport(id: string, loading?: Ref<boolean>): Promise<Result<FaultReport>> {
  return get(`${prefix()}/fault-report/${id}`, undefined, loading)
}

function operateFaultReport(
  id: string,
  data: {
    action: FaultReportAction
    note?: string
    level?: FaultReportLevel | null
    attachments?: FaultReportAttachment[]
    event_at?: string
  },
  loading?: Ref<boolean>,
): Promise<Result<{ report: FaultReport }>> {
  return post(`${prefix()}/fault-report/${id}/operate`, data, undefined, loading)
}

function createAuxiliarySimulation(
  instanceId: string,
  data: {
    request_id: string
    name?: string
    seed: number
    duration_minutes: number
    factors: Array<Pick<RandomFactorDefinition, 'code'> & Partial<RandomFactorDefinition>>
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; simulation: AuxiliarySimulation }>> {
  return post(`${prefix()}/instance/${instanceId}/auxiliary-simulation`, data, undefined, loading)
}

function getAuxiliarySimulations(
  params: AuxiliarySimulationFilters,
  loading?: Ref<boolean>,
): Promise<Result<AuxiliarySimulationPage>> {
  return get(`${prefix()}/auxiliary-simulation`, params, loading)
}

function getAuxiliarySimulation(
  id: string,
  loading?: Ref<boolean>,
): Promise<Result<AuxiliarySimulation>> {
  return get(`${prefix()}/auxiliary-simulation/${id}`, undefined, loading)
}

function exportAuxiliarySimulation(
  simulation: AuxiliarySimulation,
  exportFormat: AuxiliaryReportFormat,
  reportLevel: AuxiliaryReportLevel,
  loading?: Ref<boolean>,
) {
  const levelLabel = reportLevel === 'full' ? '完整版' : '精简版'
  return exportFile(
    `${simulation.name}-${levelLabel}.${exportFormat}`,
    `${prefix()}/auxiliary-simulation/${simulation.id}/export`,
    { export_format: exportFormat, report_level: reportLevel },
    loading,
  )
}

function createSceneScript(
  data: {
    scenario_id: string
    code: string
    name: string
    description?: string
    steps: SceneScriptStep[]
  },
  loading?: Ref<boolean>,
): Promise<Result<SceneScript>> {
  return post(`${prefix()}/scene-script`, data, undefined, loading)
}

function createSceneRun(
  instanceId: string,
  data: {
    request_id: string
    script_id: string
    name?: string
    complaint_batch_ids?: string[]
    data_batch_ids?: string[]
    process_run_ids?: string[]
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; run: SceneRun }>> {
  return post(`${prefix()}/instance/${instanceId}/scene-run`, data, undefined, loading)
}

function createSceneLibrary(
  data: {
    request_id: string
    scenario_id: string
    script_id: string
    code: string
    name: string
    description?: string
    default_instance_id?: string | null
    process_template_id?: string | null
    data_model_id?: string | null
    visibility?: SceneLibraryVisibility
    permission_roles?: string[]
    configuration?: Record<string, unknown>
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; library: SceneLibrary }>> {
  return post(`${prefix()}/scene-library`, data, undefined, loading)
}

function getSceneLibraries(
  params: SceneLibraryFilters,
  loading?: Ref<boolean>,
): Promise<Result<SceneLibraryPage>> {
  return get(`${prefix()}/scene-library`, params, loading)
}

function getSceneLibrary(id: string, loading?: Ref<boolean>): Promise<Result<SceneLibrary>> {
  return get(`${prefix()}/scene-library/${id}`, undefined, loading)
}

function cloneSceneLibrary(
  id: string,
  data: {
    request_id: string
    name?: string
    description?: string
    default_instance_id?: string | null
    process_template_id?: string | null
    data_model_id?: string | null
    visibility?: SceneLibraryVisibility
    permission_roles?: string[]
    steps?: SceneScriptStep[]
    configuration?: Record<string, unknown>
    note?: string
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; library: SceneLibrary }>> {
  return post(`${prefix()}/scene-library/${id}/clone`, data, undefined, loading)
}

function operateSceneLibrary(
  id: string,
  data: { action: SceneLibraryAction; note?: string },
  loading?: Ref<boolean>,
): Promise<Result<{ library: SceneLibrary; event: SceneLibraryEvent }>> {
  return post(`${prefix()}/scene-library/${id}/operate`, data, undefined, loading)
}

function createSceneRunFromLibrary(
  id: string,
  data: {
    request_id: string
    instance_id?: string | null
    name?: string
    include_latest_complaint_batch?: boolean
    include_latest_data_batch?: boolean
    include_latest_process_run?: boolean
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; run: SceneRun }>> {
  return post(`${prefix()}/scene-library/${id}/run`, data, undefined, loading)
}

function getSceneRuns(params: SceneRunFilters, loading?: Ref<boolean>): Promise<Result<SceneRunPage>> {
  return get(`${prefix()}/scene-run`, params, loading)
}

function getSceneRun(id: string, loading?: Ref<boolean>): Promise<Result<SceneRun>> {
  return get(`${prefix()}/scene-run/${id}`, undefined, loading)
}

function operateSceneRun(
  id: string,
  data: { action: SceneRunAction; note?: string; reason?: string; output?: Record<string, unknown> },
  loading?: Ref<boolean>,
): Promise<Result<{ run: SceneRun; event: SceneEvent }>> {
  return post(`${prefix()}/scene-run/${id}/operate`, data, undefined, loading)
}

function createWorkOrder(
  sceneRunId: string,
  data: {
    request_id: string
    title: string
    description?: string
    priority?: WorkOrderPriority
    assignee?: string
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; work_order: WorkOrder }>> {
  return post(`${prefix()}/scene-run/${sceneRunId}/work-order`, data, undefined, loading)
}

function getWorkOrders(
  params: WorkOrderFilters,
  loading?: Ref<boolean>,
): Promise<Result<WorkOrderPage>> {
  return get(`${prefix()}/work-order`, params, loading)
}

function operateWorkOrder(
  id: string,
  data: { action: WorkOrderAction; note?: string; resolution?: string; assignee?: string },
  loading?: Ref<boolean>,
): Promise<Result<{ work_order: WorkOrder; event: WorkOrderEvent }>> {
  return post(`${prefix()}/work-order/${id}/operate`, data, undefined, loading)
}

function createAlertTemplate(
  data: {
    scenario_id: string
    code: string
    name: string
    description?: string
    default_severity: AlertSeverity
    rules: AlertRule[]
  },
  loading?: Ref<boolean>,
): Promise<Result<AlertTemplate>> {
  return post(`${prefix()}/alert-template`, data, undefined, loading)
}

function createAlert(
  instanceId: string,
  data: {
    request_id: string
    template_id: string
    rule_code?: string
    scene_run_id?: string | null
    data_batch_id?: string | null
    title?: string
    description?: string
    severity?: AlertSeverity | null
    source_system?: string
    resource_type?: string
    resource_id?: string
    resource_name?: string
    metric_code?: string
    metric_name?: string
    metric_value?: number | null
    threshold?: number | null
    occurred_at?: string
    context?: Record<string, unknown>
  },
  loading?: Ref<boolean>,
): Promise<Result<{ created: boolean; alert: RehearsalAlert }>> {
  return post(`${prefix()}/instance/${instanceId}/alert`, data, undefined, loading)
}

function getAlerts(params: AlertFilters, loading?: Ref<boolean>): Promise<Result<AlertPage>> {
  return get(`${prefix()}/alert`, params, loading)
}

function getAlert(id: string, loading?: Ref<boolean>): Promise<Result<RehearsalAlert>> {
  return get(`${prefix()}/alert/${id}`, undefined, loading)
}

function operateAlert(
  id: string,
  data: {
    action: AlertAction
    note?: string
    event_at?: string
    metric_value?: number | null
    detail?: Record<string, unknown>
  },
  loading?: Ref<boolean>,
): Promise<Result<{ alert: RehearsalAlert; event: AlertEvent }>> {
  return post(`${prefix()}/alert/${id}/operate`, data, undefined, loading)
}

function getInstanceTimeline(
  instanceId: string,
  loading?: Ref<boolean>,
): Promise<Result<RehearsalTimeline>> {
  return get(`${prefix()}/instance/${instanceId}/timeline`, undefined, loading)
}

export default {
  getDashboard,
  createInstance,
  getInstance,
  operateInstance,
  generateComplaints,
  importComplaints,
  getComplaints,
  exportComplaints,
  downloadImportTemplate,
  exportBatchValidation,
  createProcessRun,
  getProcessRuns,
  getProcessRun,
  operateProcessRun,
  exportProcessRuns,
  generateSimulationData,
  getDataSimulations,
  getDataSimulation,
  exportDataSimulations,
  createDataModel,
  getDataModels,
  getDataModel,
  loadDataModel,
  createTraceback,
  getTracebacks,
  getTraceback,
  exportTracebacks,
  getSimulationRecords,
  getSimulationRecord,
  exportSimulationRecords,
  getCapabilityMocks,
  createCapabilityMock,
  invokeCapability,
  getCapabilityCalls,
  getCapabilityCall,
  replayCapabilityCall,
  getFaultConfigurations,
  getFaultConfiguration,
  createFaultConfiguration,
  cloneFaultConfiguration,
  validateFaultConfiguration,
  archiveFaultConfiguration,
  applyFaultConfiguration,
  createSceneReplay,
  getSceneReplays,
  getSceneReplay,
  getFaultReportTemplates,
  createFaultReportTemplate,
  createFaultReport,
  getFaultReports,
  getFaultReport,
  operateFaultReport,
  createAuxiliarySimulation,
  getAuxiliarySimulations,
  getAuxiliarySimulation,
  exportAuxiliarySimulation,
  createSceneScript,
  createSceneLibrary,
  getSceneLibraries,
  getSceneLibrary,
  cloneSceneLibrary,
  operateSceneLibrary,
  createSceneRunFromLibrary,
  createSceneRun,
  getSceneRuns,
  getSceneRun,
  operateSceneRun,
  createWorkOrder,
  getWorkOrders,
  operateWorkOrder,
  createAlertTemplate,
  createAlert,
  getAlerts,
  getAlert,
  operateAlert,
  getInstanceTimeline,
}
