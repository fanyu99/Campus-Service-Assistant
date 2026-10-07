import { ref } from 'vue'

/**
 * 个人资料的单一数据源。
 *
 * 背景（2026-10-07 修正）：设置页原本把资料写进
 * `localStorage['campus-service-assistant-settings']`（字段 displayName/school/campus），
 * 而首页 `readProfileName()` 却去读 `campus-assistant.user` / `campus-assistant.profile` /
 * `userProfile` / `currentUser` 四个键、再取 name/realName/username —— 键名与字段全不匹配，
 * 于是「设置页改显示名称」在首页、侧栏永远不生效。这里把键与字段收敛到一处，三处共用。
 *
 * 与 useTheme.ts 共用同一个存储键：写入必须与已存对象 merge，
 * 否则会把 theme 冲掉（反之亦然）。
 */

export interface UserProfile {
  displayName: string
  school: string
  campus: string
}

/** 必须与 useTheme.ts 的 STORAGE_KEY 保持一致 */
export const SETTINGS_STORAGE_KEY = 'campus-service-assistant-settings'
/** 首页输入框草稿 */
export const DRAFT_STORAGE_KEY = 'campus-assistant.draft'

/** 演示默认值：保持与原界面一致的开箱观感 */
const DEFAULTS: UserProfile = {
  displayName: '林同学',
  school: '华中科技大学',
  campus: '主校区',
}

function readStored(): Record<string, unknown> {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : null
    return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : {}
  } catch {
    return {}
  }
}

function str(value: unknown, fallback: string): string {
  return typeof value === 'string' && value.trim() ? value.trim() : fallback
}

function readProfile(): UserProfile {
  const saved = readStored()
  return {
    displayName: str(saved.displayName, DEFAULTS.displayName),
    school: str(saved.school, DEFAULTS.school),
    campus: str(saved.campus, DEFAULTS.campus),
  }
}

const profile = ref<UserProfile>(readProfile())

/** 更新资料并持久化（与已存对象 merge，保留 theme 等其它字段） */
export function setProfile(patch: Partial<UserProfile>): void {
  profile.value = { ...profile.value, ...patch }
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify({ ...readStored(), ...profile.value }))
  } catch {
    /* 隐私模式 / 配额满：存不进去也不影响本次会话内的显示 */
  }
}

/**
 * 清空本机保存的数据：设置（含主题）与首页草稿。
 * 注意这里不写回存储，否则等于「清完又立刻建回来」。
 */
export function clearLocalData(): void {
  try {
    localStorage.removeItem(SETTINGS_STORAGE_KEY)
    localStorage.removeItem(DRAFT_STORAGE_KEY)
  } catch {
    /* 忽略 */
  }
  profile.value = { ...DEFAULTS }
}

/** 头像文字：取显示名首字 */
export function avatarInitial(name: string): string {
  const trimmed = name.trim()
  return trimmed ? Array.from(trimmed)[0] : '林'
}

export function useProfile() {
  return { profile, setProfile, clearLocalData }
}
