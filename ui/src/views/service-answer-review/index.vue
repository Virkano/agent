<template>
  <div class="service-review-page p-16-24">
    <header class="review-heading">
      <div>
        <p class="review-eyebrow">服务助手 / 回答安全</p>
        <h2>人工复核队列</h2>
        <p>只显示客户实际收到的安全答复；原始生成内容不在此页展示。</p>
      </div>
      <el-button :loading="loading" @click="loadReviews">刷新</el-button>
    </header>

    <el-card shadow="never" class="review-card">
      <div class="review-toolbar">
        <div class="review-count"><strong>{{ total }}</strong><span>条匹配记录</span></div>
        <el-segmented v-model="status" :options="statusOptions" @change="resetPage" />
      </div>
      <el-table v-loading="loading" :data="records" row-key="id" empty-text="当前没有待复核记录">
        <el-table-column label="风险与处置" min-width="220">
          <template #default="{ row }">
            <div class="risk-cell">
              <el-tag :type="row.delivery_action === 'BLOCKED' ? 'danger' : 'warning'" size="small">
                {{ actionLabels[row.delivery_action] || row.delivery_action }}
              </el-tag>
              <span>{{ row.risk_types.map((item: string) => riskLabels[item] || item).join('、') }}</span>
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

    <el-dialog v-model="dialogVisible" title="人工复核" width="520px" destroy-on-close>
      <p class="dialog-hint">复核结论只改变后台处理状态，不会重新向客户发送回答。</p>
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
import { onMounted, ref } from 'vue'
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
const statusOptions = [
  { label: '待复核', value: 'PENDING' },
  { label: '全部记录', value: 'ALL' },
]
const riskLabels: Record<string, string> = {
  NO_REFERENCE: '缺少依据',
  SENSITIVE_CONTENT: '敏感内容',
  PRIVATE_DATA: '个人信息',
  RUNTIME_ERROR: '运行异常',
}
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

onMounted(loadReviews)
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
.answer-text { white-space: pre-wrap; overflow-wrap: anywhere; color: #33465f; }
.review-pagination { justify-content: flex-end; margin-top: 20px; }
.dialog-hint { color: #66788d; margin-top: 0; }
.review-note { margin-top: 20px; }
@media (max-width: 760px) { .review-heading, .review-toolbar { align-items: flex-start; flex-direction: column; } .review-card { margin: 0 0 24px; } .review-heading { margin-left: 0; } }
</style>
