<template>
  <el-popover
    v-model:visible="visible"
    placement="bottom-end"
    :width="410"
    trigger="click"
    popper-class="marketing-notification-popover"
    @show="loadNotifications"
  >
    <template #reference>
      <el-badge :value="unreadCount" :hidden="!unreadCount" :max="99" class="notice-badge">
        <el-button link class="notice-trigger" aria-label="全局通知">
          <el-icon><Bell /></el-icon>
        </el-button>
      </el-badge>
    </template>

    <div class="notice-panel">
      <header>
        <div>
          <strong>全局通知</strong>
          <span>告警与报告 · {{ unreadCount ? `${unreadCount} 条未读` : '全部已读' }}</span>
        </div>
        <div class="notice-header-actions">
          <el-button
            link
            :icon="Refresh"
            :loading="refreshing"
            aria-label="刷新通知"
            @click="refreshAll"
          />
          <el-button v-if="unreadCount" link type="primary" @click="readAll">全部已读</el-button>
        </div>
      </header>

      <div class="notice-filters">
        <el-radio-group v-model="statusFilter" size="small" @change="loadNotifications">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="UNREAD">未读</el-radio-button>
        </el-radio-group>
        <el-select
          v-model="severityFilter"
          size="small"
          aria-label="告警级别"
          @change="loadNotifications"
        >
          <el-option label="全部级别" value="" />
          <el-option label="紧急" value="CRITICAL" />
          <el-option label="关注" value="WARNING" />
          <el-option label="提示" value="INFO" />
        </el-select>
      </div>

      <div v-loading="loading" class="notice-list">
        <button
          v-for="item in notifications"
          :key="item.id"
          type="button"
          class="notice-item"
          :class="{ unread: item.status === 'UNREAD' }"
          @click="openNotification(item)"
        >
          <i :class="`is-${item.severity.toLowerCase()}`" />
          <span class="notice-copy">
            <span class="notice-title-row">
              <strong>{{ item.title }}</strong>
              <el-tag size="small" effect="plain">{{ getActionLabel(item.action) }}</el-tag>
            </span>
            <small>{{ item.content }}</small>
            <time>{{ datetimeFormat(item.create_time) }}</time>
          </span>
          <b v-if="item.status === 'UNREAD'" aria-label="未读" />
        </button>
        <el-empty v-if="!loading && !notifications.length" :image-size="64" description="暂无全局通知" />
      </div>

      <footer>
        <el-button link type="primary" @click="openOperations">进入告警处理台</el-button>
      </footer>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Refresh } from '@element-plus/icons-vue'

import notificationApi, {
  type MarketingNotification,
  type MarketingNotificationAction,
  type MarketingNotificationSeverity,
  type MarketingNotificationStatus,
} from '@/api/marketing/notification'
import { datetimeFormat } from '@/utils/time'

const router = useRouter()
const visible = ref(false)
const loading = ref(false)
const refreshing = ref(false)
const unreadCount = ref(0)
const notifications = ref<MarketingNotification[]>([])
const statusFilter = ref<MarketingNotificationStatus | ''>('')
const severityFilter = ref<MarketingNotificationSeverity | ''>('')
let pollingTimer: ReturnType<typeof setInterval> | undefined

const actionLabels: Record<MarketingNotificationAction, string> = {
  CREATED: '新告警',
  REOPENED: '重新打开',
  RESPONSE_OVERDUE: '响应超时',
  RESOLUTION_OVERDUE: '处理超时',
  ASSIGNED: '指派',
  TRANSFERRED: '转派',
  COMMENTED: '评论',
  CLOSED: '关闭',
  SUBSCRIBED: '关注',
  UNSUBSCRIBED: '取消关注',
  ATTACHED: '附件',
  REPORT_GENERATED: '报告完成',
  REPORT_FAILED: '报告失败',
  PLATFORM_ALERT: '平台告警',
  METRIC_DISPATCH_ORDER: '指标派单',
}

function getActionLabel(action: MarketingNotificationAction) {
  return actionLabels[action]
}

function refreshUnreadCount() {
  return notificationApi.unreadCount().then((res) => {
    unreadCount.value = res.data.unread_count
  })
}

function loadNotifications() {
  return notificationApi.page(1, 30, statusFilter.value, severityFilter.value, loading).then((res) => {
    notifications.value = res.data.records
    unreadCount.value = res.data.unread_count
  })
}

function refreshAll() {
  refreshing.value = true
  Promise.all([refreshUnreadCount(), loadNotifications()]).finally(() => {
    refreshing.value = false
  })
}

function openNotification(item: MarketingNotification) {
  const navigate = () => {
    visible.value = false
    router.push(item.target_route || '/marketing-operations')
  }
  if (item.status === 'READ') {
    navigate()
    return
  }
  notificationApi.markRead(item.id).then(() => {
    item.status = 'READ'
    unreadCount.value = Math.max(unreadCount.value - 1, 0)
    if (statusFilter.value === 'UNREAD') {
      notifications.value = notifications.value.filter((row) => row.id !== item.id)
    }
    navigate()
  })
}

function readAll() {
  notificationApi.markAllRead().then(() => {
    notifications.value.forEach((item) => {
      item.status = 'READ'
    })
    if (statusFilter.value === 'UNREAD') notifications.value = []
    unreadCount.value = 0
  })
}

function openOperations() {
  visible.value = false
  router.push('/marketing-operations')
}

function handleNotificationUpdated() {
  refreshUnreadCount()
  if (visible.value) loadNotifications()
}

onMounted(() => {
  refreshUnreadCount()
  pollingTimer = setInterval(refreshUnreadCount, 60_000)
  window.addEventListener('marketing-notification-updated', handleNotificationUpdated)
})

onBeforeUnmount(() => {
  if (pollingTimer) clearInterval(pollingTimer)
  window.removeEventListener('marketing-notification-updated', handleNotificationUpdated)
})
</script>

<style scoped lang="scss">
.notice-trigger {
  width: 34px;
  height: 34px;
  color: var(--el-text-color-primary);
  font-size: 19px;
}

.notice-badge {
  margin-right: 5px;
}

.notice-panel header,
.notice-panel footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.notice-panel header {
  padding: 4px 4px 12px;
  border-bottom: 1px solid #e1e6ea;
}

.notice-panel header strong,
.notice-panel header span {
  display: block;
}

.notice-header-actions {
  display: flex;
  align-items: center;
}

.notice-filters {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 4px;
  border-bottom: 1px solid #edf0f2;
}

.notice-filters :deep(.el-select) {
  width: 112px;
}

.notice-panel header strong {
  font-family: 'STSong', 'Songti SC', serif;
  font-size: 17px;
}

.notice-panel header span {
  margin-top: 2px;
  color: #728092;
  font-size: 12px;
}

.notice-list {
  max-height: 430px;
  overflow-y: auto;
}

.notice-item {
  position: relative;
  display: grid;
  grid-template-columns: 8px minmax(0, 1fr) 7px;
  gap: 11px;
  align-items: start;
  width: 100%;
  padding: 14px 6px;
  border: none;
  border-bottom: 1px solid #edf0f2;
  color: #1d2935;
  text-align: left;
  background: transparent;
  cursor: pointer;
}

.notice-item:hover,
.notice-item.unread {
  background: #f4f8f9;
}

.notice-item > i {
  width: 7px;
  height: 7px;
  margin-top: 6px;
  border-radius: 50%;
  background: #7c8996;
}

.notice-item > i.is-warning {
  background: #c78916;
}

.notice-item > i.is-critical {
  background: #c0392b;
}

.notice-copy strong,
.notice-copy small,
.notice-copy time {
  display: block;
}

.notice-title-row {
  display: flex !important;
  align-items: center;
  gap: 8px;
}

.notice-title-row strong {
  min-width: 0;
  flex: 1;
}

.notice-copy strong {
  overflow: hidden;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice-copy small {
  display: -webkit-box;
  overflow: hidden;
  margin-top: 5px;
  color: #687587;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.notice-copy time {
  margin-top: 7px;
  color: #929da8;
  font-size: 11px;
}

.notice-item > b {
  width: 6px;
  height: 6px;
  margin-top: 7px;
  border-radius: 50%;
  background: #2c78a0;
}

.notice-panel footer {
  justify-content: center;
  padding-top: 10px;
}
</style>
