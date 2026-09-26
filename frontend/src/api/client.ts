import type { ServiceItem } from '../types/home'

export interface ChatMessageRequest {
  conversation_id: string | null
  message: string
  context?: { campus?: string | null; student_type?: string | null }
}

export async function fetchServiceItems(): Promise<ServiceItem[]> {
  // TODO: 接入 GET /api/service-items
  return []
}

export async function sendChatMessage(payload: ChatMessageRequest) {
  // TODO: 接入 POST /api/chat/messages
  return { conversation_id: payload.conversation_id ?? 'demo-local', status: 'mock' as const }
}
