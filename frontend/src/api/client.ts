import type { ServiceItem } from '../types/home'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/+$/, '')
const REQUEST_TIMEOUT = 8000

/** 问答上下文（可选，用于缩小检索范围） */
export interface ChatContext {
  campus?: string | null
  student_type?: string | null
}

export interface ChatMessageRequest {
  conversation_id: string | null
  message: string
  context?: ChatContext
}

/** 知识状态（对应实施方案 7.2 status 字段） */
export type SourceStatus = 'draft' | 'verified' | 'expired' | 'conflict'

/** 来源（对应实施方案 8.1 sources / 7.2 来源元数据） */
export interface Source {
  title: string
  department: string
  published_at: string
  url: string
  /** 事项编码，如 S01 */
  item_code?: string | null
  /** 知识状态：verified 为正式依据，expired / conflict 需风险提示 */
  status?: SourceStatus | null
}

/**
 * 结构化办事卡片（对应实施方案 8.1 的 answer 对象）。
 * 原实现把 answer 定义成 `string | null`，与计划不一致 —— 计划要求的是
 * 含条件/材料/步骤/地点/时间/来源的结构化对象。
 */
export interface AnswerCard {
  title: string
  summary: string
  eligibility: string[]
  materials: string[]
  steps: string[]
  location: string | null
  deadline: string | null
  contacts: string[]
  warnings: string[]
}

/** 回答状态（对应实施方案 8.2） */
export type AnswerStatus =
  | 'answered'
  | 'need_clarification'
  | 'unsupported'
  | 'insufficient_evidence'
  | 'conflict'
  | 'service_error'

export interface ChatResponse {
  conversation_id: string
  status: AnswerStatus
  /** 识别到的事项编码；未识别时为 null */
  intent: string | null
  /** 仅 status === 'answered' 时为结构化卡片，其余状态为 null */
  answer: AnswerCard | null
  sources: Source[]
  /** 是否需要追问（语义等价于 status === 'need_clarification'） */
  need_clarification: boolean
  clarifying_question: string | null
}

/** 反馈原因码（对应实施方案 9.4 reason_code） */
export type FeedbackReasonCode = 'SOURCE_ERROR' | 'INCOMPLETE_STEPS' | 'OUTDATED_CONTENT' | 'OTHER'

export interface FeedbackRequest {
  conversation_id: string
  helpful: boolean
  /** helpful === false 时建议提供 */
  reason_code?: FeedbackReasonCode | null
  /** 可选短评，≤ 200 字 */
  comment?: string | null
}

/** 会话摘要（最近记录页，对应实施方案 9.3 conversations 表） */
export interface ConversationSummary {
  id: string
  question: string
  last_intent: string | null
  result_status: AnswerStatus
  started_at: string
  last_message_at: string
}

export interface ConversationListResponse {
  conversations: ConversationSummary[]
  total: number
}

export interface HealthResponse {
  status: string
}

export class ApiError extends Error {
  status: number
  code?: string

  constructor(message: string, status: number, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT)
  try {
    // 用 Headers 合并：直接展开 init.headers 时，若调用方传的是 Headers 实例会丢字段
    const headers = new Headers(init?.headers)
    if (!headers.has('Accept')) headers.set('Accept', 'application/json')
    if (init?.body != null && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')

    const response = await fetch(`${API_BASE}${path}`, { ...init, headers, signal: controller.signal })

    if (!response.ok) {
      const payload = await response.json().catch(() => null)
      throw new ApiError(
        payload?.error?.message ?? `请求失败（${response.status}）`,
        response.status,
        payload?.error?.code,
      )
    }

    // 204 或空响应体不强行 JSON.parse，避免把「无内容」误判成网络异常
    if (response.status === 204) return undefined as T
    const text = await response.text()
    if (!text) return undefined as T
    try {
      return JSON.parse(text) as T
    } catch {
      throw new ApiError('响应格式异常', response.status, 'INVALID_RESPONSE')
    }
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('请求超时，请重试', 408, 'TIMEOUT')
    }
    throw new ApiError('网络异常，请检查连接后重试', 0, 'NETWORK_ERROR')
  } finally {
    clearTimeout(timer)
  }
}

/** 健康检查：GET /api/health（联调探测） */
export function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

/** 查询支持事项：GET /api/service-items */
export function fetchServiceItems(): Promise<ServiceItem[]> {
  return request<ServiceItem[]>('/service-items')
}

/** 发起问答：POST /api/chat/messages */
export function sendChatMessage(payload: ChatMessageRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/chat/messages', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/** 提交反馈：POST /api/feedback */
export function submitFeedback(payload: FeedbackRequest): Promise<{ status: string }> {
  return request<{ status: string }>('/feedback', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/** 查询最近会话：GET /api/conversations */
export function fetchConversations(limit = 10): Promise<ConversationListResponse> {
  return request<ConversationListResponse>(`/conversations?limit=${encodeURIComponent(limit)}`)
}

/**
 * 来源链接安全校验：仅允许 http / https。
 * 后端返回的 url 不可直接信任，渲染成 <a href> 前必须过滤，
 * 避免 javascript: / data: 等伪协议被点击执行（OWASP A08）。
 */
export function isSafeSourceUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}
