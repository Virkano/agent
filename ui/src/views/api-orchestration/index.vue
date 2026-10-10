<template>
  <div class="api-page" v-loading="loading">
    <header class="api-hero">
      <div>
        <span class="eyebrow">API CONTRACT HUB · M05-03 / X10</span>
        <h2>API 编排与晓搭适配</h2>
        <p>用环境门禁、鉴权证明和调用韧性治理晓搭接口契约；当前调用使用隔离回放。</p>
      </div>
      <div class="hero-actions">
        <el-button :icon="Refresh" @click="loadDashboard">刷新</el-button>
        <el-button :icon="Plus" @click="openCreate">登记接口</el-button>
        <el-button type="primary" :icon="MagicStick" :loading="bootstrapping" @click="bootstrapDemo">
          生成 V1 验收样例
        </el-button>
      </div>
    </header>

    <section class="summary-grid">
      <article><span>接口资产</span><strong>{{ dashboard.summary.asset_count }}</strong><small>工作空间内登记</small></article>
      <article><span>已发布</span><strong>{{ dashboard.summary.published_count }}</strong><small>可供本地契约回放</small></article>
      <article><span>契约版本</span><strong>{{ dashboard.summary.version_count }}</strong><small>历史版本不可覆盖</small></article>
      <article><span>隔离调用</span><strong>{{ dashboard.summary.invocation_count }}</strong><small>审计事实已留存</small></article>
      <article class="success"><span>成功</span><strong>{{ dashboard.summary.success_count }}</strong><small>鉴权与 Schema 均通过</small></article>
      <article :class="{ danger: dashboard.summary.failure_count }"><span>受控失败</span><strong>{{ dashboard.summary.failure_count }}</strong><small>异常 {{ dashboard.summary.failure_count }} · 熔断 {{ dashboard.summary.circuit_open_count }}</small></article>
    </section>

    <section class="flow-strip">
      <template v-for="(step, index) in flowSteps" :key="step.code">
        <article><code>{{ step.code }}</code><div><strong>{{ step.name }}</strong><small>{{ step.note }}</small></div></article>
        <span v-if="index < flowSteps.length - 1">→</span>
      </template>
    </section>

    <section class="workspace-grid">
      <el-card shadow="never" class="asset-panel">
        <template #header>
          <div class="panel-title"><div><strong>接口资产</strong><small>点击资产查看版本、发布和回滚</small></div><el-tag type="info">{{ dashboard.assets.length }} ASSETS</el-tag></div>
        </template>
        <div v-if="dashboard.assets.length" class="asset-list">
          <button v-for="asset in dashboard.assets" :key="asset.id" class="asset-card" @click="openAsset(asset)">
            <span class="method">API</span>
            <div class="asset-main"><strong>{{ asset.name }}</strong><code>{{ asset.asset_key }}</code><small>{{ asset.description || '暂无说明' }}</small></div>
            <div class="asset-meta"><el-tag :type="asset.enabled ? 'success' : 'info'" size="small">{{ asset.enabled ? `V${asset.published_version_no} 已启用` : '已停用' }}</el-tag><el-tag v-if="asset.circuit_state === 'OPEN'" type="danger" size="small">熔断打开</el-tag><span>{{ asset.auth_scheme_label }}</span><span>{{ asset.version_count }} 个版本</span></div>
          </button>
        </div>
        <el-empty v-else description="暂无接口资产，生成样例或登记第一个接口" />
      </el-card>

      <el-card shadow="never" class="audit-panel">
        <template #header>
          <div class="panel-title"><div><strong>调用审计</strong><small>请求快照已去除凭证内容</small></div><el-tag type="warning">APPEND ONLY</el-tag></div>
        </template>
        <el-table :data="dashboard.recent_audits" height="440" @row-click="openAudit">
          <el-table-column label="接口 / 请求号" min-width="190">
            <template #default="{ row }"><div class="primary-cell"><strong>{{ row.asset_name }}</strong><code>{{ row.request_id }}</code></div></template>
          </el-table-column>
          <el-table-column label="结果" width="110"><template #default="{ row }"><el-tag :type="auditTag(row.status)" size="small">{{ row.status_label }}</el-tag></template></el-table-column>
          <el-table-column label="版本" width="72"><template #default="{ row }">V{{ row.version_no }}</template></el-table-column>
          <el-table-column prop="duration_ms" label="耗时" width="72"><template #default="{ row }">{{ row.duration_ms }}ms</template></el-table-column>
          <el-table-column label="时间" width="145"><template #default="{ row }">{{ formatTime(row.create_time) }}</template></el-table-column>
        </el-table>
      </el-card>
    </section>

    <el-drawer v-model="editorOpen" size="680px" class="api-editor-drawer" :title="editingId ? '创建新契约版本' : '登记 API 资产'">
      <div class="drawer-scroll">
        <div class="security-note"><el-icon><Lock /></el-icon><div><strong>只保存凭证引用</strong><span>此处不录入 API Key、JWT 或 OAuth 密钥；真实凭证由独立密钥能力托管。</span></div></div>
        <section class="import-panel">
          <header><div><strong>OpenAPI 3.x 导入</strong><small>解析第一个可用操作，自动回填路径、Schema 与请求参数来源。</small></div><div><el-button size="small" @click="fillOpenApiSample">载入样例</el-button><el-button size="small" type="primary" plain :loading="importing" @click="parseOpenApi">解析并回填</el-button></div></header>
          <el-input v-model="openApiText" type="textarea" :rows="5" placeholder="粘贴 OpenAPI 3.x JSON 文档" />
        </section>
        <el-form label-position="top">
          <div class="form-grid">
            <el-form-item label="接口标识"><el-input v-model="form.asset_key" :disabled="Boolean(editingId)" placeholder="customer_recommendation" /></el-form-item>
            <el-form-item label="接口名称"><el-input v-model="form.name" placeholder="客户产品推荐" /></el-form-item>
            <el-form-item label="鉴权方式"><el-select v-model="form.auth_scheme"><el-option v-for="item in authOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
            <el-form-item label="凭证引用"><el-input v-model="form.auth_reference" :disabled="form.auth_scheme === 'NONE'" placeholder="system-api-key:asset-code" /></el-form-item>
            <el-form-item label="环境"><el-select v-model="form.environment"><el-option label="测试" value="TEST" /><el-option label="灰度" value="GRAY" /><el-option label="生产" value="PRODUCTION" /></el-select></el-form-item>
            <el-form-item label="请求方法"><el-select v-model="form.method"><el-option v-for="method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']" :key="method" :label="method" :value="method" /></el-select></el-form-item>
          </div>
          <el-form-item label="接口路径"><el-input v-model="form.endpoint_path" placeholder="/xiaoda/v1/customer/recommendation"><template #prepend>XIADA_SANDBOX</template></el-input></el-form-item>
          <el-form-item label="IP 白名单"><el-input v-model="ipAllowlistText" placeholder="127.0.0.1, 10.0.0.8" /><small class="field-tip">逗号分隔；测试环境可以为空。</small></el-form-item>
          <el-form-item label="接口说明"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
          <section class="governance-config">
            <header><strong>发布与调用治理</strong><small>灰度和生产网关必须使用 HTTPS；失败重试不会超过 5 次。</small></header>
            <div class="form-grid">
              <el-form-item label="适配模式"><el-select v-model="form.adapter_mode"><el-option label="晓搭隔离回放" value="MOCK" /><el-option label="晓搭网关配置（暂未直连）" value="GATEWAY" /></el-select></el-form-item>
              <el-form-item label="晓搭网关地址"><el-input v-model="form.gateway_base_url" :disabled="form.adapter_mode === 'MOCK'" placeholder="https://gateway.example.com" /></el-form-item>
              <el-form-item label="JWT / OAuth2 权限"><el-input v-model="requiredScopesText" placeholder="tool:invoke, customer:read" /></el-form-item>
              <el-form-item label="超时（毫秒）"><el-input-number v-model="form.timeout_ms" :min="100" :max="120000" :step="100" /></el-form-item>
              <el-form-item label="最大重试"><el-input-number v-model="form.max_retries" :min="0" :max="5" /></el-form-item>
              <el-form-item label="熔断失败阈值"><el-input-number v-model="form.circuit_failure_threshold" :min="1" :max="20" /></el-form-item>
              <el-form-item label="熔断恢复窗口（秒）"><el-input-number v-model="form.circuit_recovery_seconds" :min="1" :max="3600" /></el-form-item>
            </div>
            <small class="field-tip">网关模式当前只保存并校验配置快照；调用验收仍使用隔离回放，不会向外部地址发送请求。</small>
          </section>
          <div class="json-grid">
            <el-form-item label="输入 Schema (JSON)"><el-input v-model="inputSchemaText" type="textarea" :rows="11" /></el-form-item>
            <el-form-item label="输出 Schema (JSON)"><el-input v-model="outputSchemaText" type="textarea" :rows="11" /></el-form-item>
            <el-form-item label="隔离返回 (JSON)"><el-input v-model="mockResponseText" type="textarea" :rows="8" /></el-form-item>
            <el-form-item label="字段映射 (JSON)"><el-input v-model="mappingText" type="textarea" :rows="8" /></el-form-item>
            <el-form-item label="参数来源与依赖 (JSON)"><el-input v-model="bindingsText" type="textarea" :rows="10" /><small class="field-tip">支持 REQUEST / CONTEXT / CONSTANT / PREVIOUS_OUTPUT；depends_on 决定解析顺序。</small></el-form-item>
          </div>
        </el-form>
      </div>
      <template #footer><el-button @click="editorOpen = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitAsset">{{ editingId ? '保存为新草稿版本' : '登记并生成 V1 草稿' }}</el-button></template>
    </el-drawer>

    <el-drawer v-model="detailOpen" size="720px" class="api-detail-drawer" title="接口契约详情">
      <div v-if="currentAsset" class="drawer-scroll">
        <div class="detail-hero"><div><small>{{ currentAsset.asset_key }}</small><h3>{{ currentAsset.name }}</h3><p>{{ currentAsset.description }}</p></div><el-tag :type="currentAsset.enabled ? 'success' : 'info'">{{ currentAsset.published_version_no ? `V${currentAsset.published_version_no} ${currentAsset.enabled ? '已启用' : '已停用'}` : '尚未发布' }}</el-tag></div>
        <div class="detail-toolbar"><el-button :icon="Edit" @click="editCurrent">创建新版本</el-button><el-button :type="currentAsset.enabled ? 'danger' : 'success'" plain @click="toggleEnabled">{{ currentAsset.enabled ? '停用接口' : '启用接口' }}</el-button><el-button v-if="currentAsset.enabled" type="primary" plain :icon="Promotion" @click="invokeScenario('success')">成功调用</el-button><el-button v-if="currentAsset.enabled" type="success" plain @click="invokeScenario('retry')">重试恢复</el-button><el-button v-if="currentAsset.enabled" type="danger" plain @click="invokeScenario('circuit')">触发熔断</el-button><el-button v-if="currentAsset.enabled" type="warning" plain @click="invokeScenario('auth')">鉴权失败</el-button><el-button v-if="currentAsset.enabled" type="danger" plain @click="invokeScenario('schema')">Schema 失败</el-button></div>
        <div class="contract-facts"><article><span>鉴权</span><strong>{{ currentAsset.auth_scheme_label }}</strong><small>{{ currentAsset.auth_reference || '无需鉴权' }}</small></article><article><span>IP 白名单</span><strong>{{ currentAsset.ip_allowlist.length }}</strong><small>{{ currentAsset.ip_allowlist.join(', ') || '未限制' }}</small></article><article :class="{ alerting: currentAsset.circuit_state === 'OPEN' }"><span>熔断状态</span><strong>{{ currentAsset.circuit_state_label }}</strong><small>连续失败 {{ currentAsset.consecutive_failures }} 次</small></article><article><span>当前适配器</span><strong>{{ publishedVersion?.adapter_mode_label || '—' }}</strong><small>{{ publishedVersion?.gateway_base_url || '本地契约回放' }}</small></article></div>
        <h4>契约版本</h4>
        <article v-for="version in currentAsset.versions" :key="version.id" class="version-card">
          <header><div><strong>V{{ version.version_no }}</strong><code>{{ version.method }} {{ version.endpoint_path }}</code></div><el-tag :type="versionTag(version.status)" size="small">{{ version.status_label }}</el-tag></header>
          <div class="version-meta"><span>{{ version.environment_label }}</span><span>{{ version.adapter_mode_label }}</span><span>{{ version.timeout_ms }}ms / 重试 {{ version.max_retries }}</span><span>{{ formatTime(version.create_time) }}</span></div>
          <div class="contract-badges"><el-tag size="small" type="info">{{ version.parameter_bindings.length }} 个参数来源</el-tag><el-tag v-if="Object.keys(version.openapi_snapshot).length" size="small">OpenAPI</el-tag></div>
          <pre>{{ compactSchema(version.input_schema) }}</pre>
          <footer><el-button v-if="(currentAsset.versions?.length || 0) > 1" size="small" @click="compareVersion(version)">版本差异</el-button><el-button v-if="version.status === 'DRAFT'" type="primary" size="small" :loading="operating" @click="publishVersion(version)">发布此版本</el-button><el-button v-if="version.status !== 'DRAFT' && version.version_no !== currentAsset.published_version_no" size="small" :loading="operating" @click="rollbackVersion(version)">基于此版本回滚</el-button></footer>
        </article>
        <h4>治理事件</h4>
        <div class="event-list"><article v-for="event in currentAsset.governance_events" :key="event.id"><code>{{ governanceEventLabel(event.event_type) }}</code><div><strong>{{ event.version_no ? `V${event.version_no}` : currentAsset.asset_key }}</strong><small>{{ formatTime(event.create_time) }} · {{ event.operator_name }}</small></div><pre>{{ compactSchema(event.event_snapshot) }}</pre></article><el-empty v-if="!currentAsset.governance_events?.length" description="暂无治理事件" /></div>
      </div>
    </el-drawer>

    <el-drawer v-model="compareOpen" size="640px" class="api-compare-drawer" title="契约版本差异">
      <div v-if="comparison" class="drawer-scroll compare-detail">
        <div class="compare-hero" :class="{ safe: comparison.compatible }"><div><small>V{{ comparison.base_version.version_no }} → V{{ comparison.target_version.version_no }}</small><h3>{{ comparison.compatible ? '兼容性变更' : `${comparison.breaking_count} 项破坏性变更` }}</h3></div><el-tag :type="comparison.compatible ? 'success' : 'danger'">{{ comparison.compatible ? '可兼容' : '需确认' }}</el-tag></div>
        <el-alert v-if="comparison.breaking_changes.length" type="error" :closable="false" title="发布前需处理或确认"><ul><li v-for="item in comparison.breaking_changes" :key="item">{{ item }}</li></ul></el-alert>
        <h4>变更字段</h4><div class="tag-cloud"><el-tag v-for="item in comparison.changed_fields" :key="item" type="info">{{ item }}</el-tag><span v-if="!comparison.changed_fields.length">没有配置变化</span></div>
        <div class="diff-grid"><section><h4>输入 Schema</h4><p><strong>新增</strong>{{ listText(comparison.input_schema_diff.added) }}</p><p><strong>删除</strong>{{ listText(comparison.input_schema_diff.removed) }}</p><p><strong>新增必填</strong>{{ listText(comparison.input_schema_diff.required_added) }}</p><p><strong>类型变化</strong>{{ typeChangeText(comparison.input_schema_diff.type_changed) }}</p></section><section><h4>输出 Schema</h4><p><strong>新增</strong>{{ listText(comparison.output_schema_diff.added) }}</p><p><strong>删除</strong>{{ listText(comparison.output_schema_diff.removed) }}</p><p><strong>新增必填</strong>{{ listText(comparison.output_schema_diff.required_added) }}</p><p><strong>类型变化</strong>{{ typeChangeText(comparison.output_schema_diff.type_changed) }}</p></section></div>
      </div>
    </el-drawer>

    <el-drawer v-model="auditOpen" size="580px" class="api-audit-drawer" title="调用审计详情">
      <div v-if="currentAudit" class="drawer-scroll audit-detail">
        <div class="audit-status"><el-tag :type="auditTag(currentAudit.status)" size="large">{{ currentAudit.status_label }}</el-tag><strong>{{ currentAudit.request_id }}</strong><small>{{ currentAudit.asset_name }} · V{{ currentAudit.version_no }} · {{ currentAudit.duration_ms }}ms</small></div>
        <div class="check-grid"><article :class="{ passed: currentAudit.auth_result }"><span>鉴权检查</span><strong>{{ currentAudit.auth_result ? '通过' : '未通过' }}</strong></article><article :class="{ passed: currentAudit.schema_result }"><span>Schema 检查</span><strong>{{ currentAudit.schema_result ? '通过' : '未通过' }}</strong></article></div>
        <el-alert v-if="currentAudit.error_message" type="error" :closable="false" :title="currentAudit.error_message" />
        <h4>已脱敏请求快照</h4><pre>{{ pretty(currentAudit.request_snapshot) }}</pre>
        <h4>返回快照</h4><pre>{{ pretty(currentAudit.response_snapshot) }}</pre>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Lock, MagicStick, Plus, Promotion, Refresh } from '@element-plus/icons-vue'

import {
  bootstrapApiOrchestration,
  compareApiVersions,
  getApiAsset,
  getApiOrchestrationDashboard,
  importOpenApi,
  invokeApiMock,
  publishApiVersion,
  rollbackApiVersion,
  saveApiAsset,
  setApiAssetEnabled,
  type ApiAssetForm,
  type ApiAuthScheme,
  type ApiInvocationAudit,
  type ApiInvocationStatus,
  type ApiOrchestrationAsset,
  type ApiOrchestrationDashboard,
  type ApiOrchestrationVersion,
  type ApiParameterBinding,
  type ApiVersionComparison,
  type ApiVersionStatus,
} from '@/api/api-orchestration'

const emptyDashboard = (): ApiOrchestrationDashboard => ({ summary: { asset_count: 0, published_count: 0, version_count: 0, invocation_count: 0, success_count: 0, failure_count: 0, circuit_open_count: 0 }, assets: [], recent_audits: [] })
const defaultForm = (): ApiAssetForm => ({ asset_key: '', name: '', description: '', icon: 'Connection', auth_scheme: 'API_KEY', auth_reference: '', ip_allowlist: [], environment: 'TEST', method: 'POST', endpoint_path: '/xiaoda/v1/', input_schema: { type: 'object', required: ['customer_id'], additionalProperties: false, properties: { customer_id: { type: 'string' } } }, output_schema: { type: 'object', required: ['result'], properties: { result: { type: 'object' } } }, request_mapping: {}, response_mapping: {}, openapi_snapshot: {}, parameter_bindings: [], adapter_mode: 'MOCK', gateway_base_url: '', required_scopes: [], timeout_ms: 3000, max_retries: 2, circuit_failure_threshold: 3, circuit_recovery_seconds: 60, mock_response: { result: {} } })

const dashboard = ref(emptyDashboard())
const loading = ref(false)
const bootstrapping = ref(false)
const saving = ref(false)
const operating = ref(false)
const importing = ref(false)
const editorOpen = ref(false)
const detailOpen = ref(false)
const auditOpen = ref(false)
const compareOpen = ref(false)
const editingId = ref('')
const currentAsset = ref<ApiOrchestrationAsset | null>(null)
const currentAudit = ref<ApiInvocationAudit | null>(null)
const comparison = ref<ApiVersionComparison | null>(null)
const form = reactive(defaultForm())
const ipAllowlistText = ref('')
const inputSchemaText = ref('')
const outputSchemaText = ref('')
const mockResponseText = ref('')
const mappingText = ref('')
const bindingsText = ref('[]')
const openApiText = ref('')
const requiredScopesText = ref('')
const publishedVersion = computed(() => currentAsset.value?.versions?.find(item => item.version_no === currentAsset.value?.published_version_no))
const flowSteps = [
  { code: '01', name: '资产登记', note: '元数据与鉴权引用' },
  { code: '02', name: '契约校验', note: '输入 / 输出 Schema' },
  { code: '03', name: '版本发布', note: '不可变快照' },
  { code: '04', name: '晓搭隔离回放', note: '成功与受控失败' },
  { code: '05', name: '审计留痕', note: '脱敏请求事实' },
]
const authOptions: { value: ApiAuthScheme; label: string }[] = [{ value: 'NONE', label: '无需鉴权' }, { value: 'API_KEY', label: 'API Key' }, { value: 'JWT', label: 'JWT' }, { value: 'OAUTH2', label: 'OAuth2' }, { value: 'SIGNATURE', label: '请求签名' }]

async function loadDashboard() { dashboard.value = (await getApiOrchestrationDashboard(loading)).data }
async function bootstrapDemo() { dashboard.value = (await bootstrapApiOrchestration(bootstrapping)).data; ElMessage.success('已生成接口资产和三类调用审计') }
function openCreate() { editingId.value = ''; Object.assign(form, defaultForm()); syncTexts(); editorOpen.value = true }
async function openAsset(asset: ApiOrchestrationAsset) { currentAsset.value = (await getApiAsset(asset.id, operating)).data; detailOpen.value = true }
function openAudit(row: ApiInvocationAudit) { currentAudit.value = row; auditOpen.value = true }
function syncTexts() { ipAllowlistText.value = form.ip_allowlist.join(', '); requiredScopesText.value = form.required_scopes.join(', '); inputSchemaText.value = pretty(form.input_schema); outputSchemaText.value = pretty(form.output_schema); mockResponseText.value = pretty(form.mock_response); mappingText.value = pretty({ request: form.request_mapping, response: form.response_mapping }); bindingsText.value = pretty(form.parameter_bindings); openApiText.value = Object.keys(form.openapi_snapshot).length ? pretty(form.openapi_snapshot) : '' }
function editCurrent() {
  if (!currentAsset.value) return
  const latest = currentAsset.value.versions?.[0]
  if (!latest) return
  editingId.value = currentAsset.value.id
  Object.assign(form, { asset_key: currentAsset.value.asset_key, name: currentAsset.value.name, description: currentAsset.value.description, icon: currentAsset.value.icon, auth_scheme: currentAsset.value.auth_scheme, auth_reference: currentAsset.value.auth_reference, ip_allowlist: currentAsset.value.ip_allowlist, environment: latest.environment, method: latest.method, endpoint_path: latest.endpoint_path, input_schema: latest.input_schema, output_schema: latest.output_schema, request_mapping: latest.request_mapping, response_mapping: latest.response_mapping, openapi_snapshot: latest.openapi_snapshot, parameter_bindings: latest.parameter_bindings, adapter_mode: latest.adapter_mode, gateway_base_url: latest.gateway_base_url, required_scopes: latest.required_scopes, timeout_ms: latest.timeout_ms, max_retries: latest.max_retries, circuit_failure_threshold: latest.circuit_failure_threshold, circuit_recovery_seconds: latest.circuit_recovery_seconds, mock_response: latest.mock_response })
  syncTexts(); detailOpen.value = false; editorOpen.value = true
}
function parseObject(text: string, label: string) { try { const value = JSON.parse(text); if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error(); return value as Record<string, unknown> } catch { throw new Error(`${label} 必须是合法 JSON 对象`) } }
function parseBindings(text: string) { try { const value: unknown = JSON.parse(text); if (!Array.isArray(value)) throw new Error(); return value as ApiParameterBinding[] } catch { throw new Error('参数来源与依赖必须是合法 JSON 数组') } }
function fillOpenApiSample() {
  openApiText.value = pretty({ openapi: '3.0.3', info: { title: 'Customer Recommendation API', version: '2.0.0' }, paths: { '/xiaoda/v2/customer/recommendation': { post: { operationId: 'recommendCustomerProduct', requestBody: { required: true, content: { 'application/json': { schema: { type: 'object', required: ['customer_id', 'channel'], properties: { customer_id: { type: 'string' }, channel: { type: 'string' } } } } } }, responses: { 200: { description: 'OK', content: { 'application/json': { schema: { type: 'object', required: ['items'], properties: { items: { type: 'array' } } } } } } } } } } })
}
async function parseOpenApi() {
  try {
    const document = parseObject(openApiText.value, 'OpenAPI 文档')
    const imported = (await importOpenApi(document, importing)).data
    Object.assign(form, { method: imported.method, endpoint_path: imported.endpoint_path, input_schema: imported.input_schema, output_schema: imported.output_schema, parameter_bindings: imported.parameter_bindings, openapi_snapshot: imported.openapi_snapshot })
    inputSchemaText.value = pretty(imported.input_schema); outputSchemaText.value = pretty(imported.output_schema); bindingsText.value = pretty(imported.parameter_bindings)
    ElMessage.success(`已导入 ${imported.summary.title || imported.endpoint_path} ${imported.summary.version}`)
  } catch (error) { if (error instanceof Error) ElMessage.error(error.message) }
}
async function submitAsset() {
  try {
    const mapping = parseObject(mappingText.value, '字段映射') as { request?: Record<string, unknown>; response?: Record<string, unknown> }
    const payload: ApiAssetForm = { ...form, ip_allowlist: ipAllowlistText.value.split(',').map(value => value.trim()).filter(Boolean), required_scopes: requiredScopesText.value.split(',').map(value => value.trim()).filter(Boolean), input_schema: parseObject(inputSchemaText.value, '输入 Schema'), output_schema: parseObject(outputSchemaText.value, '输出 Schema'), mock_response: parseObject(mockResponseText.value, '隔离返回'), request_mapping: mapping.request || {}, response_mapping: mapping.response || {}, parameter_bindings: parseBindings(bindingsText.value) }
    const response = await saveApiAsset(payload, editingId.value || undefined, saving)
    editorOpen.value = false; await loadDashboard(); await openAsset(response.data); ElMessage.success(editingId.value ? '新草稿版本已保存' : '接口资产已登记')
  } catch (error) { if (error instanceof Error) ElMessage.error(error.message) }
}
async function publishVersion(version: ApiOrchestrationVersion) {
  if (!currentAsset.value) return
  let options: { breaking_change_confirmed?: boolean; change_ticket?: string } = {}
  if (version.environment === 'PRODUCTION') {
    const current = currentAsset.value.versions?.find(item => item.version_no === currentAsset.value?.published_version_no)
    const diff = current ? (await compareApiVersions(currentAsset.value.id, current.id, version.id, operating)).data : null
    if (diff?.breaking_count) {
      const prompt = await ElMessageBox.prompt(`检测到 ${diff.breaking_count} 项破坏性变更。确认发布需填写变更单号。`, '生产发布门禁', { confirmButtonText: '确认风险并发布', inputPlaceholder: '例如 CHG-20260921-001', inputPattern: /\S+/, inputErrorMessage: '变更单号不能为空' })
      options = { breaking_change_confirmed: true, change_ticket: prompt.value }
    } else await ElMessageBox.confirm(`发布生产版本 V${version.version_no}？`, '生产发布门禁')
  } else await ElMessageBox.confirm(`发布 ${version.environment_label} V${version.version_no} 后，原发布版本会归档。`, '发布契约版本')
  currentAsset.value = (await publishApiVersion(currentAsset.value.id, version.id, options, operating)).data
  await loadDashboard(); ElMessage.success(`V${version.version_no} 已发布`)
}
async function toggleEnabled() {
  if (!currentAsset.value) return
  const enabled = !currentAsset.value.enabled
  const prompt = await ElMessageBox.prompt(`请输入${enabled ? '启用' : '停用'}原因。`, `${enabled ? '启用' : '停用'}接口`, { inputPlaceholder: '治理事件将永久保留', inputPattern: /\S+/, inputErrorMessage: '原因不能为空' })
  currentAsset.value = (await setApiAssetEnabled(currentAsset.value.id, { enabled, reason: prompt.value }, operating)).data
  await loadDashboard(); ElMessage.success(`接口已${enabled ? '启用' : '停用'}`)
}
async function rollbackVersion(version: ApiOrchestrationVersion) { if (!currentAsset.value) return; await ElMessageBox.confirm(`将基于 V${version.version_no} 创建并发布一个全新版本，历史事实不会改写。`, '版本回滚'); currentAsset.value = (await rollbackApiVersion(currentAsset.value.id, version.id, operating)).data; await loadDashboard(); ElMessage.success('已生成并发布回滚版本') }
async function compareVersion(version: ApiOrchestrationVersion) {
  if (!currentAsset.value?.versions?.length) return
  const versions = currentAsset.value.versions
  const published = versions.find(item => item.version_no === currentAsset.value?.published_version_no)
  const target = version.id === published?.id ? versions.find(item => item.version_no < version.version_no) : published
  if (!target) return ElMessage.info('暂无可比较的目标版本')
  const [baseVersion, targetVersion] = version.version_no < target.version_no ? [version, target] : [target, version]
  comparison.value = (await compareApiVersions(currentAsset.value.id, baseVersion.id, targetVersion.id, operating)).data
  compareOpen.value = true
}
async function invokeScenario(scenario: 'success' | 'retry' | 'circuit' | 'auth' | 'schema') {
  if (!currentAsset.value) return
  const version = currentAsset.value.versions?.find(item => item.version_no === currentAsset.value?.published_version_no)
  if (!version) return
  const required = (version?.input_schema.required as string[] | undefined) || []
  const properties = (version?.input_schema.properties as Record<string, { type?: string }> | undefined) || {}
  const payload = scenario === 'schema' ? {} : Object.fromEntries(required.map(key => [key, sampleValue(properties[key]?.type)]))
  const auth_context = scenario === 'auth' ? { validated: false } : buildAuthContext(currentAsset.value, version)
  let audit: ApiInvocationAudit
  if (scenario === 'circuit') {
    for (let index = 0; index < version.circuit_failure_threshold; index += 1) {
      audit = (await invokeApiMock(currentAsset.value.id, { payload, auth_context, simulated_failures: version.max_retries + 1 }, operating)).data
    }
    audit = (await invokeApiMock(currentAsset.value.id, { payload, auth_context }, operating)).data
  } else {
    audit = (await invokeApiMock(currentAsset.value.id, { payload, auth_context, simulated_failures: scenario === 'retry' ? Math.min(1, version.max_retries) : 0 }, operating)).data
  }
  await loadDashboard(); currentAsset.value = (await getApiAsset(currentAsset.value.id)).data; openAudit(audit); ElMessage.success(`已完成${scenarioLabel(scenario)}场景`)
}
function buildAuthContext(asset: ApiOrchestrationAsset, version: ApiOrchestrationVersion) { return { validated: true, scheme: asset.auth_scheme, credential_reference: asset.auth_reference, source_ip: asset.ip_allowlist[0] || '127.0.0.1', expires_at: Math.floor(Date.now() / 1000) + 3600, scopes: version.required_scopes, signature_valid: true, timestamp_valid: true, nonce_replayed: false } }
function scenarioLabel(scenario: 'success' | 'retry' | 'circuit' | 'auth' | 'schema') { return ({ success: '成功', retry: '重试恢复', circuit: '熔断', auth: '鉴权失败', schema: 'Schema 失败' } as const)[scenario] }
function sampleValue(type?: string) { return ({ string: 'DEMO-001', number: 1.2, integer: 1, boolean: true, object: {}, array: [] } as Record<string, unknown>)[type || 'string'] ?? 'DEMO-001' }
function auditTag(status: ApiInvocationStatus) { return ({ SUCCESS: 'success', AUTH_FAILED: 'warning', SCHEMA_FAILED: 'danger', RESPONSE_FAILED: 'danger', TIMEOUT: 'danger', RETRY_EXHAUSTED: 'warning', CIRCUIT_OPEN: 'danger' } as const)[status] }
function versionTag(status: ApiVersionStatus) { return ({ DRAFT: 'warning', PUBLISHED: 'success', ARCHIVED: 'info' } as const)[status] }
function governanceEventLabel(value: string) { return ({ VERSION_PUBLISHED: '版本发布', ASSET_ENABLED: '接口启用', ASSET_DISABLED: '接口停用', CIRCUIT_OPENED: '熔断打开', CIRCUIT_RECOVERED: '熔断恢复' } as Record<string, string>)[value] || value }
function pretty(value: unknown) { return JSON.stringify(value, null, 2) }
function compactSchema(value: Record<string, unknown>) { return JSON.stringify(value) }
function listText(value: string[]) { return value.length ? value.join('、') : '—' }
function typeChangeText(value: { field: string; from?: string; to?: string }[]) { return value.length ? value.map(item => `${item.field}: ${item.from} → ${item.to}`).join('；') : '—' }
function formatTime(value: string | null) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-') : '—' }

loadDashboard()
</script>

<style scoped lang="scss">
.api-page { --ink: #172b35; --muted: #687b84; --line: #d6e0e2; --cyan: #087b79; --orange: #ce6d2c; height: 100%; padding: 24px 28px 42px; overflow-y: auto; color: var(--ink); background: linear-gradient(90deg, rgb(8 123 121 / 4%) 1px, transparent 1px), linear-gradient(rgb(8 123 121 / 4%) 1px, transparent 1px), #f3f6f6; background-size: 28px 28px; }
.api-hero, .hero-actions, .panel-title, .detail-toolbar, .version-card header, .version-meta, .version-card footer { display: flex; align-items: center; }.api-hero { justify-content: space-between; gap: 24px; margin-bottom: 18px; }.api-hero h2 { margin: 4px 0; font-size: 28px; letter-spacing: -.7px; }.api-hero p { margin: 0; color: var(--muted); }.eyebrow { color: var(--cyan); font: 700 12px 'SFMono-Regular', Consolas, monospace; letter-spacing: 1.2px; }.hero-actions { gap: 8px; }
.summary-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin-bottom: 12px; }.summary-grid article { padding: 15px 16px; border: 1px solid var(--line); border-top: 3px solid var(--cyan); border-radius: 5px; background: rgb(255 255 255 / 94%); }.summary-grid article.danger { border-top-color: #c85249; }.summary-grid article.success { border-top-color: #4d966c; }.summary-grid span, .summary-grid small { display: block; color: var(--muted); }.summary-grid strong { display: block; margin: 6px 0 2px; font: 28px Georgia, serif; }
.flow-strip { display: flex; align-items: stretch; margin-bottom: 12px; padding: 12px 16px; border: 1px solid var(--line); background: #fff; }.flow-strip article { display: flex; flex: 1; align-items: center; gap: 10px; min-width: 0; }.flow-strip > span { align-self: center; padding: 0 8px; color: #91a2a9; }.flow-strip code { display: grid; width: 30px; height: 30px; place-items: center; color: var(--cyan); border: 1px solid #b9d2d1; border-radius: 50%; background: #f1f8f8; }.flow-strip article div { display: grid; gap: 2px; }.flow-strip small { color: var(--muted); }
.workspace-grid { display: grid; grid-template-columns: minmax(480px, .9fr) minmax(620px, 1.1fr); gap: 12px; }.asset-panel, .audit-panel { border-color: var(--line); }.panel-title { justify-content: space-between; }.panel-title > div { display: grid; gap: 3px; }.panel-title small { color: var(--muted); }.asset-list { display: grid; gap: 8px; }.asset-card { display: grid; grid-template-columns: 45px 1fr auto; gap: 12px; width: 100%; padding: 15px; text-align: left; color: var(--ink); border: 1px solid var(--line); border-radius: 4px; background: #fff; cursor: pointer; transition: transform .15s, border-color .15s; }.asset-card:hover { transform: translateY(-1px); border-color: #77aaa8; }.method { display: grid; width: 42px; height: 42px; place-items: center; color: #fff; font: 700 11px monospace; border-radius: 4px; background: var(--cyan); }.asset-main, .asset-meta, .primary-cell { display: grid; gap: 4px; }.asset-main code, .primary-cell code { width: max-content; color: #3f6873; font-size: 12px; }.asset-main small, .asset-meta span, .primary-cell code { color: var(--muted); }.asset-meta { justify-items: end; font-size: 12px; }
.drawer-scroll { height: calc(100vh - 145px); padding: 0 20px 32px; overflow-y: auto; }.security-note { display: flex; gap: 12px; margin-bottom: 18px; padding: 13px; color: #4e6069; border-left: 3px solid var(--cyan); background: #f0f7f7; }.security-note div { display: grid; gap: 3px; }.security-note span { font-size: 12px; }.form-grid, .json-grid, .contract-facts, .check-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 14px; }.form-grid :deep(.el-select) { width: 100%; }.field-tip { display: block; color: var(--muted); font-size: 12px; }.json-grid :deep(textarea), .audit-detail pre, .version-card pre { font-family: 'SFMono-Regular', Consolas, monospace; font-size: 12px; }
.import-panel { margin-bottom: 18px; padding: 14px; border: 1px solid #bdd4d3; background: #f8fbfb; }.import-panel header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 10px; }.import-panel header > div:first-child { display: grid; gap: 3px; }.import-panel small { color: var(--muted); }.import-panel :deep(textarea) { font-family: 'SFMono-Regular', Consolas, monospace; font-size: 12px; }
.governance-config { margin: 6px 0 18px; padding: 14px; border: 1px solid #e0c8b8; border-left: 4px solid var(--orange); background: #fffaf6; }.governance-config header { display: grid; gap: 3px; margin-bottom: 12px; }.governance-config header small { color: var(--muted); }.governance-config :deep(.el-input-number) { width: 100%; }
.detail-hero { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; padding: 16px; border-left: 4px solid var(--cyan); background: #f1f7f7; }.detail-hero h3 { margin: 4px 0; }.detail-hero p, .detail-hero small { margin: 0; color: var(--muted); }.detail-toolbar { flex-wrap: wrap; gap: 8px; margin: 14px 0; }.detail-toolbar .el-button + .el-button { margin-left: 0; }.contract-facts article, .check-grid article { display: grid; gap: 5px; padding: 12px; border: 1px solid var(--line); background: #fff; }.contract-facts span, .contract-facts small, .check-grid span { color: var(--muted); font-size: 12px; }.version-card { margin-bottom: 10px; padding: 14px; border: 1px solid var(--line); background: #fff; }.version-card header { justify-content: space-between; }.version-card header > div { display: flex; align-items: center; gap: 10px; }.version-card header code { color: var(--cyan); }.version-meta { gap: 14px; margin: 8px 0; color: var(--muted); font-size: 12px; }.version-card pre, .audit-detail pre { padding: 12px; overflow: auto; color: #39505b; border: 1px solid #e0e6e8; background: #f6f8f8; white-space: pre-wrap; word-break: break-all; }.version-card footer { justify-content: flex-end; }
.contract-facts { grid-template-columns: repeat(4, 1fr); gap: 8px; }.contract-facts article.alerting { border-top: 3px solid #c85249; background: #fff4f2; }.event-list { display: grid; gap: 8px; }.event-list article { display: grid; grid-template-columns: 92px 130px 1fr; align-items: center; gap: 12px; padding: 10px 12px; border: 1px solid var(--line); background: #fff; }.event-list code { color: var(--cyan); font-weight: 700; }.event-list article > div { display: grid; gap: 2px; }.event-list small { color: var(--muted); }.event-list pre { margin: 0; overflow: hidden; color: var(--muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.contract-badges, .tag-cloud { display: flex; flex-wrap: wrap; gap: 6px; }.compare-hero { display: flex; align-items: center; justify-content: space-between; padding: 16px; color: #74362f; border-left: 4px solid #c85249; background: #fff2f0; }.compare-hero.safe { color: #2d6344; border-left-color: #4d966c; background: #f0f8f3; }.compare-hero h3 { margin: 4px 0 0; }.compare-detail :deep(.el-alert) { align-items: flex-start; margin: 14px 0; }.compare-detail :deep(.el-alert__content) { width: 100%; }.compare-detail ul { margin: 8px 0 0; padding-left: 20px; }.diff-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }.diff-grid section { padding: 14px; border: 1px solid var(--line); background: #fff; }.diff-grid h4 { margin-top: 0; }.diff-grid p { display: grid; grid-template-columns: 70px 1fr; gap: 8px; margin: 9px 0; color: var(--muted); }.diff-grid p strong { color: var(--ink); }
.audit-status { display: grid; gap: 6px; padding-bottom: 16px; border-bottom: 1px solid var(--line); }.audit-status .el-tag { width: max-content; }.audit-status strong { font: 18px monospace; }.audit-status small { color: var(--muted); }.check-grid { gap: 10px; margin: 14px 0; }.check-grid article { border-top: 3px solid #c85249; }.check-grid article.passed { border-top-color: #4d966c; }.audit-detail h4 { margin: 18px 0 8px; }
@media (max-width: 1300px) { .summary-grid { grid-template-columns: repeat(3, 1fr); }.workspace-grid { grid-template-columns: 1fr; } }
@media (max-width: 900px) { .api-hero { align-items: flex-start; flex-direction: column; }.flow-strip { display: grid; grid-template-columns: 1fr; gap: 8px; }.flow-strip > span { display: none; }.contract-facts { grid-template-columns: 1fr 1fr; } }
@media (max-width: 680px) { .api-page { padding: 16px; }.summary-grid, .form-grid, .json-grid, .contract-facts, .check-grid, .diff-grid { grid-template-columns: 1fr; }.import-panel header { flex-direction: column; }.asset-card { grid-template-columns: 44px 1fr; }.asset-meta { grid-column: 2; justify-items: start; }.event-list article { grid-template-columns: 1fr; } }
</style>
