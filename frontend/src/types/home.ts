export interface ServiceItem {
  id: string
  title: string
  description: string
  category: string
  icon: string
  tone: 'orange' | 'blue' | 'green' | 'purple'
  prompt: string
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
