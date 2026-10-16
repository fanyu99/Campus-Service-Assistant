import { describe, expect, it } from 'vitest'

import { ITEM_CODE_TO_ID, itemIdFromCode } from '../src/data/service-codes'

describe('ITEM_CODE_TO_ID（契约 §3.5 定稿映射表）', () => {
  it('覆盖 S01–S08 且与契约一致', () => {
    expect(ITEM_CODE_TO_ID).toEqual({
      S01: 'student-card',
      S02: 'campus-card',
      S03: 'repair',
      S04: 'leave',
      S05: 'scholarship',
      S06: 'grant',
      S07: 'major-transfer',
      S08: 'graduation',
    })
  })
})

describe('itemIdFromCode', () => {
  it('已知编码映射为 UI key', () => {
    expect(itemIdFromCode('S01')).toBe('student-card')
    expect(itemIdFromCode('S08')).toBe('graduation')
  })

  it('未知编码回退为小写，避免返回空值', () => {
    expect(itemIdFromCode('S09')).toBe('s09')
  })

  it('空值返回 null', () => {
    expect(itemIdFromCode(null)).toBeNull()
    expect(itemIdFromCode(undefined)).toBeNull()
    expect(itemIdFromCode('')).toBeNull()
  })
})
