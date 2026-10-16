import { beforeEach, describe, expect, it } from 'vitest'
import { ApiError, getSessionToken, isSafeSourceUrl } from '../src/api/client'

const SESSION_TOKEN_KEY = 'campus-service-assistant-session-token'

describe('getSessionToken', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('首次访问生成 UUID 形态的匿名标识并持久化', () => {
    const token = getSessionToken()
    expect(token).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
    expect(localStorage.getItem(SESSION_TOKEN_KEY)).toBe(token)
  })

  it('重复调用复用同一标识', () => {
    const first = getSessionToken()
    expect(getSessionToken()).toBe(first)
  })

  it('沿用已存在的标识', () => {
    localStorage.setItem(SESSION_TOKEN_KEY, 'existing-token')
    expect(getSessionToken()).toBe('existing-token')
  })
})

describe('isSafeSourceUrl', () => {
  it('允许 http / https 链接', () => {
    expect(isSafeSourceUrl('https://example.edu.cn/notice/001')).toBe(true)
    expect(isSafeSourceUrl('http://example.edu.cn/notice/001')).toBe(true)
  })

  it('拒绝伪协议与非绝对地址（OWASP A08）', () => {
    expect(isSafeSourceUrl('javascript:alert(1)')).toBe(false)
    expect(isSafeSourceUrl('data:text/html,<script>1</script>')).toBe(false)
    expect(isSafeSourceUrl('/notice/001')).toBe(false)
    expect(isSafeSourceUrl('')).toBe(false)
  })
})

describe('ApiError', () => {
  it('保留 HTTP 状态码与业务错误码', () => {
    const error = new ApiError('请求超时，请重试', 408, 'TIMEOUT')
    expect(error).toBeInstanceOf(Error)
    expect(error.name).toBe('ApiError')
    expect(error.status).toBe(408)
    expect(error.code).toBe('TIMEOUT')
  })
})
