/**
 * 事务图标映射（首页服务行 + 支持事项列表共用）。
 *
 * 之前 HomeView 与 ServicesView 各维护一份，Services 那份多出
 * scholarship / network，容易漂移；收敛到这里统一维护。
 * 六页接线后页面数据来自后端，但图标仍以本表为准（后端 icon 字段为选返，
 * 其缺省值与本表保持一致，见 backend/app/services/service_items.py）。
 */
export const SERVICE_ICON: Record<string, string> = {
  'student-card': 'i-id',
  'campus-card': 'i-card',
  repair: 'i-wrench',
  leave: 'i-calendar',
  scholarship: 'i-award',
  network: 'i-wifi',
}

/** 未在映射表中的事项回退图标 */
export const FALLBACK_SERVICE_ICON = 'i-doc'
