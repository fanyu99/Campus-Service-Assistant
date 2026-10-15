import { beforeEach, describe, expect, it } from 'vitest'
import {
  DRAFT_STORAGE_KEY,
  SETTINGS_STORAGE_KEY,
  avatarInitial,
  clearLocalData,
  setProfile,
  useProfile,
} from '../src/composables/useProfile'

describe('useProfile', () => {
  beforeEach(() => {
    clearLocalData()
    localStorage.clear()
  })

  it('写入资料时会与已存的 theme 字段合并，不互相覆盖', () => {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify({ theme: '深色' }))
    setProfile({ displayName: '王小明' })

    const saved = JSON.parse(localStorage.getItem(SETTINGS_STORAGE_KEY) as string)
    expect(saved.displayName).toBe('王小明')
    expect(saved.theme).toBe('深色')
    expect(useProfile().profile.value.displayName).toBe('王小明')
  })

  it('clearLocalData 同时清掉设置与首页草稿，并回到默认资料', () => {
    setProfile({ displayName: '王小明' })
    localStorage.setItem(DRAFT_STORAGE_KEY, '学生证丢了怎么补办？')

    clearLocalData()

    expect(localStorage.getItem(SETTINGS_STORAGE_KEY)).toBeNull()
    expect(localStorage.getItem(DRAFT_STORAGE_KEY)).toBeNull()
    expect(useProfile().profile.value.displayName).toBe('林同学')
  })
})

describe('avatarInitial', () => {
  it('取显示名首字，空白输入回退到默认字', () => {
    expect(avatarInitial('林同学')).toBe('林')
    expect(avatarInitial('   ')).toBe('林')
  })
})
