<template>
  <main class="orchestration-page" v-loading="loading">
    <section class="hero-panel">
      <div class="hero-copy">
        <p class="eyebrow">ADAPTIVE ROUTING · M06-03 / X17</p>
        <h1>执行路径动态规划</h1>
        <p>在版本化 DAG 上按事件条件选路；节点超时后释放资源并有限重试，主路径耗尽后切换备用路径，全程保留 Trace、Span 与不可变恢复事实。</p>
      </div>
      <div class="hero-actions">
        <el-button @click="loadDashboard">刷新链路</el-button>
        <el-button @click="openFlowDrawer">创建流程版本</el-button>
        <el-button type="primary" :disabled="!publishedFlows.length" @click="openEventDrawer">注入标准事件</el-button>
      </div>
    </section>

    <section class="metric-grid">
      <article><span>已发布流程</span><strong>{{ dashboard.summary.published_flow_count }}</strong><small>{{ dashboard.flows.length }} 个版本快照</small></article>
      <article><span>已接收事件</span><strong>{{ dashboard.summary.event_count }}</strong><small>事件 ID + 幂等键双门禁</small></article>
      <article class="active"><span>执行中</span><strong>{{ dashboard.summary.running_count }}</strong><small>DAG 节点正在推进</small></article>
      <article class="waiting"><span>等待处理</span><strong>{{ dashboard.summary.waiting_count }}</strong><small>{{ dashboard.summary.resource_waiting_count }} 资源 · {{ dashboard.summary.manual_waiting_count }} 人工</small></article>
      <article class="done"><span>成功闭环</span><strong>{{ dashboard.summary.succeeded_count }}</strong><small>{{ dashboard.summary.failed_count }} 条失败链路</small></article>
      <article class="recovered"><span>自愈路由</span><strong>{{ dashboard.summary.retried_node_count + dashboard.summary.fallback_count }}</strong><small>{{ dashboard.summary.retried_node_count }} 重试 · {{ dashboard.summary.fallback_count }} 降级</small></article>
    </section>

    <section class="section-panel flow-catalog">
      <div class="section-heading">
        <div><p class="eyebrow">VERSIONED BLUEPRINTS</p><h2>流程版本库</h2></div>
        <span>发布新版本后，旧版本归档；历史运行仍绑定原快照</span>
      </div>
      <div v-if="dashboard.flows.length" class="flow-grid">
        <article v-for="flow in dashboard.flows" :key="flow.id" class="flow-card">
          <div class="flow-card__top">
            <span :class="['status-pill', flow.status.toLowerCase()]">{{ flow.status_label }}</span>
            <strong>V{{ flow.version_no }}</strong>
          </div>
          <h3>{{ flow.name }}</h3>
          <code>{{ flow.event_type }}</code>
          <p>{{ flow.description || '暂无流程说明' }}</p>
          <div class="flow-meta"><span>{{ flow.node_count }} 个节点</span><span>{{ sourceLabel(flow.source_types) }}</span></div>
          <el-button v-if="flow.status === 'DRAFT'" text type="primary" @click="publishFlow(flow)">发布此版本</el-button>
        </article>
      </div>
      <el-empty v-else description="还没有流程版本" />
    </section>

    <section class="section-panel run-board">
      <div class="section-heading">
        <div><p class="eyebrow">LIVE EXECUTION</p><h2>运行实例与节点进度</h2></div>
        <span>点击实例查看路径决策、每次尝试、Trace 与不可变事件</span>
      </div>
      <el-table :data="dashboard.runs" @row-click="openRun">
        <el-table-column label="运行实例" min-width="270">
          <template #default="{ row }">
            <button class="record-link" @click.stop="openRun(row)">
              <span>{{ row.code }}</span><strong>{{ row.subject || row.flow_name }}</strong><small>{{ row.flow_name }} · V{{ row.flow_version }}</small>
            </button>
          </template>
        </el-table-column>
        <el-table-column label="事件" min-width="210"><template #default="{ row }"><code>{{ row.event_type }}</code><small class="table-sub">{{ row.event_id }}</small></template></el-table-column>
        <el-table-column label="来源" width="100"><template #default="{ row }">{{ sourceName(row.source_type) }}</template></el-table-column>
        <el-table-column label="节点进度" width="180"><template #default="{ row }"><div class="progress-copy"><b>{{ row.completed_node_count }}/{{ row.node_count }}</b><i><span :style="{ width: `${row.node_count ? row.completed_node_count / row.node_count * 100 : 0}%` }"></span></i></div></template></el-table-column>
        <el-table-column label="状态" width="120"><template #default="{ row }"><span :class="['status-pill', row.status.toLowerCase()]">{{ row.status_label }}</span></template></el-table-column>
        <el-table-column label="启动时间" width="180"><template #default="{ row }">{{ formatTime(row.started_at) }}</template></el-table-column>
      </el-table>
      <el-empty v-if="!dashboard.runs.length" description="注入一个标准事件开始运行" />
    </section>

    <section class="section-panel contract-panel">
      <div><p class="eyebrow">EXECUTION CONTRACT</p><h2>这一版真正执行了什么</h2></div>
      <div class="contract-steps">
        <article><b>01</b><strong>事件标准化</strong><span>来源、类型、载荷和幂等键先固化</span></article>
        <article><b>02</b><strong>流程匹配</strong><span>只匹配已发布版本及允许来源</span></article>
        <article><b>03</b><strong>条件选路</strong><span>安全字段比较决定执行或跳过</span></article>
        <article><b>04</b><strong>超时自愈</strong><span>释放租约、有限重试并记录尝试</span></article>
        <article><b>05</b><strong>失败降级</strong><span>重试耗尽后激活备用节点继续闭环</span></article>
      </div>
    </section>

    <el-drawer v-model="flowDrawerOpen" title="创建流程版本" size="680px" class="event-flow-create-drawer">
      <div class="drawer-scroll">
        <div class="drawer-intro"><p class="eyebrow">ADAPTIVE BLUEPRINT</p><h3>故障动态处置链路</h3><p>预置“查询 → 主模型研判 → 重试或规则降级 → 报告 → 条件告警 → 人工复核”，用于直接验收动态路径。</p></div>
        <el-form label-position="top">
          <div class="form-grid">
            <el-form-item label="流程编号"><el-input v-model="flowForm.code" placeholder="INCIDENT_ANALYSIS" /></el-form-item>
            <el-form-item label="流程名称"><el-input v-model="flowForm.name" /></el-form-item>
            <el-form-item label="事件类型"><el-input v-model="flowForm.event_type" placeholder="network.incident.detected" /></el-form-item>
            <el-form-item label="允许来源"><el-select v-model="flowForm.source_types" multiple><el-option v-for="item in sourceTypes" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
          </div>
          <el-form-item label="流程说明"><el-input v-model="flowForm.description" type="textarea" :rows="2" /></el-form-item>
          <div class="route-policy">
            <div><strong>主路径恢复策略</strong><span>超时与执行失败共享同一重试预算</span></div>
            <el-form-item label="最大重试次数"><el-input-number v-model="routePolicy.maxRetries" :min="0" :max="5" /></el-form-item>
            <el-form-item label="单次超时（秒）"><el-input-number v-model="routePolicy.timeoutSeconds" :min="30" :max="86400" /></el-form-item>
          </div>
          <div class="resource-binding">
            <h4>节点资源绑定</h4>
            <p>人工复核不占用资源池，其余节点会在执行时申请 1 单位租约。</p>
            <el-form-item label="数据查询资源池"><el-select v-model="nodePools.query"><el-option v-for="pool in pools" :key="pool.id" :label="pool.name" :value="pool.id" /></el-select></el-form-item>
            <el-form-item label="智能体分析资源池"><el-select v-model="nodePools.agent"><el-option v-for="pool in pools" :key="pool.id" :label="pool.name" :value="pool.id" /></el-select></el-form-item>
            <el-form-item label="报告、告警与降级资源池"><el-select v-model="nodePools.output"><el-option v-for="pool in pools" :key="pool.id" :label="`${pool.name} · 容量 ${pool.capacity}`" :value="pool.id" /></el-select></el-form-item>
          </div>
          <el-checkbox v-model="flowForm.publish">保存后立即发布</el-checkbox>
        </el-form>
      </div>
      <template #footer><el-button @click="flowDrawerOpen = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submitFlow">保存版本</el-button></template>
    </el-drawer>

    <el-drawer v-model="eventDrawerOpen" title="注入标准事件" size="620px" class="standard-event-create-drawer">
      <div class="drawer-scroll">
        <div class="drawer-intro dark"><p class="eyebrow">EVENT INGRESS</p><h3>事件只接收一次，流程可以稳定重放</h3><p>相同事件 ID 或幂等键再次提交时，不会重复创建运行实例。</p></div>
        <el-form label-position="top">
          <el-form-item label="目标事件类型"><el-select v-model="eventForm.event_type" @change="syncEventType"><el-option v-for="flow in publishedFlows" :key="flow.id" :label="`${flow.name} · ${flow.event_type}`" :value="flow.event_type" /></el-select></el-form-item>
          <div class="form-grid">
            <el-form-item label="事件 ID"><el-input v-model="eventForm.event_id" /></el-form-item>
            <el-form-item label="幂等键"><el-input v-model="eventForm.idempotency_key" /></el-form-item>
            <el-form-item label="事件来源"><el-select v-model="eventForm.source_type"><el-option v-for="item in sourceTypes" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
            <el-form-item label="事件主题"><el-input v-model="eventForm.subject" /></el-form-item>
          </div>
          <el-form-item label="载荷 JSON"><el-input v-model="payloadText" type="textarea" :rows="8" /><small class="field-help">载荷会按流程契约校验，并作为运行输入快照保存。</small></el-form-item>
        </el-form>
      </div>
      <template #footer><el-button @click="eventDrawerOpen = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submitEvent">接收并启动</el-button></template>
    </el-drawer>

    <el-drawer v-model="runDrawerOpen" :title="selectedRun?.code || '运行详情'" size="760px" class="event-run-detail-drawer">
      <div v-if="selectedRun" class="drawer-scroll">
        <div class="run-hero">
          <div><p>{{ selectedRun.event_id }} · {{ selectedRun.event_type }}</p><h3>{{ selectedRun.subject || selectedRun.flow_name }}</h3><span>{{ selectedRun.flow_name }} V{{ selectedRun.flow_version }} · {{ formatTime(selectedRun.started_at) }}</span><code>TRACE {{ selectedRun.trace_id }}</code></div>
          <div class="run-hero__actions"><span :class="['status-pill', selectedRun.status.toLowerCase()]">{{ selectedRun.status_label }}</span><el-button v-if="isTerminalRun(selectedRun.status)" size="small" @click="replayRun">按原版本重放</el-button></div>
        </div>
        <section class="detail-section">
          <div class="detail-heading"><div><p class="eyebrow">DAG TOPOLOGY</p><h3>节点执行图</h3></div><el-button size="small" @click="advanceRun">同步推进</el-button></div>
          <div class="node-list">
            <article v-for="node in selectedRun.nodes || []" :key="node.id" :class="['node-card', node.status.toLowerCase()]">
              <span class="node-index">{{ String(node.sequence_no).padStart(2, '0') }}</span>
              <div><strong>{{ node.node_name }}</strong><small>{{ node.node_type_label }} · {{ dependencyName(node.dependency_mode) }} · 依赖 {{ node.dependencies.join('、') || '无' }}</small><div class="policy-tags"><span v-if="node.max_retries">最多 {{ node.max_retries }} 次重试</span><span v-if="node.timeout_seconds">{{ node.timeout_seconds }}s 超时</span><span v-if="node.activation_mode === 'FALLBACK_ONLY'">备用路径</span><span v-if="Object.keys(node.condition || {}).length">条件路由</span><span v-if="node.active_attempt_no">第 {{ node.active_attempt_no }} 次尝试</span><span v-if="node.failure_handled">失败已处理</span></div><p v-if="node.dispatch_task?.queue_reason">{{ node.dispatch_task.queue_reason }}</p></div>
              <span :class="['status-pill', node.status.toLowerCase()]">{{ node.status_label }}</span>
              <div class="node-actions">
                <template v-if="node.status === 'RUNNING'"><el-button size="small" type="success" @click="operateNode(node, 'SUCCEED')">完成</el-button><el-button size="small" type="danger" plain @click="operateNode(node, 'FAIL')">失败</el-button></template>
                <template v-if="node.status === 'WAITING_MANUAL'"><el-button size="small" type="primary" @click="operateNode(node, 'APPROVE')">通过</el-button><el-button size="small" type="danger" plain @click="operateNode(node, 'REJECT')">拒绝</el-button></template>
              </div>
            </article>
          </div>
        </section>
        <section class="detail-section">
          <p class="eyebrow">TRACE ATTEMPTS</p><h3>执行尝试与 Span</h3>
          <div v-if="selectedRun.attempts?.length" class="attempt-grid">
            <article v-for="attempt in selectedRun.attempts" :key="attempt.id">
              <div><strong>{{ attempt.node_code }} · #{{ attempt.attempt_no }}</strong><span :class="['status-pill', attempt.status.toLowerCase()]">{{ attempt.status_label }}</span></div>
              <code>{{ attempt.span_id }}</code><small>{{ attempt.timeout_seconds }}s 超时门限 · {{ formatTime(attempt.started_at) }}</small>
            </article>
          </div>
          <el-empty v-else :image-size="56" description="尚未产生执行尝试" />
        </section>
        <section class="detail-section"><p class="eyebrow">IMMUTABLE EVENT LEDGER</p><h3>运行事实链</h3><div class="timeline"><article v-for="event in selectedRun.events || []" :key="event.id"><b>{{ String(event.sequence_no).padStart(2, '0') }}</b><div><strong>{{ event.event_type_label }}</strong><p>{{ event.node_code || '流程' }} · {{ event.operator_name }}</p><small>{{ formatTime(event.create_time) }}</small></div></article></div></section>
      </div>
    </el-drawer>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import {
  advanceEventFlowRun,
  createEventFlow,
  getEventFlowRun,
  getEventOrchestrationDashboard,
  operateEventFlowNode,
  publishEventFlow,
  receiveStandardEvent,
  replayEventFlowRun,
  type EventFlow,
  type EventFlowCreateForm,
  type EventFlowNodeRun,
  type EventFlowRun,
  type EventOrchestrationDashboard,
  type EventSourceType,
  type StandardEventCreateForm,
} from '@/api/event-orchestration'
import { getResourceCoordinationDashboard, type ResourcePool } from '@/api/resource-coordination'

const emptyDashboard = (): EventOrchestrationDashboard => ({
  summary: { published_flow_count: 0, event_count: 0, running_count: 0, waiting_count: 0, succeeded_count: 0, failed_count: 0, manual_waiting_count: 0, resource_waiting_count: 0, retried_node_count: 0, fallback_count: 0, skipped_node_count: 0 },
  flows: [], runs: [],
})
const loading = ref(false)
const submitting = ref(false)
const dashboard = ref<EventOrchestrationDashboard>(emptyDashboard())
const pools = ref<ResourcePool[]>([])
const flowDrawerOpen = ref(false)
const eventDrawerOpen = ref(false)
const runDrawerOpen = ref(false)
const selectedRun = ref<EventFlowRun | null>(null)
const payloadText = ref('')
const nodePools = reactive({ query: '', agent: '', output: '' })
const routePolicy = reactive({ maxRetries: 1, timeoutSeconds: 120 })
const sourceTypes = [{ value: 'SYSTEM', label: '系统状态' }, { value: 'WEBHOOK', label: 'Webhook' }, { value: 'SCHEDULED', label: '定时事件' }, { value: 'USER', label: '用户行为' }] as const
const flowForm = reactive<Omit<EventFlowCreateForm, 'nodes'>>({ code: '', name: '', description: '', event_type: '', source_types: ['SYSTEM'], event_schema: { required: ['alarm_id'] }, publish: true })
const eventForm = reactive<StandardEventCreateForm>({ event_id: '', idempotency_key: '', source_type: 'SYSTEM', event_type: '', subject: '', payload: {}, metadata: {} })
const publishedFlows = computed(() => dashboard.value.flows.filter((flow) => flow.status === 'PUBLISHED'))

const formatTime = (value: string | null) => value ? new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(new Date(value)) : '—'
const sourceName = (source: EventSourceType) => sourceTypes.find((item) => item.value === source)?.label || source
const sourceLabel = (sources: EventSourceType[]) => sources.map(sourceName).join('、')
const dependencyName = (mode: EventFlowNodeRun['dependency_mode']) => ({ ALL_SUCCESS: '全部成功', ANY_SUCCESS: '任一成功', ALL_TERMINAL: '全部结束' }[mode])
const isTerminalRun = (status: EventFlowRun['status']) => ['SUCCEEDED', 'FAILED', 'CANCELLED'].includes(status)
const newEventKey = () => `EVT-${Date.now()}-${Math.random().toString(16).slice(2, 7).toUpperCase()}`

const loadDashboard = async () => {
  const response = await getEventOrchestrationDashboard(loading)
  dashboard.value = response.data
}
const loadPools = async () => {
  const response = await getResourceCoordinationDashboard()
  pools.value = response.data.pools.filter((pool) => pool.enabled)
}
const openFlowDrawer = async () => {
  await loadPools()
  if (!pools.value.length) return ElMessage.warning('请先在资源协调中心创建可用资源池')
  const defaultPool = pools.value[0]?.id || ''
  Object.assign(nodePools, { query: defaultPool, agent: defaultPool, output: defaultPool })
  Object.assign(routePolicy, { maxRetries: 1, timeoutSeconds: 120 })
  Object.assign(flowForm, { code: 'DYNAMIC_INCIDENT_RESPONSE', name: '故障动态处置链路', description: '事件触发后查询上下文，主模型失败时有限重试并自动切换规则引擎，按严重度决定告警，最后人工复核。', event_type: 'network.incident.dynamic', source_types: ['SYSTEM', 'WEBHOOK'], event_schema: { required: ['alarm_id', 'severity'] }, publish: true })
  flowDrawerOpen.value = true
}
const submitFlow = async () => {
  if (!flowForm.code || !flowForm.name || !flowForm.event_type) return ElMessage.warning('请填写流程编号、名称和事件类型')
  if (!nodePools.query || !nodePools.agent || !nodePools.output) return ElMessage.warning('请完成节点资源绑定')
  const nodes: EventFlowCreateForm['nodes'] = [
    { code: 'QUERY_DATA', name: '查询事件上下文', node_type: 'DATA_QUERY', dependencies: [], resource_pool_id: nodePools.query, priority: 80, required_units: 1, mutex_keys: [] },
    { code: 'AGENT_ANALYSIS', name: '主模型智能研判', node_type: 'AGENT', dependencies: ['QUERY_DATA'], resource_pool_id: nodePools.agent, priority: 90, required_units: 1, mutex_keys: [], max_retries: routePolicy.maxRetries, timeout_seconds: routePolicy.timeoutSeconds, failure_strategy: 'FALLBACK', fallback_node_code: 'RULE_FALLBACK', recovery_action: 'RELEASE_AND_REROUTE' },
    { code: 'RULE_FALLBACK', name: '规则引擎降级研判', node_type: 'TOOL', dependencies: ['AGENT_ANALYSIS'], resource_pool_id: nodePools.output, priority: 88, required_units: 1, mutex_keys: [], activation_mode: 'FALLBACK_ONLY' },
    { code: 'REPORT_OUTPUT', name: '生成分析报告', node_type: 'REPORT', dependencies: ['AGENT_ANALYSIS', 'RULE_FALLBACK'], dependency_mode: 'ANY_SUCCESS', resource_pool_id: nodePools.output, priority: 70, required_units: 1, mutex_keys: [] },
    { code: 'ALERT_OUTPUT', name: '发送重大告警', node_type: 'NOTIFICATION', dependencies: ['REPORT_OUTPUT'], resource_pool_id: nodePools.output, priority: 85, required_units: 1, mutex_keys: [], condition: { source: 'EVENT_PAYLOAD', path: 'severity', operator: 'EQ', value: 'critical' } },
    { code: 'MANUAL_REVIEW', name: '人工复核', node_type: 'MANUAL', dependencies: ['REPORT_OUTPUT', 'ALERT_OUTPUT'], dependency_mode: 'ALL_TERMINAL', resource_pool_id: null, priority: 50, required_units: 1, mutex_keys: [] },
  ]
  await createEventFlow({ ...flowForm, nodes }, submitting)
  flowDrawerOpen.value = false
  ElMessage.success('流程版本已保存')
  await loadDashboard()
}
const publishFlow = async (flow: EventFlow) => {
  await publishEventFlow(flow.id, loading)
  ElMessage.success(`已发布 ${flow.name} V${flow.version_no}`)
  await loadDashboard()
}
const openEventDrawer = () => {
  const key = newEventKey()
  const flow = publishedFlows.value[0]
  Object.assign(eventForm, { event_id: key, idempotency_key: `idempotency:${key}`, source_type: flow?.source_types[0] || 'SYSTEM', event_type: flow?.event_type || '', subject: '核心网质量告警', payload: {}, metadata: {} })
  payloadText.value = JSON.stringify({ alarm_id: `ALARM-${Date.now()}`, severity: 'critical', region: '华东' }, null, 2)
  eventDrawerOpen.value = true
}
const syncEventType = () => {
  const flow = publishedFlows.value.find((item) => item.event_type === eventForm.event_type)
  if (flow && !flow.source_types.includes(eventForm.source_type)) eventForm.source_type = flow.source_types[0]
}
const submitEvent = async () => {
  try {
    eventForm.payload = JSON.parse(payloadText.value) as Record<string, unknown>
  } catch {
    return ElMessage.error('载荷不是有效 JSON')
  }
  const response = await receiveStandardEvent({ ...eventForm }, submitting)
  eventDrawerOpen.value = false
  ElMessage.success(response.data.created ? `事件已接收，创建 ${response.data.runs.length} 个运行实例` : '幂等命中，未重复创建实例')
  await loadDashboard()
  if (response.data.runs[0]) await openRun(response.data.runs[0])
}
const openRun = async (run: EventFlowRun) => {
  const response = await getEventFlowRun(run.id, loading)
  selectedRun.value = response.data
  runDrawerOpen.value = true
}
const advanceRun = async () => {
  if (!selectedRun.value) return
  const response = await advanceEventFlowRun(selectedRun.value.id, loading)
  selectedRun.value = response.data
  ElMessage.success('已同步资源状态并推进可执行节点')
  await loadDashboard()
}
const replayRun = async () => {
  if (!selectedRun.value) return
  const key = `replay:${selectedRun.value.id}:${Date.now()}`
  const response = await replayEventFlowRun(selectedRun.value.id, key, submitting)
  ElMessage.success('已按原流程版本创建重放实例')
  await loadDashboard()
  if (response.data.runs[0]) await openRun(response.data.runs[0])
}
const operateNode = async (node: EventFlowNodeRun, action: 'SUCCEED' | 'FAIL' | 'APPROVE' | 'REJECT') => {
  if (!selectedRun.value) return
  const response = await operateEventFlowNode(selectedRun.value.id, node.id, { action, note: action === 'APPROVE' ? '人工复核通过' : '' }, submitting)
  selectedRun.value = response.data
  ElMessage.success('节点状态已更新，后续依赖已重新计算')
  await loadDashboard()
}

onMounted(loadDashboard)
</script>

<style scoped lang="scss">
.orchestration-page { height: 100%; overflow-y: auto; padding: 24px; color: #202f3d; background: radial-gradient(circle at 8% 4%, rgba(15, 118, 110, .1), transparent 25%), linear-gradient(180deg, #f7faf9, #edf2f3); }
.hero-panel, .section-panel { max-width: 1440px; margin: 0 auto 18px; border: 1px solid #d8dce7; background: rgba(255, 255, 255, .92); box-shadow: 0 16px 38px rgba(34, 39, 62, .06); }
.hero-panel { min-height: 224px; padding: 36px 40px; display: flex; align-items: flex-end; justify-content: space-between; gap: 30px; color: #f7fbfb; background: linear-gradient(122deg, #102b31, #173d43 58%, #16615d); position: relative; overflow: hidden; }
.hero-panel::after { content: ''; position: absolute; inset: 0; background: repeating-linear-gradient(120deg, transparent 0 42px, rgba(255,255,255,.035) 43px 44px); pointer-events: none; }
.hero-panel > * { position: relative; z-index: 1; }.hero-copy { max-width: 820px; }.eyebrow { margin: 0 0 8px; color: #6255c8; font-size: 11px; font-weight: 800; letter-spacing: .18em; }.hero-panel .eyebrow, .drawer-intro.dark .eyebrow { color: #a9a3ff; }.hero-panel h1 { margin: 0; font-size: 40px; letter-spacing: -.045em; }.hero-copy > p:last-child { margin: 14px 0 0; color: #d6d6ef; line-height: 1.75; }.hero-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.metric-grid { max-width: 1440px; margin: 0 auto 18px; display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; }.metric-grid article { padding: 18px 20px; border: 1px solid #dcdfea; border-top: 3px solid #397d78; background: #fff; }.metric-grid article.active { border-top-color: #197d80; }.metric-grid article.waiting { border-top-color: #d8942f; }.metric-grid article.done { border-top-color: #3c9a68; }.metric-grid article.recovered { border-top-color: #d8752f; }.metric-grid span, .metric-grid small { display: block; color: #758092; }.metric-grid strong { display: block; margin: 8px 0 5px; font-size: 30px; color: #232d42; }
.section-panel { padding: 25px; }.section-heading, .detail-heading { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 18px; }.section-heading h2, .detail-heading h3 { margin: 0; }.section-heading > span { color: #778194; font-size: 13px; }.flow-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }.flow-card { padding: 18px; border: 1px solid #dedfea; background: linear-gradient(145deg, #fff, #f5f4fb); }.flow-card__top, .flow-meta { display: flex; justify-content: space-between; gap: 12px; }.flow-card__top > strong { color: #5e54ba; }.flow-card h3 { margin: 18px 0 7px; }.flow-card code, .run-board code { color: #5c4fa8; word-break: break-all; }.flow-card p { min-height: 42px; color: #798194; font-size: 13px; line-height: 1.6; }.flow-meta { margin: 16px 0 4px; color: #71798a; font-size: 12px; }
.record-link { display: flex; flex-direction: column; gap: 4px; padding: 0; border: 0; background: none; color: inherit; text-align: left; cursor: pointer; }.record-link > span { color: #6960be; font: 11px monospace; }.record-link small, .table-sub { display: block; margin-top: 4px; color: #7c8494; }.progress-copy { display: flex; align-items: center; gap: 10px; }.progress-copy i { width: 90px; height: 7px; overflow: hidden; background: #e2e4ec; }.progress-copy i span { display: block; height: 100%; background: linear-gradient(90deg, #6458c2, #38a083); }.status-pill { display: inline-flex; padding: 4px 9px; border-radius: 2px; color: #4c5362; background: #e8e9ef; font-size: 12px; white-space: nowrap; }.status-pill.published, .status-pill.succeeded { color: #147052; background: #dff4e9; }.status-pill.running { color: #176b74; background: #ddf2f2; }.status-pill.waiting, .status-pill.waiting_resource, .status-pill.waiting_manual { color: #946019; background: #fff0cf; }.status-pill.failed { color: #a83d45; background: #fbe3e4; }.status-pill.archived { color: #707687; background: #eceef2; }.status-pill.draft, .status-pill.pending, .status-pill.ready { color: #594da9; background: #e9e6fb; }
.contract-panel { color: #f2f1ff; background: #1c2138; border-color: #1c2138; }.contract-panel .eyebrow { color: #9890ec; }.contract-panel h2 { margin: 0 0 20px; }.contract-steps { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1px; background: rgba(255,255,255,.12); }.contract-steps article { min-height: 130px; padding: 18px; display: flex; flex-direction: column; background: #242944; }.contract-steps b { color: #8e86df; font: 22px monospace; }.contract-steps strong { margin: 16px 0 6px; }.contract-steps span { color: #aeb3ca; font-size: 12px; line-height: 1.6; }
.drawer-scroll { height: 100%; overflow-y: auto; padding: 0 4px 22px; }.drawer-intro, .run-hero { margin-bottom: 22px; padding: 22px; border: 1px solid #dedfea; background: #f5f4fb; }.drawer-intro.dark, .run-hero { color: #f3f2ff; background: #202440; border-color: #202440; }.drawer-intro h3, .run-hero h3 { margin: 0 0 8px; }.drawer-intro p:last-child, .run-hero span { margin: 0; color: #747d8e; line-height: 1.65; }.drawer-intro.dark p:last-child, .run-hero span { color: #bfc2d5; }.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 14px; }.resource-binding { margin: 8px 0 18px; padding: 18px; background: #f5f6fa; border-left: 3px solid #6359bf; }.resource-binding h4 { margin: 0 0 4px; }.resource-binding > p { margin: 0 0 14px; color: #788092; font-size: 12px; }.field-help { display: block; margin-top: 5px; color: #7c8494; }.run-hero { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }.run-hero p { margin: 0 0 10px; color: #9c96e4; font: 12px monospace; }.detail-section { margin: 0 0 20px; padding: 20px; border: 1px solid #dfe1e9; }.detail-section > h3 { margin: 0 0 16px; }.node-list { display: flex; flex-direction: column; gap: 9px; }.node-card { display: grid; grid-template-columns: 42px 1fr auto auto; gap: 13px; align-items: center; padding: 14px; border-left: 3px solid #b5b8c4; background: #f6f7fa; }.node-card.running { border-color: #24858a; }.node-card.succeeded { border-color: #3b9a69; }.node-card.waiting_resource, .node-card.waiting_manual { border-color: #dc9632; }.node-index { color: #6b61c1; font: 18px monospace; }.node-card small { display: block; margin-top: 4px; color: #7c8494; }.node-card p { margin: 5px 0 0; color: #a56822; font-size: 12px; }.node-actions { display: flex; gap: 5px; }.timeline article { display: grid; grid-template-columns: 40px 1fr; gap: 12px; padding: 0 0 18px; }.timeline article > b { color: #675dc0; font: 15px monospace; }.timeline p, .timeline small { margin: 4px 0 0; color: #7c8494; font-size: 12px; }
.hero-panel .eyebrow, .drawer-intro.dark .eyebrow { color: #83e4d7; }
.status-pill.failed, .status-pill.timed_out { color: #a83d45; background: #fbe3e4; }
.status-pill.skipped { color: #586678; background: #e9edf1; }
.resource-binding { background: #f5f8f8; border-left-color: #27857d; }
.route-policy { margin: 8px 0 18px; padding: 16px 18px; display: grid; grid-template-columns: 1fr 140px 160px; gap: 14px; align-items: end; border: 1px solid #cbdedb; background: #f1f8f7; }
.route-policy > div { align-self: center; }.route-policy strong, .route-policy span { display: block; }.route-policy span { margin-top: 4px; color: #758092; font-size: 12px; }.route-policy .el-form-item { margin-bottom: 0; }
.run-hero p { color: #7ed8ce; }.run-hero code { display: block; margin-top: 10px; color: #8fcbc5; font-size: 11px; word-break: break-all; }.run-hero__actions { display: flex; flex-direction: column; align-items: flex-end; gap: 10px; }
.node-card.skipped { border-color: #84909f; opacity: .76; }.node-card.failed { border-color: #c5555e; }
.policy-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 7px; }.policy-tags span { padding: 2px 6px; color: #2d6865; background: #dcefed; font-size: 10px; }
.attempt-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }.attempt-grid article { padding: 12px; border: 1px solid #dfe5e5; background: #f7f9f9; }.attempt-grid article > div { display: flex; justify-content: space-between; gap: 10px; }.attempt-grid code, .attempt-grid small { display: block; margin-top: 7px; color: #738087; font-size: 10px; word-break: break-all; }
@media (max-width: 1100px) { .metric-grid { grid-template-columns: repeat(2, 1fr); }.flow-grid { grid-template-columns: repeat(2, 1fr); }.contract-steps { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 720px) { .orchestration-page { padding: 12px; }.hero-panel { padding: 26px 22px; align-items: flex-start; flex-direction: column; }.hero-panel h1 { font-size: 32px; }.metric-grid, .flow-grid, .contract-steps, .form-grid, .route-policy, .attempt-grid { grid-template-columns: 1fr; }.node-card { grid-template-columns: 34px 1fr; }.node-card > .status-pill, .node-actions { grid-column: 2; } }
</style>

<style lang="scss">
.event-flow-create-drawer .el-drawer__body, .standard-event-create-drawer .el-drawer__body, .event-run-detail-drawer .el-drawer__body { overflow: hidden; }
</style>
