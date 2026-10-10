import type { Ref } from 'vue'
import { del, get, post, put } from '@/request'
import type { Result } from '@/request/Result'
import useStore from '@/stores'
import type {
  EvaluationWriteRequest,
  ExperimentStatus,
  ExperimentWriteRequest,
  LifecycleModelVersion,
  LifecycleOverview,
  ModelExperiment,
  ModelReleaseRecord,
  ModelVersionStatus,
  ModelVersionWriteRequest,
} from '@/api/type/model-lifecycle'

const prefix = () => {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/model-lifecycle`
}

export const getLifecycleOverview = (loading?: Ref<boolean>): Promise<Result<LifecycleOverview>> =>
  get(`${prefix()}/overview`, {}, loading)

export const getExperiments = (
  params?: { status?: ExperimentStatus | ''; keyword?: string },
  loading?: Ref<boolean>,
): Promise<Result<ModelExperiment[]>> => get(`${prefix()}/experiment`, params, loading)

export const createExperiment = (
  data: ExperimentWriteRequest,
  loading?: Ref<boolean>,
): Promise<Result<ModelExperiment>> => post(`${prefix()}/experiment`, data, {}, loading)

export const updateExperiment = (
  id: string,
  data: Partial<ExperimentWriteRequest> & { status?: ExperimentStatus },
  loading?: Ref<boolean>,
): Promise<Result<ModelExperiment>> => put(`${prefix()}/experiment/${id}`, data, {}, loading)

export const deleteExperiment = (id: string): Promise<Result<boolean>> =>
  del(`${prefix()}/experiment/${id}`)

export const getVersions = (
  params?: { registry_name?: string; status?: ModelVersionStatus | '' },
  loading?: Ref<boolean>,
): Promise<Result<LifecycleModelVersion[]>> => get(`${prefix()}/version`, params, loading)

export const createVersion = (
  data: ModelVersionWriteRequest,
  loading?: Ref<boolean>,
): Promise<Result<LifecycleModelVersion>> => post(`${prefix()}/version`, data, {}, loading)

export const deleteVersion = (id: string): Promise<Result<boolean>> =>
  del(`${prefix()}/version/${id}`)

export const evaluateVersion = (
  id: string,
  data: EvaluationWriteRequest,
  loading?: Ref<boolean>,
): Promise<Result<{ evaluation: unknown; version: LifecycleModelVersion }>> =>
  post(`${prefix()}/version/${id}/evaluate`, data, {}, loading)

export const publishVersion = (
  id: string,
  reason: string,
  loading?: Ref<boolean>,
): Promise<Result<unknown>> => post(`${prefix()}/version/${id}/publish`, { reason }, {}, loading)

export const rollbackVersion = (
  id: string,
  reason: string,
  loading?: Ref<boolean>,
): Promise<Result<unknown>> => post(`${prefix()}/version/${id}/rollback`, { reason }, {}, loading)

export const getReleases = (
  registryName?: string,
  loading?: Ref<boolean>,
): Promise<Result<ModelReleaseRecord[]>> =>
  get(`${prefix()}/release`, registryName ? { registry_name: registryName } : {}, loading)
