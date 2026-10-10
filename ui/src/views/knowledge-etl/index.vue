<template>
  <div class="etl-console" v-loading="loading">
    <header class="console-header">
      <div>
        <span class="eyebrow">DATA FACTORY / 非结构化数据工厂</span>
        <h2>{{ dashboard?.knowledge.name || '知识库 ETL' }}</h2>
        <p>从现有文档产物构建可审计的向量索引版本，通过质量门禁后再发布上线。</p>
      </div>
      <div class="header-actions">
        <el-button @click="loadDashboard">刷新</el-button>
        <el-button type="primary" :disabled="!dashboard?.documents.length" @click="openRunDialog">
          新建 ETL 运行
        </el-button>
      </div>
    </header>

    <section class="metric-grid">
      <article>
        <span>可用文档</span>
        <strong>{{ dashboard?.summary.document_count || 0 }}</strong>
        <small>当前知识库已启用文档</small>
      </article>
      <article>
        <span>当前线上版本</span>
        <strong class="metric-text">{{ dashboard?.summary.published_version || '未发布' }}</strong>
        <small>发布与回滚均保留记录</small>
      </article>
      <article>
        <span>候选版本</span>
        <strong>{{ dashboard?.summary.candidate_count || 0 }}</strong>
        <small>已通过质量门禁，等待发布</small>
      </article>
      <article :class="{ alert: dashboard?.summary.failed_run_count }">
        <span>失败运行</span>
        <strong>{{ dashboard?.summary.failed_run_count || 0 }}</strong>
        <small>修复数据后可以原配置重试</small>
      </article>
    </section>

    <section class="stage-map">
      <article v-for="(stage, index) in stageGuide" :key="stage.name">
        <span>{{ String(index + 1).padStart(2, '0') }}</span>
        <div>
          <strong>{{ stage.name }}</strong>
          <small>{{ stage.description }}</small>
        </div>
      </article>
    </section>

    <el-card shadow="never" class="section-card run-card">
      <template #header>
        <div class="card-heading">
          <div><span>01</span><strong>ETL 运行</strong></div>
          <small>解析 → 清洗 → 切分 → 向量化 → 质量门禁 → 版本固化</small>
        </div>
      </template>
      <el-empty v-if="!dashboard?.runs.length" description="暂无 ETL 运行，先创建第一版索引" />
      <el-table v-else :data="dashboard.runs" row-key="id">
        <el-table-column label="运行" width="104">
          <template #default="scope">
            <div class="run-number">
              <strong>#{{ scope.row.run_number }}</strong>
              <small>{{ scope.row.trigger_label }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="scope">
            <el-tag :type="statusType(scope.row.status)" size="small" effect="plain">
              {{ scope.row.status_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="处理范围" min-width="170">
          <template #default="scope">
            {{ scope.row.document_ids.length }} 份文档 · {{ scope.row.current_stage_label }}
          </template>
        </el-table-column>
        <el-table-column label="质量" width="115">
          <template #default="scope">
            <span :class="scope.row.quality_result.passed ? 'quality-pass' : 'quality-fail'">
              {{ qualityLabel(scope.row) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="索引版本" width="110">
          <template #default="scope">{{ scope.row.index_version?.version_label || '—' }}</template>
        </el-table-column>
        <el-table-column label="执行人 / 时间" min-width="195">
          <template #default="scope">
            <div class="muted-stack">
              <span>{{ scope.row.operator_name }}</span>
              <small>{{ datetimeFormat(scope.row.create_time) }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="openRunDetail(scope.row.id)">详情</el-button>
            <el-button
              v-if="scope.row.status === 'WAITING_RELEASE'"
              link
              type="success"
              @click="publish(scope.row)"
            >
              发布
            </el-button>
            <el-button
              v-if="scope.row.status === 'FAILED'"
              link
              type="warning"
              @click="retry(scope.row)"
            >
              重试
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="lower-grid">
      <el-card shadow="never" class="section-card version-card">
        <template #header>
          <div class="card-heading">
            <div><span>02</span><strong>索引版本</strong></div>
            <small>候选 / 线上 / 历史</small>
          </div>
        </template>
        <el-empty v-if="!dashboard?.versions.length" description="尚未生成索引版本" />
        <div v-else class="version-list">
          <article v-for="version in dashboard.versions" :key="version.id">
            <div class="version-mark" :class="`version-${version.status.toLowerCase()}`">
              {{ version.version_label }}
            </div>
            <div class="version-main">
              <div>
                <strong>{{ version.status_label }}</strong>
                <el-tag
                  v-if="version.status === 'PUBLISHED'"
                  type="success"
                  size="small"
                  effect="dark"
                >
                  ONLINE
                </el-tag>
              </div>
              <span>
                {{ version.document_count }} 文档 · {{ version.paragraph_count }} 段落 ·
                {{ version.embedding_count }} 向量
              </span>
              <small>
                覆盖率 {{ coverageLabel(version) }} · {{ datetimeFormat(version.create_time) }}
              </small>
            </div>
            <el-button
              v-if="version.status === 'ARCHIVED'"
              link
              type="warning"
              @click="rollback(version)"
            >
              回滚到此版本
            </el-button>
          </article>
        </div>
      </el-card>

      <el-card shadow="never" class="section-card release-card">
        <template #header>
          <div class="card-heading">
            <div><span>03</span><strong>发布审计</strong></div>
            <small>记录每一次版本切换</small>
          </div>
        </template>
        <el-empty v-if="!dashboard?.releases.length" description="暂无发布记录" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="release in dashboard.releases"
            :key="release.id"
            :type="release.action === 'ROLLBACK' ? 'warning' : 'success'"
            :timestamp="datetimeFormat(release.create_time)"
          >
            <strong>{{ release.action_label }}：{{ release.target_version_label }}</strong>
            <p>{{ release.from_version_label }} → {{ release.target_version_label }}</p>
            <small>{{ release.operator_name }} · {{ release.reason || '未填写说明' }}</small>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>

    <el-dialog v-model="runDialogVisible" title="新建 ETL 运行" width="620px" destroy-on-close>
      <el-alert
        title="本次运行会校验现有解析、段落与向量产物，并固化为一个不可变索引版本。"
        type="info"
        :closable="false"
        show-icon
      />
      <el-form label-position="top" class="run-form">
        <el-form-item label="处理文档">
          <el-select
            v-model="runForm.document_ids"
            multiple
            filterable
            collapse-tags
            collapse-tags-tooltip
            placeholder="不选择则处理全部启用文档"
          >
            <el-option
              v-for="document in dashboard?.documents || []"
              :key="document.id"
              :value="document.id"
              :label="`${document.name}（${document.paragraph_count} 段 / ${document.embedding_count} 向量）`"
            />
          </el-select>
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="最少有效段落">
            <el-input-number v-model="runForm.min_paragraph_count" :min="1" :max="100000" />
          </el-form-item>
          <el-form-item label="最低向量覆盖率">
            <el-input-number
              v-model="runForm.min_embedding_coverage"
              :min="0"
              :max="1"
              :step="0.05"
              :precision="2"
            />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="runDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="running" @click="startRun">执行并生成候选版本</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="ETL 运行详情" size="820px">
      <div v-loading="detailLoading" class="detail-body">
        <template v-if="selectedRun">
          <section class="detail-summary">
            <div><span>运行</span><strong>#{{ selectedRun.run_number }}</strong></div>
            <div><span>状态</span><strong>{{ selectedRun.status_label }}</strong></div>
            <div><span>质量分</span><strong>{{ selectedRun.quality_result.score ?? '—' }}</strong></div>
            <div>
              <span>版本</span><strong>{{ selectedRun.index_version?.version_label || '—' }}</strong>
            </div>
          </section>
          <el-alert
            v-if="selectedRun.error_message"
            :title="selectedRun.error_message"
            type="error"
            show-icon
            :closable="false"
          />
          <div class="stage-detail-list">
            <article v-for="stage in selectedRun.stages || []" :key="stage.id">
              <span class="stage-sequence">{{ String(stage.sequence).padStart(2, '0') }}</span>
              <div class="stage-content">
                <div>
                  <strong>{{ stage.stage_label }}</strong>
                  <el-tag :type="statusType(stage.status)" size="small" effect="plain">
                    {{ stage.status_label }}
                  </el-tag>
                </div>
                <small v-if="stage.finished_at">完成于 {{ datetimeFormat(stage.finished_at) }}</small>
                <p v-if="stage.error_message">{{ stage.error_message }}</p>
                <pre v-if="Object.keys(stage.output_snapshot).length">{{ pretty(stage.output_snapshot) }}</pre>
              </div>
            </article>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import knowledgeEtlApi, {
  type KnowledgeEtlDashboard,
  type KnowledgeEtlRun,
  type KnowledgeIndexVersion,
} from '@/api/knowledge/etl'
import { datetimeFormat } from '@/utils/time'

const route = useRoute()
const knowledgeId = computed(() => String(route.params.id || ''))
const loading = ref(false)
const running = ref(false)
const detailLoading = ref(false)
const actionLoading = ref(false)
const runDialogVisible = ref(false)
const detailVisible = ref(false)
const dashboard = ref<KnowledgeEtlDashboard>()
const selectedRun = ref<KnowledgeEtlRun>()
const runForm = ref({
  document_ids: [] as string[],
  min_paragraph_count: 1,
  min_embedding_coverage: 0.8,
})

const stageGuide = [
  { name: '解析', description: '确认文档范围' },
  { name: '清洗', description: '剔除空白内容' },
  { name: '切分', description: '统计有效段落' },
  { name: '向量化', description: '核对向量产物' },
  { name: '质检', description: '执行准入门禁' },
  { name: '版本', description: '固化内容快照' },
]

function statusType(status: string): '' | 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  if (['SUCCESS', 'PUBLISHED'].includes(status)) return 'success'
  if (['FAILED'].includes(status)) return 'danger'
  if (['WAITING_RELEASE', 'CANDIDATE'].includes(status)) return 'warning'
  if (['SKIPPED', 'ARCHIVED'].includes(status)) return 'info'
  return 'primary'
}

function loadDashboard() {
  return knowledgeEtlApi.getDashboard(knowledgeId.value, loading).then((res) => {
    dashboard.value = res.data
  })
}

function openRunDialog() {
  runForm.value = { document_ids: [], min_paragraph_count: 1, min_embedding_coverage: 0.8 }
  runDialogVisible.value = true
}

async function startRun() {
  running.value = true
  try {
    const { document_ids, ...thresholds } = runForm.value
    const payload = document_ids.length ? { ...thresholds, document_ids } : thresholds
    const res = await knowledgeEtlApi.startRun(knowledgeId.value, payload)
    runDialogVisible.value = false
    selectedRun.value = res.data
    detailVisible.value = true
    await loadDashboard()
    ElMessage.success(
      res.data.status === 'WAITING_RELEASE' ? '质量门禁已通过，候选版本已生成' : 'ETL 运行已结束',
    )
  } finally {
    running.value = false
  }
}

function openRunDetail(runId: string) {
  selectedRun.value = undefined
  detailVisible.value = true
  knowledgeEtlApi.getRun(knowledgeId.value, runId, detailLoading).then((res) => {
    selectedRun.value = res.data
  })
}

async function publish(run: KnowledgeEtlRun) {
  try {
    const { value } = await ElMessageBox.prompt(
      `确认将 ${run.index_version?.version_label || '候选版本'} 发布为线上索引吗？`,
      '发布索引版本',
      {
        inputPlaceholder: '填写发布说明（可选）',
        confirmButtonText: '确认发布',
        cancelButtonText: '取消',
      },
    )
    await knowledgeEtlApi.publishRun(knowledgeId.value, run.id, value || '', actionLoading)
    await loadDashboard()
    ElMessage.success('索引版本已发布')
  } catch {
    return undefined
  }
}

async function retry(run: KnowledgeEtlRun) {
  try {
    await ElMessageBox.confirm('将按原文档范围和质量阈值重新执行，确认继续吗？', '重试 ETL', {
      type: 'warning',
      confirmButtonText: '确认重试',
      cancelButtonText: '取消',
    })
    const res = await knowledgeEtlApi.retryRun(knowledgeId.value, run.id, actionLoading)
    await loadDashboard()
    selectedRun.value = res.data
    detailVisible.value = true
    ElMessage.success('重试已完成')
  } catch {
    return undefined
  }
}

async function rollback(version: KnowledgeIndexVersion) {
  try {
    const { value } = await ElMessageBox.prompt(
      `回滚后 ${version.version_label} 将成为线上索引，确认继续吗？`,
      '回滚索引版本',
      {
        inputPlaceholder: '填写回滚原因（建议填写）',
        confirmButtonText: '确认回滚',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    await knowledgeEtlApi.rollbackVersion(knowledgeId.value, version.id, value || '', actionLoading)
    await loadDashboard()
    ElMessage.success(`已回滚到 ${version.version_label}`)
  } catch {
    return undefined
  }
}

function qualityLabel(run: KnowledgeEtlRun) {
  if (!run.quality_result.checks?.length) return '未执行'
  return run.quality_result.passed ? `${run.quality_result.score ?? 100} 分` : '未通过'
}

function coverageLabel(version: KnowledgeIndexVersion) {
  const check = version.quality_result.checks?.find((item) => item.key === 'embedding_coverage')
  return check ? `${Math.round(check.actual * 100)}%` : '—'
}

function pretty(value: Record<string, unknown>) {
  return JSON.stringify(value, null, 2)
}

onMounted(loadDashboard)
</script>

<style scoped lang="scss">
.etl-console {
  --ink: #1d2b35;
  --muted: #687985;
  --line: #d9e1e5;
  --paper: #fff;
  --blue: #156082;
  --cyan: #198b91;
  box-sizing: border-box;
  height: 100%;
  min-height: 0;
  padding: 24px;
  overflow-y: auto;
  color: var(--ink);
  background:
    radial-gradient(circle at 88% 3%, rgba(38, 144, 154, 0.1), transparent 26%),
    linear-gradient(rgba(28, 70, 87, 0.035) 1px, transparent 1px), #f4f7f8;
  background-size: auto, 100% 28px;
}

.console-header,
.header-actions,
.card-heading,
.card-heading > div,
.stage-map article,
.version-list article,
.version-main > div,
.stage-content > div {
  display: flex;
  align-items: center;
}

.console-header {
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 18px;
}

.console-header h2 {
  margin: 5px 0 6px;
  font-family: 'Songti SC', 'STSong', serif;
  font-size: 29px;
}

.console-header p {
  margin: 0;
  color: var(--muted);
}

.eyebrow,
.card-heading span {
  color: var(--cyan);
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.13em;
}

.header-actions {
  gap: 9px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 11px;
  margin-bottom: 12px;
}

.metric-grid article {
  position: relative;
  padding: 16px 18px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.92);
}

.metric-grid article::before {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--cyan);
  content: '';
}

.metric-grid article.alert::before {
  background: #c84c3c;
}

.metric-grid span,
.metric-grid small,
.run-number small,
.muted-stack span,
.muted-stack small,
.version-main span,
.version-main small {
  display: block;
}

.metric-grid span,
.metric-grid small,
.muted-stack small,
.version-main span,
.version-main small {
  color: var(--muted);
}

.metric-grid strong {
  display: block;
  margin: 5px 0 1px;
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 27px;
}

.metric-grid .metric-text {
  font-family: inherit;
  font-size: 23px;
}

.stage-map {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  margin-bottom: 12px;
  border: 1px solid #244958;
  border-radius: 7px;
  background: #183744;
}

.stage-map article {
  position: relative;
  gap: 10px;
  min-width: 0;
  padding: 13px 14px;
  color: #fff;
  border-right: 1px solid rgba(255, 255, 255, 0.14);
}

.stage-map article:last-child {
  border-right: 0;
}

.stage-map article > span {
  color: #6fd0d2;
  font-family: monospace;
  font-size: 12px;
}

.stage-map strong,
.stage-map small {
  display: block;
}

.stage-map small {
  margin-top: 2px;
  color: #a9c0c8;
}

.section-card {
  border-color: var(--line);
  border-radius: 7px;
}

.run-card {
  margin-bottom: 12px;
}

.card-heading {
  justify-content: space-between;
  gap: 16px;
}

.card-heading > div {
  gap: 9px;
}

.card-heading > small {
  color: var(--muted);
}

.run-number strong {
  display: block;
  font-family: monospace;
  font-size: 16px;
}

.run-number small {
  color: var(--muted);
}

.quality-pass {
  color: #13805f;
  font-weight: 600;
}

.quality-fail {
  color: #bd4339;
  font-weight: 600;
}

.lower-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(340px, 0.65fr);
  gap: 12px;
  padding-bottom: 24px;
}

.version-list article {
  gap: 14px;
  padding: 13px 0;
  border-bottom: 1px solid #e8edef;
}

.version-list article:last-child {
  border-bottom: 0;
}

.version-mark {
  display: grid;
  width: 52px;
  height: 52px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid #b8c7ce;
  border-radius: 5px;
  color: #536b77;
  background: #f2f6f7;
  font-family: monospace;
  font-weight: 700;
}

.version-published {
  border-color: #168a77;
  color: #fff;
  background: #168a77;
}

.version-candidate {
  border-color: #c88a28;
  color: #9a6410;
  background: #fff7e9;
}

.version-main {
  min-width: 0;
  flex: 1;
}

.version-main > div {
  gap: 7px;
}

.version-main span {
  margin: 4px 0 2px;
}

.release-card :deep(.el-timeline) {
  padding-left: 5px;
}

.release-card p {
  margin: 3px 0;
  color: var(--blue);
  font-family: monospace;
}

.release-card small {
  color: var(--muted);
}

.run-form {
  margin-top: 18px;
}

.run-form :deep(.el-select) {
  width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.detail-body {
  min-height: 260px;
}

.detail-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 9px;
  margin-bottom: 15px;
}

.detail-summary div {
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #f7f9fa;
}

.detail-summary span,
.detail-summary strong {
  display: block;
}

.detail-summary span {
  margin-bottom: 4px;
  color: var(--muted);
  font-size: 12px;
}

.stage-detail-list {
  margin-top: 16px;
}

.stage-detail-list > article {
  display: grid;
  grid-template-columns: 42px 1fr;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}

.stage-sequence {
  color: var(--cyan);
  font-family: monospace;
  font-weight: 700;
}

.stage-content > div {
  gap: 8px;
}

.stage-content > small {
  color: var(--muted);
}

.stage-content > p {
  color: #bd4339;
}

.stage-content pre {
  max-height: 210px;
  margin: 9px 0 0;
  padding: 10px;
  overflow: auto;
  border-radius: 4px;
  color: #d5eef0;
  background: #183744;
  font-size: 11px;
  white-space: pre-wrap;
}

@media (max-width: 1100px) {
  .metric-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .stage-map {
    grid-template-columns: repeat(3, 1fr);
  }

  .lower-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .etl-console {
    padding: 14px;
  }

  .console-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-grid,
  .stage-map,
  .detail-summary,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
