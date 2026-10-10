<template>
  <div class="evaluation-lab" v-loading="loading">
    <header class="lab-header">
      <div>
        <span class="eyebrow">RETRIEVAL LAB / 检索实验台</span>
        <h2>{{ dashboard?.knowledge.name || '知识库检索评估' }}</h2>
        <p>用固定问题集对比不同检索链路，定位“没召回、排位低、模型不可用”的真实原因。</p>
      </div>
      <div class="header-actions">
        <el-button @click="loadDashboard">刷新状态</el-button>
        <el-button :disabled="!dashboard?.latest_run" :loading="exporting" @click="exportLatest">
          导出最近结果
        </el-button>
        <el-button
          type="primary"
          :disabled="!dashboard?.case_summary.enabled_count"
          @click="openRunDialog"
        >
          运行评估
        </el-button>
      </div>
    </header>

    <section class="health-strip">
      <article v-for="item in dashboard?.dependency_health || []" :key="item.key">
        <i :class="`status-${item.status.toLowerCase()}`"></i>
        <div>
          <strong>{{ item.name }}</strong>
          <span>{{ item.detail }}</span>
        </div>
        <small>{{ dependencyLabel(item.status) }}</small>
      </article>
    </section>

    <section class="metric-grid">
      <article>
        <span>启用样本</span>
        <strong>{{ dashboard?.case_summary.enabled_count || 0 }}</strong>
        <small>共 {{ dashboard?.case_summary.total_count || 0 }} 条</small>
      </article>
      <article>
        <span>最佳检索链路</span>
        <strong class="metric-text">{{ latestSummary.best_mode_label || '等待评估' }}</strong>
        <small>按命中率、MRR 和耗时综合排序</small>
      </article>
      <article>
        <span>最佳命中率</span>
        <strong>{{ latestSummary.best_hit_rate || 0 }}%</strong>
        <small>Recall@{{ dashboard?.latest_run?.top_number || 0 }}</small>
      </article>
      <article>
        <span>文档 / 段落目标</span>
        <strong>
          {{ dashboard?.case_summary.document_target_count || 0 }} /
          {{ dashboard?.case_summary.paragraph_target_count || 0 }}
        </strong>
        <small>可按文档或精确段落验收</small>
      </article>
      <article :class="{ 'metric-alert': latestSummary.error_count }">
        <span>执行异常</span>
        <strong>{{ latestSummary.error_count || 0 }}</strong>
        <small>单模式失败不会丢失其他结果</small>
      </article>
    </section>

    <div class="dashboard-grid">
      <el-card shadow="never" class="comparison-card">
        <template #header>
          <div class="card-heading">
            <div>
              <span class="section-index">01</span>
              <strong>检索链路对比</strong>
            </div>
            <span v-if="dashboard?.latest_run">
              {{ datetimeFormat(dashboard.latest_run.create_time) }} · Top
              {{ dashboard.latest_run.top_number }}
            </span>
          </div>
        </template>
        <el-empty
          v-if="!latestSummary.mode_metrics.length"
          description="运行一次评估后展示链路差异"
        />
        <div v-else class="mode-comparison">
          <article v-for="(item, index) in latestSummary.mode_metrics" :key="item.mode">
            <div class="mode-rank">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="mode-name">
              <strong>{{ item.mode_label }}</strong>
              <span
                >{{ item.hit_count }}/{{ item.case_count }} 命中 ·
                {{ item.failed_count }} 异常</span
              >
            </div>
            <div class="score-track">
              <i :style="{ width: `${item.hit_rate}%` }"></i>
            </div>
            <strong class="hit-rate">{{ item.hit_rate }}%</strong>
            <dl>
              <div>
                <dt>MRR</dt>
                <dd>{{ item.mrr }}</dd>
              </div>
              <div>
                <dt>无答案率</dt>
                <dd>{{ item.no_answer_rate }}%</dd>
              </div>
              <div>
                <dt>平均耗时</dt>
                <dd>{{ item.avg_latency_ms }} ms</dd>
              </div>
            </dl>
          </article>
        </div>
      </el-card>

      <el-card shadow="never" class="history-card">
        <template #header>
          <div class="card-heading">
            <div>
              <span class="section-index">02</span>
              <strong>最近执行</strong>
            </div>
            <span>保留可追溯结果</span>
          </div>
        </template>
        <el-empty v-if="!dashboard?.runs.length" description="暂无评估记录" />
        <div v-else class="run-list">
          <button v-for="run in dashboard.runs" :key="run.id" @click="openRunDetail(run.id)">
            <i :class="`run-${run.status.toLowerCase()}`"></i>
            <div>
              <strong>{{ run.summary.best_mode_label || run.status_label }}</strong>
              <span>{{ datetimeFormat(run.create_time) }} · {{ run.user_name }}</span>
            </div>
            <div class="run-score">
              <strong>{{ run.summary.best_hit_rate || 0 }}%</strong>
              <small>{{ run.summary.case_count || 0 }} 个样本</small>
            </div>
          </button>
        </div>
      </el-card>
    </div>

    <el-card shadow="never" class="case-card">
      <template #header>
        <div class="card-heading">
          <div>
            <span class="section-index">03</span>
            <strong>评估问题集</strong>
          </div>
          <div class="case-actions">
            <input
              ref="caseImportInput"
              class="case-import-input"
              type="file"
              accept=".csv,text/csv"
              @change="importCaseFile"
            />
            <el-button :loading="caseExporting" @click="downloadCaseTemplate">下载模板</el-button>
            <el-button :loading="caseImporting" @click="caseImportInput?.click()">
              批量导入
            </el-button>
            <el-button
              :disabled="!dashboard?.case_summary.total_count"
              :loading="caseExporting"
              @click="exportCases"
            >
              导出样本
            </el-button>
            <el-button type="primary" plain @click="openCaseDialog()">新增评估样本</el-button>
          </div>
        </div>
      </template>
      <el-table :data="dashboard?.cases || []" row-key="id">
        <el-table-column label="状态" width="76">
          <template #default="scope">
            <el-tag :type="scope.row.enabled ? 'success' : 'info'" size="small" effect="plain">
              {{ scope.row.enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="question" label="评估问题" min-width="260" show-overflow-tooltip />
        <el-table-column label="期望目标" min-width="260">
          <template #default="scope">
            <div class="expected-target">
              <strong>{{ scope.row.expected_document_name || '答案文本匹配' }}</strong>
              <span v-if="scope.row.expected_paragraph_title">
                段落：{{ scope.row.expected_paragraph_title }}
              </span>
              <span v-else-if="scope.row.expected_answer">
                答案：{{ scope.row.expected_answer }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="update_time" label="最近修改" width="170">
          <template #default="scope">{{ datetimeFormat(scope.row.update_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="openCaseDialog(scope.row)">编辑</el-button>
            <el-button link type="danger" @click="removeCase(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="caseDialogVisible"
      :title="caseForm.id ? '编辑评估样本' : '新增评估样本'"
      width="620px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="评估问题" required>
          <el-input
            v-model="caseForm.question"
            type="textarea"
            :rows="3"
            maxlength="1000"
            show-word-limit
            placeholder="输入真实用户可能提出的问题"
          />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="期望命中文档">
            <el-select
              v-model="caseForm.expected_document_id"
              clearable
              filterable
              placeholder="可选：先定位到文档"
              @change="documentChanged"
            >
              <el-option
                v-for="document in dashboard?.documents || []"
                :key="document.id"
                :label="document.name"
                :value="document.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="期望命中段落">
            <el-select
              v-model="caseForm.expected_paragraph_id"
              :disabled="!caseForm.expected_document_id"
              :loading="paragraphLoading"
              clearable
              filterable
              placeholder="可选：精确到段落"
            >
              <el-option
                v-for="paragraph in paragraphOptions"
                :key="paragraph.id"
                :label="paragraph.title || paragraph.content"
                :value="paragraph.id"
              />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="期望答案">
          <el-input
            v-model="caseForm.expected_answer"
            type="textarea"
            :rows="3"
            placeholder="没有固定文档时，可填写应出现在召回内容中的关键答案"
          />
        </el-form-item>
        <el-form-item>
          <el-switch v-model="caseForm.enabled" active-text="参与后续评估" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="caseSaving" @click="saveCase">保存样本</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="runDialogVisible" title="运行检索评估" width="620px">
      <div class="run-callout">
        本次将执行
        {{ dashboard?.case_summary.enabled_count || 0 }}
        个启用样本。每种模式独立记录结果，单个依赖失败不会丢失其他模式数据。
      </div>
      <el-form label-position="top">
        <el-form-item label="对比模式" required>
          <el-checkbox-group v-model="runForm.search_modes">
            <el-checkbox value="embedding">向量检索</el-checkbox>
            <el-checkbox value="keywords">关键词检索</el-checkbox>
            <el-checkbox value="blend">混合检索</el-checkbox>
            <el-checkbox value="reranker" :disabled="!dashboard?.reranker_models.length">
              混合检索 + 重排
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item v-if="runForm.search_modes.includes('reranker')" label="重排模型" required>
          <el-select v-model="runForm.reranker_model_id" placeholder="选择重排模型">
            <el-option
              v-for="model in dashboard?.reranker_models || []"
              :key="model.id"
              :label="`${model.name} · ${model.model_name}`"
              :value="model.id"
            />
          </el-select>
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="Top K">
            <el-input-number v-model="runForm.top_number" :min="1" :max="50" />
          </el-form-item>
          <el-form-item label="最低相似度">
            <el-input-number
              v-model="runForm.similarity"
              :min="0"
              :max="2"
              :step="0.05"
              :precision="2"
            />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="runDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="running" @click="startEvaluation">开始执行</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="resultDrawerVisible" title="评估执行详情" size="920px">
      <div v-loading="resultLoading">
        <template v-if="selectedRun">
          <div class="result-summary">
            <div>
              <span>状态</span><strong>{{ selectedRun.status_label }}</strong>
            </div>
            <div>
              <span>最佳链路</span><strong>{{ selectedRun.summary.best_mode_label || '—' }}</strong>
            </div>
            <div>
              <span>最佳命中率</span><strong>{{ selectedRun.summary.best_hit_rate || 0 }}%</strong>
            </div>
            <div>
              <span>执行人</span><strong>{{ selectedRun.user_name }}</strong>
            </div>
          </div>
          <el-alert
            v-if="selectedRun.error_message"
            title="部分检索链路执行失败"
            :description="selectedRun.error_message"
            type="warning"
            show-icon
            :closable="false"
          />
          <div class="result-actions">
            <el-button @click="exportRun(selectedRun.id)">导出本次结果</el-button>
          </div>
          <el-table :data="selectedRun.results || []" row-key="id">
            <el-table-column label="结果" width="76">
              <template #default="scope">
                <el-tag
                  :type="scope.row.error_message ? 'danger' : scope.row.hit ? 'success' : 'warning'"
                  size="small"
                >
                  {{ scope.row.error_message ? '异常' : scope.row.hit ? '命中' : '未命中' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="mode_label" label="模式" width="150" />
            <el-table-column prop="question" label="问题" min-width="220" show-overflow-tooltip />
            <el-table-column label="排名" width="80">
              <template #default="scope">{{ scope.row.expected_rank || '—' }}</template>
            </el-table-column>
            <el-table-column label="Top 分数" width="100">
              <template #default="scope">{{ Number(scope.row.top_score).toFixed(3) }}</template>
            </el-table-column>
            <el-table-column prop="latency_ms" label="耗时 ms" width="95" />
            <el-table-column type="expand">
              <template #default="scope">
                <div class="match-list">
                  <p v-if="scope.row.error_message" class="result-error">
                    {{ scope.row.error_message }}
                  </p>
                  <article v-for="(match, index) in scope.row.matches" :key="match.paragraph_id">
                    <div>
                      <strong>#{{ index + 1 }} {{ match.document_name }}</strong>
                      <span>{{ match.paragraph_title || '未命名段落' }}</span>
                    </div>
                    <small>
                      综合 {{ match.comprehensive_score.toFixed(3) }}
                      <template
                        v-if="match.reranker_score !== null && match.reranker_score !== undefined"
                      >
                        · 重排 {{ match.reranker_score.toFixed(3) }}
                      </template>
                    </small>
                    <p>{{ match.content }}</p>
                  </article>
                  <el-empty
                    v-if="!scope.row.matches.length && !scope.row.error_message"
                    description="本次没有召回内容"
                    :image-size="52"
                  />
                </div>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import knowledgeEvaluationApi, {
  type KnowledgeDependencyStatus,
  type KnowledgeEvaluationCase,
  type KnowledgeEvaluationCasePayload,
  type KnowledgeEvaluationDashboard,
  type KnowledgeEvaluationRun,
  type KnowledgeEvaluationRunPayload,
  type KnowledgeEvaluationSummary,
} from '@/api/knowledge/evaluation'
import { datetimeFormat } from '@/utils/time'

const route = useRoute()
const knowledgeId = computed(() => String(route.params.id || ''))
const loading = ref(false)
const exporting = ref(false)
const caseExporting = ref(false)
const caseImporting = ref(false)
const running = ref(false)
const caseSaving = ref(false)
const paragraphLoading = ref(false)
const resultLoading = ref(false)
const dashboard = ref<KnowledgeEvaluationDashboard>()
const caseDialogVisible = ref(false)
const runDialogVisible = ref(false)
const resultDrawerVisible = ref(false)
const selectedRun = ref<KnowledgeEvaluationRun>()
const caseImportInput = ref<HTMLInputElement>()
const paragraphOptions = ref<Array<{ id: string; title: string; content: string }>>([])

const emptySummary = (): KnowledgeEvaluationSummary => ({
  case_count: 0,
  mode_count: 0,
  result_count: 0,
  error_count: 0,
  best_mode: '',
  best_mode_label: '',
  best_hit_rate: 0,
  mode_metrics: [],
})
const latestSummary = computed(() => dashboard.value?.latest_run?.summary || emptySummary())

const caseForm = ref<KnowledgeEvaluationCasePayload & { id?: string }>({
  question: '',
  expected_document_id: null,
  expected_paragraph_id: null,
  expected_answer: '',
  enabled: true,
})
const runForm = ref<KnowledgeEvaluationRunPayload>({
  search_modes: ['embedding', 'keywords', 'blend'],
  top_number: 5,
  similarity: 0,
  reranker_model_id: null,
})

function dependencyLabel(status: KnowledgeDependencyStatus) {
  return {
    HEALTHY: '正常',
    WARNING: '需关注',
    ERROR: '不可用',
    NOT_CONFIGURED: '未配置',
  }[status]
}

function loadDashboard() {
  return knowledgeEvaluationApi.getDashboard(knowledgeId.value, loading).then((res) => {
    dashboard.value = res.data
  })
}

function openCaseDialog(row?: KnowledgeEvaluationCase) {
  caseForm.value = row
    ? {
        id: row.id,
        question: row.question,
        expected_document_id: row.expected_document_id,
        expected_paragraph_id: row.expected_paragraph_id,
        expected_answer: row.expected_answer,
        enabled: row.enabled,
      }
    : {
        question: '',
        expected_document_id: null,
        expected_paragraph_id: null,
        expected_answer: '',
        enabled: true,
      }
  paragraphOptions.value = []
  caseDialogVisible.value = true
  if (caseForm.value.expected_document_id) loadParagraphs(caseForm.value.expected_document_id)
}

function loadParagraphs(documentId: string) {
  return knowledgeEvaluationApi
    .getOptions(knowledgeId.value, documentId, paragraphLoading)
    .then((res) => {
      paragraphOptions.value = res.data.paragraphs
    })
}

function documentChanged(value: string | null) {
  caseForm.value.expected_paragraph_id = null
  paragraphOptions.value = []
  if (value) loadParagraphs(value)
}

async function saveCase() {
  if (!caseForm.value.question.trim()) {
    ElMessage.warning('请填写评估问题')
    return
  }
  if (
    !caseForm.value.expected_document_id &&
    !caseForm.value.expected_paragraph_id &&
    !caseForm.value.expected_answer?.trim()
  ) {
    ElMessage.warning('期望文档、期望段落和期望答案至少填写一项')
    return
  }
  caseSaving.value = true
  try {
    const { id, ...payload } = caseForm.value
    if (id) await knowledgeEvaluationApi.updateCase(knowledgeId.value, id, payload)
    else await knowledgeEvaluationApi.createCase(knowledgeId.value, payload)
    caseDialogVisible.value = false
    await loadDashboard()
    ElMessage.success(id ? '评估样本已更新' : '评估样本已创建')
  } finally {
    caseSaving.value = false
  }
}

function removeCase(row: KnowledgeEvaluationCase) {
  ElMessageBox.confirm(
    `确认删除评估问题“${row.question}”吗？历史执行结果会继续保留。`,
    '删除样本',
    {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    },
  )
    .then(async () => {
      await knowledgeEvaluationApi.deleteCase(knowledgeId.value, row.id)
      await loadDashboard()
      ElMessage.success('评估样本已删除')
    })
    .catch(() => undefined)
}

function downloadCaseTemplate() {
  return knowledgeEvaluationApi.downloadCaseTemplate(knowledgeId.value, caseExporting)
}

async function importCaseFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.csv')) {
    ElMessage.warning('请选择 CSV 格式的评估样本文件')
    input.value = ''
    return
  }
  try {
    const res = await knowledgeEvaluationApi.importCases(knowledgeId.value, file, caseImporting)
    await loadDashboard()
    ElMessage.success(
      `已导入 ${res.data.imported_count} 条样本，跳过 ${res.data.skipped_count} 条重复问题`,
    )
  } finally {
    input.value = ''
  }
}

function exportCases() {
  return knowledgeEvaluationApi.exportCases(knowledgeId.value, caseExporting)
}

function openRunDialog() {
  runDialogVisible.value = true
}

async function startEvaluation() {
  if (!runForm.value.search_modes.length) {
    ElMessage.warning('请至少选择一种检索模式')
    return
  }
  if (runForm.value.search_modes.includes('reranker') && !runForm.value.reranker_model_id) {
    ElMessage.warning('请选择重排模型')
    return
  }
  running.value = true
  try {
    const res = await knowledgeEvaluationApi.runEvaluation(knowledgeId.value, runForm.value)
    runDialogVisible.value = false
    selectedRun.value = res.data
    resultDrawerVisible.value = true
    await loadDashboard()
    ElMessage.success('检索评估已完成')
  } finally {
    running.value = false
  }
}

function openRunDetail(runId: string) {
  resultDrawerVisible.value = true
  selectedRun.value = undefined
  knowledgeEvaluationApi.getRun(knowledgeId.value, runId, resultLoading).then((res) => {
    selectedRun.value = res.data
  })
}

function exportRun(runId: string) {
  return knowledgeEvaluationApi.exportRun(knowledgeId.value, runId, exporting)
}

function exportLatest() {
  if (dashboard.value?.latest_run) exportRun(dashboard.value.latest_run.id)
}

onMounted(loadDashboard)
</script>

<style scoped lang="scss">
.evaluation-lab {
  --lab-ink: #18232c;
  --lab-muted: #697782;
  --lab-line: #d9e0e3;
  --lab-paper: #fff;
  --lab-teal: #0f756d;
  --lab-amber: #bd7a12;
  box-sizing: border-box;
  height: 100%;
  min-height: 0;
  padding: 24px;
  overflow-y: auto;
  color: var(--lab-ink);
  background:
    linear-gradient(rgba(27, 54, 65, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(27, 54, 65, 0.035) 1px, transparent 1px), #f4f7f7;
  background-size: 26px 26px;
}

.lab-header,
.header-actions,
.card-heading,
.card-heading > div,
.health-strip article,
.mode-comparison article,
.run-list button,
.result-actions {
  display: flex;
  align-items: center;
}

.lab-header {
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 18px;
  padding: 4px 2px;
}

.lab-header h2 {
  margin: 5px 0 6px;
  font-family: 'Songti SC', 'STSong', serif;
  font-size: 29px;
  letter-spacing: 0.02em;
}

.lab-header p {
  margin: 0;
  color: var(--lab-muted);
}

.eyebrow,
.section-index {
  color: var(--lab-teal);
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.13em;
}

.header-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 9px;
}

.health-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}

.health-strip article {
  position: relative;
  gap: 11px;
  min-width: 0;
  padding: 13px 15px;
  overflow: hidden;
  border: 1px solid var(--lab-line);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.88);
}

.health-strip i,
.run-list i {
  width: 9px;
  height: 9px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #94a1aa;
  box-shadow: 0 0 0 4px rgba(148, 161, 170, 0.12);
}

.health-strip .status-healthy,
.run-list .run-success {
  background: #15926f;
  box-shadow: 0 0 0 4px rgba(21, 146, 111, 0.12);
}

.health-strip .status-warning,
.run-list .run-partial {
  background: #d28b18;
  box-shadow: 0 0 0 4px rgba(210, 139, 24, 0.12);
}

.health-strip .status-error,
.run-list .run-failed {
  background: #c54339;
  box-shadow: 0 0 0 4px rgba(197, 67, 57, 0.12);
}

.health-strip div {
  min-width: 0;
  flex: 1;
}

.health-strip strong,
.health-strip span {
  display: block;
}

.health-strip span {
  margin-top: 3px;
  overflow: hidden;
  color: var(--lab-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.health-strip small {
  color: var(--lab-muted);
  font-size: 11px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}

.metric-grid article {
  min-width: 0;
  padding: 16px;
  border: 1px solid var(--lab-line);
  border-top: 3px solid #b6c4ca;
  border-radius: 7px;
  background: var(--lab-paper);
}

.metric-grid article:nth-child(2),
.metric-grid article:nth-child(3) {
  border-top-color: var(--lab-teal);
}

.metric-grid .metric-alert {
  border-top-color: #c54339;
}

.metric-grid span,
.metric-grid strong,
.metric-grid small {
  display: block;
}

.metric-grid span,
.metric-grid small {
  color: var(--lab-muted);
  font-size: 11px;
}

.metric-grid strong {
  margin: 9px 0 5px;
  font-family: 'DIN Alternate', 'Avenir Next', sans-serif;
  font-size: 25px;
}

.metric-grid .metric-text {
  overflow: hidden;
  font-family: inherit;
  font-size: 17px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(310px, 0.8fr);
  gap: 14px;
  margin-bottom: 14px;
}

.comparison-card,
.history-card,
.case-card {
  border-color: var(--lab-line);
  border-radius: 8px;
}

.card-heading {
  justify-content: space-between;
  gap: 16px;
}

.card-heading > div {
  gap: 10px;
}

.card-heading > div > strong {
  font-size: 16px;
}

.card-heading > span {
  color: var(--lab-muted);
  font-size: 11px;
}

.case-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.case-import-input {
  display: none;
}

.mode-comparison {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.mode-comparison article {
  display: grid;
  grid-template-columns: 30px minmax(150px, 1.1fr) minmax(100px, 1fr) 58px minmax(230px, 1fr);
  gap: 12px;
  padding: 11px 12px;
  border: 1px solid #e2e7e9;
  border-radius: 6px;
  background: #f8faf9;
}

.mode-rank {
  color: #8a989f;
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 12px;
}

.mode-name strong,
.mode-name span {
  display: block;
}

.mode-name span {
  margin-top: 3px;
  color: var(--lab-muted);
  font-size: 11px;
}

.score-track {
  height: 6px;
  overflow: hidden;
  border-radius: 6px;
  background: #dce4e5;
}

.score-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #0e716a, #43aa91);
}

.hit-rate {
  color: var(--lab-teal);
  text-align: right;
}

.mode-comparison dl {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7px;
  margin: 0;
}

.mode-comparison dl div {
  padding-left: 9px;
  border-left: 1px solid var(--lab-line);
}

.mode-comparison dt {
  color: var(--lab-muted);
  font-size: 10px;
}

.mode-comparison dd {
  margin: 3px 0 0;
  font-size: 12px;
  font-weight: 700;
}

.run-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.run-list button {
  width: 100%;
  gap: 10px;
  padding: 10px;
  border: 1px solid transparent;
  border-radius: 5px;
  color: inherit;
  text-align: left;
  background: #f6f8f8;
  cursor: pointer;
}

.run-list button:hover {
  border-color: #abc9c5;
  background: #f0f8f6;
}

.run-list button > div:nth-child(2) {
  min-width: 0;
  flex: 1;
}

.run-list button strong,
.run-list button span,
.run-list button small {
  display: block;
}

.run-list button span,
.run-list button small {
  margin-top: 3px;
  color: var(--lab-muted);
  font-size: 10px;
}

.run-score {
  text-align: right;
}

.expected-target strong,
.expected-target span {
  display: block;
}

.expected-target span {
  margin-top: 3px;
  overflow: hidden;
  color: var(--lab-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.form-grid :deep(.el-select),
.form-grid :deep(.el-input-number) {
  width: 100%;
}

.run-callout {
  margin-bottom: 16px;
  padding: 12px 14px;
  border-left: 3px solid var(--lab-teal);
  color: #47605e;
  font-size: 12px;
  line-height: 1.6;
  background: #eff7f5;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  overflow: hidden;
  margin-bottom: 14px;
  border: 1px solid var(--lab-line);
  border-radius: 6px;
  background: var(--lab-line);
}

.result-summary > div {
  padding: 13px;
  background: #f7f9f9;
}

.result-summary span,
.result-summary strong {
  display: block;
}

.result-summary span {
  margin-bottom: 5px;
  color: var(--lab-muted);
  font-size: 11px;
}

.result-actions {
  justify-content: flex-end;
  margin: 12px 0;
}

.match-list {
  padding: 8px 48px;
}

.match-list article {
  padding: 11px 12px;
  border: 1px solid var(--lab-line);
  border-radius: 5px;
  background: #f8faf9;
}

.match-list article + article {
  margin-top: 8px;
}

.match-list article > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.match-list article span,
.match-list article small,
.match-list article p {
  color: var(--lab-muted);
  font-size: 11px;
}

.match-list article p {
  margin: 7px 0 0;
  line-height: 1.6;
}

.result-error {
  padding: 10px;
  color: #a7352d;
  background: #fff2f0;
}

@media (max-width: 1280px) {
  .metric-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .evaluation-lab {
    padding: 16px;
  }

  .lab-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .health-strip,
  .metric-grid,
  .result-summary {
    grid-template-columns: 1fr;
  }

  .mode-comparison article {
    grid-template-columns: 28px 1fr 54px;
  }

  .score-track,
  .mode-comparison dl {
    grid-column: 2 / -1;
  }
}
</style>
