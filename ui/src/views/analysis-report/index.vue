<template>
  <div class="report-page">
    <header class="report-hero">
      <div class="hero-copy">
        <span class="eyebrow">DECISION INTELLIGENCE · V1</span>
        <h2>AI 分析报告中心</h2>
        <p>把营销触达、转化和经营投入沉淀成可追溯的决策简报。</p>
      </div>
      <div class="hero-actions">
        <el-button :icon="Calendar" @click="openSubscriptionDrawer">报告订阅</el-button>
        <el-button :icon="Setting" @click="templateDrawerVisible = true">报告模板</el-button>
        <el-button type="primary" :icon="Plus" @click="openGenerate">生成报告</el-button>
      </div>
    </header>

    <section class="summary-strip">
      <div>
        <span>报告总数</span>
        <strong>{{ pagination.total }}</strong>
        <small>当前工作空间</small>
      </div>
      <div>
        <span>最近触达率</span>
        <strong>{{ metricValue('touch_rate', '%') }}</strong>
        <small>去重触达 / 批次曝光</small>
      </div>
      <div>
        <span>最近转化率</span>
        <strong>{{ metricValue('conversion_rate', '%') }}</strong>
        <small>确认转化 / 实际触达</small>
      </div>
      <div class="accent-metric">
        <span>最近 ROI</span>
        <strong>{{ metricValue('roi', '%') }}</strong>
        <small>（归因收入 - 投入）/ 投入</small>
      </div>
    </section>

    <section class="report-workbench">
      <aside class="report-library">
        <div class="section-heading">
          <div>
            <span>REPORT LIBRARY</span>
            <h3>报告库</h3>
          </div>
          <el-button circle :icon="Refresh" :loading="listLoading" @click="loadReports(1)" />
        </div>
        <div class="filters">
          <el-input
            v-model="filters.keyword"
            clearable
            :prefix-icon="Search"
            placeholder="搜索标题或任务"
            @keyup.enter="loadReports(1)"
            @clear="loadReports(1)"
          />
          <el-select v-model="filters.status" clearable placeholder="全部状态" @change="loadReports(1)">
            <el-option label="已完成" value="SUCCESS" />
            <el-option label="生成失败" value="FAILED" />
            <el-option label="生成中" value="RUNNING" />
          </el-select>
        </div>
        <div v-loading="listLoading" class="report-list">
          <button
            v-for="report in reports"
            :key="report.id"
            type="button"
            class="report-item"
            :class="{ active: selectedReport?.id === report.id }"
            @click="selectReport(report.id)"
          >
            <span class="status-dot" :class="`is-${report.status.toLowerCase()}`" />
            <span class="report-item-copy">
              <strong>{{ report.title }}</strong>
              <small>{{ report.task_name }} · {{ formatDate(report.create_time) }}</small>
              <span>{{ statusLabel[report.status] }} · {{ report.model_name }}</span>
            </span>
            <ArrowRight class="report-arrow" />
          </button>
          <el-empty v-if="!reports.length && !listLoading" :image-size="64" description="还没有分析报告">
            <el-button type="primary" @click="openGenerate">生成第一份报告</el-button>
          </el-empty>
        </div>
        <el-pagination
          v-if="pagination.total > pagination.size"
          small
          background
          layout="prev, pager, next"
          :total="pagination.total"
          :page-size="pagination.size"
          :current-page="pagination.current"
          @current-change="loadReports"
        />
      </aside>

      <main v-loading="detailLoading" class="report-preview">
        <template v-if="selectedReport">
          <div class="preview-toolbar">
            <div>
              <el-tag :type="statusType[selectedReport.status]" effect="plain">
                {{ statusLabel[selectedReport.status] }}
              </el-tag>
              <span>模板 {{ selectedReport.template_name || '—' }}</span>
              <span>生成方式 {{ selectedReport.model_name }}</span>
            </div>
            <div class="preview-actions">
              <el-dropdown v-if="selectedReport.status === 'SUCCESS'" @command="handleDownload">
                <el-button :icon="Download" :loading="downloading">下载报告</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="html">HTML 网页</el-dropdown-item>
                    <el-dropdown-item command="pdf">PDF 文档</el-dropdown-item>
                    <el-dropdown-item command="docx">Word 文档</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button
                v-if="selectedReport.status === 'FAILED'"
                type="danger"
                plain
                :icon="RefreshRight"
                :loading="retrying"
                @click="retrySelected"
              >
                重试生成
              </el-button>
            </div>
          </div>
          <div v-if="selectedReport.status === 'FAILED'" class="failure-panel">
            <WarningFilled />
            <div>
              <strong>本次报告生成失败</strong>
              <p>{{ selectedReport.error_message || '未获取到错误信息' }}</p>
              <small>已保留参数快照，可直接重试。历史尝试 {{ selectedReport.runs?.length || 1 }} 次。</small>
            </div>
          </div>
          <div
            v-else-if="selectedReport.html_content"
            class="document-shell"
            v-html="safeReportHtml"
          />
          <div v-else class="generating-panel">
            <Loading class="rotating" />
            <strong>报告正在生成</strong>
            <p>指标快照与解读完成后会显示在这里。</p>
          </div>
        </template>
        <div v-else class="preview-empty">
          <DataAnalysis />
          <h3>从一次经营复盘开始</h3>
          <p>选择统计周期和营销任务，系统会计算指标并生成结构化报告。</p>
          <el-button type="primary" @click="openGenerate">生成报告</el-button>
        </div>
      </main>
    </section>

    <el-dialog v-model="generateDialogVisible" title="生成营销分析报告" width="680px" destroy-on-close>
      <el-form ref="generateFormRef" :model="generateForm" :rules="generateRules" label-position="top">
        <div class="form-grid">
          <el-form-item label="报告模板" prop="template_id">
            <el-select v-model="generateForm.template_id" placeholder="选择报告模板">
              <el-option
                v-for="template in metadata.templates.filter((item) => item.active)"
                :key="template.id"
                :label="`${template.name} · V${template.version}`"
                :value="template.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="营销任务">
            <el-select v-model="generateForm.task_id" clearable filterable placeholder="全部营销任务">
              <el-option v-for="task in metadata.tasks" :key="task.id" :label="task.name" :value="task.id" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="统计周期" prop="period">
          <el-date-picker
            v-model="generateForm.period"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="转化归因方式">
          <el-radio-group v-model="generateForm.attribution_method">
            <el-radio-button value="LAST_TOUCH">最终点击</el-radio-button>
            <el-radio-button value="LINEAR">线性归因</el-radio-button>
          </el-radio-group>
          <span class="form-hint">最终点击将收入计入最近触达；线性归因会平均分配给周期内各触达批次。</span>
        </el-form-item>
        <el-form-item label="报告标题">
          <el-input v-model="generateForm.title" maxlength="256" placeholder="留空则按模板自动生成" />
        </el-form-item>
        <div class="finance-box">
          <div class="finance-title">
            <strong>经营投入参数</strong>
            <span>用于计算边际贡献和 ROI；暂未接财务系统时可手动录入</span>
          </div>
          <div class="form-grid three-cols">
            <el-form-item label="归因收入（元）">
              <el-input-number v-model="generateForm.attributed_revenue" :min="0" :precision="2" controls-position="right" />
            </el-form-item>
            <el-form-item label="营销投入（元）">
              <el-input-number v-model="generateForm.marketing_cost" :min="0" :precision="2" controls-position="right" />
            </el-form-item>
            <el-form-item label="变动成本（元）">
              <el-input-number v-model="generateForm.variable_cost" :min="0" :precision="2" controls-position="right" />
            </el-form-item>
          </div>
        </div>
        <div class="ai-option" :class="{ enabled: generateForm.use_llm }">
          <div>
            <strong>启用模型智能解读</strong>
            <span>关闭时仍会生成基于规则的完整报告</span>
          </div>
          <el-switch v-model="generateForm.use_llm" />
        </div>
        <el-form-item v-if="generateForm.use_llm" label="分析模型" prop="model_id">
          <el-select v-model="generateForm.model_id" filterable placeholder="选择已配置的 LLM">
            <el-option
              v-for="model in metadata.models"
              :key="model.id"
              :label="`${model.name} · ${model.provider}`"
              :value="model.id"
            />
          </el-select>
          <span v-if="!metadata.models.length" class="form-hint">当前工作空间没有可用 LLM，可关闭智能解读后生成。</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="submitGenerate">开始生成</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="templateDrawerVisible" title="报告模板" size="620px">
      <div class="template-toolbar">
        <p>模板控制报告标题与智能解读要求，修改后自动增加版本号。</p>
        <el-button type="primary" :icon="Plus" @click="openTemplateEditor()">新建模板</el-button>
      </div>
      <div class="template-list">
        <article v-for="template in metadata.templates" :key="template.id">
          <div>
            <span class="template-version">V{{ template.version }}</span>
            <el-tag size="small" :type="template.active ? 'success' : 'info'">
              {{ template.active ? '启用' : '停用' }}
            </el-tag>
          </div>
          <h4>{{ template.name }}</h4>
          <p>{{ template.description || '暂无说明' }}</p>
          <small>{{ template.title_template }}</small>
          <footer>
            <el-button link type="primary" @click="openTemplateEditor(template)">编辑</el-button>
            <el-button
              v-if="template.name !== '经营成效分析模板'"
              link
              type="danger"
              @click="removeTemplate(template)"
            >
              删除
            </el-button>
          </footer>
        </article>
      </div>
    </el-drawer>

    <el-drawer v-model="subscriptionDrawerVisible" title="报告订阅" size="680px">
      <div class="template-toolbar">
        <p>按天、周或月自动生成报告；结果统一进入右上角告警铃铛，可选邮件同步送达。</p>
        <el-button type="primary" :icon="Plus" @click="openSubscriptionEditor()">新建订阅</el-button>
      </div>
      <div v-loading="subscriptionLoading" class="subscription-list">
        <article v-for="item in subscriptions" :key="item.id">
          <div class="subscription-heading">
            <div>
              <el-tag size="small" :type="item.enabled ? 'success' : 'info'">
                {{ item.enabled ? '执行中' : '已停用' }}
              </el-tag>
              <strong>{{ item.name }}</strong>
            </div>
            <span>{{ frequencyLabel[item.frequency] }} · {{ item.run_time.slice(0, 5) }}</span>
          </div>
          <p>{{ item.template_name }} · {{ item.task_name }} · 最近 {{ item.period_days }} 天</p>
          <small>
            下次执行 {{ formatDate(item.next_run_at) }}
            <template v-if="item.email_enabled"> · 邮件 {{ item.recipient_emails.join('、') }}</template>
          </small>
          <footer>
            <el-button link type="primary" :loading="runningSubscriptionId === item.id" @click="runSubscription(item)">立即执行</el-button>
            <el-button link type="primary" @click="openSubscriptionEditor(item)">编辑</el-button>
            <el-button link type="danger" @click="removeSubscription(item)">删除</el-button>
          </footer>
        </article>
        <el-empty v-if="!subscriptionLoading && !subscriptions.length" description="还没有报告订阅" />
      </div>
    </el-drawer>

    <el-dialog
      v-model="subscriptionDialogVisible"
      :title="editingSubscriptionId ? '编辑报告订阅' : '新建报告订阅'"
      width="680px"
      append-to-body
    >
      <el-form ref="subscriptionFormRef" :model="subscriptionForm" :rules="subscriptionRules" label-position="top">
        <div class="form-grid">
          <el-form-item label="订阅名称" prop="name">
            <el-input v-model="subscriptionForm.name" maxlength="128" />
          </el-form-item>
          <el-form-item label="报告模板" prop="template_id">
            <el-select v-model="subscriptionForm.template_id">
              <el-option v-for="item in metadata.templates.filter((row) => row.active)" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="营销任务">
            <el-select v-model="subscriptionForm.task_id" clearable placeholder="全部营销任务">
              <el-option v-for="item in metadata.tasks" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="统计范围">
            <el-input-number v-model="subscriptionForm.period_days" :min="1" :max="365" />
            <span class="form-hint">每次统计最近若干天</span>
          </el-form-item>
          <el-form-item label="执行频率">
            <el-select v-model="subscriptionForm.frequency">
              <el-option label="每天" value="DAILY" />
              <el-option label="每周" value="WEEKLY" />
              <el-option label="每月" value="MONTHLY" />
            </el-select>
          </el-form-item>
          <el-form-item label="执行时间">
            <el-time-picker v-model="subscriptionForm.run_time" value-format="HH:mm:ss" format="HH:mm" />
          </el-form-item>
          <el-form-item v-if="subscriptionForm.frequency === 'WEEKLY'" label="执行日">
            <el-select v-model="subscriptionForm.weekday">
              <el-option v-for="(label, index) in weekdayLabels" :key="label" :label="label" :value="index" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="subscriptionForm.frequency === 'MONTHLY'" label="每月日期">
            <el-input-number v-model="subscriptionForm.month_day" :min="1" :max="28" />
          </el-form-item>
          <el-form-item label="归因方式">
            <el-select v-model="subscriptionForm.attribution_method">
              <el-option label="最终点击" value="LAST_TOUCH" />
              <el-option label="线性归因" value="LINEAR" />
            </el-select>
          </el-form-item>
          <el-form-item label="订阅状态">
            <el-switch v-model="subscriptionForm.enabled" active-text="启用" inactive-text="停用" />
          </el-form-item>
        </div>
        <div class="ai-option" :class="{ enabled: subscriptionForm.use_llm }">
          <div><strong>模型智能解读</strong><span>关闭时使用稳定的规则分析，开启后由所选 LLM 补充经营建议。</span></div>
          <el-switch v-model="subscriptionForm.use_llm" />
        </div>
        <el-form-item v-if="subscriptionForm.use_llm" label="分析模型">
          <el-select v-model="subscriptionForm.model_id" filterable placeholder="选择已配置的 LLM">
            <el-option v-for="item in metadata.models" :key="item.id" :label="`${item.name} · ${item.provider}`" :value="item.id" />
          </el-select>
        </el-form-item>
        <div class="ai-option" :class="{ enabled: subscriptionForm.email_enabled }">
          <div><strong>邮件同步送达</strong><span>无论是否启用邮件，报告都会进入全局通知铃铛。</span></div>
          <el-switch v-model="subscriptionForm.email_enabled" />
        </div>
        <el-form-item v-if="subscriptionForm.email_enabled" label="接收邮箱" prop="recipientText">
          <el-input v-model="subscriptionRecipientText" placeholder="多个邮箱用逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="subscriptionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingSubscription" @click="saveSubscription">保存订阅</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="templateDialogVisible"
      :title="editingTemplateId ? '编辑报告模板' : '新建报告模板'"
      width="620px"
      append-to-body
    >
      <el-form ref="templateFormRef" :model="templateForm" :rules="templateRules" label-position="top">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="templateForm.name" maxlength="128" />
        </el-form-item>
        <el-form-item label="模板说明">
          <el-input v-model="templateForm.description" type="textarea" :rows="2" maxlength="500" />
        </el-form-item>
        <el-form-item label="标题格式" prop="title_template">
          <el-input v-model="templateForm.title_template" maxlength="256" />
          <span class="form-hint">支持 {start_date}、{end_date}、{task_name}</span>
        </el-form-item>
        <el-form-item label="智能解读要求" prop="narrative_prompt">
          <el-input v-model="templateForm.narrative_prompt" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item label="模板状态">
          <el-switch v-model="templateForm.active" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingTemplate" @click="saveTemplate">保存模板</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import DOMPurify from 'dompurify'
import {
  ArrowRight,
  Calendar,
  DataAnalysis,
  Download,
  Loading,
  Plus,
  Refresh,
  RefreshRight,
  Search,
  Setting,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useRoute } from 'vue-router'

import {
  createReportSubscription,
  createReportTemplate,
  deleteReportTemplate,
  deleteReportSubscription,
  downloadReport,
  generateReport,
  getReportDetail,
  getReportMetadata,
  getReportPage,
  getReportSubscriptions,
  retryReport,
  runReportSubscription,
  updateReportSubscription,
  updateReportTemplate,
  type MarketingAttributionMethod,
  type MarketingAnalysisReport,
  type MarketingReportGeneratePayload,
  type MarketingReportMetadata,
  type MarketingReportStatus,
  type MarketingReportSubscription,
  type MarketingReportSubscriptionFrequency,
  type MarketingReportSubscriptionPayload,
  type MarketingReportTemplate,
  type MarketingReportTemplatePayload,
} from '@/api/marketing/report'

interface GenerateFormState extends Omit<MarketingReportGeneratePayload, 'period_start' | 'period_end'> {
  period: string[]
  attributed_revenue: number
  marketing_cost: number
  variable_cost: number
}

const route = useRoute()

const listLoading = ref(false)
const detailLoading = ref(false)
const generating = ref(false)
const retrying = ref(false)
const savingTemplate = ref(false)
const downloading = ref(false)
const subscriptionLoading = ref(false)
const savingSubscription = ref(false)
const runningSubscriptionId = ref('')
const generateDialogVisible = ref(false)
const templateDrawerVisible = ref(false)
const templateDialogVisible = ref(false)
const subscriptionDrawerVisible = ref(false)
const subscriptionDialogVisible = ref(false)
const editingTemplateId = ref('')
const editingSubscriptionId = ref('')
const generateFormRef = ref<FormInstance>()
const templateFormRef = ref<FormInstance>()
const subscriptionFormRef = ref<FormInstance>()
const reports = ref<MarketingAnalysisReport[]>([])
const selectedReport = ref<MarketingAnalysisReport>()
const metadata = ref<MarketingReportMetadata>({ templates: [], tasks: [], models: [] })
const subscriptions = ref<MarketingReportSubscription[]>([])
const pagination = reactive({ current: 1, size: 10, total: 0 })
const filters = reactive<{ keyword: string; status: MarketingReportStatus | '' }>({ keyword: '', status: '' })

const defaultPrompt =
  '你是电信营销分析师。请根据指标数据输出一段简洁、客观、可执行的中文经营分析，依次说明核心表现、主要问题和下一步建议。不要虚构数据。'

const generateForm = reactive<GenerateFormState>({
  template_id: null,
  task_id: null,
  model_id: null,
  title: '',
  period: defaultPeriod(),
  attribution_method: 'LAST_TOUCH',
  attributed_revenue: 0,
  marketing_cost: 0,
  variable_cost: 0,
  use_llm: false,
})

const subscriptionRecipientText = ref('')
const subscriptionForm = reactive<MarketingReportSubscriptionPayload>({
  name: '',
  template_id: '',
  task_id: null,
  model_id: null,
  frequency: 'WEEKLY',
  run_time: '09:00:00',
  weekday: 0,
  month_day: 1,
  period_days: 7,
  attribution_method: 'LAST_TOUCH',
  use_llm: false,
  email_enabled: false,
  recipient_emails: [],
  enabled: true,
})

const templateForm = reactive<MarketingReportTemplatePayload>({
  name: '',
  description: '',
  title_template: '{start_date} 至 {end_date} 营销分析报告',
  narrative_prompt: defaultPrompt,
  active: true,
})

const generateRules = computed<FormRules>(() => ({
  template_id: [{ required: true, message: '请选择报告模板', trigger: 'change' }],
  period: [{ required: true, type: 'array', min: 2, message: '请选择统计周期', trigger: 'change' }],
  model_id: generateForm.use_llm
    ? [{ required: true, message: '请选择智能解读模型', trigger: 'change' }]
    : [],
}))

const templateRules: FormRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  title_template: [{ required: true, message: '请输入标题格式', trigger: 'blur' }],
  narrative_prompt: [{ required: true, message: '请输入智能解读要求', trigger: 'blur' }],
}

const subscriptionRules: FormRules = {
  name: [{ required: true, message: '请输入订阅名称', trigger: 'blur' }],
  template_id: [{ required: true, message: '请选择报告模板', trigger: 'change' }],
}

const frequencyLabel: Record<MarketingReportSubscriptionFrequency, string> = {
  DAILY: '每天',
  WEEKLY: '每周',
  MONTHLY: '每月',
}
const weekdayLabels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const statusLabel: Record<MarketingReportStatus, string> = {
  PENDING: '待生成',
  RUNNING: '生成中',
  SUCCESS: '已完成',
  FAILED: '生成失败',
}

const statusType: Record<MarketingReportStatus, 'info' | 'warning' | 'success' | 'danger'> = {
  PENDING: 'info',
  RUNNING: 'warning',
  SUCCESS: 'success',
  FAILED: 'danger',
}

const safeReportHtml = computed(() => DOMPurify.sanitize(selectedReport.value?.html_content || ''))

function localDate(date: Date) {
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 10)
}

function defaultPeriod() {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - 29)
  return [localDate(start), localDate(end)]
}

function formatDate(value?: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value.replace('T', ' ').slice(0, 16)
  const pad = (part: number) => String(part).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function metricValue(key: 'touch_rate' | 'conversion_rate' | 'roi', suffix = '') {
  const value = selectedReport.value?.metrics?.[key]
  return typeof value === 'number' ? `${value}${suffix}` : '—'
}

async function loadMetadata() {
  const response = await getReportMetadata()
  metadata.value = response.data
  if (!generateForm.template_id && metadata.value.templates.length) {
    generateForm.template_id = metadata.value.templates.find((item) => item.active)?.id || null
  }
}

async function loadReports(page = pagination.current, preferredId?: string) {
  pagination.current = page
  const response = await getReportPage(
    { current_page: page, page_size: pagination.size },
    { keyword: filters.keyword || undefined, status: filters.status || undefined },
    listLoading,
  )
  reports.value = response.data.records
  pagination.total = response.data.total
  const reportId = preferredId || selectedReport.value?.id || reports.value[0]?.id
  if (reportId && reports.value.some((item) => item.id === reportId)) await selectReport(reportId)
  else if (reports.value[0]) await selectReport(reports.value[0].id)
  else selectedReport.value = undefined
}

async function selectReport(id: string) {
  const response = await getReportDetail(id, detailLoading)
  selectedReport.value = response.data
}

function openGenerate() {
  generateForm.period = defaultPeriod()
  generateForm.title = ''
  generateDialogVisible.value = true
}

async function submitGenerate() {
  if (!(await generateFormRef.value?.validate().catch(() => false))) return
  const [period_start, period_end] = generateForm.period
  const response = await generateReport(
    {
      template_id: generateForm.template_id,
      task_id: generateForm.task_id,
      model_id: generateForm.use_llm ? generateForm.model_id : null,
      title: generateForm.title,
      period_start,
      period_end,
      attribution_method: generateForm.attribution_method as MarketingAttributionMethod,
      attributed_revenue: generateForm.attributed_revenue,
      marketing_cost: generateForm.marketing_cost,
      variable_cost: generateForm.variable_cost,
      use_llm: generateForm.use_llm,
    },
    generating,
  )
  generateDialogVisible.value = false
  selectedReport.value = response.data
  await loadReports(1, response.data.id)
  window.dispatchEvent(new CustomEvent('marketing-notification-updated'))
  if (response.data.status === 'SUCCESS') ElMessage.success('分析报告已生成')
  else ElMessage.warning('报告生成失败，参数已保留，可在报告库中重试')
}

async function handleDownload(command: 'html' | 'pdf' | 'docx') {
  if (!selectedReport.value) return
  await downloadReport(selectedReport.value.id, command, downloading)
  ElMessage.success('报告文件已下载')
}

async function openSubscriptionDrawer() {
  subscriptionDrawerVisible.value = true
  const response = await getReportSubscriptions(subscriptionLoading)
  subscriptions.value = response.data
}

function openSubscriptionEditor(item?: MarketingReportSubscription) {
  editingSubscriptionId.value = item?.id || ''
  const activeTemplate = metadata.value.templates.find((row) => row.active)
  Object.assign(subscriptionForm, {
    name: item?.name || '',
    template_id: item?.template_id || activeTemplate?.id || '',
    task_id: item?.task_id || null,
    model_id: item?.model_id || null,
    frequency: item?.frequency || 'WEEKLY',
    run_time: item?.run_time || '09:00:00',
    weekday: item?.weekday ?? 0,
    month_day: item?.month_day ?? 1,
    period_days: item?.period_days ?? 7,
    attribution_method: item?.attribution_method || 'LAST_TOUCH',
    use_llm: item?.use_llm ?? false,
    email_enabled: item?.email_enabled ?? false,
    recipient_emails: item?.recipient_emails || [],
    enabled: item?.enabled ?? true,
  })
  subscriptionRecipientText.value = (item?.recipient_emails || []).join(', ')
  subscriptionDialogVisible.value = true
}

async function saveSubscription() {
  if (!(await subscriptionFormRef.value?.validate().catch(() => false))) return
  const recipient_emails = subscriptionRecipientText.value
    .split(/[，,;；\s]+/)
    .map((value) => value.trim())
    .filter(Boolean)
  if (subscriptionForm.email_enabled && !recipient_emails.length) {
    ElMessage.warning('启用邮件时至少填写一个接收邮箱')
    return
  }
  const payload = { ...subscriptionForm, recipient_emails }
  if (editingSubscriptionId.value) {
    await updateReportSubscription(editingSubscriptionId.value, payload, savingSubscription)
  } else {
    await createReportSubscription(payload, savingSubscription)
  }
  subscriptionDialogVisible.value = false
  await openSubscriptionDrawer()
  ElMessage.success('报告订阅已保存')
}

async function runSubscription(item: MarketingReportSubscription) {
  runningSubscriptionId.value = item.id
  try {
    const response = await runReportSubscription(item.id)
    await Promise.all([openSubscriptionDrawer(), loadReports(1, response.data.report_id)])
    window.dispatchEvent(new CustomEvent('marketing-notification-updated'))
    ElMessage.success('订阅报告已执行')
  } finally {
    runningSubscriptionId.value = ''
  }
}

async function removeSubscription(item: MarketingReportSubscription) {
  await ElMessageBox.confirm(`确认删除订阅“${item.name}”吗？`, '删除订阅', { type: 'warning' })
  await deleteReportSubscription(item.id)
  await openSubscriptionDrawer()
  ElMessage.success('报告订阅已删除')
}

async function retrySelected() {
  if (!selectedReport.value) return
  const response = await retryReport(selectedReport.value.id, retrying)
  selectedReport.value = response.data
  await loadReports(pagination.current, response.data.id)
  window.dispatchEvent(new CustomEvent('marketing-notification-updated'))
  if (response.data.status === 'SUCCESS') ElMessage.success('报告重试成功')
  else ElMessage.warning('重试仍未完成，请检查模型服务后再次尝试')
}

function openTemplateEditor(template?: MarketingReportTemplate) {
  editingTemplateId.value = template?.id || ''
  Object.assign(templateForm, {
    name: template?.name || '',
    description: template?.description || '',
    title_template: template?.title_template || '{start_date} 至 {end_date} 营销分析报告',
    narrative_prompt: template?.narrative_prompt || defaultPrompt,
    active: template?.active ?? true,
  })
  templateDialogVisible.value = true
}

async function saveTemplate() {
  if (!(await templateFormRef.value?.validate().catch(() => false))) return
  if (editingTemplateId.value) {
    await updateReportTemplate(editingTemplateId.value, { ...templateForm }, savingTemplate)
  } else {
    await createReportTemplate({ ...templateForm }, savingTemplate)
  }
  templateDialogVisible.value = false
  await loadMetadata()
  ElMessage.success('报告模板已保存')
}

async function removeTemplate(template: MarketingReportTemplate) {
  await ElMessageBox.confirm(`确认删除模板“${template.name}”吗？历史报告不会受影响。`, '删除模板', {
    type: 'warning',
  })
  await deleteReportTemplate(template.id)
  await loadMetadata()
  ElMessage.success('报告模板已删除')
}

onMounted(async () => {
  await loadMetadata()
  const reportId = typeof route.query.report_id === 'string' ? route.query.report_id : undefined
  await loadReports(1, reportId)
})
</script>

<style scoped lang="scss">
.report-page {
  --ink: #13202d;
  --muted: #677685;
  --line: #dfe5e8;
  --paper: #fbfaf6;
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding: 20px 24px 28px;
  color: var(--ink);
  background:
    radial-gradient(circle at 88% 0%, rgb(12 139 143 / 10%), transparent 30%),
    linear-gradient(180deg, #f7f9f8 0%, #edf1f1 100%);
}

.report-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  min-height: 130px;
  padding: 26px 30px;
  border-radius: 18px 18px 4px 4px;
  color: #fff;
  background:
    linear-gradient(100deg, rgb(7 33 46 / 96%), rgb(11 67 74 / 92%)),
    repeating-linear-gradient(90deg, transparent, transparent 38px, rgb(255 255 255 / 3%) 39px);
  box-shadow: 0 14px 35px rgb(18 45 54 / 16%);
}

.eyebrow,
.section-heading span {
  color: #7ed5cd;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.hero-copy h2 {
  margin: 8px 0 6px;
  font-family: Georgia, 'Noto Serif SC', serif;
  font-size: 29px;
  font-weight: 600;
}

.hero-copy p { margin: 0; color: rgb(255 255 255 / 68%); }
.hero-actions { display: flex; gap: 10px; }

.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 16px;
  border: 1px solid var(--line);
  border-top: 0;
  border-radius: 0 0 14px 14px;
  background: rgb(255 255 255 / 86%);
}

.summary-strip > div { position: relative; padding: 18px 22px; }
.summary-strip > div + div::before { position: absolute; inset: 18px auto 18px 0; width: 1px; content: ''; background: var(--line); }
.summary-strip span, .summary-strip small { display: block; color: var(--muted); }
.summary-strip span { font-size: 12px; }
.summary-strip strong { display: block; margin: 5px 0; font-family: 'DIN Alternate', Arial, sans-serif; font-size: 25px; }
.summary-strip small { font-size: 11px; }
.summary-strip .accent-metric strong { color: #c2642e; }

.report-workbench {
  display: grid;
  grid-template-columns: minmax(300px, 360px) minmax(0, 1fr);
  min-height: 610px;
  border: 1px solid var(--line);
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
}

.report-library { display: flex; min-height: 0; padding: 20px 18px; border-right: 1px solid var(--line); flex-direction: column; background: #f8faf9; }
.section-heading { display: flex; align-items: center; justify-content: space-between; }
.section-heading h3 { margin: 3px 0 0; font-size: 20px; }
.section-heading span { color: #247d7b; }
.filters { display: grid; grid-template-columns: 1fr 120px; gap: 8px; margin: 16px 0 12px; }
.report-list { min-height: 220px; flex: 1; }
.report-item { display: grid; width: 100%; padding: 14px 10px; border: 0; border-bottom: 1px solid #e6ebeb; text-align: left; color: inherit; background: transparent; cursor: pointer; grid-template-columns: 9px minmax(0, 1fr) 16px; gap: 10px; align-items: center; transition: 160ms ease; }
.report-item:hover, .report-item.active { margin-left: -4px; padding-left: 14px; border-radius: 9px; background: #fff; box-shadow: 0 8px 20px rgb(22 53 59 / 8%); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #9aa5ad; }
.status-dot.is-success { background: #1f9d75; }.status-dot.is-failed { background: #d85c4a; }.status-dot.is-running { background: #d39138; }
.report-item-copy { min-width: 0; }
.report-item-copy strong, .report-item-copy small, .report-item-copy span { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.report-item-copy strong { margin-bottom: 5px; font-size: 14px; }
.report-item-copy small, .report-item-copy span { color: var(--muted); font-size: 11px; line-height: 1.6; }
.report-arrow { width: 14px; color: #84949c; }

.report-preview { min-width: 0; min-height: 610px; background: #eef2f1; }
.preview-toolbar { display: flex; min-height: 60px; padding: 0 22px; border-bottom: 1px solid var(--line); align-items: center; justify-content: space-between; background: #fff; }
.preview-toolbar > div { display: flex; gap: 14px; align-items: center; color: var(--muted); font-size: 12px; }
.document-shell { max-width: 900px; margin: 24px auto; padding: 0 24px; }

:deep(.analysis-report-document) { padding: 52px 60px; border-top: 5px solid #0d7c7c; color: #27323b; background: var(--paper); box-shadow: 0 18px 42px rgb(31 52 60 / 15%); }
:deep(.analysis-report-document header) { padding-bottom: 28px; border-bottom: 1px solid #cfd7d6; }
:deep(.analysis-report-document header p) { margin: 0; color: #0d7c7c; font-size: 11px; font-weight: 700; letter-spacing: .18em; }
:deep(.analysis-report-document h1) { margin: 12px 0 10px; font-family: Georgia, 'Noto Serif SC', serif; font-size: 30px; line-height: 1.35; }
:deep(.analysis-report-document header span) { color: #718087; font-size: 12px; }
:deep(.analysis-report-document section) { margin-top: 30px; }
:deep(.analysis-report-document h2) { margin: 0 0 14px; font-size: 16px; }
:deep(.analysis-report-document table) { width: 100%; border-collapse: collapse; }
:deep(.analysis-report-document th), :deep(.analysis-report-document td) { padding: 10px 12px; border-bottom: 1px solid #dde2df; text-align: left; }
:deep(.analysis-report-document th) { width: 40%; color: #68767b; font-weight: 500; }
:deep(.analysis-report-document td) { font-family: 'DIN Alternate', Arial, sans-serif; font-weight: 700; }
:deep(.analysis-report-document section > p), :deep(.analysis-report-document li) { color: #4e5b61; line-height: 1.9; }
:deep(.attribution-bar) { margin: 14px 0; }
:deep(.attribution-bar > div) { display: flex; margin-bottom: 6px; align-items: center; justify-content: space-between; color: #4e5b61; }
:deep(.attribution-bar span) { color: #718087; font-size: 12px; }
:deep(.attribution-bar i) { display: block; min-width: 3px; height: 8px; border-radius: 8px; background: linear-gradient(90deg, #0d7c7c, #55b9ae); }
.preview-actions { display: flex; gap: 8px; }

.failure-panel, .generating-panel, .preview-empty { display: flex; align-items: center; justify-content: center; min-height: 500px; color: var(--muted); flex-direction: column; text-align: center; }
.failure-panel { margin: 30px; min-height: 220px; padding: 34px; border: 1px solid #f0c6bf; border-radius: 12px; color: #8d4539; background: #fff6f4; flex-direction: row; gap: 18px; text-align: left; justify-content: flex-start; }
.failure-panel > svg, .preview-empty > svg, .generating-panel > svg { width: 40px; height: 40px; }
.failure-panel p { margin: 8px 0; }
.failure-panel small { color: #9b6a62; }
.preview-empty > svg { width: 56px; height: 56px; color: #3b9996; }
.preview-empty h3 { margin: 18px 0 4px; color: var(--ink); }
.preview-empty p, .generating-panel p { margin: 4px 0 18px; }
.rotating { animation: rotate 1.2s linear infinite; }
@keyframes rotate { to { transform: rotate(360deg); } }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-grid.three-cols { grid-template-columns: repeat(3, 1fr); }
.form-grid :deep(.el-select), .form-grid :deep(.el-input-number) { width: 100%; }
.finance-box { margin-bottom: 18px; padding: 16px 16px 0; border: 1px solid #dde5e3; border-radius: 10px; background: #f7faf9; }
.finance-title { margin-bottom: 12px; }.finance-title strong, .finance-title span { display: block; }.finance-title span, .form-hint { margin-top: 4px; color: var(--muted); font-size: 12px; }
.ai-option { display: flex; margin-bottom: 18px; padding: 14px 16px; border: 1px solid var(--line); border-radius: 10px; align-items: center; justify-content: space-between; }
.ai-option.enabled { border-color: #84bbb6; background: #f1faf8; }.ai-option strong, .ai-option span { display: block; }.ai-option span { margin-top: 3px; color: var(--muted); font-size: 12px; }
.template-toolbar { display: flex; margin-bottom: 18px; align-items: center; justify-content: space-between; }.template-toolbar p { max-width: 350px; margin: 0; color: var(--muted); font-size: 13px; }
.template-list { display: grid; gap: 12px; }.template-list article { padding: 18px; border: 1px solid var(--line); border-radius: 12px; background: #fbfcfb; }.template-version { margin-right: 8px; color: #167e7c; font-size: 12px; font-weight: 700; }.template-list h4 { margin: 10px 0 5px; }.template-list p, .template-list small { color: var(--muted); }.template-list p { margin: 0 0 8px; }.template-list footer { display: flex; margin-top: 10px; justify-content: flex-end; }
.subscription-list { display: grid; gap: 12px; }
.subscription-list article { padding: 17px 18px; border: 1px solid var(--line); border-radius: 12px; background: #fbfcfb; }
.subscription-heading, .subscription-heading > div { display: flex; align-items: center; justify-content: space-between; gap: 9px; }
.subscription-heading > span, .subscription-list p, .subscription-list small { color: var(--muted); font-size: 12px; }
.subscription-list p { margin: 12px 0 6px; }
.subscription-list footer { display: flex; margin-top: 9px; justify-content: flex-end; }

@media (max-width: 1100px) {
  .report-workbench { grid-template-columns: 310px minmax(0, 1fr); }
  :deep(.analysis-report-document) { padding: 36px; }
}

@media (max-width: 820px) {
  .report-page { padding: 12px; }
  .report-hero { min-height: auto; align-items: flex-start; flex-direction: column; gap: 18px; }
  .summary-strip { grid-template-columns: 1fr 1fr; }
  .summary-strip > div:nth-child(3)::before { display: none; }
  .report-workbench { grid-template-columns: 1fr; }
  .report-library { border-right: 0; border-bottom: 1px solid var(--line); }
  .form-grid, .form-grid.three-cols { grid-template-columns: 1fr; }
}
</style>
