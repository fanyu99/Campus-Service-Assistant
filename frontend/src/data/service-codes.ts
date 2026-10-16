/**
 * 事项编码 ↔ 前端 UI key 的映射（契约 §3.5 定稿表）。
 *
 * 后端 `intent` / `last_intent` / `sources[].item_code` 一律用 S01–S08，
 * 而 `ServiceItem.id` 是 kebab-case 的 UI key；记录页要把 `last_intent`
 * 还原成事项名，就需要这张表。改动必须同步 `docs/api.md` §3.5。
 */
export const ITEM_CODE_TO_ID: Record<string, string> = {
  S01: 'student-card',
  S02: 'campus-card',
  S03: 'repair',
  S04: 'leave',
  S05: 'scholarship',
  S06: 'grant',
  S07: 'major-transfer',
  S08: 'graduation',
}

/** 未命中映射表时返回原始编码，避免展示空白 */
export function itemIdFromCode(code: string | null | undefined): string | null {
  if (!code) return null
  return ITEM_CODE_TO_ID[code] ?? code.toLowerCase()
}
