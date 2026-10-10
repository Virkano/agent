export type ExperimentStatus = 'DRAFT' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED'

export type ModelVersionStatus =
  | 'REGISTERED'
  | 'EVALUATING'
  | 'APPROVED'
  | 'REJECTED'
  | 'PUBLISHED'
  | 'ARCHIVED'

export type EvaluationStatus = 'PENDING' | 'RUNNING' | 'PASSED' | 'FAILED' | 'ERROR'
export type ReleaseAction = 'PUBLISH' | 'ROLLBACK'

export interface ModelExperiment {
  id: string
  workspace_id: string
  name: string
  description: string
  status: ExperimentStatus
  status_label: string
  source_type: string
  dataset_name: string
  dataset_version: string
  parameters: Record<string, unknown>
  tags: Record<string, unknown>
  external_run_id: string
  user_id: string | null
  started_at: string | null
  finished_at: string | null
  create_time: string
  update_time: string
}

export interface ModelEvaluation {
  id: string
  model_version_id: string
  dataset_name: string
  dataset_version: string
  status: EvaluationStatus
  status_label: string
  metrics: Record<string, number>
  thresholds: Record<string, number | { min?: number; max?: number }>
  summary: string
  started_at: string | null
  finished_at: string | null
  create_time: string
}

export interface LifecycleModelVersion {
  id: string
  workspace_id: string
  registry_name: string
  version: number
  version_label: string
  status: ModelVersionStatus
  status_label: string
  experiment_id: string | null
  experiment_name: string
  provider_model_id: string | null
  provider_model_name: string
  artifact_uri: string
  artifact_digest: string
  dataset_version: string
  parameters: Record<string, unknown>
  metrics: Record<string, number>
  created_by_id: string | null
  published_at: string | null
  create_time: string
  update_time: string
  evaluations?: ModelEvaluation[]
}

export interface ModelReleaseRecord {
  id: string
  registry_name: string
  action: ReleaseAction
  action_label: string
  status: 'SUCCESS' | 'FAILED'
  status_label: string
  from_version_id: string | null
  from_version: number | null
  target_version_id: string
  target_version: number
  reason: string
  details: Record<string, unknown>
  operator_id: string | null
  create_time: string
}

export interface LifecycleOverview {
  experiment_total: number
  experiment_counts: Partial<Record<ExperimentStatus, number>>
  version_total: number
  version_counts: Partial<Record<ModelVersionStatus, number>>
  published_total: number
  published_versions: LifecycleModelVersion[]
  recent_releases: ModelReleaseRecord[]
}

export interface ExperimentWriteRequest {
  name: string
  description?: string
  source_type?: string
  dataset_name?: string
  dataset_version?: string
  parameters?: Record<string, unknown>
  tags?: Record<string, unknown>
}

export interface ModelVersionWriteRequest {
  registry_name: string
  experiment_id: string
  provider_model_id?: string | null
  artifact_uri?: string
  artifact_digest?: string
  dataset_version?: string
  parameters?: Record<string, unknown>
  metrics?: Record<string, number>
}

export interface EvaluationWriteRequest {
  dataset_name: string
  dataset_version?: string
  metrics: Record<string, number>
  thresholds: Record<string, number | { min?: number; max?: number }>
  summary?: string
}
