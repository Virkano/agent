<template>
  <section class="control-workbench">
    <div class="control-heading">
      <div>
        <div class="section-kicker">M09-03 / CONTROL & REPORT</div>
        <h3>事中提醒、割接告知与质量报告</h3>
        <p>发送记录进入右上角全局铃铛；开始与完成操作受提醒告知门禁控制。</p>
      </div>
      <el-button :loading="loading" @click="loadDashboard">刷新管控台</el-button>
    </div>

    <div class="control-summary-grid">
      <article v-for="item in summaryCards" :key="item.label" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </div>

    <div class="control-main-grid">
      <el-card shadow="never" class="operation-card">
        <template #header>
          <div class="card-heading">
            <div>
              <strong>执行管控台账</strong>
              <span>变更前通知 → 开始执行 → 事中提醒 → 完成或终止</span>
            </div>
          </div>
        </template>
        <el-table v-loading="loading" :data="dashboard.operations" row-key="id" max-height="430">
          <el-table-column label="变更操作" min-width="220">
            <template #default="{ row }">
              <div class="cell-primary">{{ row.name }}</div>
              <div class="cell-secondary">{{ row.code }}</div>
            </template>
          </el-table-column>
          <el-table-column label="风险" width="105" align="center">
            <template #default="{ row }">
              <el-tag :type="getRiskType(row.risk_level)">
                {{ row.risk_level_label }} {{ row.risk_score }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="执行状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getControlType(row.control_status)">
                {{ row.control_status_label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="提醒 / 待发" width="110" align="center">
            <template #default="{ row }">
              {{ row.communication_count }} / {{ row.pending_communication_count }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="openOperation(row.id)">进入管控</el-button>
            </template>
          </el-table-column>
          <template #empty><el-empty description="暂无可管控的变更操作" /></template>
        </el-table>
      </el-card>

      <el-card shadow="never" class="report-card">
        <template #header>
          <div class="card-heading">
            <div>
              <strong>周期质量报告</strong>
              <span>生成后可按日期下钻，并导出 CSV / PDF</span>
            </div>
          </div>
        </template>
        <el-date-picker
          v-model="reportRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          class="full-width"
        />
        <el-input v-model="reportTitle" class="report-title" placeholder="报告标题（可选）" />
        <el-button
          type="primary"
          class="full-width"
          :loading="generatingReport"
          @click="handleGenerateReport"
        >
          生成质量报告
        </el-button>
        <div class="recent-report-title">最近报告</div>
        <div v-if="dashboard.reports.length" class="report-list">
          <article v-for="report in dashboard.reports" :key="report.id">
            <button type="button" @click="openReport(report.id)">
              <strong>{{ report.title }}</strong>
              <span>{{ report.period_start }} 至 {{ report.period_end }}</span>
            </button>
            <el-dropdown @command="handleReportDownloadCommand($event, report.id)">
              <el-button link type="primary">导出</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="csv">CSV</el-dropdown-item>
                  <el-dropdown-item command="pdf">PDF</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </article>
        </div>
        <el-empty v-else :image-size="70" description="尚未生成质量报告" />
      </el-card>
    </div>

    <el-drawer v-model="operationDrawerVisible" size="760px" destroy-on-close>
      <template #header>
        <div v-if="selectedOperation" class="drawer-heading">
          <div>
            <strong>{{ selectedOperation.name }}</strong>
            <span>{{ selectedOperation.code }} · {{ selectedOperation.control_status_label }}</span>
          </div>
          <el-tag :type="getRiskType(selectedOperation.risk_level)">
            {{ selectedOperation.risk_level_label }} {{ selectedOperation.risk_score }} 分
          </el-tag>
        </div>
      </template>

      <div v-if="selectedOperation" v-loading="detailLoading" class="drawer-content">
        <section class="gate-strip">
          <div>
            <span>风险状态</span><strong>{{ selectedOperation.status_label }}</strong>
          </div>
          <div>
            <span>执行状态</span><strong>{{ selectedOperation.control_status_label }}</strong>
          </div>
          <div>
            <span>实际开始</span
            ><strong>{{ formatTime(selectedOperation.actual_start_at) }}</strong>
          </div>
          <div>
            <span>完成 / 终止</span
            ><strong>{{ formatTime(selectedOperation.completed_at) }}</strong>
          </div>
        </section>

        <el-alert
          :type="gateAlert.type"
          :closable="false"
          show-icon
          :title="gateAlert.title"
          class="gate-alert"
        />

        <section class="control-actions">
          <el-button
            type="primary"
            :disabled="selectedOperation.control_status !== 'NOT_STARTED'"
            :loading="controlling"
            @click="handleControl('START')"
          >
            开始执行
          </el-button>
          <el-button
            type="success"
            :disabled="selectedOperation.control_status !== 'IN_PROGRESS'"
            :loading="controlling"
            @click="handleControl('COMPLETE')"
          >
            完成变更
          </el-button>
          <el-button
            type="danger"
            plain
            :disabled="!canAbort"
            :loading="controlling"
            @click="handleControl('ABORT')"
          >
            终止变更
          </el-button>
        </section>

        <el-card shadow="never" class="communication-form-card">
          <template #header>
            <div class="card-heading">
              <div>
                <strong>新增提醒或告知</strong>
                <span>站内发送后同步进入全局通知铃铛</span>
              </div>
            </div>
          </template>
          <el-form label-position="top" :model="communicationForm">
            <div class="form-grid">
              <el-form-item label="事件类型">
                <el-select v-model="communicationForm.kind" class="full-width">
                  <el-option label="管控提醒" value="CONTROL_REMINDER" />
                  <el-option label="割接告知" value="CUTOVER_NOTICE" />
                </el-select>
              </el-form-item>
              <el-form-item label="阶段">
                <el-select v-model="communicationForm.phase" class="full-width">
                  <el-option label="变更前" value="BEFORE" />
                  <el-option label="执行中" value="DURING" />
                  <el-option label="完成后" value="AFTER" />
                </el-select>
              </el-form-item>
              <el-form-item label="接收对象">
                <el-select v-model="communicationForm.audience" class="full-width">
                  <el-option label="操作人员" value="OPERATOR" />
                  <el-option label="受影响客户" value="CUSTOMER" />
                </el-select>
              </el-form-item>
              <el-form-item label="渠道">
                <el-select v-model="communicationForm.channel" class="full-width">
                  <el-option label="站内通知" value="IN_APP" />
                  <el-option label="IVR 播报" value="IVR" />
                  <el-option label="短信" value="SMS" />
                  <el-option label="人工告知" value="MANUAL" />
                </el-select>
              </el-form-item>
            </div>
            <el-form-item label="主题">
              <el-input
                v-model="communicationForm.subject"
                placeholder="例如：割接前回退方案确认"
              />
            </el-form-item>
            <el-form-item label="内容">
              <el-input
                v-model="communicationForm.content"
                type="textarea"
                :rows="3"
                placeholder="填写核验要求、影响范围或客户可见告知"
              />
            </el-form-item>
            <el-button
              type="primary"
              :loading="creatingCommunication"
              @click="handleCreateCommunication"
            >
              保存为待发送
            </el-button>
          </el-form>
        </el-card>

        <section class="history-section">
          <div class="section-heading">
            <strong>提醒与告知记录</strong>
            <span>{{ selectedOperation.communications?.length || 0 }} 条</span>
          </div>
          <article
            v-for="item in selectedOperation.communications"
            :key="item.id"
            class="communication-item"
          >
            <div class="communication-head">
              <div>
                <el-tag size="small" :type="item.kind === 'CUTOVER_NOTICE' ? 'primary' : 'warning'">
                  {{ item.kind_label }}
                </el-tag>
                <strong>{{ item.subject }}</strong>
              </div>
              <el-tag size="small" :type="getCommunicationType(item.status)">
                {{ item.status_label }}
              </el-tag>
            </div>
            <p>{{ item.content }}</p>
            <div class="communication-meta">
              <span
                >{{ item.phase_label }} · {{ item.audience_label }} · {{ item.channel_label }}</span
              >
              <span>{{ formatTime(item.create_time) }}</span>
            </div>
            <div v-if="item.status !== 'ACKNOWLEDGED'" class="communication-actions">
              <el-button
                v-if="item.status === 'PENDING' || item.status === 'FAILED'"
                size="small"
                type="primary"
                @click="handleCommunicationStatus(item, 'SENT')"
              >
                {{ item.status === 'FAILED' ? '重新发送' : '标记已发送' }}
              </el-button>
              <el-button
                v-if="item.status === 'SENT'"
                size="small"
                type="success"
                @click="handleCommunicationStatus(item, 'ACKNOWLEDGED')"
              >
                标记已确认
              </el-button>
              <el-button
                v-if="item.status === 'PENDING' || item.status === 'SENT'"
                size="small"
                type="danger"
                plain
                @click="handleCommunicationStatus(item, 'FAILED')"
              >
                标记失败
              </el-button>
            </div>
          </article>
          <el-empty
            v-if="!selectedOperation.communications?.length"
            :image-size="72"
            description="尚无提醒或告知记录"
          />
        </section>

        <section v-if="selectedOperation.control_actions?.length" class="history-section">
          <div class="section-heading">
            <strong>执行操作轨迹</strong>
            <span>{{ selectedOperation.control_actions.length }} 步</span>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="action in selectedOperation.control_actions"
              :key="action.id"
              :timestamp="formatTime(action.create_time)"
              placement="top"
            >
              <strong>v{{ action.revision }} · {{ action.action_label }}</strong>
              <p>{{ action.previous_status_label }} → {{ action.current_status_label }}</p>
            </el-timeline-item>
          </el-timeline>
        </section>
      </div>
    </el-drawer>

    <el-drawer v-model="reportDrawerVisible" size="820px" destroy-on-close>
      <template #header>
        <div v-if="selectedReport" class="drawer-heading">
          <div>
            <strong>{{ selectedReport.title }}</strong>
            <span>{{ selectedReport.period_start }} 至 {{ selectedReport.period_end }}</span>
          </div>
          <el-dropdown @command="handleSelectedReportDownload">
            <el-button type="primary">导出报告</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="csv">CSV</el-dropdown-item>
                <el-dropdown-item command="pdf">PDF</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </template>
      <div v-if="selectedReport" v-loading="reportLoading" class="drawer-content">
        <div class="report-metric-grid">
          <article>
            <span>变更操作</span><strong>{{ selectedReport.metrics.operation_count }}</strong>
          </article>
          <article>
            <span>红灯变更</span><strong>{{ selectedReport.metrics.red_count }}</strong>
          </article>
          <article>
            <span>通信覆盖率</span
            ><strong>{{ selectedReport.metrics.communication_coverage_rate }}%</strong>
          </article>
          <article>
            <span>执行完成率</span
            ><strong>{{ selectedReport.metrics.control_completion_rate }}%</strong>
          </article>
        </div>
        <section class="history-section">
          <div class="section-heading">
            <strong>日期下钻</strong>
            <span>点击有数据的日期查看明细</span>
          </div>
          <el-table :data="activeTrend" max-height="280">
            <el-table-column prop="date" label="日期" width="130" />
            <el-table-column prop="operation_count" label="变更" width="80" align="center" />
            <el-table-column prop="red_count" label="红灯" width="80" align="center" />
            <el-table-column
              prop="communication_count"
              label="提醒告知"
              width="100"
              align="center"
            />
            <el-table-column prop="completed_count" label="完成" width="80" align="center" />
            <el-table-column label="操作" min-width="90">
              <template #default="{ row }">
                <el-button type="primary" link @click="openDrilldown(row.date)">下钻</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>
        <section v-if="drilldown" class="history-section drilldown-section">
          <div class="section-heading">
            <strong>{{ drilldown.date }} 变更明细</strong>
            <span>{{ drilldown.operations.length }} 条</span>
          </div>
          <article v-for="item in drilldown.operations" :key="item.id">
            <div>
              <strong>{{ item.name }}</strong>
              <el-tag :type="getRiskType(item.risk_level)" size="small">
                {{ item.risk_level_label }} {{ item.risk_score }}
              </el-tag>
            </div>
            <span
              >{{ item.code }} · {{ item.control_status_label }} ·
              {{ item.communication_count }} 条提醒告知</span
            >
          </article>
        </section>
      </div>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  controlChangeOperation,
  createChangeCommunication,
  downloadChangeQualityReport,
  generateChangeQualityReport,
  getChangeControlDashboard,
  getChangeControlOperation,
  getChangeQualityDrilldown,
  getChangeQualityReport,
  updateChangeCommunicationStatus,
  type ChangeCommunicationAudience,
  type ChangeCommunicationChannel,
  type ChangeCommunicationKind,
  type ChangeCommunicationPhase,
  type ChangeCommunicationStatus,
  type ChangeControlAction,
  type ChangeControlDashboard,
  type ChangeControlOperation,
  type ChangeControlStatus,
  type ChangeOperationCommunication,
  type ChangeQualityOperationSnapshot,
  type ChangeQualityReport,
  type ChangeQualityTrendItem,
  type ChangeRiskLevel,
} from '@/api/marketing/ivr'
import { datetimeFormat } from '@/utils/time'

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'
type ExportFormat = 'csv' | 'pdf'

interface DrilldownState {
  date: string
  summary: ChangeQualityTrendItem
  operations: ChangeQualityOperationSnapshot[]
}

const emptyDashboard: ChangeControlDashboard = {
  summary: {
    operation_count: 0,
    not_started_count: 0,
    in_progress_count: 0,
    completed_count: 0,
    aborted_count: 0,
    pending_communication_count: 0,
    failed_communication_count: 0,
    report_count: 0,
  },
  communication_counts: { PENDING: 0, SENT: 0, ACKNOWLEDGED: 0, FAILED: 0 },
  operations: [],
  reports: [],
}

const formatDate = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
const today = new Date()
const periodStart = new Date(today)
periodStart.setDate(periodStart.getDate() - 29)

const dashboard = ref<ChangeControlDashboard>(emptyDashboard)
const selectedOperation = ref<ChangeControlOperation | null>(null)
const selectedReport = ref<ChangeQualityReport | null>(null)
const drilldown = ref<DrilldownState | null>(null)
const loading = ref(false)
const detailLoading = ref(false)
const creatingCommunication = ref(false)
const communicationUpdating = ref(false)
const controlling = ref(false)
const generatingReport = ref(false)
const reportLoading = ref(false)
const downloading = ref(false)
const operationDrawerVisible = ref(false)
const reportDrawerVisible = ref(false)
const reportRange = ref<[string, string]>([formatDate(periodStart), formatDate(today)])
const reportTitle = ref('')
const communicationForm = ref({
  kind: 'CONTROL_REMINDER' as ChangeCommunicationKind,
  phase: 'BEFORE' as ChangeCommunicationPhase,
  audience: 'OPERATOR' as ChangeCommunicationAudience,
  channel: 'IN_APP' as ChangeCommunicationChannel,
  subject: '',
  content: '',
})

const summaryCards = computed(() => [
  {
    label: '执行中',
    value: dashboard.value.summary.in_progress_count,
    hint: '当前窗口',
    tone: 'primary',
  },
  {
    label: '已完成',
    value: dashboard.value.summary.completed_count,
    hint: '闭环变更',
    tone: 'success',
  },
  {
    label: '待发送提醒',
    value: dashboard.value.summary.pending_communication_count,
    hint: '需要处理',
    tone: 'warning',
  },
  { label: '质量报告', value: dashboard.value.summary.report_count, hint: '周期快照', tone: '' },
])
const canAbort = computed(() =>
  ['NOT_STARTED', 'IN_PROGRESS'].includes(selectedOperation.value?.control_status || ''),
)
const gateAlert = computed<{ type: 'success' | 'warning' | 'error' | 'info'; title: string }>(
  () => {
    if (!selectedOperation.value) return { type: 'info', title: '' }
    if (selectedOperation.value.confirmation_status === 'PENDING') {
      return { type: 'error', title: '红灯变更尚未人工确认，禁止开始执行。' }
    }
    if (selectedOperation.value.control_status === 'NOT_STARTED') {
      return { type: 'warning', title: '开始执行前必须至少发送一条“变更前”提醒或告知。' }
    }
    if (selectedOperation.value.control_status === 'IN_PROGRESS') {
      return { type: 'warning', title: '完成变更前必须至少发送一条“执行中”提醒或告知。' }
    }
    return {
      type: 'success',
      title: `变更已${selectedOperation.value.control_status === 'COMPLETED' ? '完成' : '终止'}，操作轨迹已留痕。`,
    }
  },
)
const activeTrend = computed(() =>
  (selectedReport.value?.daily_trend || []).filter(
    (item) => item.operation_count || item.communication_count || item.completed_count,
  ),
)

const getRiskType = (level: ChangeRiskLevel): TagType =>
  ({ RED: 'danger', YELLOW: 'warning', GREEN: 'success' })[level] as TagType
const getControlType = (status: ChangeControlStatus): TagType =>
  ({ NOT_STARTED: 'info', IN_PROGRESS: 'primary', COMPLETED: 'success', ABORTED: 'danger' })[
    status
  ] as TagType
const getCommunicationType = (status: ChangeCommunicationStatus): TagType =>
  ({ PENDING: 'warning', SENT: 'primary', ACKNOWLEDGED: 'success', FAILED: 'danger' })[
    status
  ] as TagType
const formatTime = (value: string | null) => (value ? datetimeFormat(value) : '—')
const makeRequestId = () =>
  `ui:change-communication:${Date.now()}:${Math.random().toString(36).slice(2, 9)}`

const loadDashboard = async () => {
  const result = await getChangeControlDashboard(loading)
  dashboard.value = result.data
}

const resetCommunicationForm = (status: ChangeControlStatus) => {
  communicationForm.value = {
    kind: status === 'NOT_STARTED' ? 'CONTROL_REMINDER' : 'CUTOVER_NOTICE',
    phase: status === 'NOT_STARTED' ? 'BEFORE' : status === 'IN_PROGRESS' ? 'DURING' : 'AFTER',
    audience: status === 'NOT_STARTED' ? 'OPERATOR' : 'CUSTOMER',
    channel: 'IN_APP',
    subject: '',
    content: '',
  }
}

const openOperation = async (operationId: string) => {
  operationDrawerVisible.value = true
  const result = await getChangeControlOperation(operationId, detailLoading)
  selectedOperation.value = result.data
  resetCommunicationForm(result.data.control_status)
}

const refreshSelectedOperation = async () => {
  if (!selectedOperation.value) return
  const result = await getChangeControlOperation(selectedOperation.value.id, detailLoading)
  selectedOperation.value = result.data
}

const handleCreateCommunication = async () => {
  if (!selectedOperation.value) return
  if (!communicationForm.value.subject.trim() || !communicationForm.value.content.trim()) {
    ElMessage.warning('请填写提醒或告知主题和内容')
    return
  }
  await createChangeCommunication(
    selectedOperation.value.id,
    {
      request_id: makeRequestId(),
      ...communicationForm.value,
      subject: communicationForm.value.subject.trim(),
      content: communicationForm.value.content.trim(),
    },
    creatingCommunication,
  )
  ElMessage.success('已保存为待发送记录')
  communicationForm.value.subject = ''
  communicationForm.value.content = ''
  await Promise.all([refreshSelectedOperation(), loadDashboard()])
}

const handleCommunicationStatus = async (
  item: ChangeOperationCommunication,
  status: 'SENT' | 'ACKNOWLEDGED' | 'FAILED',
) => {
  let failureReason = ''
  if (status === 'FAILED') {
    try {
      const prompt = await ElMessageBox.prompt('请填写发送失败原因', '标记发送失败', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        inputValidator: (value) => Boolean(value.trim()) || '失败原因不能为空',
      })
      failureReason = prompt.value.trim()
    } catch {
      return
    }
  }
  const result = await updateChangeCommunicationStatus(
    item.id,
    { status, failure_reason: failureReason },
    communicationUpdating,
  )
  ElMessage.success(
    status === 'SENT'
      ? `已发送，并写入 ${result.data.notification_count || 0} 条全局通知`
      : `状态已更新为${result.data.communication.status_label}`,
  )
  await Promise.all([refreshSelectedOperation(), loadDashboard()])
}

const handleControl = async (action: ChangeControlAction) => {
  if (!selectedOperation.value) return
  let note = ''
  try {
    if (action === 'ABORT') {
      const prompt = await ElMessageBox.prompt('请填写终止原因', '终止变更', {
        type: 'warning',
        confirmButtonText: '确认终止',
        cancelButtonText: '取消',
        inputValidator: (value) => Boolean(value.trim()) || '终止原因不能为空',
      })
      note = prompt.value.trim()
    } else {
      await ElMessageBox.confirm(
        action === 'START' ? '确认已完成变更前核验并开始执行？' : '确认执行结果正常并完成变更？',
        action === 'START' ? '开始执行' : '完成变更',
        { type: action === 'START' ? 'warning' : 'success' },
      )
    }
  } catch {
    return
  }
  const result = await controlChangeOperation(
    selectedOperation.value.id,
    { action, note },
    controlling,
  )
  ElMessage.success(result.data.action_record.action_label)
  await Promise.all([refreshSelectedOperation(), loadDashboard()])
}

const handleGenerateReport = async () => {
  if (!reportRange.value?.[0] || !reportRange.value?.[1]) {
    ElMessage.warning('请选择统计周期')
    return
  }
  const result = await generateChangeQualityReport(
    {
      title: reportTitle.value.trim() || undefined,
      period_start: reportRange.value[0],
      period_end: reportRange.value[1],
    },
    generatingReport,
  )
  reportTitle.value = ''
  ElMessage.success('质量报告已生成')
  await loadDashboard()
  await openReport(result.data.id)
}

const openReport = async (reportId: string) => {
  reportDrawerVisible.value = true
  drilldown.value = null
  const result = await getChangeQualityReport(reportId, reportLoading)
  selectedReport.value = result.data
}

const openDrilldown = async (date: string) => {
  if (!selectedReport.value) return
  const result = await getChangeQualityDrilldown(selectedReport.value.id, date, reportLoading)
  drilldown.value = result.data
}

const handleDownload = async (reportId: string, format: ExportFormat) => {
  await downloadChangeQualityReport(reportId, format, downloading)
  ElMessage.success(`${format.toUpperCase()} 报告已导出`)
}

const handleSelectedReportDownload = async (format: ExportFormat) => {
  if (!selectedReport.value) return
  await handleDownload(selectedReport.value.id, format)
}

const handleReportDownloadCommand = async (format: ExportFormat, reportId: string) => {
  await handleDownload(reportId, format)
}

onMounted(loadDashboard)
</script>

<style scoped lang="scss">
.control-workbench {
  margin-top: 22px;
  padding-top: 22px;
  border-top: 1px solid #dce3ed;
}

.control-heading,
.card-heading,
.drawer-heading,
.section-heading,
.communication-head,
.communication-meta,
.drilldown-section article > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.control-heading {
  margin-bottom: 16px;
}

.control-heading h3 {
  margin: 4px 0 5px;
  font-size: 22px;
}

.control-heading p {
  margin: 0;
  color: #64748b;
}

.section-kicker {
  color: #0f766e;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.control-summary-grid,
.report-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.control-summary-grid article,
.report-metric-grid article {
  padding: 15px 17px;
  border: 1px solid #e4eaf1;
  border-radius: 12px;
  background: #fff;
}

.control-summary-grid article.primary {
  border-color: #bfdbfe;
  background: #f5f9ff;
}

.control-summary-grid article.success {
  border-color: #bbf7d0;
  background: #f5fff8;
}

.control-summary-grid article.warning {
  border-color: #fde68a;
  background: #fffdf5;
}

.control-summary-grid span,
.control-summary-grid small,
.report-metric-grid span,
.card-heading span,
.drawer-heading span,
.gate-strip span,
.communication-meta,
.recent-report-title,
.report-list span,
.section-heading span,
.drilldown-section article > span {
  display: block;
  color: #8492a6;
}

.control-summary-grid strong,
.report-metric-grid strong {
  display: block;
  margin: 5px 0;
  font-size: 25px;
}

.control-main-grid {
  display: grid;
  grid-template-columns: minmax(650px, 1.45fr) minmax(340px, 0.55fr);
  gap: 16px;
}

.card-heading > div > strong,
.drawer-heading > div > strong {
  display: block;
  margin-bottom: 4px;
}

.cell-primary {
  font-weight: 600;
}

.cell-secondary {
  margin-top: 4px;
  color: #8492a6;
  font-size: 12px;
}

.full-width {
  width: 100%;
}

.report-title {
  margin: 12px 0;
}

.recent-report-title {
  margin: 18px 0 8px;
  font-size: 12px;
  font-weight: 600;
}

.report-list article {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 0;
  border-top: 1px solid #edf0f4;
}

.report-list article > button {
  min-width: 0;
  flex: 1;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.report-list strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-list span {
  margin-top: 3px;
  font-size: 12px;
}

.drawer-content {
  padding: 0 6px 28px;
}

.gate-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px;
}

.gate-strip > div {
  padding: 11px;
  border-radius: 9px;
  background: #f6f8fb;
}

.gate-strip strong {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  overflow-wrap: anywhere;
}

.gate-alert,
.communication-form-card,
.history-section {
  margin-top: 16px;
}

.control-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.section-heading {
  margin-bottom: 10px;
}

.communication-item,
.drilldown-section article {
  margin-bottom: 9px;
  padding: 12px 14px;
  border: 1px solid #e5eaf1;
  border-radius: 10px;
  background: #fff;
}

.communication-head > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.communication-item p {
  margin: 9px 0;
  color: #526174;
}

.communication-meta,
.drilldown-section article > span {
  font-size: 12px;
}

.communication-actions {
  margin-top: 10px;
}

.drilldown-section {
  padding-top: 14px;
  border-top: 1px dashed #dce3ed;
}

@media (max-width: 1180px) {
  .control-main-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .control-heading,
  .drawer-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .control-summary-grid,
  .report-metric-grid,
  .gate-strip,
  .form-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
