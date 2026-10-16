import { get, post } from '@/request/index'
import useStore from '@/stores'
import type { Ref } from 'vue'

export interface ServiceAnswerReview {
  id: string
  record_id: string
  chat_id: string
  application_id: string
  application_name?: string
  conversation_title?: string
  user_question?: string
  status: 'PENDING' | 'CONFIRMED' | 'DISMISSED'
  risk_types: string[]
  risk_details?: Array<{
    code: string
    label: string
    description: string
    review_guidance: string
  }>
  delivery_action: string
  reference_count: number
  rule_version: string
  revision: number
  delivered_answer: string
  create_time: string
  update_time: string
}

export interface ServiceAnswerReviewPage {
  total: number
  records: ServiceAnswerReview[]
}

function prefix() {
  const { user } = useStore()
  return `/workspace/${user.getWorkspaceId()}/service-answer-review`
}

export function getServiceAnswerReviews(page: number, size: number, status: string, loading: Ref<boolean>) {
  return get(`${prefix()}/${page}/${size}`, { status }, loading) as Promise<{ data: ServiceAnswerReviewPage }>
}

export function handleServiceAnswerReview(
  id: string,
  action: 'CONFIRMED' | 'DISMISSED',
  note: string,
  loading: Ref<boolean>,
) {
  return post(`${prefix()}/${id}/handle`, { action, note }, undefined, loading)
}
