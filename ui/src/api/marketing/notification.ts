import type { Ref } from 'vue'

import { get, post } from '@/request/index'
import type { Result } from '@/request/Result'
import useStore from '@/stores'

export type MarketingNotificationSeverity = 'INFO' | 'WARNING' | 'CRITICAL'
export type MarketingNotificationStatus = 'UNREAD' | 'READ'
export type MarketingNotificationAction =
  | 'CREATED'
  | 'REOPENED'
  | 'RESPONSE_OVERDUE'
  | 'RESOLUTION_OVERDUE'
  | 'ASSIGNED'
  | 'TRANSFERRED'
  | 'COMMENTED'
  | 'CLOSED'
  | 'SUBSCRIBED'
  | 'UNSUBSCRIBED'
  | 'ATTACHED'
  | 'REPORT_GENERATED'
  | 'REPORT_FAILED'
  | 'PLATFORM_ALERT'
  | 'METRIC_DISPATCH_ORDER'

export interface MarketingNotification {
  id: string
  alert_id?: string | null
  alert_type: string
  source_type: string
  source_id: string
  action: MarketingNotificationAction
  title: string
  content: string
  severity: MarketingNotificationSeverity
  status: MarketingNotificationStatus
  target_route: string
  read_at?: string | null
  create_time: string
}

export interface MarketingNotificationPage {
  total: number
  records: MarketingNotification[]
  current: number
  size: number
  unread_count: number
}

function prefix() {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/marketing/notification`
}

function page(
  currentPage = 1,
  pageSize = 20,
  status: MarketingNotificationStatus | '' = '',
  severity: MarketingNotificationSeverity | '' = '',
  loading?: Ref<boolean>,
): Promise<Result<MarketingNotificationPage>> {
  return get(`${prefix()}/${currentPage}/${pageSize}`, { status, severity }, loading)
}

function unreadCount(): Promise<Result<{ unread_count: number }>> {
  return get(`${prefix()}/unread-count`)
}

function markRead(id: string): Promise<Result<MarketingNotification>> {
  return post(`${prefix()}/${id}/read`, {})
}

function markAllRead(): Promise<Result<{ updated_count: number; unread_count: number }>> {
  return post(`${prefix()}/read-all`, {})
}

export default { page, unreadCount, markRead, markAllRead }
