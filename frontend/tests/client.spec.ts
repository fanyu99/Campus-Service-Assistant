import { describe, expect, it } from 'vitest'
import { ApiError, isSafeSourceUrl } from '../src/api/client'

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
