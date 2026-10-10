<template>
  <div class="pipeline-workbench">
    <div class="table-toolbar">
      <div>
        <strong>自动训练与部署流水线</strong>
        <p>串联特征处理、训练、评估、审批和部署，支持 Cron 定时重训。</p>
      </div>
      <div>
        <el-button :icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="dialogVisible = true">新建流水线</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="pipelines" stripe>
      <el-table-column label="流水线" min-width="210">
        <template #default="{ row }">
          <div class="primary-cell">
            <strong>{{ row.name }}</strong>
            <span>{{ row.registry_name }} · {{ row.dataset_name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="发布策略" width="150">
        <template #default="{ row }">
          <el-tag effect="plain" :type="row.approval_mode === 'AUTO' ? 'success' : 'warning'">
            {{ row.approval_mode_label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="定时重训" min-width="190">
        <template #default="{ row }">
          <span v-if="row.schedule_enabled">{{ row.cron_expression }}</span>
          <span v-else>未启用</span>
          <small v-if="row.next_run_at">下次：{{ formatDate(row.next_run_at) }}</small>
        </template>
      </el-table-column>
      <el-table-column label="最近运行" width="180">
        <template #default="{ row }">{{ formatDate(row.last_run_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="!row.active" @click="startRun(row)">立即运行</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!pipelines.length && !loading" description="还没有自动训练流水线" />

    <div class="run-header">
      <strong>运行记录</strong>
      <span>保留每个阶段的输入、输出和错误信息</span>
    </div>
    <el-table v-loading="loading" :data="runs" stripe>
      <el-table-column label="运行" min-width="200">
        <template #default="{ row }">
          <div class="primary-cell">
            <strong>{{ row.pipeline_name }} #{{ row.run_number }}</strong>
            <span>{{ row.trigger_label }} · {{ formatDate(row.started_at || row.create_time) }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="当前阶段" width="130">
        <template #default="{ row }">{{ row.current_stage_label }}</template>
      </el-table-column>
      <el-table-column label="状态" width="130">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" effect="plain">{{ row.status_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="模型版本" width="120">
        <template #default="{ row }">{{ row.model_version_label || '—' }}</template>
      </el-table-column>
      <el-table-column label="异常" min-width="180">
        <template #default="{ row }">{{ row.error_message || '—' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <template v-if="row.status === 'WAITING_APPROVAL'">
            <el-button link type="success" @click="approveRun(row, 'APPROVE')">通过</el-button>
            <el-button link type="danger" @click="approveRun(row, 'REJECT')">拒绝</el-button>
          </template>
          <el-button
            v-if="['FAILED', 'REJECTED'].includes(row.status)"
            link
            type="warning"
            @click="retryRun(row)"
          >
            重试
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新建自动训练流水线" width="700px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid">
          <el-form-item label="流水线名称" prop="name"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="注册模型名称" prop="registry_name"><el-input v-model="form.registry_name" /></el-form-item>
          <el-form-item label="数据集名称" prop="dataset_name"><el-input v-model="form.dataset_name" /></el-form-item>
          <el-form-item label="数据集版本"><el-input v-model="form.dataset_version" /></el-form-item>
          <el-form-item label="评估准确率"><el-input-number v-model="form.accuracy" :min="0" :max="1" :step="0.01" /></el-form-item>
          <el-form-item label="准确率下限"><el-input-number v-model="form.min_accuracy" :min="0" :max="1" :step="0.01" /></el-form-item>
          <el-form-item label="评估延迟（ms）"><el-input-number v-model="form.latency_ms" :min="0" :step="10" /></el-form-item>
          <el-form-item label="延迟上限（ms）"><el-input-number v-model="form.max_latency_ms" :min="0" :step="10" /></el-form-item>
          <el-form-item label="审批模式">
            <el-radio-group v-model="form.approval_mode">
              <el-radio value="MANUAL">人工审批</el-radio>
              <el-radio value="AUTO">自动审批</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="审批后部署"><el-switch v-model="form.auto_deploy" /></el-form-item>
          <el-form-item label="定时重训"><el-switch v-model="form.schedule_enabled" /></el-form-item>
          <el-form-item v-if="form.schedule_enabled" label="Cron 表达式" prop="cron_expression">
            <el-input v-model="form.cron_expression" placeholder="例如：0 2 * * *" />
          </el-form-item>
        </div>
        <el-form-item label="说明"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitPipeline">创建流水线</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawerVisible" title="流水线运行详情" size="580px">
      <div v-if="selectedRun" class="run-detail">
        <el-alert
          :title="`${selectedRun.pipeline_name} #${selectedRun.run_number} · ${selectedRun.status_label}`"
          :description="selectedRun.error_message || '各阶段执行信息如下'"
          :type="selectedRun.status === 'FAILED' ? 'error' : 'info'"
          :closable="false"
        />
        <el-timeline>
          <el-timeline-item
            v-for="stage in selectedRun.stages"
            :key="stage.id"
            :type="stageType[stage.status]"
            :timestamp="formatDate(stage.finished_at || stage.started_at)"
          >
            <strong>{{ stage.stage_label }} · {{ stage.status_label }}</strong>
            <p v-if="stage.error_message">{{ stage.error_message }}</p>
            <pre v-if="Object.keys(stage.output_snapshot).length">{{ pretty(stage.output_snapshot) }}</pre>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import {
  approveModelPipelineRun,
  createModelPipeline,
  getModelPipelineRun,
  getModelPipelineRuns,
  getModelPipelines,
  retryModelPipelineRun,
  startModelPipeline,
} from '@/api/model/pipeline'
import type {
  ModelPipelineRun,
  ModelTrainingPipeline,
  PipelineRunStatus,
  PipelineStageStatus,
} from '@/api/type/model-pipeline'

type TagType = '' | 'success' | 'warning' | 'info' | 'primary' | 'danger'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const formRef = ref<FormInstance>()
const pipelines = ref<ModelTrainingPipeline[]>([])
const runs = ref<ModelPipelineRun[]>([])
const selectedRun = ref<ModelPipelineRun>()
const statusType: Record<PipelineRunStatus, TagType> = {
  PENDING: 'info', RUNNING: 'primary', WAITING_APPROVAL: 'warning', SUCCESS: 'success', FAILED: 'danger', REJECTED: 'danger',
}
const getStatusType = (status: PipelineRunStatus) => statusType[status]
const stageType: Record<PipelineStageStatus, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  PENDING: 'info', RUNNING: 'primary', SUCCESS: 'success', FAILED: 'danger', SKIPPED: 'warning',
}
const defaultForm = () => ({
  name: '', description: '', registry_name: '', dataset_name: '', dataset_version: '',
  accuracy: 0.92, min_accuracy: 0.9, latency_ms: 90, max_latency_ms: 120,
  approval_mode: 'MANUAL' as const, auto_deploy: true, schedule_enabled: false, cron_expression: '',
})
const form = ref(defaultForm())
const rules: FormRules = {
  name: [{ required: true, message: '请输入流水线名称', trigger: 'blur' }],
  registry_name: [{ required: true, message: '请输入注册模型名称', trigger: 'blur' }],
  dataset_name: [{ required: true, message: '请输入数据集名称', trigger: 'blur' }],
  cron_expression: [{ validator: (_rule, value, callback) => {
    if (form.value.schedule_enabled && !value) callback(new Error('请输入 Cron 表达式'))
    else callback()
  }, trigger: 'blur' }],
}

const formatDate = (value?: string | null) => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '—'
const pretty = (value: Record<string, unknown>) => JSON.stringify(value, null, 2)
const loadData = async () => {
  const [pipelineResponse, runResponse] = await Promise.all([getModelPipelines(loading), getModelPipelineRuns()])
  pipelines.value = pipelineResponse.data
  runs.value = runResponse.data
}
const submitPipeline = async () => {
  await formRef.value?.validate()
  await createModelPipeline({
    name: form.value.name, description: form.value.description, registry_name: form.value.registry_name,
    dataset_name: form.value.dataset_name, dataset_version: form.value.dataset_version,
    parameters: {}, evaluation_metrics: { accuracy: form.value.accuracy, latency_ms: form.value.latency_ms },
    thresholds: { accuracy: { min: form.value.min_accuracy }, latency_ms: { max: form.value.max_latency_ms } },
    approval_mode: form.value.approval_mode, auto_deploy: form.value.auto_deploy,
    schedule_enabled: form.value.schedule_enabled, cron_expression: form.value.cron_expression,
  }, submitLoading)
  dialogVisible.value = false
  form.value = defaultForm()
  ElMessage.success('流水线创建成功')
  await loadData()
}
const startRun = async (row: ModelTrainingPipeline) => {
  await startModelPipeline(row.id, submitLoading)
  ElMessage.success('流水线运行完成')
  await loadData()
}
const openDetail = async (row: ModelPipelineRun) => {
  selectedRun.value = (await getModelPipelineRun(row.id, loading)).data
  drawerVisible.value = true
}
const approveRun = async (row: ModelPipelineRun, action: 'APPROVE' | 'REJECT') => {
  const label = action === 'APPROVE' ? '通过' : '拒绝'
  const { value } = await ElMessageBox.prompt(`请输入${label}意见`, `${label}发布审批`, { inputPlaceholder: '审批意见' })
  await approveModelPipelineRun(row.id, action, value, submitLoading)
  ElMessage.success(`审批已${label}`)
  await loadData()
}
const retryRun = async (row: ModelPipelineRun) => {
  await retryModelPipelineRun(row.id, submitLoading)
  ElMessage.success('已完成重试')
  await loadData()
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.pipeline-workbench { min-width: 0; }
.table-toolbar, .run-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.table-toolbar p, .run-header span { margin: 4px 0 0; color: var(--el-text-color-secondary); font-size: 13px; }
.run-header { margin: 28px 0 12px; }
.primary-cell { display: flex; flex-direction: column; }
.primary-cell span, .el-table-column small { color: var(--el-text-color-secondary); font-size: 12px; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 18px; }
.form-grid :deep(.el-input-number) { width: 100%; }
.run-detail :deep(.el-alert) { margin-bottom: 24px; }
.run-detail pre { max-height: 180px; overflow: auto; padding: 10px; border-radius: 6px; background: var(--el-fill-color-light); font-size: 12px; }
@media (max-width: 900px) { .form-grid { grid-template-columns: 1fr; } }
</style>
