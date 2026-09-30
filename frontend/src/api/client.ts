import type { ServiceItem } from '../types/home'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/+$/, '')
const REQUEST_TIMEOUT = 8000

export interface ChatMessageRequest {
  conversation_id: string | null
  message: string
  context?: { campus?: string | null; student_type?: string | null }
}

export interface Source {
  title: string
  department: string
  published_at: string
  url: string
}

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
  answer?: string | null
  sources?: Source[]
  clarifying_question?: string | null
}

export interface FeedbackRequest {
  conversation_id: string
  helpful: boolean
  reason_code?: string | null
  comment?: string | null
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
    const response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(init?.headers ?? {}),
      },
      signal: controller.signal,
    })
    if (!response.ok) {
      const payload = await response.json().catch(() => null)
      throw new ApiError(
        payload?.error?.message ?? `请求失败（${response.status}）`,
        response.status,
        payload?.error?.code,
      )
    }
    return (await response.json()) as T
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

export function fetchServiceItems(): Promise<ServiceItem[]> {
  return request<ServiceItem[]>('/service-items')
}

export function sendChatMessage(payload: ChatMessageRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/chat/messages', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function submitFeedback(payload: FeedbackRequest): Promise<{ status: string }> {
  return request<{ status: string }>('/feedback', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
