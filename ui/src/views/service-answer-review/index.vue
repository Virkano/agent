<template>
  <div class="service-review-page p-16-24">
    <header class="review-heading">
      <div>
        <p class="review-eyebrow">服务助手 / 回答安全</p>
        <h2>人工复核队列</h2>
        <p>集中核对用户问题、拦截原因和客户实际收到的安全答复；页面每 10 秒自动刷新。</p>
      </div>
      <el-button :loading="loading" @click="loadReviews">刷新</el-button>
    </header>

    <el-card shadow="never" class="review-card">
      <div class="review-toolbar">
        <div class="review-count"><strong>{{ total }}</strong><span>条匹配记录</span></div>
        <el-segmented v-model="status" :options="statusOptions" @change="resetPage" />
      </div>
      <el-table v-loading="loading" :data="records" row-key="id" empty-text="当前没有待复核记录">
        <el-table-column label="用户问题" min-width="280">
          <template #default="{ row }">
            <div class="question-cell">
              <strong>{{ row.application_name || '未知应用' }}</strong>
              <span>{{ row.user_question || '用户问题加载中' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="问题点" min-width="260">
          <template #default="{ row }">
            <div class="risk-cell">
              <el-tag :type="row.delivery_action === 'BLOCKED' ? 'danger' : 'warning'" size="small">
                {{ actionLabels[row.delivery_action] || row.delivery_action }}
              </el-tag>
              <div class="risk-summary">
                <strong>{{ formatRiskLabels(row) }}</strong>
                <span>{{ formatRiskDescriptions(row) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="客户实际收到的答复" min-width="300">
          <template #default="{ row }"><span class="answer-text">{{ row.delivered_answer }}</span></template>
        </el-table-column>
        <el-table-column prop="reference_count" label="引用数" width="84" />
        <el-table-column label="状态" width="104">
          <template #default="{ row }">{{ statusLabels[row.status] || row.status }}</template>
        </el-table-column>
        <el-table-column label="发生时间" width="170">
          <template #default="{ row }">{{ datetimeFormat(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'PENDING'" link type="primary" @click="openReview(row)">复核</el-button>
            <span v-else>已处理</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="page"
        class="review-pagination"
        :page-size="20"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadReviews"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" title="人工复核" width="720px" destroy-on-close>
      <p class="dialog-hint">复核结论只改变后台处理状态，不会重新向客户发送回答。用户问题中的个人信息已脱敏。</p>
      <div v-if="selected" class="review-context">
        <section>
          <span class="context-label">应用</span>
          <p>{{ selected.application_name || '未知应用' }}</p>
        </section>
        <section>
          <span class="context-label">用户问题</span>
          <p>{{ selected.user_question || '用户问题加载中' }}</p>
        </section>
        <section>
          <span class="context-label">客户实际收到的答复</span>
          <p>{{ selected.delivered_answer }}</p>
        </section>
        <section>
          <span class="context-label">具体问题点</span>
          <div v-for="risk in getRiskDetails(selected)" :key="risk.code" class="risk-detail">
            <el-tag type="danger" size="small">{{ risk.label }}</el-tag>
            <div>
              <p>{{ risk.description }}</p>
              <small>复核建议：{{ risk.review_guidance }}</small>
            </div>
          </div>
        </section>
        <section class="context-meta">
          <span>规则版本：{{ selected.rule_version }}</span>
          <span>知识引用：{{ selected.reference_count }} 条</span>
        </section>
      </div>
      <el-radio-group v-model="decision">
        <el-radio value="CONFIRMED">确认存在问题</el-radio>
        <el-radio value="DISMISSED">排除问题</el-radio>
      </el-radio-group>
      <el-input v-model="note" class="review-note" type="textarea" :rows="4" maxlength="2000" show-word-limit placeholder="填写核实依据与处理说明" />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="!note.trim()" @click="submitReview">提交结论</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onActivated, onBeforeUnmount, onDeactivated, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { datetimeFormat } from '@/utils/time'
import {
  getServiceAnswerReviews,
  handleServiceAnswerReview,
  type ServiceAnswerReview,
} from '@/api/service-answer-review'

const loading = ref(false)
const submitting = ref(false)
const records = ref<ServiceAnswerReview[]>([])
const total = ref(0)
const page = ref(1)
const status = ref('PENDING')
const dialogVisible = ref(false)
const selected = ref<ServiceAnswerReview>()
const decision = ref<'CONFIRMED' | 'DISMISSED'>('CONFIRMED')
const note = ref('')
let autoRefreshTimer: number | undefined
const statusOptions = [
  { label: '待复核', value: 'PENDING' },
  { label: '全部记录', value: 'ALL' },
]
const actionLabels: Record<string, string> = {
  BLOCKED: '已拦截',
  FALLBACK: '已兜底',
  REDACTED: '已脱敏',
}
const statusLabels: Record<string, string> = {
  PENDING: '待复核',
  CONFIRMED: '确认问题',
  DISMISSED: '已排除',
}

const fallbackRiskDetails: Record<string, NonNullable<ServiceAnswerReview['risk_details']>[number]> = {
  NO_REFERENCE: { code: 'NO_REFERENCE', label: '缺少知识依据', description: '没有检索到可核实的知识引用。', review_guidance: '核对知识库内容和检索配置。' },
  SENSITIVE_CONTENT: { code: 'SENSITIVE_CONTENT', label: '命中敏感内容规则', description: '生成答复命中了受限表达规则。', review_guidance: '判断是否误判，并检查提示词和回答边界。' },
  PRIVATE_DATA: { code: 'PRIVATE_DATA', label: '包含个人信息', description: '生成答复中检测到需要脱敏的个人信息。', review_guidance: '确认脱敏是否完整。' },
  RUNTIME_ERROR: { code: 'RUNTIME_ERROR', label: '回答生成运行异常', description: '模型、工具或依赖服务调用失败。', review_guidance: '检查模型和依赖服务，恢复后重新验证。' },
}

function getRiskDetails(record: ServiceAnswerReview) {
  if (record.risk_details?.length) return record.risk_details
  return record.risk_types.map(code => fallbackRiskDetails[code] || {
    code,
    label: '其他风险',
    description: '该回答命中了需要人工判断的规则。',
    review_guidance: '结合关联对话记录进行核实。',
  })
}

function formatRiskLabels(record: ServiceAnswerReview) {
  return getRiskDetails(record).map(item => item.label).join('、')
}

function formatRiskDescriptions(record: ServiceAnswerReview) {
  return getRiskDetails(record).map(item => item.description).join('；')
}

async function loadReviews() {
  try {
    const response = await getServiceAnswerReviews(page.value, 20, status.value, loading)
    records.value = response.data.records
    total.value = response.data.total
  } catch {
    records.value = []
    total.value = 0
  }
}

function refreshVisibleQueue() {
  if (document.visibilityState === 'visible' && !loading.value && !submitting.value) {
    loadReviews()
  }
}

function startAutoRefresh() {
  if (autoRefreshTimer !== undefined) return
  loadReviews()
  autoRefreshTimer = window.setInterval(refreshVisibleQueue, 10_000)
  document.addEventListener('visibilitychange', refreshVisibleQueue)
}

function stopAutoRefresh() {
  if (autoRefreshTimer !== undefined) {
    window.clearInterval(autoRefreshTimer)
    autoRefreshTimer = undefined
  }
  document.removeEventListener('visibilitychange', refreshVisibleQueue)
}

function resetPage() {
  page.value = 1
  loadReviews()
}

function openReview(record: ServiceAnswerReview) {
  selected.value = record
  decision.value = 'CONFIRMED'
  note.value = ''
  dialogVisible.value = true
}

async function submitReview() {
  if (!selected.value || !note.value.trim()) return
  try {
    await handleServiceAnswerReview(selected.value.id, decision.value, note.value.trim(), submitting)
    ElMessage.success('复核结论已保存')
    dialogVisible.value = false
    await loadReviews()
  } catch {
    // Request interceptor displays the server error.
  }
}

onMounted(startAutoRefresh)
onActivated(startAutoRefresh)
onDeactivated(stopAutoRefresh)
onBeforeUnmount(stopAutoRefresh)
</script>

<style scoped>
.service-review-page { height: 100%; overflow-y: auto; background: #f7f9fc; }
.review-heading { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin: 8px 24px 20px; }
.review-heading h2 { margin: 4px 0; font-size: 24px; color: #17283e; }
.review-heading p { margin: 0; color: #66788d; }
.review-heading .review-eyebrow { color: #2f70c5; font-size: 12px; letter-spacing: .08em; }
.review-card { margin: 0 24px 24px; border-color: #e3eaf2; }
.review-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.review-count { display: flex; align-items: baseline; gap: 8px; color: #66788d; }
.review-count strong { font-size: 25px; color: #17283e; }
.risk-cell { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.question-cell, .risk-summary { display: flex; flex-direction: column; gap: 5px; }
.question-cell strong, .risk-summary strong { color: #263b55; font-size: 13px; }
.question-cell span, .risk-summary span { color: #66788d; line-height: 1.55; overflow-wrap: anywhere; }
.answer-text { white-space: pre-wrap; overflow-wrap: anywhere; color: #33465f; }
.review-pagination { justify-content: flex-end; margin-top: 20px; }
.dialog-hint { color: #66788d; margin-top: 0; }
.review-context { display: grid; gap: 12px; margin: 16px 0 20px; padding: 16px; border: 1px solid #e3eaf2; border-radius: 8px; background: #f8fafc; }
.review-context section { min-width: 0; }
.review-context p { margin: 5px 0 0; color: #33465f; line-height: 1.6; white-space: pre-wrap; overflow-wrap: anywhere; }
.context-label { color: #7a899b; font-size: 12px; }
.risk-detail { display: flex; align-items: flex-start; gap: 10px; margin-top: 8px; }
.risk-detail p { margin-top: 0; }
.risk-detail small { display: block; margin-top: 3px; color: #7a899b; line-height: 1.5; }
.context-meta { display: flex; flex-wrap: wrap; gap: 20px; color: #7a899b; font-size: 12px; }
.review-note { margin-top: 20px; }
@media (max-width: 760px) { .review-heading, .review-toolbar { align-items: flex-start; flex-direction: column; } .review-card { margin: 0 0 24px; } .review-heading { margin-left: 0; } :deep(.el-dialog) { width: 92% !important; } }
</style>
