<template>
  <div class="monitoring-page" v-loading="pageLoading">
    <header class="monitoring-hero">
      <div>
        <span class="eyebrow">OBSERVABILITY / X35</span>
        <h2>全维度监控与告警</h2>
        <p>统一查看模型性能、数据质量、知识时效和系统资源；异常自动进入右上角全局告警铃铛。</p>
      </div>
      <div class="hero-actions">
        <el-button :icon="Refresh" @click="loadAll">刷新</el-button>
        <el-button type="primary" :icon="DataAnalysis" :loading="collecting" @click="collectNow">
          立即采集
        </el-button>
      </div>
    </header>

    <section class="summary-grid">
      <article>
        <span>监控指标</span>
        <strong>{{ dashboard.summary.metric_count }}</strong>
        <small>四个监控维度统一采集</small>
      </article>
      <article :class="{ attention: dashboard.summary.active_alert_count }">
        <span>活动告警</span>
        <strong>{{ dashboard.summary.active_alert_count }}</strong>
        <small>{{ dashboard.summary.critical_alert_count }} 条紧急告警</small>
      </article>
      <article>
        <span>启用规则</span>
        <strong>{{ enabledRuleCount }}</strong>
        <small>共 {{ dashboard.summary.rule_count }} 条规则</small>
      </article>
      <article>
        <span>最近采集</span>
        <strong class="summary-time">{{ lastCollectedAt }}</strong>
        <small>{{ dashboard.latest_run?.status || '尚未采集' }}</small>
      </article>
    </section>

    <el-alert
      v-if="dashboard.latest_run?.error_message"
      :title="dashboard.latest_run.error_message"
      type="warning"
      show-icon
      :closable="false"
      class="run-warning"
    />

    <section class="dimension-grid">
      <article v-for="group in dashboard.scopes" :key="group.scope" class="dimension-card">
        <header>
          <div>
            <span>{{ scopeCodes[group.scope] }}</span>
            <strong>{{ group.scope_label }}</strong>
          </div>
          <el-tag :type="scopeTagType(group.metrics)" effect="plain">{{ scopeStatus(group.metrics) }}</el-tag>
        </header>
        <el-empty v-if="!group.metrics.length" :image-size="50" description="等待首次采集" />
        <div v-else class="metric-list">
          <div v-for="metric in group.metrics" :key="metric.id" class="metric-row">
            <div>
              <i :class="`status-${metric.status.toLowerCase()}`" />
              <span>{{ metric.metric_name }}</span>
            </div>
            <strong>{{ formatMetricValue(metric) }}</strong>
            <div class="trend" :aria-label="`${metric.metric_name}近期趋势`">
              <b
                v-for="(point, index) in trendPoints(metric.metric_key)"
                :key="`${metric.metric_key}-${index}`"
                :style="{ height: `${trendHeight(metric.metric_key, point.value)}%` }"
              />
            </div>
          </div>
        </div>
      </article>
    </section>

    <el-card shadow="never" class="workbench">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="`活动告警 ${activeAlerts.length}`" name="alerts">
          <div class="table-toolbar">
            <div>
              <strong>异常响应闭环</strong>
              <span>确认、恢复和自动响应结果均在这里留痕</span>
            </div>
            <el-select v-model="alertStatus" clearable placeholder="全部状态" @change="loadAlerts">
              <el-option label="待处理" value="OPEN" />
              <el-option label="已确认" value="ACKNOWLEDGED" />
              <el-option label="已恢复" value="RESOLVED" />
            </el-select>
          </div>
          <el-table :data="alerts" stripe>
            <el-table-column label="告警" min-width="260">
              <template #default="{ row }">
                <div class="primary-cell">
                  <strong>{{ row.title }}</strong>
                  <span>{{ row.message }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="维度" width="110">
              <template #default="{ row }">{{ row.scope_label }}</template>
            </el-table-column>
            <el-table-column label="级别" width="90">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.severity)" effect="plain">{{ statusLabel(row.severity) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="自动响应" min-width="180">
              <template #default="{ row }">
                <div class="response-cell">
                  <strong>{{ getAutoActionLabel(row.auto_action) }}</strong>
                  <span>{{ responseStatusLabel(row.response_status) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="最近触发" width="170">
              <template #default="{ row }">{{ datetimeFormat(row.last_triggered_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status === 'OPEN'"
                  link
                  type="primary"
                  @click="operateAlert(row, 'ACKNOWLEDGE')"
                >确认</el-button>
                <el-button
                  v-if="row.status !== 'RESOLVED'"
                  link
                  type="success"
                  @click="operateAlert(row, 'RESOLVE')"
                >标记恢复</el-button>
                <el-button
                  v-if="row.response_status === 'FAILED'"
                  link
                  type="warning"
                  @click="operateAlert(row, 'RETRY_RESPONSE')"
                >重试响应</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!alerts.length" description="当前筛选条件下没有告警" />
        </el-tab-pane>

        <el-tab-pane :label="`监控规则 ${rules.length}`" name="rules">
          <div class="table-toolbar">
            <div>
              <strong>阈值与自动响应</strong>
              <span>默认规则覆盖四个维度，可继续添加业务规则</span>
            </div>
            <el-button type="primary" :icon="Plus" @click="openRuleDialog()">新增规则</el-button>
          </div>
          <el-table :data="rules" stripe>
            <el-table-column label="规则" min-width="220">
              <template #default="{ row }">
                <div class="primary-cell"><strong>{{ row.name }}</strong><span>{{ row.metric_name }}</span></div>
              </template>
            </el-table-column>
            <el-table-column prop="scope_label" label="维度" width="110" />
            <el-table-column label="触发条件" min-width="180">
              <template #default="{ row }">
                {{ row.operator_label }} {{ row.warning_threshold ?? '—' }} / {{ row.critical_threshold ?? '—' }}
              </template>
            </el-table-column>
            <el-table-column label="自动响应" min-width="170">
              <template #default="{ row }">{{ row.auto_action_label }}</template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" @change="toggleRule(row)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90">
              <template #default="{ row }"><el-button link type="primary" @click="openRuleDialog(row)">编辑</el-button></template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="ruleDialogVisible" :title="editingRuleId ? '编辑监控规则' : '新增监控规则'" width="620px">
      <el-form ref="ruleFormRef" :model="ruleForm" :rules="ruleFormRules" label-position="top">
        <el-form-item label="规则名称" prop="name"><el-input v-model="ruleForm.name" maxlength="128" /></el-form-item>
        <el-form-item label="监控指标" prop="metric_key">
          <el-select v-model="ruleForm.metric_key" filterable :disabled="Boolean(editingRuleId)">
            <el-option-group v-for="group in metricOptions" :key="group.label" :label="group.label">
              <el-option v-for="item in group.options" :key="item.value" :label="item.label" :value="item.value" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="比较方式" prop="operator">
            <el-select v-model="ruleForm.operator">
              <el-option label="大于" value="GT" /><el-option label="大于等于" value="GTE" />
              <el-option label="小于" value="LT" /><el-option label="小于等于" value="LTE" />
            </el-select>
          </el-form-item>
          <el-form-item label="自动响应">
            <el-select v-model="ruleForm.auto_action">
              <el-option v-for="(label, value) in autoActionLabels" :key="value" :label="label" :value="value" />
            </el-select>
          </el-form-item>
          <el-form-item label="关注阈值"><el-input-number v-model="ruleForm.warning_threshold" /></el-form-item>
          <el-form-item label="紧急阈值"><el-input-number v-model="ruleForm.critical_threshold" /></el-form-item>
          <el-form-item label="冷却时间（分钟）">
            <el-input-number v-model="ruleForm.cooldown_minutes" :min="1" :max="10080" />
          </el-form-item>
          <el-form-item label="启用"><el-switch v-model="ruleForm.enabled" /></el-form-item>
        </div>
        <el-form-item label="说明"><el-input v-model="ruleForm.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingRule" @click="saveRule">保存规则</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { DataAnalysis, Plus, Refresh } from '@element-plus/icons-vue'

import {
  collectMonitoringMetrics,
  createMonitoringRule,
  getMonitoringAlerts,
  getMonitoringDashboard,
  getMonitoringRules,
  operateMonitoringAlert,
  updateMonitoringRule,
  type MonitoringAlert,
  type MonitoringAutoAction,
  type MonitoringDashboard,
  type MonitoringMetric,
  type MonitoringRule,
  type MonitoringRuleWriteRequest,
  type MonitoringScope,
  type MonitoringStatus,
} from '@/api/platform-monitoring'
import { datetimeFormat } from '@/utils/time'

const emptyDashboard = (): MonitoringDashboard => ({
  latest_run: null,
  scopes: [
    { scope: 'MODEL', scope_label: '模型性能', metrics: [] },
    { scope: 'DATA', scope_label: '数据质量', metrics: [] },
    { scope: 'KNOWLEDGE', scope_label: '知识时效', metrics: [] },
    { scope: 'RESOURCE', scope_label: '系统资源', metrics: [] },
  ],
  trends: {},
  summary: { metric_count: 0, active_alert_count: 0, critical_alert_count: 0, rule_count: 0 },
})

const dashboard = ref<MonitoringDashboard>(emptyDashboard())
const rules = ref<MonitoringRule[]>([])
const alerts = ref<MonitoringAlert[]>([])
const pageLoading = ref(false)
const collecting = ref(false)
const savingRule = ref(false)
const activeTab = ref('alerts')
const alertStatus = ref('')
const ruleDialogVisible = ref(false)
const editingRuleId = ref('')
const ruleFormRef = ref<FormInstance>()

const scopeCodes: Record<MonitoringScope, string> = { MODEL: '01', DATA: '02', KNOWLEDGE: '03', RESOURCE: '04' }
const autoActionLabels: Record<MonitoringAutoAction, string> = {
  NONE: '仅告警',
  RETRY_FAILED_RUN: '重试最近失败任务',
  CREATE_ROLLBACK_TASK: '生成回滚任务',
}
const metricOptions = [
  { label: '模型性能', options: [
    { value: 'model_pipeline_success_rate', label: '训练流水线成功率' },
    { value: 'model_pipeline_failure_count', label: '训练流水线失败数' },
    { value: 'model_evaluation_pass_rate', label: '模型评估通过率' },
    { value: 'published_model_count', label: '已发布模型版本' },
  ] },
  { label: '数据质量', options: [
    { value: 'etl_success_rate', label: 'ETL 成功率' },
    { value: 'etl_failure_count', label: 'ETL 失败数' },
    { value: 'etl_quality_score', label: 'ETL 平均质量分' },
    { value: 'index_embedding_coverage', label: '索引向量覆盖率' },
  ] },
  { label: '知识时效', options: [
    { value: 'knowledge_active_document_count', label: '有效知识文档' },
    { value: 'knowledge_stale_days', label: '知识最长未更新时间' },
    { value: 'knowledge_retrieval_hit_rate', label: '检索评估命中率' },
    { value: 'published_index_count', label: '已发布索引版本' },
  ] },
  { label: '系统资源', options: [
    { value: 'backend_available', label: '后端服务' }, { value: 'database_available', label: 'PostgreSQL' },
    { value: 'redis_available', label: 'Redis' }, { value: 'ollama_available', label: 'Ollama' },
    { value: 'vector_service_available', label: '向量服务' },
  ] },
]

const initialRuleForm = (): MonitoringRuleWriteRequest => ({
  name: '', metric_key: 'model_pipeline_failure_count', operator: 'GTE', warning_threshold: 1,
  critical_threshold: 3, enabled: true, auto_action: 'NONE', cooldown_minutes: 30, description: '',
})
const ruleForm = ref<MonitoringRuleWriteRequest>(initialRuleForm())
const ruleFormRules: FormRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  metric_key: [{ required: true, message: '请选择监控指标', trigger: 'change' }],
  operator: [{ required: true, message: '请选择比较方式', trigger: 'change' }],
}

const enabledRuleCount = computed(() => rules.value.filter((row) => row.enabled).length)
const activeAlerts = computed(() => alerts.value.filter((row) => row.status !== 'RESOLVED'))
const lastCollectedAt = computed(() => dashboard.value.latest_run?.finished_at
  ? datetimeFormat(dashboard.value.latest_run.finished_at) : '—')

function statusTagType(status: MonitoringStatus) {
  return status === 'CRITICAL' ? 'danger' : status === 'WARNING' ? 'warning' : 'success'
}
function statusLabel(status: MonitoringStatus) {
  return { HEALTHY: '正常', WARNING: '关注', CRITICAL: '紧急', UNKNOWN: '未知' }[status]
}
function scopeTagType(metrics: MonitoringMetric[]) {
  return statusTagType(metrics.some((item) => item.status === 'CRITICAL') ? 'CRITICAL'
    : metrics.some((item) => item.status === 'WARNING') ? 'WARNING' : 'HEALTHY')
}
function scopeStatus(metrics: MonitoringMetric[]) {
  if (!metrics.length) return '待采集'
  if (metrics.some((item) => item.status === 'CRITICAL')) return '存在紧急异常'
  if (metrics.some((item) => item.status === 'WARNING')) return '需要关注'
  return '运行正常'
}
function formatMetricValue(metric: MonitoringMetric) {
  if (metric.scope === 'RESOURCE') return metric.value === 1 ? '在线' : '离线'
  return `${Number.isInteger(metric.value) ? metric.value : metric.value.toFixed(2)}${metric.unit}`
}
function trendPoints(metricKey: string) { return [...(dashboard.value.trends[metricKey] || [])].reverse().slice(-8) }
function trendHeight(metricKey: string, value: number) {
  const values = trendPoints(metricKey).map((item) => item.value)
  const max = Math.max(...values, 1)
  return Math.max(15, Math.round(value * 100 / max))
}
function responseStatusLabel(status: string) {
  return { NOT_REQUIRED: '无需自动响应', TASK_CREATED: '任务已生成', SUCCEEDED: '自动响应成功',
    FAILED: '自动响应失败', SKIPPED: '暂无可执行任务' }[status] || status
}
function getAutoActionLabel(action: MonitoringAutoAction | string) {
  return autoActionLabels[action as MonitoringAutoAction] || action
}

async function loadDashboard() { dashboard.value = (await getMonitoringDashboard()).data }
async function loadRules() { rules.value = (await getMonitoringRules()).data }
async function loadAlerts() { alerts.value = (await getMonitoringAlerts(alertStatus.value)).data }
async function loadAll() {
  pageLoading.value = true
  try { await Promise.all([loadDashboard(), loadRules(), loadAlerts()]) } finally { pageLoading.value = false }
}
async function collectNow() {
  const result = await collectMonitoringMetrics(collecting)
  dashboard.value = result.data
  await Promise.all([loadRules(), loadAlerts()])
  window.dispatchEvent(new CustomEvent('marketing-notification-updated'))
  ElMessage.success('四个维度采集完成')
}
function openRuleDialog(row?: MonitoringRule) {
  editingRuleId.value = row?.id || ''
  ruleForm.value = row ? {
    name: row.name, metric_key: row.metric_key, operator: row.operator,
    warning_threshold: row.warning_threshold, critical_threshold: row.critical_threshold,
    enabled: row.enabled, auto_action: row.auto_action, cooldown_minutes: row.cooldown_minutes,
    description: row.description,
  } : initialRuleForm()
  ruleDialogVisible.value = true
}
async function saveRule() {
  if (!await ruleFormRef.value?.validate()) return
  const request = editingRuleId.value
    ? updateMonitoringRule(editingRuleId.value, ruleForm.value, savingRule)
    : createMonitoringRule(ruleForm.value, savingRule)
  await request
  ruleDialogVisible.value = false
  await loadRules()
  ElMessage.success('监控规则已保存')
}
async function toggleRule(row: MonitoringRule) {
  await updateMonitoringRule(row.id, { enabled: row.enabled })
  ElMessage.success(row.enabled ? '规则已启用' : '规则已停用')
}
async function operateAlert(row: MonitoringAlert, action: 'ACKNOWLEDGE' | 'RESOLVE' | 'RETRY_RESPONSE') {
  await operateMonitoringAlert(row.id, action)
  await Promise.all([loadDashboard(), loadAlerts()])
  ElMessage.success(action === 'ACKNOWLEDGE' ? '告警已确认' : action === 'RESOLVE' ? '告警已恢复' : '自动响应已重试')
}

onMounted(loadAll)
</script>

<style scoped lang="scss">
.monitoring-page {
  --ink: #16313c;
  --muted: #667b84;
  --line: #dde6e9;
  height: 100%;
  padding: 22px 26px 36px;
  overflow-y: auto;
  color: var(--ink);
  background: #f4f7f7;
}
.monitoring-hero, .monitoring-hero > div, .hero-actions, .dimension-card header,
.dimension-card header > div, .metric-row > div, .table-toolbar { display: flex; align-items: center; }
.monitoring-hero { justify-content: space-between; gap: 24px; margin-bottom: 18px; }
.monitoring-hero > div:first-child { align-items: flex-start; flex-direction: column; }
.monitoring-hero h2 { margin: 5px 0 2px; font-size: 27px; letter-spacing: -.5px; }
.monitoring-hero p { margin: 0; color: var(--muted); }
.eyebrow { color: #087d74; font-family: monospace; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
.hero-actions { gap: 8px; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px; }
.summary-grid article, .dimension-card { border: 1px solid var(--line); border-radius: 7px; background: #fff; }
.summary-grid article { padding: 16px 18px; }
.summary-grid span, .summary-grid small { display: block; color: var(--muted); }
.summary-grid strong { display: block; margin: 8px 0 4px; font-size: 29px; }
.summary-grid .summary-time { font-size: 15px; font-family: monospace; }
.summary-grid article.attention { border-top: 3px solid #d98232; }
.run-warning { margin-bottom: 12px; }
.dimension-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 12px; }
.dimension-card { padding: 16px 18px; }
.dimension-card header { justify-content: space-between; padding-bottom: 11px; border-bottom: 1px solid var(--line); }
.dimension-card header > div { gap: 9px; }
.dimension-card header span:first-child { color: #0d857a; font-family: monospace; font-weight: 700; }
.metric-list { padding-top: 4px; }
.metric-row { display: grid; grid-template-columns: minmax(160px, 1fr) 90px 86px; align-items: center; gap: 10px; min-height: 43px; border-bottom: 1px dashed #e4eaec; }
.metric-row:last-child { border-bottom: 0; }
.metric-row > div:first-child { gap: 8px; }
.metric-row i { width: 7px; height: 7px; border-radius: 50%; background: #1a9b78; }
.metric-row i.status-warning { background: #d98b2b; }
.metric-row i.status-critical { background: #d54b45; box-shadow: 0 0 0 4px #f9e4e1; }
.metric-row > strong { text-align: right; font-family: monospace; }
.trend { display: flex; align-items: flex-end; justify-content: flex-end; gap: 3px; height: 26px; }
.trend b { width: 6px; min-height: 4px; border-radius: 1px 1px 0 0; background: #77aaa7; }
.workbench { border-color: var(--line); }
.table-toolbar { justify-content: space-between; gap: 18px; margin-bottom: 14px; }
.table-toolbar > div { display: grid; gap: 3px; }
.table-toolbar span, .primary-cell span, .response-cell span { color: var(--muted); font-size: 12px; }
.table-toolbar .el-select { width: 150px; }
.primary-cell, .response-cell { display: grid; gap: 4px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }
.el-select, .el-input-number { width: 100%; }
@media (max-width: 1000px) { .summary-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 760px) {
  .monitoring-page { padding: 16px; }
  .monitoring-hero { align-items: flex-start; flex-direction: column; }
  .summary-grid, .dimension-grid, .form-grid { grid-template-columns: 1fr; }
  .metric-row { grid-template-columns: minmax(130px, 1fr) 74px; }
  .trend { display: none; }
}
</style>
