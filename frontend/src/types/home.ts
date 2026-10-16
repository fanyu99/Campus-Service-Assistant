export interface ServiceItem {
  id: string
  title: string
  description: string
  category: string
  /** 契约 §3.1 的「选返」字段：后端可能返回 null，渲染前需本地兜底 */
  icon?: string | null
  tone?: 'orange' | 'blue' | 'green' | 'purple' | null
  prompt?: string | null
}

export interface TodoItem {
  id: string
  title: string
  detail: string
  status: '待确认' | '即将截止' | '已完成'
}

export interface RecentConversation {
  id: string
  question: string
  time: string
  tag: string
}
