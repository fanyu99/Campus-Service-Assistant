import type { RecentConversation, ServiceItem, TodoItem } from '../types/home'

export const serviceItems: ServiceItem[] = [
  { id: 'student-card', title: '学生证补办', description: '材料、流程与办理地点', category: '证件', icon: '▣', tone: 'orange', prompt: '学生证丢了怎么补办？' },
  { id: 'campus-card', title: '校园卡补办', description: '挂失、补办与余额处理', category: '校园卡', icon: '⌁', tone: 'blue', prompt: '校园卡丢失后应该怎么处理？' },
  { id: 'repair', title: '宿舍报修', description: '提交前先确认问题类型', category: '生活', icon: '⌂', tone: 'green', prompt: '宿舍水龙头坏了，应该在哪里报修？' },
  { id: 'leave', title: '请假办理', description: '了解条件与所需证明', category: '学业', icon: '◷', tone: 'purple', prompt: '因病请假需要准备哪些材料？' },
]

export const todoItems: TodoItem[] = [
  { id: 'todo-1', title: '确认校园卡补办地点', detail: '你上次咨询后还没有查看来源', status: '待确认' },
  { id: 'todo-2', title: '奖学金申请材料准备', detail: '距离材料提交截止还有 6 天', status: '即将截止' },
]

export const recentConversations: RecentConversation[] = [
  { id: 'recent-1', question: '学生证丢了怎么补办？', time: '今天 09:42', tag: '学生证补办' },
  { id: 'recent-2', question: '校园卡挂失后余额怎么办？', time: '昨天 18:16', tag: '校园卡补办' },
  { id: 'recent-3', question: '宿舍报修需要填写什么？', time: '周一 14:05', tag: '宿舍报修' },
]
