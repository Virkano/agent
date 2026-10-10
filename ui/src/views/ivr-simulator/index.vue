<template>
  <div class="ivr-page p-16-24">
    <section class="hero-panel">
      <div>
        <div class="eyebrow">IVR / M09-01～M09-03</div>
        <h2>IVR 与变更操作控制</h2>
        <p>贯通协议会话、风险灯、执行提醒和质量报告；生产 IVR 长连接仍待网关联调。</p>
      </div>
      <div class="hero-actions">
        <el-tag type="warning" effect="dark">外部接入待联调</el-tag>
        <el-button :loading="loading" @click="loadDashboard">刷新</el-button>
      </div>
    </section>

    <el-alert
      class="boundary-alert"
      type="warning"
      :closable="false"
      show-icon
      title="当前 WebSocket 为 JSON 消息契约回放，不代表真实电话线路或生产长连接已经接通。"
    />

    <section class="summary-grid">
      <article v-for="item in summaryCards" :key="item.label" class="summary-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </section>

    <section class="main-grid">
      <el-card class="create-card" shadow="never">
        <template #header>
          <div class="card-heading">
            <div>
              <strong>创建演练会话</strong>
              <span>输入号码只用于生成脱敏结果，原号码不会入库</span>
            </div>
          </div>
        </template>
        <el-form label-position="top" :model="createForm">
          <el-form-item label="外部会话编号">
            <el-input v-model="createForm.external_session_id" placeholder="留空则自动生成" />
          </el-form-item>
          <div class="form-grid">
            <el-form-item label="传输方式">
              <el-select v-model="createForm.transport" class="full-width">
                <el-option label="HTTP 接口" value="HTTP" />
                <el-option label="WebSocket 契约回放" value="WEBSOCKET_REPLAY" />
              </el-select>
            </el-form-item>
            <el-form-item label="语言">
              <el-select v-model="createForm.language" class="full-width">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
          </div>
          <el-form-item label="来电号码">
            <el-input v-model="createForm.caller_number" placeholder="例如 13800138000" />
          </el-form-item>
          <el-form-item label="来电标签">
            <el-input v-model="createForm.caller_label" placeholder="例如：套餐变更咨询" />
          </el-form-item>
          <el-button type="primary" :loading="creating" class="full-width" @click="handleCreate">
            创建并进入演练
          </el-button>
        </el-form>
      </el-card>

      <el-card class="protocol-card" shadow="never">
        <template #header>
          <div class="card-heading">
            <div>
              <strong>协议实现边界</strong>
              <span>{{ dashboard.protocol.version }}</span>
            </div>
            <el-tag type="info">{{ dashboard.protocol.mode }}</el-tag>
          </div>
        </template>
        <div class="protocol-block">
          <div class="protocol-title">
            <span>HTTP</span>
            <el-tag type="success" size="small">可调用</el-tag>
          </div>
          <code v-for="(path, key) in dashboard.protocol.http" :key="key">{{ path }}</code>
        </div>
        <div class="protocol-block">
          <div class="protocol-title">
            <span>WebSocket</span>
            <el-tag type="warning" size="small">{{ dashboard.protocol.websocket.status }}</el-tag>
          </div>
          <code>{{ dashboard.protocol.websocket.future_endpoint }}</code>
          <p>{{ dashboard.protocol.websocket.note }}</p>
        </div>
        <div class="command-list">
          <span v-for="command in dashboard.protocol.response_commands" :key="command">{{
            command
          }}</span>
        </div>
      </el-card>
    </section>

    <el-card class="session-card" shadow="never">
      <template #header>
        <div class="card-heading">
          <div>
            <strong>最近会话</strong>
            <span>最多显示最近更新的 30 条，验收数据默认保留</span>
          </div>
        </div>
      </template>
      <el-table v-loading="loading" :data="dashboard.sessions" row-key="id">
        <el-table-column label="会话" min-width="210">
          <template #default="{ row }">
            <div class="cell-primary">{{ row.external_session_id }}</div>
            <div class="cell-secondary">{{ row.caller_label || '未设置标签' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="来电号码" width="145">
          <template #default="{ row }">{{ row.caller_masked || '—' }}</template>
        </el-table-column>
        <el-table-column label="传输" width="165">
          <template #default="{ row }">
            <el-tag :type="row.transport === 'HTTP' ? 'success' : 'warning'">
              {{ row.transport_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最近转写 / 响应" min-width="330">
          <template #default="{ row }">
            <div class="cell-primary text-ellipsis">
              {{ row.latest_transcript || '等待音频分片' }}
            </div>
            <div class="cell-secondary text-ellipsis">
              {{ row.latest_response || '尚未生成响应指令' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="事件" width="80" align="center" prop="current_sequence" />
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">{{ formatTime(row.update_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openSession(row.id)">查看与演练</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="还没有 IVR 演练会话" />
        </template>
      </el-table>
    </el-card>

    <ChangeRiskPanel :sessions="dashboard.sessions" />

    <ChangeControlReportPanel />

    <el-drawer v-model="drawerVisible" size="720px" destroy-on-close>
      <template #header>
        <div v-if="selectedSession" class="drawer-heading">
          <div>
            <strong>{{ selectedSession.external_session_id }}</strong>
            <span>{{ selectedSession.caller_label || 'IVR 演练会话' }}</span>
          </div>
          <el-tag :type="statusMeta[selectedSession.status].type">
            {{ selectedSession.status_label }}
          </el-tag>
        </div>
      </template>

      <div v-if="selectedSession" v-loading="detailLoading" class="drawer-content">
        <section class="state-strip">
          <div>
            <span>传输</span><strong>{{ selectedSession.transport_label }}</strong>
          </div>
          <div>
            <span>脱敏号码</span><strong>{{ selectedSession.caller_masked || '—' }}</strong>
          </div>
          <div>
            <span>Redis 状态</span
            ><strong>{{ selectedSession.redis_state ? '已同步' : '未命中' }}</strong>
          </div>
          <div>
            <span>事件序号</span><strong>{{ selectedSession.current_sequence }}</strong>
          </div>
        </section>

        <el-card class="simulation-card" shadow="never">
          <template #header><strong>发送音频分片（文本代替真实音频）</strong></template>
          <el-form label-position="top" :model="audioForm">
            <el-form-item label="演练转写文本">
              <el-input
                v-model="audioForm.transcript_hint"
                type="textarea"
                :rows="3"
                placeholder="输入客户在电话中说的话，例如：请帮我查询当前套餐"
                :disabled="isTerminal"
              />
            </el-form-item>
            <div class="form-grid">
              <el-form-item label="分片序号">
                <el-input-number v-model="audioForm.chunk_index" :min="0" class="full-width" />
              </el-form-item>
              <el-form-item label="分片时长（毫秒）">
                <el-input-number v-model="audioForm.duration_ms" :min="0" class="full-width" />
              </el-form-item>
            </div>
            <el-checkbox v-model="audioForm.is_final" :disabled="isTerminal"
              >最后一个分片</el-checkbox
            >
            <el-button
              type="primary"
              class="send-button"
              :loading="sending"
              :disabled="isTerminal"
              @click="handleSendAudio"
            >
              发送分片并生成响应
            </el-button>
          </el-form>
        </el-card>

        <el-card v-if="latestInstruction" class="instruction-card" shadow="never">
          <template #header>
            <div class="card-heading">
              <strong>最新响应指令</strong>
              <el-tag>{{ latestInstruction.command }}</el-tag>
            </div>
          </template>
          <p>{{ latestInstruction.tts_text }}</p>
          <small>{{ latestInstruction.reason }}</small>
        </el-card>

        <section class="state-actions">
          <span>回放 IVR 侧状态：</span>
          <el-button
            v-for="action in stateActions"
            :key="action.value"
            :type="action.type"
            plain
            size="small"
            :loading="eventSending"
            :disabled="isTerminal"
            @click="handleStateEvent(action.value)"
          >
            {{ action.label }}
          </el-button>
        </section>

        <section class="event-section">
          <div class="section-heading">
            <strong>事件链路</strong>
            <span>数据库为审计事实，Redis 仅保存当前会话状态</span>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="event in orderedEvents"
              :key="event.id"
              :timestamp="formatTime(event.occurred_at)"
              :type="directionType[event.direction]"
              placement="top"
            >
              <article class="event-item">
                <div>
                  <strong>#{{ event.sequence }} {{ event.event_type_label }}</strong>
                  <el-tag size="small" effect="plain">{{ event.direction_label }}</el-tag>
                </div>
                <p>{{ eventSummary(event) }}</p>
                <code v-if="event.request_id">{{ event.request_id }}</code>
              </article>
            </el-timeline-item>
          </el-timeline>
        </section>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import {
  createIvrSession,
  getIvrDashboard,
  getIvrSession,
  sendIvrAudioChunk,
  sendIvrStateEvent,
  type IvrDashboard,
  type IvrEvent,
  type IvrEventDirection,
  type IvrEventType,
  type IvrInstruction,
  type IvrSession,
  type IvrSessionStatus,
  type IvrTransport,
} from '@/api/marketing/ivr'
import { datetimeFormat } from '@/utils/time'
import ChangeControlReportPanel from './ChangeControlReportPanel.vue'
import ChangeRiskPanel from './ChangeRiskPanel.vue'

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'

const emptyProtocol = {
  version: 'ivr-simulator-v1',
  mode: 'LOCAL_PROTOCOL_REPLAY' as const,
  external_integration_status: 'PENDING' as const,
  http: {},
  websocket: {
    status: 'CONTRACT_REPLAY' as const,
    future_endpoint: '/ws/workspace/{workspace_id}/marketing/ivr/{session_id}',
    note: '当前通过相同 JSON 消息契约进行回放；生产长连接待 IVR 网关联调。',
  },
  message_types: [],
  response_commands: ['PLAY_TEXT', 'TRANSFER_TO_AGENT', 'END_SESSION'] as Array<
    'PLAY_TEXT' | 'TRANSFER_TO_AGENT' | 'END_SESSION'
  >,
}

const dashboard = ref<IvrDashboard>({
  summary: { session_count: 0, active_session_count: 0, event_count: 0, websocket_replay_count: 0 },
  status_counts: {
    CREATED: 0,
    ACTIVE: 0,
    BROADCASTING: 0,
    TRANSFERRED: 0,
    ENDED: 0,
    FAILED: 0,
  },
  protocol: emptyProtocol,
  sessions: [],
})
const loading = ref(false)
const creating = ref(false)
const detailLoading = ref(false)
const sending = ref(false)
const eventSending = ref(false)
const drawerVisible = ref(false)
const selectedSession = ref<IvrSession | null>(null)
const latestInstruction = ref<IvrInstruction | null>(null)

const createForm = reactive({
  external_session_id: '',
  transport: 'WEBSOCKET_REPLAY' as IvrTransport,
  caller_number: '',
  caller_label: '',
  language: 'zh-CN',
})
const audioForm = reactive({
  transcript_hint: '',
  chunk_index: 0,
  duration_ms: 1800,
  is_final: true,
})

const statusMeta: Record<IvrSessionStatus, { type: TagType }> = {
  CREATED: { type: 'info' },
  ACTIVE: { type: 'success' },
  BROADCASTING: { type: 'primary' },
  TRANSFERRED: { type: 'warning' },
  ENDED: { type: 'info' },
  FAILED: { type: 'danger' },
}
const directionType: Record<IvrEventDirection, TagType> = {
  INBOUND: 'primary',
  OUTBOUND: 'success',
  SYSTEM: 'info',
}
const stateActions: Array<{ label: string; value: IvrEventType; type: TagType }> = [
  { label: '开始播报', value: 'BROADCAST_STARTED', type: 'primary' },
  { label: '播报结束', value: 'BROADCAST_ENDED', type: 'success' },
  { label: '转人工', value: 'TRANSFERRED', type: 'warning' },
  { label: '结束会话', value: 'SESSION_ENDED', type: 'info' },
  { label: '标记失败', value: 'FAILED', type: 'danger' },
]

const summaryCards = computed(() => [
  { label: '会话总数', value: dashboard.value.summary.session_count, hint: '数据库审计记录' },
  {
    label: '活动会话',
    value: dashboard.value.summary.active_session_count,
    hint: '活动中或正在播报',
  },
  { label: '链路事件', value: dashboard.value.summary.event_count, hint: '按序号完整留痕' },
  {
    label: 'WS 契约回放',
    value: dashboard.value.summary.websocket_replay_count,
    hint: '非生产长连接',
  },
])
const isTerminal = computed(() =>
  selectedSession.value ? ['ENDED', 'FAILED'].includes(selectedSession.value.status) : true,
)
const orderedEvents = computed(() =>
  [...(selectedSession.value?.events || [])].sort((left, right) => right.sequence - left.sequence),
)

const makeRequestId = (kind: string) =>
  `ui:${kind}:${Date.now()}:${Math.random().toString(36).slice(2, 9)}`
const formatTime = (value: string | null) => (value ? datetimeFormat(value) : '—')
const getStatusType = (status: string): TagType =>
  statusMeta[status as IvrSessionStatus]?.type || 'info'

const eventSummary = (event: IvrEvent) => {
  const payload = event.payload || {}
  if (event.event_type === 'STT_COMPLETED') return String(payload.text || '转写完成')
  if (event.event_type === 'RESPONSE_CREATED') {
    const instruction = payload.instruction as IvrInstruction | undefined
    return instruction ? `${instruction.command} · ${instruction.tts_text}` : '响应指令已生成'
  }
  if (event.event_type === 'AUDIO_CHUNK_RECEIVED') {
    return `分片 #${payload.chunk_index ?? 0} · ${payload.duration_ms ?? 0} ms`
  }
  return Object.keys(payload).length ? JSON.stringify(payload) : '状态事件已记录'
}

const loadDashboard = async () => {
  const result = await getIvrDashboard(loading)
  dashboard.value = result.data
}

const refreshSelected = async () => {
  if (!selectedSession.value) return
  const result = await getIvrSession(selectedSession.value.id, detailLoading)
  selectedSession.value = result.data
}

const openSession = async (id: string) => {
  drawerVisible.value = true
  latestInstruction.value = null
  const result = await getIvrSession(id, detailLoading)
  selectedSession.value = result.data
  audioForm.chunk_index =
    result.data.events?.filter((event) => event.event_type === 'AUDIO_CHUNK_RECEIVED').length || 0
}

const handleCreate = async () => {
  const result = await createIvrSession(
    {
      external_session_id: createForm.external_session_id.trim() || undefined,
      transport: createForm.transport,
      caller_number: createForm.caller_number.trim(),
      caller_label: createForm.caller_label.trim(),
      language: createForm.language,
    },
    creating,
  )
  ElMessage.success(result.data.created ? '演练会话已创建' : '相同外部编号的会话已存在')
  createForm.external_session_id = ''
  createForm.caller_number = ''
  await loadDashboard()
  await openSession(result.data.session.id)
}

const handleSendAudio = async () => {
  if (!selectedSession.value) return
  if (!audioForm.transcript_hint.trim()) {
    ElMessage.warning('请输入本次演练的转写文本')
    return
  }
  const result = await sendIvrAudioChunk(
    selectedSession.value.id,
    {
      request_id: makeRequestId('audio'),
      chunk_index: audioForm.chunk_index,
      duration_ms: audioForm.duration_ms,
      transcript_hint: audioForm.transcript_hint.trim(),
      is_final: audioForm.is_final,
    },
    sending,
  )
  latestInstruction.value = result.data.instruction
  audioForm.chunk_index += 1
  audioForm.transcript_hint = ''
  ElMessage.success(`已生成 ${result.data.instruction.command} 指令`)
  await Promise.all([refreshSelected(), loadDashboard()])
}

const handleStateEvent = async (eventType: IvrEventType) => {
  if (!selectedSession.value) return
  await sendIvrStateEvent(
    selectedSession.value.id,
    {
      request_id: makeRequestId(eventType.toLowerCase()),
      event_type: eventType,
      payload: { source: 'ADMIN_PROTOCOL_REPLAY' },
    },
    eventSending,
  )
  ElMessage.success('状态事件已写入链路')
  await Promise.all([refreshSelected(), loadDashboard()])
}

onMounted(loadDashboard)
</script>

<style scoped lang="scss">
.ivr-page {
  height: 100%;
  overflow-y: auto;
  background: #f5f7fb;
  color: #1f2937;
}

.hero-panel,
.hero-actions,
.card-heading,
.protocol-title,
.drawer-heading,
.state-actions,
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.hero-panel {
  min-height: 138px;
  padding: 28px 32px;
  border-radius: 18px;
  color: #fff;
  background:
    radial-gradient(circle at 84% 10%, rgb(110 231 183 / 26%), transparent 28%),
    linear-gradient(125deg, #172554, #164e63 72%, #115e59);
  box-shadow: 0 16px 40px rgb(15 23 42 / 14%);
}

.eyebrow {
  margin-bottom: 7px;
  color: #99f6e4;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
}

.hero-panel h2 {
  margin: 0 0 8px;
  font-size: 28px;
}

.hero-panel p {
  margin: 0;
  color: #dbeafe;
}

.boundary-alert {
  margin: 16px 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.summary-card {
  padding: 18px 20px;
  border: 1px solid #e5eaf3;
  border-radius: 14px;
  background: #fff;
}

.summary-card span,
.summary-card small,
.card-heading span,
.section-heading span,
.drawer-heading span,
.state-strip span {
  display: block;
  color: #8492a6;
}

.summary-card strong {
  display: block;
  margin: 7px 0 4px;
  color: #0f766e;
  font-size: 28px;
}

.main-grid {
  display: grid;
  grid-template-columns: minmax(360px, 0.8fr) minmax(460px, 1.2fr);
  gap: 16px;
  margin-bottom: 16px;
}

.card-heading > div:first-child strong,
.drawer-heading strong {
  display: block;
  margin-bottom: 4px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.full-width {
  width: 100%;
}

.protocol-block {
  padding: 14px 0;
  border-bottom: 1px solid #eef1f6;
}

.protocol-block code,
.event-item code {
  display: block;
  margin-top: 8px;
  padding: 7px 9px;
  border-radius: 6px;
  color: #155e75;
  background: #ecfeff;
  font-size: 12px;
  overflow-wrap: anywhere;
}

.protocol-block p {
  margin: 9px 0 0;
  color: #64748b;
  line-height: 1.6;
}

.command-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.command-list span {
  padding: 6px 10px;
  border-radius: 999px;
  color: #0f766e;
  background: #f0fdfa;
  font-size: 12px;
  font-weight: 600;
}

.cell-primary {
  color: #243047;
  font-weight: 600;
}

.cell-secondary {
  margin-top: 4px;
  color: #8a97aa;
  font-size: 12px;
}

.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-content {
  padding: 0 6px 24px;
}

.state-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.state-strip > div {
  padding: 12px;
  border-radius: 10px;
  background: #f6f8fb;
}

.state-strip strong {
  display: block;
  margin-top: 4px;
  font-size: 13px;
}

.simulation-card,
.instruction-card {
  margin-bottom: 14px;
}

.send-button {
  float: right;
}

.state-actions {
  justify-content: flex-start;
  flex-wrap: wrap;
  padding: 14px 0 20px;
}

.event-section {
  padding-top: 8px;
}

.section-heading {
  align-items: flex-start;
  margin-bottom: 22px;
}

.event-item {
  padding: 12px 14px;
  border: 1px solid #e7ecf3;
  border-radius: 10px;
  background: #fff;
}

.event-item > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-item p {
  margin: 8px 0 0;
  color: #526174;
  line-height: 1.55;
}

@media (max-width: 1100px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .main-grid {
    grid-template-columns: 1fr;
  }
}
</style>
