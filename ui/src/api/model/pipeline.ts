import type { Ref } from 'vue'
import { get, post } from '@/request'
import type { Result } from '@/request/Result'
import useStore from '@/stores'
import type {
  ModelPipelineRun,
  ModelPipelineWriteRequest,
  ModelTrainingPipeline,
} from '@/api/type/model-pipeline'

const workspacePrefix = () => {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}`
}

export const getModelPipelines = (loading?: Ref<boolean>): Promise<Result<ModelTrainingPipeline[]>> =>
  get(`${workspacePrefix()}/model-pipeline`, {}, loading)

export const createModelPipeline = (
  data: ModelPipelineWriteRequest,
  loading?: Ref<boolean>,
): Promise<Result<ModelTrainingPipeline>> => post(`${workspacePrefix()}/model-pipeline`, data, {}, loading)

export const getModelPipelineRuns = (loading?: Ref<boolean>): Promise<Result<ModelPipelineRun[]>> =>
  get(`${workspacePrefix()}/model-pipeline-run`, {}, loading)

export const getModelPipelineRun = (id: string, loading?: Ref<boolean>): Promise<Result<ModelPipelineRun>> =>
  get(`${workspacePrefix()}/model-pipeline-run/${id}`, {}, loading)

export const startModelPipeline = (
  pipelineId: string,
  loading?: Ref<boolean>,
): Promise<Result<ModelPipelineRun>> => post(`${workspacePrefix()}/model-pipeline/${pipelineId}/run`, {}, {}, loading)

export const approveModelPipelineRun = (
  id: string,
  action: 'APPROVE' | 'REJECT',
  comment: string,
  loading?: Ref<boolean>,
): Promise<Result<ModelPipelineRun>> =>
  post(`${workspacePrefix()}/model-pipeline-run/${id}/approve`, { action, comment }, {}, loading)

export const retryModelPipelineRun = (id: string, loading?: Ref<boolean>): Promise<Result<ModelPipelineRun>> =>
  post(`${workspacePrefix()}/model-pipeline-run/${id}/retry`, {}, {}, loading)
