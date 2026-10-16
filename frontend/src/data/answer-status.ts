import { ApiError } from '../api/client'
import type { AnswerStatus, ConversationSummary } from '../api/client'

/**
 * 问答结果的展示口径（文案、状态推导、时间与错误提示）。
 *
 * 集中在这里而不是散在各页面：六态文案、会话「待继续/已完成」推导规则（契约 §3.4）
 * 与接口错误提示都只应有一份定义。
 */

/** 契约 §3.3 状态文案（用于记录页标签、调试展示；smalltalk 为 v1.3 新增） */
export const ANSWER_STATUS_LABEL: Record<AnswerStatus, string> = {
  answered: '已回答',
  need_clarification: '待继续',
  unsupported: '暂不支持',
  insufficient_evidence: '依据不足',
  conflict: '资料冲突',
  service_error: '服务异常',
  smalltalk: '对话',
}

/** 契约 §3.4 定稿：need_clarification → 待继续；其余 → 已完成 */
export function conversationStatusLabel(resultStatus: AnswerStatus): '待继续' | '已完成' {
  return resultStatus === 'need_clarification' ? '待继续' : '已完成'
}

/** 记录页的一句话说明（按回答状态给出人话解释） */
export function conversationDetail(resultStatus: AnswerStatus): string {
  switch (resultStatus) {
    case 'answered':
      return '已给出办理条件、材料与入口'
    case 'need_clarification':
      return '上一轮在等你补充关键信息'
    case 'unsupported':
      return '暂未收录该事项'
    case 'insufficient_evidence':
      return '没有找到可靠的办理依据'
    case 'conflict':
      return '资料来源存在冲突，需向责任部门确认'
    case 'service_error':
      return '智能问答服务异常，可重试'
    case 'smalltalk':
      return '日常对话，未涉及具体事项'
  }
}

/** ISO 8601 → 展示用时间（当天只显示时分，跨天带上月日） */
export function formatDateTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  const time = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) return time
  const day = new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric' }).format(date)
  return `${day} ${time}`
}

/** 会话摘要 → 记录页展示模型 */
export function toHistoryRecord(summary: ConversationSummary) {
  const status = conversationStatusLabel(summary.result_status)
  return {
    id: summary.id,
    question: summary.question,
    time: formatDateTime(summary.last_message_at),
    status,
    detail: conversationDetail(summary.result_status),
    itemCode: summary.last_intent,
  }
}

/**
 * 接口/网络错误 → 面向用户的提示。
 * 文案只讲「用户能做什么」，不回传后端 message 之外的内部细节（契约 §2.1）。
 */
export function describeApiError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.code) {
      case 'TIMEOUT':
        return '回答超时了，请重试一次。'
      case 'NETWORK_ERROR':
        return '网络连接不上，请检查网络后重试。'
      case 'RATE_LIMITED':
        return '问得有点快，稍等一会儿再试。'
      case 'MESSAGE_TOO_LONG':
        return '问题太长了，请精简到 200 字以内。'
      case 'CONVERSATION_NOT_FOUND':
        return '这次会话已失效，已为你开启新会话。'
      case 'UPSTREAM_TIMEOUT':
        return '智能问答服务响应超时，请稍后重试。'
      case 'UPSTREAM_ERROR':
        return '智能问答服务暂时不可用，请稍后重试。'
      case 'INVALID_RESPONSE':
        return '服务返回异常，请稍后重试。'
      case 'INVALID_REQUEST':
        return error.message
      default:
        return error.message || '请求失败，请稍后重试。'
    }
  }
  return '出了点问题，请稍后重试。'
}
