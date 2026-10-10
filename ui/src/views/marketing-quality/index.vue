<template>
  <div class="quality-workbench p-16-24">
    <div class="page-heading ml-24 mb-16">
      <div>
        <h2>对话质检</h2>
        <p>复核智能体回答，保留原回答证据，并沉淀可追溯的修订版本。</p>
      </div>
      <el-button :loading="loading" @click="getList">刷新队列</el-button>
    </div>

    <el-card class="policy-card mb-16" shadow="never">
      <div class="policy-row">
        <div class="policy-copy">
          <div class="policy-title">
            <span class="policy-indicator" :class="`is-${qualityPolicy.mode.toLowerCase()}`" />
            发送前质量策略
          </div>
          <p>{{ policyDescription }}</p>
        </div>
        <div class="policy-actions">
          <el-radio-group v-model="qualityPolicy.mode">
            <el-radio-button value="OFF">关闭</el-radio-button>
            <el-radio-button value="SHADOW">影子检测</el-radio-button>
            <el-radio-button
              value="INTERCEPT"
              :disabled="
                !qualityPolicy.interception_available && qualityPolicy.mode !== 'INTERCEPT'
              "
            >
              灰度拦截
            </el-radio-button>
          </el-radio-group>
          <el-button
            v-if="qualityPolicy.mode === 'INTERCEPT'"
            type="danger"
            plain
            :loading="policyLoading"
            @click="disableInterception"
          >
            一键回退影子模式
          </el-button>
          <el-button type="primary" :loading="policyLoading" @click="saveQualityPolicy">
            保存策略
          </el-button>
        </div>
      </div>
      <div v-if="qualityPolicy.mode === 'INTERCEPT'" class="intercept-config">
        <div>
          <strong>本工作空间拦截规则</strong>
          <span>仅展示已通过效果准入门槛的高风险规则；未选中的规则继续只记录。</span>
        </div>
        <el-checkbox-group v-model="qualityPolicy.intercept_rule_types">
          <el-checkbox
            v-for="item in qualityPolicy.eligible_rule_options"
            :key="item.value"
            :value="item.value"
          >
            {{ item.label }}
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <el-alert
        v-else-if="!qualityPolicy.interception_available"
        class="intercept-alert"
        type="warning"
        :closable="false"
        show-icon
        title="当前没有规则达到灰度准入门槛，灰度拦截保持不可用。"
      />
      <div class="policy-meta">
        <span>规则版本：{{ qualityPolicy.rule_version }}</span>
        <span v-if="qualityPolicy.updated_by_name"
          >更新人：{{ qualityPolicy.updated_by_name }}</span
        >
        <span>已准入规则：{{ qualityPolicy.eligible_rule_options.length }} 条</span>
        <span>{{ qualityPolicy.interception_guard }}</span>
      </div>
    </el-card>

    <RuleEffectPanel :tasks="taskOptions" class="mb-16" />

    <div class="summary-grid mb-16">
      <button
        v-for="item in summaryCards"
        :key="item.key"
        class="summary-card"
        :class="[`summary-card--${item.tone}`, { active: isSummaryActive(item.key) }]"
        type="button"
        @click="applySummaryFilter(item.key)"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </button>
    </div>

    <el-card class="filter-card mb-16" shadow="never">
      <div class="filter-row">
        <el-select
          v-model="filters.task_id"
          clearable
          filterable
          placeholder="全部营销任务"
          style="width: 240px"
          @change="resetAndLoad"
        >
          <el-option
            v-for="task in taskOptions"
            :key="task.id"
            :label="task.name"
            :value="task.id"
          />
        </el-select>
        <el-select
          v-model="filters.quality_status"
          clearable
          placeholder="自动质检状态"
          style="width: 170px"
          @change="resetAndLoad"
        >
          <el-option label="高风险" value="HIGH_RISK" />
          <el-option label="需复核" value="REVIEW" />
        </el-select>
        <el-select
          v-model="filters.manual_status"
          clearable
          placeholder="人工处理状态"
          style="width: 180px"
          @change="resetAndLoad"
        >
          <el-option
            v-for="(item, key) in manualStatusMap"
            :key="key"
            :label="item.label"
            :value="key"
          />
        </el-select>
        <el-select
          v-model="filters.risk_type"
          clearable
          placeholder="问题类型"
          style="width: 210px"
          @change="resetAndLoad"
        >
          <el-option v-for="(label, key) in riskTypeMap" :key="key" :label="label" :value="key" />
        </el-select>
        <el-input
          v-model="filters.keyword"
          clearable
          placeholder="搜索任务、客户、问题或回答"
          style="width: 280px"
          @keyup.enter="resetAndLoad"
          @clear="resetAndLoad"
        >
          <template #append>
            <el-button @click="resetAndLoad">搜索</el-button>
          </template>
        </el-input>
      </div>
    </el-card>

    <el-card class="queue-card" shadow="never">
      <el-table v-loading="loading" :data="records" row-key="id" class="quality-table">
        <el-table-column label="风险" width="118">
          <template #default="{ row }">
            <el-tag :type="getQualityStatus(row.status).type" effect="dark">
              {{ getQualityStatus(row.status).label }} · {{ row.score }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="任务 / 客户" min-width="190">
          <template #default="{ row }">
            <div class="cell-primary">{{ row.task_name }}</div>
            <div class="cell-secondary">{{ row.customer_name || '未关联客户' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="客户问题" min-width="230">
          <template #default="{ row }">
            <div class="question-text">{{ row.problem_text }}</div>
            <div class="risk-list">{{ getRiskLabels(row.risk_types) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="原回答" min-width="320">
          <template #default="{ row }">
            <div class="answer-preview">{{ row.original_answer }}</div>
          </template>
        </el-table-column>
        <el-table-column label="人工状态" width="150">
          <template #default="{ row }">
            <el-tag :type="getManualStatus(row.manual_status).type">
              {{ getManualStatus(row.manual_status).label }}
            </el-tag>
            <div v-if="row.reviewer_name" class="reviewer-line">{{ row.reviewer_name }}</div>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="165">
          <template #default="{ row }">{{ datetimeFormat(row.record_create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openReview(row)">
              {{ row.manual_status === 'PENDING' ? '处理' : '查看/复核' }}
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="当前筛选条件下没有待处理回答" />
        </template>
      </el-table>
      <div class="pagination-row">
        <el-pagination
          v-model:current-page="pagination.current_page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @current-change="getList"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <el-card class="preflight-card mt-16" shadow="never">
      <template #header>
        <div class="card-heading">
          <div>
            <strong>发送前质量检测记录</strong>
            <span>展示模型原始回答、最终发送回答以及检测结论</span>
          </div>
          <el-button :loading="preflightLoading" @click="getPreflightLogs">刷新记录</el-button>
        </div>
      </template>
      <div class="preflight-summary">
        <span
          >检测总数 <strong>{{ preflightSummary.total_count }}</strong></span
        >
        <span
          >正常 <strong class="success-text">{{ preflightSummary.pass_count }}</strong></span
        >
        <span
          >需复核 <strong class="warning-text">{{ preflightSummary.review_count }}</strong></span
        >
        <span
          >高风险 <strong class="danger-text">{{ preflightSummary.high_risk_count }}</strong></span
        >
        <span>
          安全改写
          <strong class="primary-text">{{ preflightSummary.safeguard_rewritten_count }}</strong>
        </span>
        <span>
          灰度拦截
          <strong class="danger-text">{{ preflightSummary.intercepted_count }}</strong>
        </span>
        <span>
          异常旁路
          <strong class="warning-text">{{ preflightSummary.bypassed_count }}</strong>
        </span>
      </div>
      <el-table v-loading="preflightLoading" :data="preflightRecords" row-key="id">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="preflight-detail">
              <section>
                <span>模型原始回答</span>
                <p>{{ row.generated_answer }}</p>
              </section>
              <section :class="{ changed: row.generated_answer !== row.final_answer }">
                <span>最终发送回答</span>
                <p>{{ row.final_answer }}</p>
              </section>
              <section v-if="row.reasons.length" class="risk-detail">
                <span>检测依据</span>
                <p>{{ row.reasons.join('；') }}</p>
              </section>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="检测结论" width="130">
          <template #default="{ row }">
            <el-tag :type="getQualityStatus(row.status).type" effect="dark">
              {{ getQualityStatus(row.status).label }} · {{ row.score }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="任务 / 客户" min-width="190">
          <template #default="{ row }">
            <div class="cell-primary">{{ row.task_name }}</div>
            <div class="cell-secondary">{{ row.customer_name || '未关联客户' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="客户问题" min-width="260">
          <template #default="{ row }">
            <div class="question-text">{{ row.problem_text }}</div>
            <div class="risk-list">{{ getRiskLabels(row.risk_types) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="处理动作" width="150">
          <template #default="{ row }">
            <el-tag :type="getPreflightActionType(row.action)">
              {{ getPreflightActionLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="检测耗时" width="110">
          <template #default="{ row }">{{ row.evaluation_ms }} ms</template>
        </el-table-column>
        <el-table-column label="时间" width="165">
          <template #default="{ row }">{{ datetimeFormat(row.create_time) }}</template>
        </el-table-column>
        <template #empty>
          <el-empty description="开启发送前质量策略并完成一轮营销对话后，这里会生成记录" />
        </template>
      </el-table>
      <div class="pagination-row">
        <el-pagination
          v-model:current-page="preflightPagination.current_page"
          v-model:page-size="preflightPagination.page_size"
          :page-sizes="[10, 20, 50]"
          :total="preflightPagination.total"
          layout="total, sizes, prev, pager, next"
          @current-change="getPreflightLogs"
          @size-change="handlePreflightSizeChange"
        />
      </div>
    </el-card>

    <el-drawer v-model="reviewVisible" title="回答复核与修订" size="680px" destroy-on-close>
      <template v-if="currentReview">
        <div class="review-context">
          <span>客户问题</span>
          <p>{{ currentReview.problem_text }}</p>
        </div>
        <div class="review-context original">
          <span>原回答（只读证据）</span>
          <p>{{ currentReview.original_answer }}</p>
        </div>
        <el-alert
          :title="currentReview.reasons.join('；') || '未发现规则风险'"
          :description="currentReview.suggestion"
          :type="currentReview.status === 'HIGH_RISK' ? 'error' : 'warning'"
          :closable="false"
          show-icon
          class="mb-20"
        />

        <el-form ref="reviewFormRef" :model="reviewForm" :rules="reviewRules" label-position="top">
          <el-form-item label="处理结论" prop="action">
            <el-radio-group v-model="reviewForm.action" class="action-options">
              <el-radio-button value="CONFIRM_PASS">确认正常</el-radio-button>
              <el-radio-button value="CONFIRM_ISSUE">确认问题</el-radio-button>
              <el-radio-button value="REVISE">提交修订</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item
            v-if="reviewForm.action === 'REVISE'"
            label="面向客户的修订答案"
            prop="revised_answer"
          >
            <el-input
              v-model="reviewForm.revised_answer"
              type="textarea"
              :rows="7"
              maxlength="20000"
              show-word-limit
              placeholder="直接填写可展示给客户的完整答案，不要包含坐席指令或内部流程。"
            />
          </el-form-item>
          <el-form-item label="复核意见" prop="note">
            <el-input
              v-model="reviewForm.note"
              type="textarea"
              :rows="3"
              maxlength="2000"
              show-word-limit
              placeholder="说明判断依据或修订原因"
            />
          </el-form-item>
        </el-form>

        <section v-if="currentReview.manual_actions.length" class="history-section">
          <h3>处理历史</h3>
          <el-timeline>
            <el-timeline-item
              v-for="action in currentReview.manual_actions"
              :key="action.id"
              :timestamp="datetimeFormat(action.create_time)"
              placement="top"
            >
              <div class="history-title">
                第 {{ action.revision }} 次 · {{ actionMap[action.action] }} ·
                {{ action.reviewer_name || '未知人员' }}
              </div>
              <div v-if="action.note" class="cell-secondary">{{ action.note }}</div>
              <div
                v-if="action.action === 'REVISE' && action.revised_answer"
                class="history-answer"
              >
                修订答案：{{ action.revised_answer }}
              </div>
            </el-timeline-item>
          </el-timeline>
        </section>
      </template>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitReview"
          >保存处理结果</el-button
        >
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import marketingTaskApi, {
  type MarketingManualReviewAction,
  type MarketingManualReviewStatus,
  type MarketingQualityReview,
  type MarketingQualityReviewSummary,
  type MarketingQualityStatus,
  type MarketingPreflightAction,
  type MarketingPreflightRecord,
  type MarketingPreflightSummary,
  type MarketingQualityPolicy,
  type MarketingTask,
} from '@/api/marketing/task'
import { datetimeFormat } from '@/utils/time'
import RuleEffectPanel from './component/RuleEffectPanel.vue'

const loading = ref(false)
const policyLoading = ref(false)
const preflightLoading = ref(false)
const submitLoading = ref(false)
const reviewVisible = ref(false)
const reviewFormRef = ref<FormInstance>()
const records = ref<MarketingQualityReview[]>([])
const currentReview = ref<MarketingQualityReview>()
const taskOptions = ref<MarketingTask[]>([])
const qualityPolicy = ref<MarketingQualityPolicy>({
  mode: 'SHADOW',
  rule_version: 'marketing-quality-v1',
  updated_by_name: '',
  update_time: null,
  available_modes: [],
  interception_available: false,
  intercept_rule_types: [],
  eligible_rule_options: [],
  interception_guard: '',
})
const preflightRecords = ref<MarketingPreflightRecord[]>([])
const preflightSummary = ref<MarketingPreflightSummary>({
  total_count: 0,
  pass_count: 0,
  review_count: 0,
  high_risk_count: 0,
  safeguard_rewritten_count: 0,
  intercepted_count: 0,
  bypassed_count: 0,
})
const summary = ref<MarketingQualityReviewSummary>({
  total_count: 0,
  pending_count: 0,
  reviewed_count: 0,
  revised_count: 0,
  high_risk_count: 0,
})
const pagination = ref({ current_page: 1, page_size: 20, total: 0 })
const preflightPagination = ref({ current_page: 1, page_size: 10, total: 0 })
const filters = ref({
  task_id: '',
  quality_status: '',
  manual_status: 'PENDING' as MarketingManualReviewStatus | '',
  risk_type: '',
  keyword: '',
})
const reviewForm = ref({
  action: 'CONFIRM_ISSUE' as MarketingManualReviewAction,
  note: '',
  revised_answer: '',
})

const qualityStatusMap = {
  PASS: { label: '正常', type: 'success' as const },
  REVIEW: { label: '需复核', type: 'warning' as const },
  HIGH_RISK: { label: '高风险', type: 'danger' as const },
}
const manualStatusMap: Record<
  MarketingManualReviewStatus,
  { label: string; type: 'success' | 'warning' | 'danger' | 'info' }
> = {
  PENDING: { label: '待处理', type: 'warning' },
  CONFIRMED_PASS: { label: '确认正常', type: 'success' },
  CONFIRMED_ISSUE: { label: '确认问题', type: 'danger' },
  REVISED: { label: '已修订', type: 'success' },
}
const actionMap: Record<MarketingManualReviewAction, string> = {
  CONFIRM_PASS: '确认正常',
  CONFIRM_ISSUE: '确认问题',
  REVISE: '提交修订',
}
const preflightActionMap: Record<MarketingPreflightAction, string> = {
  OBSERVED: '仅观察',
  SAFEGUARD_REWRITTEN: '安全规则已改写',
  INTERCEPTED: '灰度拦截',
  BYPASSED: '检测旁路',
}
const riskTypeMap: Record<string, string> = {
  RUNTIME_ERROR: '运行错误',
  OFF_TOPIC: '答非所问',
  INTERNAL_EXPOSURE: '内部话术暴露',
  UNVERIFIED_PRICE: '未确认资费',
  UNVERIFIED_COMMITMENT: '未确认承诺',
  PROVINCE_MISMATCH: '省份不一致',
  REPEATED_ANSWER: '重复回答',
  MISSING_MATCHED_BENEFIT: '缺少活动权益',
  MISSING_REFERENCE: '缺少知识依据',
  EMPTY_OR_TOO_SHORT: '回答过短',
}

const summaryCards = computed(() => [
  {
    key: 'PENDING',
    label: '待处理',
    value: summary.value.pending_count,
    hint: '优先清理',
    tone: 'amber',
  },
  {
    key: 'HIGH_RISK',
    label: '高风险',
    value: summary.value.high_risk_count,
    hint: '建议优先复核',
    tone: 'red',
  },
  {
    key: 'REVIEWED',
    label: '已复核',
    value: summary.value.reviewed_count,
    hint: '人工已给结论',
    tone: 'blue',
  },
  {
    key: 'REVISED',
    label: '已修订',
    value: summary.value.revised_count,
    hint: '保留修订版本',
    tone: 'green',
  },
])

const policyDescription = computed(() => {
  if (qualityPolicy.value.mode === 'INTERCEPT') {
    return '仅拦截已通过人工样本和准确率门槛的高风险规则；检测超时或异常自动旁路。'
  }
  if (qualityPolicy.value.mode === 'OFF') {
    return '发送前质量检测已关闭；现有资费安全规则仍按原逻辑运行。'
  }
  return '影子检测只记录风险，不额外拦截或改写客户回答；现有资费安全规则仍按原逻辑运行。'
})

const reviewRules: FormRules = {
  action: [{ required: true, message: '请选择处理结论', trigger: 'change' }],
  revised_answer: [
    {
      validator: (_rule, value, callback) => {
        if (reviewForm.value.action === 'REVISE' && !String(value || '').trim()) {
          callback(new Error('请填写修订答案'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  note: [
    {
      validator: (_rule, value, callback) => {
        if (reviewForm.value.action === 'CONFIRM_ISSUE' && !String(value || '').trim()) {
          callback(new Error('确认问题时请填写复核意见'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

function getList() {
  const params = Object.fromEntries(
    Object.entries(filters.value).filter(([, value]) => value !== ''),
  )
  marketingTaskApi.getQualityReviewPage(pagination.value, params, loading).then((res) => {
    records.value = res.data.records
    summary.value = res.data.summary
    pagination.value.total = res.data.total
    pagination.value.current_page = res.data.current
    pagination.value.page_size = res.data.size
  })
}

function resetAndLoad() {
  pagination.value.current_page = 1
  getList()
}

function handleSizeChange() {
  pagination.value.current_page = 1
  getList()
}

function getRiskLabels(riskTypes: string[]) {
  return riskTypes.map((item) => riskTypeMap[item] || item).join(' · ') || '无规则风险'
}

function getQualityStatus(status: MarketingQualityStatus) {
  return qualityStatusMap[status]
}

function getManualStatus(status: MarketingManualReviewStatus) {
  return manualStatusMap[status]
}

function getPreflightActionLabel(action: MarketingPreflightAction) {
  return preflightActionMap[action]
}

function getPreflightActionType(action: MarketingPreflightAction) {
  if (action === 'INTERCEPTED') return 'danger'
  if (action === 'BYPASSED') return 'warning'
  if (action === 'SAFEGUARD_REWRITTEN') return 'primary'
  return 'info'
}

function normalizeQualityPolicy(value: MarketingQualityPolicy): MarketingQualityPolicy {
  return {
    ...qualityPolicy.value,
    ...value,
    available_modes: value.available_modes ?? [],
    intercept_rule_types: value.intercept_rule_types ?? [],
    eligible_rule_options: value.eligible_rule_options ?? [],
    interception_available: value.interception_available ?? false,
    interception_guard: value.interception_guard ?? '',
  }
}

function getQualityPolicy() {
  marketingTaskApi.getQualityPolicy(policyLoading).then((res) => {
    qualityPolicy.value = normalizeQualityPolicy(res.data)
  })
}

function saveQualityPolicy() {
  if (
    qualityPolicy.value.mode === 'INTERCEPT' &&
    qualityPolicy.value.intercept_rule_types.length === 0
  ) {
    ElMessage.warning('请至少选择一条已准入的高风险规则')
    return
  }
  marketingTaskApi
    .updateQualityPolicy(
      {
        mode: qualityPolicy.value.mode,
        intercept_rule_types: qualityPolicy.value.intercept_rule_types,
      },
      policyLoading,
    )
    .then((res) => {
      qualityPolicy.value = normalizeQualityPolicy(res.data)
      const message = {
        OFF: '发送前质量检测已关闭',
        SHADOW: '影子检测已开启，不会拦截客户回答',
        INTERCEPT: '灰度拦截已开启，仅作用于已选且已准入的高风险规则',
      }[res.data.mode]
      ElMessage.success(message)
    })
}

function disableInterception() {
  marketingTaskApi
    .updateQualityPolicy({ mode: 'SHADOW', intercept_rule_types: [] }, policyLoading)
    .then((res) => {
      qualityPolicy.value = normalizeQualityPolicy(res.data)
      ElMessage.success('已回退影子检测，停止新增自动拦截')
    })
}

function getPreflightLogs() {
  marketingTaskApi
    .getPreflightLogPage(preflightPagination.value, undefined, preflightLoading)
    .then((res) => {
      preflightRecords.value = res.data.records
      preflightSummary.value = { ...preflightSummary.value, ...res.data.summary }
      preflightPagination.value.total = res.data.total
      preflightPagination.value.current_page = res.data.current
      preflightPagination.value.page_size = res.data.size
    })
}

function handlePreflightSizeChange() {
  preflightPagination.value.current_page = 1
  getPreflightLogs()
}

function isSummaryActive(key: string) {
  if (key === 'PENDING') return filters.value.manual_status === 'PENDING'
  if (key === 'HIGH_RISK') return filters.value.quality_status === 'HIGH_RISK'
  if (key === 'REVIEWED') return filters.value.manual_status === ''
  return filters.value.manual_status === 'REVISED'
}

function applySummaryFilter(key: string) {
  filters.value.quality_status = key === 'HIGH_RISK' ? 'HIGH_RISK' : ''
  if (key === 'PENDING') filters.value.manual_status = 'PENDING'
  else if (key === 'REVISED') filters.value.manual_status = 'REVISED'
  else filters.value.manual_status = ''
  resetAndLoad()
}

function openReview(row: MarketingQualityReview) {
  currentReview.value = row
  reviewForm.value = {
    action:
      row.manual_status === 'REVISED'
        ? 'REVISE'
        : row.manual_status === 'CONFIRMED_PASS'
          ? 'CONFIRM_PASS'
          : 'CONFIRM_ISSUE',
    note: row.review_note || '',
    revised_answer: row.revised_answer || '',
  }
  reviewVisible.value = true
}

function submitReview() {
  reviewFormRef.value?.validate((valid) => {
    if (!valid || !currentReview.value) return
    marketingTaskApi
      .handleQualityReview(currentReview.value.id, reviewForm.value, submitLoading)
      .then(() => {
        ElMessage.success('质检处理结果已保存，原回答未被修改')
        reviewVisible.value = false
        getList()
        getQualityPolicy()
      })
  })
}

onMounted(() => {
  marketingTaskApi.getTaskList().then((res) => {
    taskOptions.value = res.data
  })
  getList()
  getQualityPolicy()
  getPreflightLogs()
})
</script>

<style scoped lang="scss">
.quality-workbench {
  --quality-ink: #203049;
  --quality-muted: #718096;
  --quality-line: #e6eaf0;
}

.page-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;

  h2 {
    margin: 0 0 4px;
    color: var(--quality-ink);
  }

  p {
    margin: 0;
    color: var(--quality-muted);
    font-size: 13px;
  }
}

.policy-card,
.preflight-card {
  border-color: var(--quality-line);
}

.policy-row,
.card-heading {
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: space-between;
}

.policy-copy p,
.card-heading span {
  margin: 6px 0 0;
  color: var(--quality-muted);
  font-size: 13px;
}

.policy-title {
  display: flex;
  gap: 9px;
  align-items: center;
  color: var(--quality-ink);
  font-size: 16px;
  font-weight: 700;
}

.policy-indicator {
  width: 9px;
  height: 9px;
  background: #94a3b8;
  border-radius: 50%;

  &.is-shadow {
    background: #278466;
    box-shadow: 0 0 0 5px rgb(39 132 102 / 12%);
  }

  &.is-intercept {
    background: #c2413b;
    box-shadow: 0 0 0 5px rgb(194 65 59 / 12%);
  }
}

.policy-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.intercept-config {
  display: grid;
  grid-template-columns: minmax(250px, 0.7fr) minmax(360px, 1.3fr);
  gap: 20px;
  padding: 14px 16px;
  margin-top: 14px;
  background: #fff8f5;
  border: 1px solid #f2d5cb;
  border-radius: 6px;

  > div {
    display: grid;
    gap: 4px;
  }

  strong {
    color: #8f312d;
    font-size: 13px;
  }

  span {
    color: var(--quality-muted);
    font-size: 12px;
    line-height: 1.6;
  }
}

.intercept-alert {
  margin-top: 14px;
}

.policy-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding-top: 14px;
  margin-top: 14px;
  color: var(--quality-muted);
  font-size: 12px;
  border-top: 1px solid var(--quality-line);
}

.card-heading > div {
  display: grid;
}

@media (width <= 900px) {
  .policy-row,
  .card-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .policy-actions {
    justify-content: flex-start;
  }

  .intercept-config {
    grid-template-columns: 1fr;
  }
}

.preflight-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 26px;
  padding: 12px 16px;
  margin-bottom: 14px;
  color: var(--quality-muted);
  background: #f7f9fc;
  border-radius: 6px;

  strong {
    margin-left: 5px;
    color: var(--quality-ink);
    font-size: 18px;
  }
}

.success-text {
  color: #278466 !important;
}

.warning-text {
  color: #d88a16 !important;
}

.danger-text {
  color: #d94747 !important;
}

.primary-text {
  color: #386bb5 !important;
}

.preflight-detail {
  display: grid;
  gap: 10px;
  padding: 8px 26px 14px;

  section {
    padding: 12px 14px;
    background: #f7f9fc;
    border-left: 3px solid #94a3b8;
    border-radius: 4px;

    &.changed {
      border-left-color: #386bb5;
    }

    &.risk-detail {
      border-left-color: #d94747;
    }
  }

  span {
    color: var(--quality-muted);
    font-size: 12px;
  }

  p {
    margin: 6px 0 0;
    color: var(--quality-ink);
    line-height: 1.65;
    white-space: pre-wrap;
  }
}

@media (max-width: 900px) {
  .policy-row,
  .policy-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  position: relative;
  display: grid;
  gap: 5px;
  min-height: 118px;
  padding: 18px 20px;
  overflow: hidden;
  text-align: left;
  cursor: pointer;
  background: #fff;
  border: 1px solid var(--quality-line);
  border-radius: 8px;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease;

  &::after {
    position: absolute;
    top: 0;
    right: 0;
    width: 6px;
    height: 100%;
    content: '';
    background: var(--summary-accent);
  }

  &:hover,
  &.active {
    border-color: var(--summary-accent);
    box-shadow: 0 8px 24px rgb(31 45 61 / 9%);
    transform: translateY(-1px);
  }

  span {
    color: var(--quality-muted);
    font-size: 13px;
  }

  strong {
    color: var(--quality-ink);
    font-size: 30px;
    font-weight: 700;
    line-height: 1;
  }

  small {
    color: var(--summary-accent);
  }

  &--amber {
    --summary-accent: #d88a16;
  }
  &--red {
    --summary-accent: #d94747;
  }
  &--blue {
    --summary-accent: #386bb5;
  }
  &--green {
    --summary-accent: #278466;
  }
}

.filter-card,
.queue-card {
  border-color: var(--quality-line);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.cell-primary,
.question-text {
  color: var(--quality-ink);
  font-weight: 600;
}

.cell-secondary,
.reviewer-line {
  margin-top: 4px;
  color: var(--quality-muted);
  font-size: 12px;
}

.risk-list {
  margin-top: 7px;
  color: #b45309;
  font-size: 12px;
}

.answer-preview {
  display: -webkit-box;
  overflow: hidden;
  color: #475569;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.pagination-row {
  display: flex;
  justify-content: flex-end;
  padding-top: 18px;
}

.review-context {
  padding: 16px 18px;
  margin-bottom: 12px;
  background: #f6f8fb;
  border-left: 4px solid #5277ad;
  border-radius: 4px;

  &.original {
    border-left-color: #d88a16;
  }

  span {
    color: var(--quality-muted);
    font-size: 12px;
  }

  p {
    margin: 8px 0 0;
    color: var(--quality-ink);
    line-height: 1.7;
    white-space: pre-wrap;
  }
}

.action-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  width: 100%;

  :deep(.el-radio-button__inner) {
    width: 100%;
  }
}

.history-section {
  padding-top: 8px;
  margin-top: 24px;
  border-top: 1px solid var(--quality-line);

  h3 {
    margin: 12px 0 18px;
  }
}

.history-title {
  color: var(--quality-ink);
  font-weight: 600;
}

.history-answer {
  padding: 8px 10px;
  margin-top: 8px;
  color: #475569;
  line-height: 1.6;
  background: #f6f8fb;
  border-radius: 4px;
}

@media (max-width: 1100px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
