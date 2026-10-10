<template>
  <main class="resource-page" v-loading="loading">
    <section class="hero-panel">
      <div>
        <p class="eyebrow">RESOURCE ARBITER · M06-01 / X16</p>
        <h1>资源协调中心</h1>
        <p class="hero-copy">
          把智能体、模型、工具和执行器纳入统一配额，按优先级分配租约，用互斥键隔离冲突，并保留完整调度事实链。
        </p>
      </div>
      <div class="hero-actions">
        <el-button @click="loadDashboard">刷新态势</el-button>
        <el-button @click="poolDrawerOpen = true">新建资源池</el-button>
        <el-button type="primary" :disabled="!dashboard.pools.length" @click="openTaskDrawer">
          提交调度任务
        </el-button>
      </div>
    </section>

    <section class="metric-grid">
      <article class="metric-card teal">
        <span>资源池</span><strong>{{ dashboard.summary.pool_count }}</strong>
        <small>{{ dashboard.summary.enabled_pool_count }} 个已启用</small>
      </article>
      <article class="metric-card orange">
        <span>执行中</span><strong>{{ dashboard.summary.running_task_count }}</strong>
        <small>{{ dashboard.summary.active_lease_count }} 份活跃租约</small>
      </article>
      <article class="metric-card gold">
        <span>等待队列</span><strong>{{ dashboard.summary.queued_task_count }}</strong>
        <small>严格按优先级与入队时间</small>
      </article>
      <article class="metric-card ink">
        <span>已分配配额</span><strong>{{ dashboard.summary.allocated_units }}</strong>
        <small>跨资源池实时汇总</small>
      </article>
      <article class="metric-card red">
        <span>互斥冲突</span><strong>{{ dashboard.summary.mutex_conflict_count }}</strong>
        <small>冲突任务保留在等待队列</small>
      </article>
    </section>

    <section class="section-panel">
      <div class="section-heading">
        <div><p class="eyebrow">CAPACITY MAP</p><h2>资源池配额地图</h2></div>
        <span>{{ totalCapacity }} 总配额 · {{ totalAvailable }} 可用</span>
      </div>
      <div v-if="dashboard.pools.length" class="pool-grid">
        <article v-for="pool in dashboard.pools" :key="pool.id" class="pool-card">
          <div class="pool-card__top">
            <span class="pool-kind">{{ pool.resource_type_label }}</span>
            <button class="text-action" @click="reclaim(pool)">回收过期租约</button>
          </div>
          <h3>{{ pool.name }}</h3>
          <p>{{ pool.code }} · 单任务上限 {{ pool.max_units_per_task }}</p>
          <div class="capacity-number"><strong>{{ pool.used_units }}</strong><span>/ {{ pool.capacity }}</span></div>
          <div class="capacity-track"><i :style="{ width: `${pool.utilization_percent}%` }"></i></div>
          <div class="pool-footer">
            <span>{{ pool.active_lease_count }} 个运行</span>
            <span>{{ pool.queued_task_count }} 个等待</span>
            <span>{{ pool.lease_timeout_seconds }}s 租约</span>
          </div>
        </article>
      </div>
      <el-empty v-else description="还没有资源池" />
    </section>

    <section class="section-panel dispatch-board">
      <div class="section-heading">
        <div><p class="eyebrow">ARBITRATION BOARD</p><h2>实时调度棋盘</h2></div>
        <span>配额门禁 → 互斥检查 → 租约分配</span>
      </div>
      <div class="lane-grid">
        <div class="task-lane running-lane">
          <header><span>RUNNING</span><strong>{{ runningTasks.length }}</strong></header>
          <button v-for="task in runningTasks" :key="task.id" class="task-ticket" @click="openDetail(task)">
            <span class="priority-mark">P{{ task.priority }}</span>
            <span><strong>{{ task.name }}</strong><small>{{ task.pool_name }} · {{ task.required_units }} 单位</small></span>
            <span class="lease-time">{{ task.lease ? timeUntil(task.lease.expires_at) : '—' }}</span>
          </button>
          <p v-if="!runningTasks.length" class="lane-empty">暂无执行中任务</p>
        </div>
        <div class="task-lane queued-lane">
          <header><span>QUEUED</span><strong>{{ queuedTasks.length }}</strong></header>
          <button v-for="task in queuedTasks" :key="task.id" class="task-ticket" @click="openDetail(task)">
            <span class="priority-mark">P{{ task.priority }}</span>
            <span><strong>{{ task.name }}</strong><small>{{ task.queue_reason || '等待调度' }}</small></span>
            <span class="mutex-count">{{ task.mutex_keys.length }} 锁</span>
          </button>
          <p v-if="!queuedTasks.length" class="lane-empty">等待队列已清空</p>
        </div>
      </div>
    </section>

    <section class="section-panel">
      <div class="section-heading table-heading">
        <div><p class="eyebrow">IMMUTABLE LEDGER</p><h2>任务与租约台账</h2></div>
        <div class="legend"><span class="dot running"></span>运行中<span class="dot queued"></span>等待<span class="dot done"></span>终态</div>
      </div>
      <el-table :data="dashboard.tasks" @row-click="openDetail">
        <el-table-column label="任务" min-width="250">
          <template #default="{ row }">
            <button class="record-link" @click.stop="openDetail(row)">
              <span class="record-code">{{ row.code }}</span>
              <span><strong>{{ row.name }}</strong><small>{{ row.source_label }} · {{ formatTime(row.queued_at) }}</small></span>
            </button>
          </template>
        </el-table-column>
        <el-table-column label="资源池" prop="pool_name" min-width="160" />
        <el-table-column label="优先级" width="100"><template #default="{ row }"><b>P{{ row.priority }}</b></template></el-table-column>
        <el-table-column label="配额" width="90"><template #default="{ row }">{{ row.required_units }}</template></el-table-column>
        <el-table-column label="互斥资源" min-width="180">
          <template #default="{ row }"><span class="mutex-text">{{ row.mutex_keys.join('、') || '无' }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="110"><template #default="{ row }"><span :class="['status-pill', row.status.toLowerCase()]">{{ row.status_label }}</span></template></el-table-column>
        <el-table-column label="队列说明" min-width="220"><template #default="{ row }">{{ row.queue_reason || '—' }}</template></el-table-column>
      </el-table>
    </section>

    <el-drawer v-model="poolDrawerOpen" title="新建资源池" size="520px" class="coordination-drawer pool-create-drawer">
      <div class="drawer-scroll">
        <div class="drawer-intro"><p class="eyebrow">CAPACITY CONTRACT</p><h3>定义可分配资源边界</h3><p>配额和租约会成为所有调度任务的统一门禁。</p></div>
        <el-form label-position="top">
          <div class="form-grid">
            <el-form-item label="资源池编号"><el-input v-model="poolForm.code" placeholder="AGENT_CORE" /></el-form-item>
            <el-form-item label="资源池名称"><el-input v-model="poolForm.name" /></el-form-item>
            <el-form-item label="资源类型"><el-select v-model="poolForm.resource_type"><el-option v-for="item in poolTypes" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
            <el-form-item label="总配额"><el-input-number v-model="poolForm.capacity" :min="1" :max="10000" /></el-form-item>
            <el-form-item label="单任务上限"><el-input-number v-model="poolForm.max_units_per_task" :min="1" :max="poolForm.capacity" /></el-form-item>
            <el-form-item label="租约超时（秒）"><el-input-number v-model="poolForm.lease_timeout_seconds" :min="30" :max="86400" /></el-form-item>
          </div>
          <el-form-item label="说明"><el-input v-model="poolForm.description" type="textarea" :rows="3" /></el-form-item>
        </el-form>
      </div>
      <template #footer><el-button @click="poolDrawerOpen = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submitPool">保存资源池</el-button></template>
    </el-drawer>

    <el-drawer v-model="taskDrawerOpen" title="提交调度任务" size="580px" class="coordination-drawer task-create-drawer">
      <div class="drawer-scroll">
        <div class="drawer-intro dark"><p class="eyebrow">ARBITRATION REQUEST</p><h3>一次提交，一条不可覆盖事实链</h3><p>幂等键防止重复任务；优先级只影响等待队列，不抢占已分配租约。</p></div>
        <el-form label-position="top">
          <el-form-item label="目标资源池"><el-select v-model="selectedPoolId"><el-option v-for="pool in dashboard.pools" :key="pool.id" :label="`${pool.name} · 剩余 ${pool.available_units}`" :value="pool.id" /></el-select></el-form-item>
          <div class="form-grid">
            <el-form-item label="任务名称"><el-input v-model="taskForm.name" /></el-form-item>
            <el-form-item label="来源"><el-select v-model="taskForm.source"><el-option v-for="item in sourceTypes" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
            <el-form-item label="优先级（1-100）"><el-input-number v-model="taskForm.priority" :min="1" :max="100" /></el-form-item>
            <el-form-item label="申请配额"><el-input-number v-model="taskForm.required_units" :min="1" :max="selectedPool?.max_units_per_task || 1" /></el-form-item>
            <el-form-item label="请求编号"><el-input v-model="taskForm.request_id" /></el-form-item>
            <el-form-item label="幂等键"><el-input v-model="taskForm.idempotency_key" /></el-form-item>
          </div>
          <el-form-item label="互斥资源键"><el-input v-model="mutexText" placeholder="customer:001, model:billing" /><small class="field-help">多个键用英文逗号分隔；任一键被占用时任务进入等待队列。</small></el-form-item>
          <el-form-item label="来源引用"><el-input v-model="taskForm.source_reference" placeholder="event:customer-complaint" /></el-form-item>
        </el-form>
      </div>
      <template #footer><el-button @click="taskDrawerOpen = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submitTask">提交并尝试分配</el-button></template>
    </el-drawer>

    <el-drawer v-model="detailDrawerOpen" :title="selectedTask?.name || '任务详情'" size="640px" class="coordination-drawer task-detail-drawer">
      <div v-if="selectedTask" class="drawer-scroll">
        <div class="detail-hero">
          <div><p>{{ selectedTask.code }}</p><h3>{{ selectedTask.status_label }}</h3><span>{{ selectedTask.pool_name }} · P{{ selectedTask.priority }} · {{ selectedTask.required_units }} 单位</span></div>
          <span :class="['status-pill', selectedTask.status.toLowerCase()]">{{ selectedTask.status_label }}</span>
        </div>
        <section class="detail-section"><p class="eyebrow">MUTEX & LEASE</p><h3>资源约束</h3><div class="detail-grid"><div><span>互斥键</span><strong>{{ selectedTask.mutex_keys.join('、') || '无' }}</strong></div><div><span>队列说明</span><strong>{{ selectedTask.queue_reason || '已通过门禁' }}</strong></div><div><span>租约到期</span><strong>{{ selectedTask.lease ? formatTime(selectedTask.lease.expires_at) : '未分配' }}</strong></div><div><span>租约状态</span><strong>{{ selectedTask.lease?.status_label || '—' }}</strong></div></div></section>
        <section class="detail-section"><p class="eyebrow">EVENT LEDGER</p><h3>不可变调度事件</h3><div class="timeline"><article v-for="event in selectedTask.events" :key="event.id"><span>{{ String(event.sequence_no).padStart(2, '0') }}</span><div><strong>{{ event.event_type_label }}</strong><p>{{ event.current_status_label }} · {{ event.operator_name }}</p><small>{{ formatTime(event.create_time) }}</small></div></article></div></section>
      </div>
      <template #footer>
        <template v-if="selectedTask?.status === 'RUNNING'"><el-button type="danger" plain @click="operate('FAIL')">标记失败</el-button><el-button type="success" @click="operate('SUCCEED')">完成并释放</el-button></template>
        <el-button v-if="selectedTask && ['QUEUED', 'RUNNING'].includes(selectedTask.status)" @click="operate('CANCEL')">取消任务</el-button>
      </template>
    </el-drawer>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import {
  createDispatchTask,
  createResourcePool,
  getDispatchTask,
  getResourceCoordinationDashboard,
  operateDispatchTask,
  reclaimResourcePool,
  type DispatchTask,
  type DispatchTaskAction,
  type DispatchTaskCreateForm,
  type ResourceCoordinationDashboard,
  type ResourcePool,
  type ResourcePoolCreateForm,
} from '@/api/resource-coordination'

const emptyDashboard = (): ResourceCoordinationDashboard => ({
  summary: { pool_count: 0, enabled_pool_count: 0, queued_task_count: 0, running_task_count: 0, succeeded_task_count: 0, failed_task_count: 0, active_lease_count: 0, allocated_units: 0, mutex_conflict_count: 0 },
  pools: [], tasks: [],
})
const loading = ref(false)
const submitting = ref(false)
const dashboard = ref<ResourceCoordinationDashboard>(emptyDashboard())
const poolDrawerOpen = ref(false)
const taskDrawerOpen = ref(false)
const detailDrawerOpen = ref(false)
const selectedPoolId = ref('')
const selectedTask = ref<DispatchTask | null>(null)
const mutexText = ref('')
const poolTypes = [{ value: 'AGENT', label: '智能体' }, { value: 'MODEL', label: '模型' }, { value: 'TOOL', label: '工具' }, { value: 'WORKER', label: '执行器' }] as const
const sourceTypes = [{ value: 'WEBHOOK', label: 'Webhook' }, { value: 'SCHEDULED', label: '定时触发' }, { value: 'USER', label: '用户发起' }, { value: 'SYSTEM', label: '系统事件' }] as const
const poolForm = reactive<ResourcePoolCreateForm>({ code: '', name: '', resource_type: 'AGENT', capacity: 4, max_units_per_task: 2, lease_timeout_seconds: 300, description: '' })
const taskForm = reactive<DispatchTaskCreateForm>({ request_id: '', idempotency_key: '', name: '', source: 'SYSTEM', source_reference: '', priority: 50, required_units: 1, mutex_keys: [], payload: {} })
const runningTasks = computed(() => dashboard.value.tasks.filter((task) => task.status === 'RUNNING'))
const queuedTasks = computed(() => dashboard.value.tasks.filter((task) => task.status === 'QUEUED'))
const totalCapacity = computed(() => dashboard.value.pools.reduce((total, pool) => total + pool.capacity, 0))
const totalAvailable = computed(() => dashboard.value.pools.reduce((total, pool) => total + pool.available_units, 0))
const selectedPool = computed(() => dashboard.value.pools.find((pool) => pool.id === selectedPoolId.value))

const formatTime = (value: string | null) => value ? new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(new Date(value)) : '—'
const timeUntil = (value: string) => {
  const seconds = Math.max(Math.floor((new Date(value).getTime() - Date.now()) / 1000), 0)
  return seconds ? `${Math.floor(seconds / 60)}m ${seconds % 60}s` : '待回收'
}
const newKey = (prefix: string) => `${prefix}:${Date.now()}:${Math.random().toString(16).slice(2, 8)}`
const loadDashboard = async () => {
  const response = await getResourceCoordinationDashboard(loading)
  dashboard.value = response.data
}
const openTaskDrawer = () => {
  selectedPoolId.value = dashboard.value.pools[0]?.id || ''
  const key = newKey('dispatch')
  Object.assign(taskForm, { request_id: key, idempotency_key: key, name: '', source: 'SYSTEM', source_reference: '', priority: 50, required_units: 1, mutex_keys: [], payload: {} })
  mutexText.value = ''
  taskDrawerOpen.value = true
}
const submitPool = async () => {
  if (!poolForm.code || !poolForm.name) return ElMessage.warning('请填写资源池编号和名称')
  await createResourcePool({ ...poolForm }, submitting)
  poolDrawerOpen.value = false
  Object.assign(poolForm, { code: '', name: '', resource_type: 'AGENT', capacity: 4, max_units_per_task: 2, lease_timeout_seconds: 300, description: '' })
  ElMessage.success('资源池已创建')
  await loadDashboard()
}
const submitTask = async () => {
  if (!selectedPoolId.value || !taskForm.name) return ElMessage.warning('请选择资源池并填写任务名称')
  const mutexKeys = mutexText.value.split(',').map((item) => item.trim()).filter(Boolean)
  const response = await createDispatchTask(selectedPoolId.value, { ...taskForm, mutex_keys: mutexKeys }, submitting)
  taskDrawerOpen.value = false
  ElMessage.success(response.data.created ? '任务已提交' : '幂等命中，已返回原任务')
  await loadDashboard()
  await openDetail(response.data.task)
}
const openDetail = async (task: DispatchTask) => {
  const response = await getDispatchTask(task.id, loading)
  selectedTask.value = response.data
  detailDrawerOpen.value = true
}
const operate = async (action: DispatchTaskAction) => {
  if (!selectedTask.value) return
  const response = await operateDispatchTask(selectedTask.value.id, { action, note: action === 'SUCCEED' ? '任务执行完成，释放资源租约' : '' }, submitting)
  selectedTask.value = response.data.task
  ElMessage.success('任务状态已更新')
  await loadDashboard()
}
const reclaim = async (pool: ResourcePool) => {
  const response = await reclaimResourcePool(pool.id, loading)
  ElMessage.success(`已回收 ${response.data.expired_lease_ids.length} 份过期租约`)
  await loadDashboard()
}

onMounted(loadDashboard)
</script>

<style scoped lang="scss">
.resource-page { height: 100%; overflow-y: auto; padding: 24px; color: #17383a; background: radial-gradient(circle at 88% 5%, rgba(13,124,120,.12), transparent 28%), linear-gradient(180deg,#f4f8f6 0%,#eef3f1 100%); }
.hero-panel,.section-panel { max-width: 1440px; margin: 0 auto 18px; border: 1px solid #cedbd7; background: rgba(255,255,255,.9); box-shadow: 0 16px 36px rgba(26,58,58,.06); }
.hero-panel { min-height: 230px; padding: 34px 38px; display:flex; align-items:flex-end; justify-content:space-between; gap:32px; color:#f4fffc; background: linear-gradient(118deg,#0f3435 0%,#174e4c 70%,#b95b3e 140%); position:relative; overflow:hidden; }
.hero-panel::after { content:''; position:absolute; inset:0; background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px); background-size:28px 28px; mask-image:linear-gradient(90deg,transparent,#000); pointer-events:none; }
.hero-panel > * { position:relative; z-index:1; }.eyebrow { margin:0 0 8px; color:#168783; font-size:11px; letter-spacing:.18em; font-weight:700; }.hero-panel .eyebrow,.drawer-intro.dark .eyebrow { color:#69d7cb; }.hero-panel h1 { margin:0; font-size:38px; letter-spacing:-.04em; }.hero-copy { max-width:760px; margin:14px 0 0; line-height:1.75; color:#cce2de; }.hero-actions { display:flex; gap:10px; flex-wrap:wrap; }
.metric-grid { max-width:1440px; margin:0 auto 18px; display:grid; grid-template-columns:repeat(5,1fr); gap:12px; }.metric-card { padding:18px 20px; background:#fff; border:1px solid #d3dfdc; border-top:3px solid var(--accent); }.metric-card span,.metric-card small { display:block; color:#71817e; }.metric-card strong { display:block; margin:8px 0 5px; font-size:30px; color:#183b3c; }.metric-card.teal{--accent:#0d7c78}.metric-card.orange{--accent:#e56b4a}.metric-card.gold{--accent:#d5a13d}.metric-card.ink{--accent:#2b4d56}.metric-card.red{--accent:#bc4d42}
.section-panel { padding:24px; }.section-heading { display:flex; justify-content:space-between; gap:20px; align-items:flex-start; margin-bottom:18px; }.section-heading h2 { margin:0; font-size:22px; }.section-heading > span,.legend { color:#758581; font-size:13px; }.pool-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }.pool-card { padding:18px; border:1px solid #d5e1de; background:linear-gradient(150deg,#fff,#f2f7f5); }.pool-card__top,.pool-footer { display:flex; justify-content:space-between; gap:8px; }.pool-kind { padding:4px 8px; color:#0d716e; background:#dff1ed; font-size:12px; }.text-action { border:0;background:none;color:#b45b40;cursor:pointer; }.pool-card h3 { margin:18px 0 5px; }.pool-card p { margin:0;color:#768480;font-size:12px; }.capacity-number { margin:20px 0 7px; }.capacity-number strong { font-size:34px; }.capacity-number span { color:#7b8c88; }.capacity-track { height:8px;background:#dce7e4;overflow:hidden; }.capacity-track i { display:block;height:100%;background:linear-gradient(90deg,#0b7a76,#e6744e); }.pool-footer { margin-top:14px;color:#667773;font-size:12px; }
.dispatch-board { background:#102f31;color:#ecf8f5;border-color:#102f31; }.dispatch-board .eyebrow{color:#6cd2c7}.dispatch-board .section-heading>span{color:#9cbab4}.lane-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.task-lane{padding:16px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.13)}.task-lane header{display:flex;justify-content:space-between;margin-bottom:12px;color:#a7c5bf;letter-spacing:.12em}.task-ticket{width:100%;display:grid;grid-template-columns:55px 1fr auto;gap:12px;align-items:center;margin-top:8px;padding:13px;border:0;text-align:left;background:#f4f8f6;color:#18393a;cursor:pointer}.task-ticket small{display:block;margin-top:4px;color:#74827f}.priority-mark{font-weight:800;color:#cf6848}.lease-time,.mutex-count{font-size:12px;color:#53716d}.lane-empty{text-align:center;color:#8da9a4;padding:28px}.queued-lane .task-ticket{background:#fff8ed}
.record-link { display:flex;gap:12px;align-items:center;border:0;background:none;text-align:left;cursor:pointer;color:inherit; }.record-link small{display:block;color:#80908c;margin-top:3px}.record-code{font:700 11px/1 monospace;padding:7px;background:#153e3f;color:#e6f9f5}.mutex-text{font-size:12px;color:#536c68}.status-pill{display:inline-flex;padding:4px 9px;border-radius:99px;font-size:12px;background:#e8eeec;color:#59706c}.status-pill.running{background:#d9f0eb;color:#08736e}.status-pill.queued{background:#fff0d7;color:#9a6114}.status-pill.succeeded{background:#e0f1e4;color:#277043}.status-pill.failed{background:#fee5df;color:#aa3f31}.status-pill.cancelled{background:#e7e9ea;color:#596267}.legend{display:flex;gap:7px;align-items:center}.dot{width:8px;height:8px;border-radius:50%;margin-left:8px}.dot.running{background:#0d7c78}.dot.queued{background:#d5a13d}.dot.done{background:#778784}
.drawer-scroll { height:100%; overflow-y:auto; padding:0 4px 20px; }.drawer-intro { padding:22px;margin-bottom:20px;background:#eef6f3;border-left:4px solid #0d7c78; }.drawer-intro.dark,.detail-hero{background:#123a3b;color:#edf9f6}.drawer-intro h3,.detail-hero h3{margin:4px 0 8px}.drawer-intro p:last-child{margin:0;line-height:1.65}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 14px}.field-help{display:block;margin-top:7px;color:#81908d}.detail-hero{display:flex;justify-content:space-between;align-items:flex-start;padding:24px}.detail-hero p{margin:0;color:#79d2c8;font:700 12px monospace}.detail-hero span{color:#b5d1cc}.detail-section{padding:22px 4px;border-bottom:1px solid #dde6e3}.detail-section h3{margin:0 0 16px}.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.detail-grid>div{padding:13px;background:#f2f6f5}.detail-grid span{display:block;color:#7c8b88;font-size:12px;margin-bottom:6px}.timeline article{display:grid;grid-template-columns:42px 1fr;gap:12px;padding:12px 0;border-bottom:1px solid #e1e8e6}.timeline article>span{font:700 13px monospace;color:#d46647}.timeline p,.timeline small{margin:4px 0 0;color:#71817e}
@media (max-width:1100px){.metric-grid{grid-template-columns:repeat(2,1fr)}.pool-grid{grid-template-columns:repeat(2,1fr)}}
@media (max-width:720px){.resource-page{padding:12px}.hero-panel{padding:24px;align-items:flex-start;flex-direction:column}.hero-panel h1{font-size:30px}.metric-grid,.pool-grid,.lane-grid,.form-grid,.detail-grid{grid-template-columns:1fr}.section-heading{flex-direction:column}.table-heading{align-items:flex-start}}
</style>
