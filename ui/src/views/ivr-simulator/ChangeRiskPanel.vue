<template>
  <section class="change-workbench">
    <div class="change-heading">
      <div>
        <div class="section-kicker">M09-02 / CHANGE GUARD</div>
        <h3>变更操作红黄绿风险与人工确认</h3>
        <p>综合指令、业务逻辑、一致性和复合影响因素判定；红灯必须人工确认。</p>
      </div>
      <el-button :loading="loading" @click="loadDashboard">刷新风险台</el-button>
    </div>

    <div class="change-summary-grid">
      <article v-for="item in summaryCards" :key="item.label">
        <span>{{ item.label }}</span>
        <strong :class="item.tone">{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </div>

    <div class="risk-rule-strip">
      <div v-for="item in riskRules" :key="item.level" class="risk-rule">
        <span class="risk-light" :class="`is-${item.level.toLowerCase()}`" />
        <div>
          <strong>{{ item.label }}</strong>
          <small>{{ item.description }}</small>
        </div>
      </div>
    </div>

    <div class="change-main-grid">
      <el-card shadow="never" class="change-create-card">
        <template #header>
          <div class="card-heading">
            <div>
              <strong>新建并评估变更</strong>
              <span>所有判断以服务端评估快照为准</span>
            </div>
          </div>
        </template>
        <el-form label-position="top" :model="operationForm">
          <div class="form-grid">
            <el-form-item label="变更名称" required>
              <el-input v-model="operationForm.name" placeholder="例如：核心套餐配置割接" />
            </el-form-item>
            <el-form-item label="变更编号">
              <el-input v-model="operationForm.code" placeholder="留空则自动生成" />
            </el-form-item>
          </div>
          <div class="form-grid">
            <el-form-item label="变更类型">
              <el-select v-model="operationForm.operation_type" class="full-width">
                <el-option
                  v-for="item in operationTypes"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="关联 IVR 会话">
              <el-select
                v-model="operationForm.ivr_session_id"
                clearable
                filterable
                class="full-width"
                placeholder="可选"
              >
                <el-option
                  v-for="session in sessions"
                  :key="session.id"
                  :label="`${session.external_session_id} · ${session.caller_label || session.caller_masked}`"
                  :value="session.id"
                />
              </el-select>
            </el-form-item>
          </div>
          <el-form-item label="变更说明">
            <el-input
              v-model="operationForm.description"
              type="textarea"
              :rows="2"
              placeholder="说明范围、目标和执行窗口"
            />
          </el-form-item>

          <div class="factor-title">核心与复合风险因素</div>
          <div class="factor-grid">
            <label v-for="item in booleanFactors" :key="item.key" class="factor-item">
              <div>
                <strong>{{ item.label }}</strong>
                <small>{{ item.hint }}</small>
              </div>
              <el-switch v-model="riskForm[item.key]" />
            </label>
          </div>
          <el-form-item label="预计影响客户数" class="impact-input">
            <el-input-number
              v-model="riskForm.affected_customer_count"
              :min="0"
              :max="100000000"
              :step="100"
              controls-position="right"
              class="full-width"
            />
          </el-form-item>
          <el-button
            type="primary"
            class="full-width"
            :loading="submitting"
            @click="handleCreateAndEvaluate"
          >
            创建并生成风险灯
          </el-button>
        </el-form>
      </el-card>

      <el-card shadow="never" class="operation-list-card">
        <template #header>
          <div class="card-heading">
            <div>
              <strong>变更风险台账</strong>
              <span>评估和确认历史不会被重新评估覆盖</span>
            </div>
          </div>
        </template>
        <el-table v-loading="loading" :data="dashboard.operations" row-key="id" height="590">
          <el-table-column label="风险" width="95" align="center">
            <template #default="{ row }">
              <div class="risk-cell">
                <span class="risk-light" :class="`is-${String(row.risk_level).toLowerCase()}`" />
                <strong>{{ row.risk_revision ? row.risk_score : '—' }}</strong>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="变更操作" min-width="220">
            <template #default="{ row }">
              <div class="cell-primary">{{ row.name }}</div>
              <div class="cell-secondary">{{ row.code }} · {{ row.operation_type_label }}</div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="130">
            <template #default="{ row }">
              <el-tag :type="getOperationStatusType(row.status)">{{ row.status_label }}</el-tag>
              <div class="cell-secondary">{{ row.confirmation_status_label }}</div>
            </template>
          </el-table-column>
          <el-table-column label="主要原因" min-width="230">
            <template #default="{ row }">
              <span>{{ firstReason(row.risk_reasons) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="关联会话" min-width="180">
            <template #default="{ row }">{{ row.ivr_session_external_id || '未关联' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="openOperation(row.id)">查看</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty description="还没有变更风险评估" />
          </template>
        </el-table>
      </el-card>
    </div>

    <el-drawer v-model="drawerVisible" size="700px" destroy-on-close>
      <template #header>
        <div v-if="selectedOperation" class="drawer-heading">
          <div>
            <strong>{{ selectedOperation.name }}</strong>
            <span>{{ selectedOperation.code }} · v{{ selectedOperation.risk_revision }}</span>
          </div>
          <div class="drawer-risk">
            <span class="risk-light" :class="`is-${selectedOperation.risk_level.toLowerCase()}`" />
            <strong
              >{{ selectedOperation.risk_level_label }} ·
              {{ selectedOperation.risk_score }} 分</strong
            >
          </div>
        </div>
      </template>

      <div v-if="selectedOperation" v-loading="detailLoading" class="risk-drawer-content">
        <section class="operation-meta">
          <div>
            <span>类型</span><strong>{{ selectedOperation.operation_type_label }}</strong>
          </div>
          <div>
            <span>状态</span><strong>{{ selectedOperation.status_label }}</strong>
          </div>
          <div>
            <span>确认状态</span><strong>{{ selectedOperation.confirmation_status_label }}</strong>
          </div>
          <div>
            <span>关联会话</span
            ><strong>{{ selectedOperation.ivr_session_external_id || '未关联' }}</strong>
          </div>
        </section>

        <el-alert
          v-if="selectedOperation.confirmation_status === 'PENDING'"
          type="error"
          :closable="false"
          show-icon
          title="红灯变更已被拦住，必须人工确认放行或驳回。"
        />

        <section class="reason-section">
          <div class="section-heading">
            <strong>本次判定依据</strong>
            <span>{{ formatTime(selectedOperation.evaluated_at) }}</span>
          </div>
          <article
            v-for="reason in selectedOperation.risk_reasons"
            :key="`${reason.factor}-${reason.message}`"
            class="reason-item"
            :class="`is-${reason.severity.toLowerCase()}`"
          >
            <div>
              <strong>{{ reason.label }}</strong>
              <el-tag :type="getReasonType(reason.severity)" size="small">
                {{ reason.points ? `+${reason.points} 分` : '通过' }}
              </el-tag>
            </div>
            <p>{{ reason.message }}</p>
          </article>
        </section>

        <el-card
          v-if="selectedOperation.confirmation_status === 'PENDING'"
          class="confirm-card"
          shadow="never"
        >
          <template #header><strong>高风险人工确认</strong></template>
          <el-radio-group v-model="confirmationForm.decision">
            <el-radio-button value="APPROVE">确认放行</el-radio-button>
            <el-radio-button value="REJECT">确认驳回</el-radio-button>
          </el-radio-group>
          <el-input
            v-model="confirmationForm.comment"
            type="textarea"
            :rows="3"
            class="confirm-comment"
            placeholder="填写核验依据；驳回时必填"
          />
          <el-button type="danger" :loading="confirming" @click="handleConfirm">
            提交人工决策
          </el-button>
        </el-card>

        <section class="history-section">
          <div class="section-heading">
            <strong>评估版本历史</strong>
            <span>{{ selectedOperation.assessments?.length || 0 }} 个版本</span>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="assessment in selectedOperation.assessments"
              :key="assessment.id"
              :timestamp="formatTime(assessment.create_time)"
              :type="getRiskType(assessment.risk_level)"
              placement="top"
            >
              <div class="history-item">
                <strong>v{{ assessment.revision }} · {{ assessment.risk_level_label }}</strong>
                <span
                  >{{ assessment.risk_score }} 分 ·
                  {{ assessment.evaluator_name || '系统评估' }}</span
                >
              </div>
            </el-timeline-item>
          </el-timeline>
        </section>

        <section v-if="selectedOperation.confirmations?.length" class="history-section">
          <div class="section-heading">
            <strong>人工确认记录</strong>
            <span>{{ selectedOperation.confirmations.length }} 条</span>
          </div>
          <article
            v-for="record in selectedOperation.confirmations"
            :key="record.id"
            class="confirmation-record"
          >
            <div>
              <el-tag :type="record.decision === 'APPROVE' ? 'success' : 'danger'">
                {{ record.decision_label }}
              </el-tag>
              <strong>{{ record.confirmer_name || '人工确认人' }}</strong>
              <span>{{ formatTime(record.create_time) }}</span>
            </div>
            <p>{{ record.comment || '未填写补充意见' }}</p>
          </article>
        </section>
      </div>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import {
  confirmChangeOperation,
  createChangeOperation,
  evaluateChangeOperation,
  getChangeOperation,
  getChangeOperationDashboard,
  type ChangeConfirmationDecision,
  type ChangeOperation,
  type ChangeOperationDashboard,
  type ChangeOperationStatus,
  type ChangeOperationType,
  type ChangeRiskInput,
  type ChangeRiskLevel,
  type ChangeRiskReason,
  type IvrSession,
} from '@/api/marketing/ivr'
import { datetimeFormat } from '@/utils/time'

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'

defineProps<{ sessions: IvrSession[] }>()

const emptyDashboard: ChangeOperationDashboard = {
  summary: { operation_count: 0, red_count: 0, pending_confirmation_count: 0, approved_count: 0 },
  risk_counts: { GREEN: 0, YELLOW: 0, RED: 0 },
  operations: [],
  risk_rules: {
    red: '存在关键校验失败或风险分达到 60',
    yellow: '风险分达到 20 且无关键校验失败',
    green: '风险分低于 20',
    confirmation: '红灯变更必须人工确认后才能放行或驳回',
  },
}

const dashboard = ref<ChangeOperationDashboard>(emptyDashboard)
const selectedOperation = ref<ChangeOperation | null>(null)
const loading = ref(false)
const submitting = ref(false)
const detailLoading = ref(false)
const confirming = ref(false)
const drawerVisible = ref(false)

const operationForm = ref({
  code: '',
  name: '',
  operation_type: 'CONFIG_CHANGE' as ChangeOperationType,
  description: '',
  ivr_session_id: '' as string | null,
})
const riskForm = ref<ChangeRiskInput>({
  instruction_complete: true,
  business_logic_passed: true,
  consistency_passed: true,
  affected_customer_count: 0,
  cross_system_change: false,
  rollback_plan_ready: true,
  emergency_change: false,
  customer_notice_ready: true,
})
const confirmationForm = ref({
  decision: 'APPROVE' as ChangeConfirmationDecision,
  comment: '',
})

const operationTypes: Array<{ value: ChangeOperationType; label: string }> = [
  { value: 'PLAN_CHANGE', label: '套餐变更' },
  { value: 'CONFIG_CHANGE', label: '配置变更' },
  { value: 'DATA_MIGRATION', label: '数据迁移' },
  { value: 'NETWORK_CUTOVER', label: '网络割接' },
  { value: 'OTHER', label: '其他变更' },
]
const booleanFactors: Array<{
  key: Exclude<keyof ChangeRiskInput, 'affected_customer_count'>
  label: string
  hint: string
}> = [
  { key: 'instruction_complete', label: '指令完整', hint: '执行步骤与参数齐备' },
  { key: 'business_logic_passed', label: '业务逻辑通过', hint: '业务规则校验正常' },
  { key: 'consistency_passed', label: '一致性通过', hint: '数据与配置保持一致' },
  { key: 'rollback_plan_ready', label: '回退方案就绪', hint: '异常时可快速恢复' },
  { key: 'customer_notice_ready', label: '客户告知就绪', hint: '影响范围已有告知' },
  { key: 'cross_system_change', label: '跨系统变更', hint: '涉及多个业务系统' },
  { key: 'emergency_change', label: '紧急变更', hint: '缺少常规观察窗口' },
]

const summaryCards = computed(() => [
  { label: '变更操作', value: dashboard.value.summary.operation_count, hint: '全部台账', tone: '' },
  { label: '红灯变更', value: dashboard.value.summary.red_count, hint: '关键风险', tone: 'danger' },
  {
    label: '待人工确认',
    value: dashboard.value.summary.pending_confirmation_count,
    hint: '当前阻断',
    tone: 'warning',
  },
  {
    label: '已放行',
    value: dashboard.value.summary.approved_count,
    hint: '自动或人工',
    tone: 'success',
  },
])
const riskRules = computed(() => [
  { level: 'RED' as const, label: '红灯', description: dashboard.value.risk_rules.red },
  { level: 'YELLOW' as const, label: '黄灯', description: dashboard.value.risk_rules.yellow },
  { level: 'GREEN' as const, label: '绿灯', description: dashboard.value.risk_rules.green },
])

const getRiskType = (level: ChangeRiskLevel): TagType =>
  ({ RED: 'danger', YELLOW: 'warning', GREEN: 'success' })[level] as TagType
const getReasonType = (severity: ChangeRiskReason['severity']): TagType =>
  ({ CRITICAL: 'danger', WARNING: 'warning', NOTICE: 'info', PASS: 'success' })[severity] as TagType
const getOperationStatusType = (status: string): TagType => {
  const types: Record<ChangeOperationStatus, TagType> = {
    DRAFT: 'info',
    RISK_EVALUATED: 'warning',
    CONFIRMATION_PENDING: 'danger',
    APPROVED: 'success',
    REJECTED: 'danger',
  }
  return types[status as ChangeOperationStatus] || 'info'
}
const firstReason = (reasons?: ChangeRiskReason[]) => reasons?.[0]?.message || '等待风险评估'
const formatTime = (value: string | null) => (value ? datetimeFormat(value) : '—')
const makeRequestId = () =>
  `ui:change-confirm:${Date.now()}:${Math.random().toString(36).slice(2, 9)}`

const loadDashboard = async () => {
  const result = await getChangeOperationDashboard(loading)
  dashboard.value = result.data
}

const openOperation = async (id: string) => {
  drawerVisible.value = true
  confirmationForm.value = { decision: 'APPROVE', comment: '' }
  const result = await getChangeOperation(id, detailLoading)
  selectedOperation.value = result.data
}

const handleCreateAndEvaluate = async () => {
  if (!operationForm.value.name.trim()) {
    ElMessage.warning('请输入变更名称')
    return
  }
  submitting.value = true
  try {
    const created = await createChangeOperation({
      code: operationForm.value.code.trim() || undefined,
      name: operationForm.value.name.trim(),
      operation_type: operationForm.value.operation_type,
      description: operationForm.value.description.trim(),
      ivr_session_id: operationForm.value.ivr_session_id || null,
    })
    const evaluated = await evaluateChangeOperation(created.data.operation.id, riskForm.value)
    ElMessage.success(
      `${created.data.created ? '变更已创建' : '已有变更已重新评估'}：${evaluated.data.assessment.risk_level_label}`,
    )
    operationForm.value.code = ''
    operationForm.value.name = ''
    operationForm.value.description = ''
    await loadDashboard()
    await openOperation(created.data.operation.id)
  } finally {
    submitting.value = false
  }
}

const handleConfirm = async () => {
  if (!selectedOperation.value) return
  if (confirmationForm.value.decision === 'REJECT' && !confirmationForm.value.comment.trim()) {
    ElMessage.warning('驳回高风险变更时必须填写原因')
    return
  }
  const result = await confirmChangeOperation(
    selectedOperation.value.id,
    {
      request_id: makeRequestId(),
      decision: confirmationForm.value.decision,
      comment: confirmationForm.value.comment.trim(),
    },
    confirming,
  )
  ElMessage.success(result.data.confirmation.decision_label)
  await loadDashboard()
  await openOperation(selectedOperation.value.id)
}

onMounted(loadDashboard)
</script>

<style scoped lang="scss">
.change-workbench {
  margin-top: 22px;
  padding-top: 22px;
  border-top: 1px solid #dce3ed;
}

.change-heading,
.card-heading,
.drawer-heading,
.section-heading,
.reason-item > div,
.confirmation-record > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.change-heading {
  margin-bottom: 16px;
}

.change-heading h3 {
  margin: 4px 0 5px;
  font-size: 22px;
}

.change-heading p {
  margin: 0;
  color: #64748b;
}

.section-kicker {
  color: #c2410c;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.change-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.change-summary-grid article {
  padding: 16px 18px;
  border: 1px solid #e5eaf3;
  border-radius: 12px;
  background: #fff;
}

.change-summary-grid span,
.change-summary-grid small,
.card-heading span,
.drawer-heading span,
.section-heading span,
.operation-meta span,
.factor-item small {
  display: block;
  color: #8492a6;
}

.change-summary-grid strong {
  display: block;
  margin: 5px 0;
  font-size: 25px;
}

.change-summary-grid strong.danger {
  color: #dc2626;
}

.change-summary-grid strong.warning {
  color: #d97706;
}

.change-summary-grid strong.success {
  color: #16a34a;
}

.risk-rule-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.risk-rule {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #fff;
}

.risk-rule small {
  display: block;
  margin-top: 3px;
  color: #7b8798;
}

.risk-light {
  display: inline-block;
  width: 14px;
  height: 14px;
  flex: 0 0 auto;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgb(148 163 184 / 15%);
}

.risk-light.is-red {
  background: #ef4444;
  box-shadow: 0 0 0 4px rgb(239 68 68 / 14%);
}

.risk-light.is-yellow {
  background: #f59e0b;
  box-shadow: 0 0 0 4px rgb(245 158 11 / 16%);
}

.risk-light.is-green {
  background: #22c55e;
  box-shadow: 0 0 0 4px rgb(34 197 94 / 16%);
}

.change-main-grid {
  display: grid;
  grid-template-columns: minmax(430px, 0.85fr) minmax(620px, 1.15fr);
  gap: 16px;
}

.card-heading > div strong,
.drawer-heading > div > strong {
  display: block;
  margin-bottom: 4px;
}

.form-grid,
.factor-grid,
.operation-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.full-width {
  width: 100%;
}

.factor-title {
  margin: 2px 0 10px;
  font-weight: 600;
}

.factor-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #e8edf4;
  border-radius: 9px;
}

.factor-item small {
  margin-top: 2px;
  font-size: 11px;
}

.impact-input {
  margin-top: 14px;
}

.risk-cell,
.drawer-risk {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.cell-primary {
  font-weight: 600;
}

.cell-secondary {
  margin-top: 4px;
  color: #8492a6;
  font-size: 12px;
}

.risk-drawer-content {
  padding: 0 6px 24px;
}

.operation-meta {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 14px;
}

.operation-meta > div {
  padding: 11px;
  border-radius: 9px;
  background: #f6f8fb;
}

.operation-meta strong {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  overflow-wrap: anywhere;
}

.reason-section,
.history-section {
  margin-top: 18px;
}

.section-heading {
  margin-bottom: 12px;
}

.reason-item,
.confirmation-record,
.history-item {
  margin-bottom: 9px;
  padding: 12px 14px;
  border: 1px solid #e7ecf3;
  border-left-width: 4px;
  border-radius: 9px;
  background: #fff;
}

.reason-item.is-critical {
  border-left-color: #ef4444;
}

.reason-item.is-warning {
  border-left-color: #f59e0b;
}

.reason-item.is-notice {
  border-left-color: #3b82f6;
}

.reason-item.is-pass {
  border-left-color: #22c55e;
}

.reason-item p,
.confirmation-record p {
  margin: 7px 0 0;
  color: #556274;
}

.confirm-card {
  margin-top: 16px;
  border-color: #fecaca;
  background: #fffafa;
}

.confirm-comment {
  margin: 12px 0;
}

.history-item {
  display: flex;
  justify-content: space-between;
  border-left-width: 1px;
}

.history-item span,
.confirmation-record span {
  color: #8492a6;
  font-size: 12px;
}

.confirmation-record > div {
  justify-content: flex-start;
}

@media (max-width: 1200px) {
  .change-main-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .change-summary-grid,
  .risk-rule-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
