<template>
  <div class="lifecycle-page">
    <header class="lifecycle-hero">
      <div>
        <el-button link :icon="ArrowLeft" @click="router.push('/model')">返回模型管理</el-button>
        <span class="eyebrow">MODEL GOVERNANCE · V1</span>
        <h2>模型生命周期</h2>
        <p>从实验、版本评估到发布回滚，为每一次模型变更保留可追溯记录。</p>
      </div>
      <el-button :icon="Refresh" :loading="pageLoading" @click="loadAll">刷新数据</el-button>
    </header>

    <section class="summary-grid">
      <article>
        <span>实验总数</span>
        <strong>{{ overview.experiment_total }}</strong>
        <small>{{ overview.experiment_counts.RUNNING || 0 }} 个正在运行</small>
      </article>
      <article>
        <span>已注册版本</span>
        <strong>{{ overview.version_total }}</strong>
        <small>{{ overview.version_counts.APPROVED || 0 }} 个通过评估</small>
      </article>
      <article class="summary-accent">
        <span>线上模型</span>
        <strong>{{ overview.published_total }}</strong>
        <small>同一注册模型仅保留一个发布版本</small>
      </article>
      <article>
        <span>最近变更</span>
        <strong>{{ overview.recent_releases.length }}</strong>
        <small>展示最近 10 条发布与回滚审计</small>
      </article>
    </section>

    <section class="lifecycle-workbench">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="自动训练流水线" name="pipelines">
          <PipelineWorkbench />
        </el-tab-pane>
        <el-tab-pane label="实验管理" name="experiments">
          <div class="table-toolbar">
            <div class="filters">
              <el-input
                v-model="experimentFilters.keyword"
                clearable
                :prefix-icon="Search"
                placeholder="搜索实验名称"
                @keyup.enter="loadExperiments"
                @clear="loadExperiments"
              />
              <el-select
                v-model="experimentFilters.status"
                clearable
                placeholder="全部状态"
                @change="loadExperiments"
              >
                <el-option v-for="item in experimentStatusOptions" :key="item.value" v-bind="item" />
              </el-select>
            </div>
            <el-button type="primary" :icon="Plus" @click="experimentDialogVisible = true">
              新建实验
            </el-button>
          </div>
          <el-table v-loading="experimentLoading" :data="experiments" stripe>
            <el-table-column label="实验名称" min-width="200">
              <template #default="{ row }">
                <div class="primary-cell">
                  <strong>{{ row.name }}</strong>
                  <span>{{ row.description || '暂无实验说明' }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="dataset_name" label="数据集" min-width="160">
              <template #default="{ row }">
                {{ row.dataset_name || '—' }}
                <small v-if="row.dataset_version"> · {{ row.dataset_version }}</small>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="getExperimentTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="更新时间" width="180">
              <template #default="{ row }">{{ formatDate(row.update_time) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="270" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status === 'DRAFT'"
                  link
                  type="primary"
                  @click="changeExperimentStatus(row, 'RUNNING')"
                >
                  开始实验
                </el-button>
                <template v-if="row.status === 'RUNNING'">
                  <el-button link type="success" @click="changeExperimentStatus(row, 'SUCCESS')">
                    标记完成
                  </el-button>
                  <el-button link type="danger" @click="changeExperimentStatus(row, 'FAILED')">
                    标记失败
                  </el-button>
                </template>
                <el-button
                  v-if="row.status === 'FAILED'"
                  link
                  type="primary"
                  @click="changeExperimentStatus(row, 'RUNNING')"
                >
                  重新运行
                </el-button>
                <el-button
                  v-if="row.status === 'DRAFT'"
                  link
                  type="danger"
                  @click="removeExperiment(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!experiments.length && !experimentLoading" description="还没有模型实验" />
        </el-tab-pane>

        <el-tab-pane label="版本与发布" name="versions">
          <div class="table-toolbar">
            <div class="filters">
              <el-input
                v-model="versionFilters.registry_name"
                clearable
                :prefix-icon="Search"
                placeholder="筛选注册模型名称"
                @keyup.enter="loadVersions"
                @clear="loadVersions"
              />
              <el-select
                v-model="versionFilters.status"
                clearable
                placeholder="全部状态"
                @change="loadVersions"
              >
                <el-option v-for="item in versionStatusOptions" :key="item.value" v-bind="item" />
              </el-select>
            </div>
            <el-button type="primary" :icon="Plus" @click="openVersionDialog">注册模型版本</el-button>
          </div>
          <el-table v-loading="versionLoading" :data="versions" stripe>
            <el-table-column label="注册模型" min-width="180">
              <template #default="{ row }">
                <div class="primary-cell">
                  <strong>{{ row.registry_name }} · {{ row.version_label }}</strong>
                  <span>来源：{{ row.experiment_name || '—' }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="评估指标" min-width="210">
              <template #default="{ row }">
                <div v-if="Object.keys(row.metrics).length" class="metric-list">
                  <span v-for="(value, key) in row.metrics" :key="key">{{ key }} {{ value }}</span>
                </div>
                <span v-else>—</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getVersionTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="发布时间" width="180">
              <template #default="{ row }">{{ formatDate(row.published_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="['REGISTERED', 'APPROVED', 'REJECTED'].includes(row.status)"
                  link
                  type="primary"
                  @click="openEvaluationDialog(row)"
                >
                  运行评估
                </el-button>
                <el-button
                  v-if="row.status === 'APPROVED'"
                  link
                  type="success"
                  @click="releaseVersion(row, 'publish')"
                >
                  发布
                </el-button>
                <el-button
                  v-if="row.status === 'ARCHIVED'"
                  link
                  type="warning"
                  @click="releaseVersion(row, 'rollback')"
                >
                  回滚至此版本
                </el-button>
                <el-button
                  v-if="row.status === 'REGISTERED'"
                  link
                  type="danger"
                  @click="removeVersion(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!versions.length && !versionLoading" description="还没有注册模型版本" />
        </el-tab-pane>

        <el-tab-pane label="发布审计" name="releases">
          <el-table v-loading="releaseLoading" :data="releases" stripe>
            <el-table-column prop="registry_name" label="注册模型" min-width="180" />
            <el-table-column label="变更" min-width="220">
              <template #default="{ row }">
                <strong>{{ row.from_version ? `v${row.from_version}` : '未发布' }}</strong>
                <span class="change-arrow">→</span>
                <strong>v{{ row.target_version }}</strong>
              </template>
            </el-table-column>
            <el-table-column label="动作" width="110">
              <template #default="{ row }">
                <el-tag :type="row.action === 'ROLLBACK' ? 'warning' : 'success'" effect="plain">
                  {{ row.action_label }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="原因" min-width="240">
              <template #default="{ row }">{{ row.reason || '未填写' }}</template>
            </el-table-column>
            <el-table-column label="时间" width="180">
              <template #default="{ row }">{{ formatDate(row.create_time) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!releases.length && !releaseLoading" description="还没有发布记录" />
        </el-tab-pane>
      </el-tabs>
    </section>

    <el-dialog v-model="experimentDialogVisible" title="新建模型实验" width="620px" destroy-on-close>
      <el-form ref="experimentFormRef" :model="experimentForm" :rules="experimentRules" label-position="top">
        <el-form-item label="实验名称" prop="name">
          <el-input v-model="experimentForm.name" maxlength="128" placeholder="例如：客服意图识别基线实验" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="数据集名称">
            <el-input v-model="experimentForm.dataset_name" placeholder="训练或验证数据集" />
          </el-form-item>
          <el-form-item label="数据集版本">
            <el-input v-model="experimentForm.dataset_version" placeholder="例如：2026.09" />
          </el-form-item>
        </div>
        <el-form-item label="实验说明">
          <el-input v-model="experimentForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="experimentDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitExperiment">创建实验</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="versionDialogVisible" title="注册模型版本" width="620px" destroy-on-close>
      <el-form ref="versionFormRef" :model="versionForm" :rules="versionRules" label-position="top">
        <div class="form-grid">
          <el-form-item label="注册模型名称" prop="registry_name">
            <el-input v-model="versionForm.registry_name" placeholder="相同名称将自动递增版本号" />
          </el-form-item>
          <el-form-item label="来源实验" prop="experiment_id">
            <el-select v-model="versionForm.experiment_id" filterable placeholder="选择已完成实验">
              <el-option
                v-for="item in completedExperiments"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="模型产物地址">
          <el-input v-model="versionForm.artifact_uri" placeholder="对象存储、制品库或本地路径" />
        </el-form-item>
        <el-form-item label="产物摘要">
          <el-input v-model="versionForm.artifact_digest" placeholder="建议填写 SHA-256，便于核对版本" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="versionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitVersion">注册版本</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="evaluationDialogVisible" title="运行发布准入评估" width="660px" destroy-on-close>
      <el-alert
        :title="`${selectedVersion?.registry_name || ''} ${selectedVersion?.version_label || ''}`"
        description="准确率不得低于阈值，延迟不得高于阈值；全部满足后版本才可发布。"
        type="info"
        show-icon
        :closable="false"
        class="mb-16"
      />
      <el-form ref="evaluationFormRef" :model="evaluationForm" :rules="evaluationRules" label-position="top">
        <el-form-item label="评估集名称" prop="dataset_name">
          <el-input v-model="evaluationForm.dataset_name" placeholder="例如：发布准入集" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="准确率" prop="accuracy">
            <el-input-number v-model="evaluationForm.accuracy" :min="0" :max="1" :step="0.01" />
          </el-form-item>
          <el-form-item label="准确率下限" prop="min_accuracy">
            <el-input-number v-model="evaluationForm.min_accuracy" :min="0" :max="1" :step="0.01" />
          </el-form-item>
          <el-form-item label="延迟（ms）" prop="latency_ms">
            <el-input-number v-model="evaluationForm.latency_ms" :min="0" :step="10" />
          </el-form-item>
          <el-form-item label="延迟上限（ms）" prop="max_latency_ms">
            <el-input-number v-model="evaluationForm.max_latency_ms" :min="0" :step="10" />
          </el-form-item>
        </div>
        <el-form-item label="评估说明">
          <el-input v-model="evaluationForm.summary" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="evaluationDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitEvaluation">运行评估</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import PipelineWorkbench from './PipelineWorkbench.vue'
import {
  createExperiment,
  createVersion,
  deleteExperiment,
  deleteVersion,
  evaluateVersion,
  getExperiments,
  getLifecycleOverview,
  getReleases,
  getVersions,
  publishVersion,
  rollbackVersion,
  updateExperiment,
} from '@/api/model/lifecycle'
import type {
  ExperimentStatus,
  LifecycleModelVersion,
  LifecycleOverview,
  ModelExperiment,
  ModelVersionStatus,
} from '@/api/type/model-lifecycle'

type TagType = '' | 'success' | 'warning' | 'info' | 'primary' | 'danger'

const router = useRouter()
const activeTab = ref('pipelines')
const pageLoading = ref(false)
const experimentLoading = ref(false)
const versionLoading = ref(false)
const releaseLoading = ref(false)
const submitLoading = ref(false)

const overview = ref<LifecycleOverview>({
  experiment_total: 0,
  experiment_counts: {},
  version_total: 0,
  version_counts: {},
  published_total: 0,
  published_versions: [],
  recent_releases: [],
})
const experiments = ref<ModelExperiment[]>([])
const versions = ref<LifecycleModelVersion[]>([])
const releases = ref<LifecycleOverview['recent_releases']>([])

const experimentFilters = ref<{ keyword: string; status: ExperimentStatus | '' }>({ keyword: '', status: '' })
const versionFilters = ref<{ registry_name: string; status: ModelVersionStatus | '' }>({
  registry_name: '',
  status: '',
})

const experimentStatusOptions = [
  { label: '草稿', value: 'DRAFT' },
  { label: '运行中', value: 'RUNNING' },
  { label: '已完成', value: 'SUCCESS' },
  { label: '失败', value: 'FAILED' },
  { label: '已取消', value: 'CANCELLED' },
]
const versionStatusOptions = [
  { label: '已注册', value: 'REGISTERED' },
  { label: '评估通过', value: 'APPROVED' },
  { label: '评估未通过', value: 'REJECTED' },
  { label: '已发布', value: 'PUBLISHED' },
  { label: '已归档', value: 'ARCHIVED' },
]
const experimentTagType: Record<ExperimentStatus, TagType> = {
  DRAFT: 'info',
  RUNNING: 'primary',
  SUCCESS: 'success',
  FAILED: 'danger',
  CANCELLED: 'warning',
}
const versionTagType: Record<ModelVersionStatus, TagType> = {
  REGISTERED: 'info',
  EVALUATING: 'primary',
  APPROVED: 'success',
  REJECTED: 'danger',
  PUBLISHED: 'primary',
  ARCHIVED: 'warning',
}
const getExperimentTagType = (status: ExperimentStatus) => experimentTagType[status]
const getVersionTagType = (status: ModelVersionStatus) => versionTagType[status]

const experimentDialogVisible = ref(false)
const experimentFormRef = ref<FormInstance>()
const experimentForm = ref({ name: '', description: '', dataset_name: '', dataset_version: '' })
const experimentRules: FormRules = { name: [{ required: true, message: '请输入实验名称', trigger: 'blur' }] }

const versionDialogVisible = ref(false)
const versionFormRef = ref<FormInstance>()
const versionForm = ref({ registry_name: '', experiment_id: '', artifact_uri: '', artifact_digest: '' })
const versionRules: FormRules = {
  registry_name: [{ required: true, message: '请输入注册模型名称', trigger: 'blur' }],
  experiment_id: [{ required: true, message: '请选择来源实验', trigger: 'change' }],
}
const completedExperiments = computed(() => experiments.value.filter((item) => item.status === 'SUCCESS'))

const evaluationDialogVisible = ref(false)
const evaluationFormRef = ref<FormInstance>()
const selectedVersion = ref<LifecycleModelVersion>()
const evaluationForm = ref({
  dataset_name: '',
  accuracy: 0.9,
  min_accuracy: 0.85,
  latency_ms: 100,
  max_latency_ms: 150,
  summary: '',
})
const evaluationRules: FormRules = {
  dataset_name: [{ required: true, message: '请输入评估集名称', trigger: 'blur' }],
}

const formatDate = (value?: string | null) => (value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '—')

const loadOverview = async () => {
  overview.value = (await getLifecycleOverview(pageLoading)).data
}

const loadExperiments = async () => {
  experiments.value = (await getExperiments(experimentFilters.value, experimentLoading)).data
}

const loadVersions = async () => {
  versions.value = (await getVersions(versionFilters.value, versionLoading)).data
}

const loadReleases = async () => {
  releases.value = (await getReleases(undefined, releaseLoading)).data
}

const loadAll = async () => {
  await Promise.all([loadOverview(), loadExperiments(), loadVersions(), loadReleases()])
}

const refreshLifecycle = async () => {
  await Promise.all([loadOverview(), loadExperiments(), loadVersions(), loadReleases()])
}

const submitExperiment = async () => {
  await experimentFormRef.value?.validate()
  try {
    await createExperiment(experimentForm.value, submitLoading)
    experimentDialogVisible.value = false
    experimentForm.value = { name: '', description: '', dataset_name: '', dataset_version: '' }
    ElMessage.success('实验创建成功')
    await refreshLifecycle()
  } catch {
    // 请求层统一提示业务错误
  }
}

const changeExperimentStatus = async (row: ModelExperiment, status: ExperimentStatus) => {
  try {
    await updateExperiment(row.id, { status }, submitLoading)
    ElMessage.success('实验状态已更新')
    await refreshLifecycle()
  } catch {
    // 请求层统一提示业务错误
  }
}

const removeExperiment = async (row: ModelExperiment) => {
  await ElMessageBox.confirm(`确认删除草稿实验“${row.name}”吗？`, '删除实验', { type: 'warning' })
  try {
    await deleteExperiment(row.id)
    ElMessage.success('实验已删除')
    await refreshLifecycle()
  } catch {
    // 请求层统一提示业务错误
  }
}

const openVersionDialog = () => {
  if (!completedExperiments.value.length) {
    ElMessage.warning('请先完成至少一个模型实验')
    activeTab.value = 'experiments'
    return
  }
  versionDialogVisible.value = true
}

const submitVersion = async () => {
  await versionFormRef.value?.validate()
  try {
    await createVersion(versionForm.value, submitLoading)
    versionDialogVisible.value = false
    versionForm.value = { registry_name: '', experiment_id: '', artifact_uri: '', artifact_digest: '' }
    ElMessage.success('模型版本注册成功')
    await refreshLifecycle()
  } catch {
    // 请求层统一提示业务错误
  }
}

const openEvaluationDialog = (row: LifecycleModelVersion) => {
  selectedVersion.value = row
  evaluationForm.value.dataset_name = row.dataset_version ? `准入评估集 ${row.dataset_version}` : '发布准入集'
  evaluationDialogVisible.value = true
}

const submitEvaluation = async () => {
  await evaluationFormRef.value?.validate()
  if (!selectedVersion.value) return
  try {
    const response = await evaluateVersion(
      selectedVersion.value.id,
      {
        dataset_name: evaluationForm.value.dataset_name,
        metrics: {
          accuracy: evaluationForm.value.accuracy,
          latency_ms: evaluationForm.value.latency_ms,
        },
        thresholds: {
          accuracy: { min: evaluationForm.value.min_accuracy },
          latency_ms: { max: evaluationForm.value.max_latency_ms },
        },
        summary: evaluationForm.value.summary,
      },
      submitLoading,
    )
    evaluationDialogVisible.value = false
    ElMessage({
      type: response.data.version.status === 'APPROVED' ? 'success' : 'warning',
      message: response.data.version.status === 'APPROVED' ? '评估通过，可以发布' : '评估未通过，请调整模型后重试',
    })
    await refreshLifecycle()
  } catch {
    // 请求层统一提示业务错误
  }
}

const releaseVersion = async (row: LifecycleModelVersion, action: 'publish' | 'rollback') => {
  const actionLabel = action === 'publish' ? '发布' : '回滚'
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入${actionLabel} ${row.registry_name} ${row.version_label} 的原因`,
      `${actionLabel}模型版本`,
      { inputPlaceholder: '说明本次变更原因，便于后续审计', inputValidator: (value) => Boolean(value.trim()) || '请输入变更原因' },
    )
    if (action === 'publish') {
      await publishVersion(row.id, value, submitLoading)
    } else {
      await rollbackVersion(row.id, value, submitLoading)
    }
    ElMessage.success(`${actionLabel}成功`)
    await refreshLifecycle()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
  }
}

const removeVersion = async (row: LifecycleModelVersion) => {
  await ElMessageBox.confirm(`确认删除 ${row.registry_name} ${row.version_label} 吗？`, '删除模型版本', {
    type: 'warning',
  })
  try {
    await deleteVersion(row.id)
    ElMessage.success('模型版本已删除')
    await refreshLifecycle()
  } catch {
    // 请求层统一提示业务错误
  }
}

onMounted(loadAll)
</script>

<style scoped lang="scss">
.lifecycle-page {
  height: var(--app-main-height);
  min-height: 0;
  overflow-y: auto;
  padding: 24px 28px 40px;
  background:
    radial-gradient(circle at 92% 4%, rgb(67 97 238 / 10%), transparent 30%),
    var(--el-bg-color-page);
}

.lifecycle-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  max-width: 1500px;
  margin: 0 auto 20px;

  .el-button.is-link {
    display: flex;
    margin: 0 0 18px;
    padding: 0;
  }

  .eyebrow {
    color: var(--el-color-primary);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.16em;
  }

  h2 {
    margin: 6px 0 8px;
    font-size: 30px;
    line-height: 1.2;
  }

  p {
    margin: 0;
    color: var(--el-text-color-secondary);
  }
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  max-width: 1500px;
  margin: 0 auto 16px;

  article {
    display: flex;
    flex-direction: column;
    min-height: 122px;
    padding: 20px;
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 14px;
    background: var(--el-bg-color);
    box-shadow: 0 8px 30px rgb(31 35 48 / 4%);
  }

  span,
  small {
    color: var(--el-text-color-secondary);
  }

  strong {
    margin: 8px 0;
    font-size: 28px;
  }

  .summary-accent {
    color: white;
    border-color: transparent;
    background: linear-gradient(135deg, #3157d5, #6844d9);

    span,
    small {
      color: rgb(255 255 255 / 74%);
    }
  }
}

.lifecycle-workbench {
  max-width: 1500px;
  min-height: 480px;
  margin: 0 auto;
  padding: 6px 22px 22px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 14px;
  background: var(--el-bg-color);
  box-shadow: 0 12px 36px rgb(31 35 48 / 5%);
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 8px 0 18px;
}

.filters {
  display: flex;
  gap: 10px;

  .el-input {
    width: 260px;
  }

  .el-select {
    width: 150px;
  }
}

.primary-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;

  span {
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }
}

.metric-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;

  span {
    padding: 3px 8px;
    border-radius: 999px;
    color: var(--el-text-color-regular);
    background: var(--el-fill-color-light);
    font-size: 12px;
  }
}

.change-arrow {
  margin: 0 12px;
  color: var(--el-text-color-placeholder);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;

  .el-select,
  .el-input-number {
    width: 100%;
  }
}

@media (max-width: 960px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .table-toolbar,
  .filters {
    align-items: stretch;
    flex-direction: column;
  }

  .filters .el-input,
  .filters .el-select {
    width: 100%;
  }
}
</style>
