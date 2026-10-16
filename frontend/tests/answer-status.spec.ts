import { describe, expect, it } from 'vitest'

import { ApiError } from '../src/api/client'
import type { AnswerStatus, ConversationSummary } from '../src/api/client'
import {
  ANSWER_STATUS_LABEL,
  conversationDetail,
  conversationStatusLabel,
  describeApiError,
  formatDateTime,
  toHistoryRecord,
} from '../src/data/answer-status'

describe('conversationStatusLabel（契约 §3.4 定稿规则）', () => {
  it('need_clarification → 待继续，其余 → 已完成', () => {
    expect(conversationStatusLabel('need_clarification')).toBe('待继续')
    for (const status of [
      'answered',
      'unsupported',
      'insufficient_evidence',
      'conflict',
      'service_error',
      'smalltalk',
    ] as AnswerStatus[]) {
      expect(conversationStatusLabel(status)).toBe('已完成')
    }
  })
})

describe('状态文案', () => {
  it('各态都有文案与说明（含 v1.3 新增 smalltalk）', () => {
    const statuses: AnswerStatus[] = [
      'answered',
      'need_clarification',
      'unsupported',
      'insufficient_evidence',
      'conflict',
      'service_error',
      'smalltalk',
    ]
    for (const status of statuses) {
      expect(ANSWER_STATUS_LABEL[status]).toBeTruthy()
      expect(conversationDetail(status)).toBeTruthy()
    }
    expect(ANSWER_STATUS_LABEL.smalltalk).toBe('对话')
  })
})

describe('describeApiError', () => {
  it('按错误码给出面向用户的提示', () => {
    expect(describeApiError(new ApiError('x', 408, 'TIMEOUT'))).toContain('超时')
    expect(describeApiError(new ApiError('x', 0, 'NETWORK_ERROR'))).toContain('网络')
    expect(describeApiError(new ApiError('x', 429, 'RATE_LIMITED'))).toContain('稍等')
    expect(describeApiError(new ApiError('x', 503, 'UPSTREAM_TIMEOUT'))).toContain('超时')
    expect(describeApiError(new ApiError('x', 503, 'UPSTREAM_ERROR'))).toContain('暂时不可用')
    expect(describeApiError(new ApiError('x', 400, 'MESSAGE_TOO_LONG'))).toContain('200')
  })

  it('INVALID_REQUEST 直接透出后端的用户安全文案', () => {
    expect(describeApiError(new ApiError('请勿填写身份证号', 400, 'INVALID_REQUEST'))).toBe(
      '请勿填写身份证号',
    )
  })

  it('未知错误给出兜底文案，不泄露内部细节', () => {
    expect(describeApiError(new Error('stack trace here'))).toBe('出了点问题，请稍后重试。')
  })
})

describe('formatDateTime', () => {
  it('非法时间原样返回', () => {
    expect(formatDateTime('not-a-date')).toBe('not-a-date')
  })

  it('当天只显示时分，跨天带上月日', () => {
    const today = new Date()
    today.setHours(9, 5, 0, 0)
    expect(formatDateTime(today.toISOString())).not.toContain('/')

    const past = new Date(today.getTime() - 3 * 24 * 3600 * 1000)
    expect(formatDateTime(past.toISOString()).length).toBeGreaterThan(
      formatDateTime(today.toISOString()).length,
    )
  })
})

describe('toHistoryRecord', () => {
  it('把会话摘要映射为记录页模型', () => {
    const summary: ConversationSummary = {
      id: 'c-1',
      question: '学生证丢了怎么补办？',
      last_intent: 'S01',
      result_status: 'need_clarification',
      started_at: '2026-10-16T09:00:00+08:00',
      last_message_at: '2026-10-16T09:05:00+08:00',
    }
    const record = toHistoryRecord(summary)
    expect(record.id).toBe('c-1')
    expect(record.question).toBe('学生证丢了怎么补办？')
    expect(record.status).toBe('待继续')
    expect(record.itemCode).toBe('S01')
    expect(record.detail).toContain('补充')
  })
})
