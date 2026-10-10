export type PipelineApprovalMode = 'AUTO' | 'MANUAL'
export type PipelineRunStatus = 'PENDING' | 'RUNNING' | 'WAITING_APPROVAL' | 'SUCCESS' | 'FAILED' | 'REJECTED'
export type PipelineRunTrigger = 'MANUAL' | 'SCHEDULED' | 'RETRY'
export type PipelineStage = 'FEATURE' | 'TRAIN' | 'EVALUATE' | 'APPROVE' | 'DEPLOY'
export type PipelineStageStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'SKIPPED'

export interface ModelTrainingPipeline {
  id: string
  name: string
  description: string
  registry_name: string
  dataset_name: string
  dataset_version: string
  parameters: Record<string, unknown>
  evaluation_metrics: Record<string, number>
  thresholds: Record<string, number | { min?: number; max?: number }>
  artifact_uri_template: string
  approval_mode: PipelineApprovalMode
  approval_mode_label: string
  auto_deploy: boolean
  active: boolean
  schedule_enabled: boolean
  cron_expression: string
  next_run_at: string | null
  last_run_at: string | null
}

export interface ModelPipelineStageRun {
  id: string
  stage: PipelineStage
  stage_label: string
  sequence: number
  status: PipelineStageStatus
  status_label: string
  input_snapshot: Record<string, unknown>
  output_snapshot: Record<string, unknown>
  error_message: string
  started_at: string | null
  finished_at: string | null
}

export interface ModelPipelineRun {
  id: string
  pipeline_id: string
  pipeline_name: string
  run_number: number
  trigger: PipelineRunTrigger
  trigger_label: string
  status: PipelineRunStatus
  status_label: string
  current_stage: PipelineStage
  current_stage_label: string
  error_message: string
  model_version_id: string | null
  model_version_label: string
  approval_comment: string
  started_at: string | null
  finished_at: string | null
  create_time: string
  stages?: ModelPipelineStageRun[]
}

export interface ModelPipelineWriteRequest {
  name: string
  description?: string
  registry_name: string
  dataset_name: string
  dataset_version?: string
  parameters?: Record<string, unknown>
  evaluation_metrics: Record<string, number>
  thresholds: Record<string, number | { min?: number; max?: number }>
  approval_mode: PipelineApprovalMode
  auto_deploy: boolean
  schedule_enabled: boolean
  cron_expression?: string
}
