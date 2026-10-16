import { computed, ref } from 'vue'

import { fetchServiceItems } from '../api/client'
import { describeApiError } from '../data/answer-status'
import { itemIdFromCode } from '../data/service-codes'
import type { ServiceItem } from '../types/home'

/**
 * 支持事项的共享数据源。
 *
 * 首页、支持事项、最近记录三页都要这份数据（记录页用于把 last_intent 还原成事项名），
 * 因此做成模块级缓存 + 单次请求：任一页面先加载，其它页面直接复用，避免重复请求。
 */
const items = ref<ServiceItem[]>([])
const loading = ref(false)
const error = ref('')
let inflight: Promise<void> | null = null

export function useServiceItems() {
  const byId = computed<Record<string, ServiceItem>>(() =>
    Object.fromEntries(items.value.map((item) => [item.id, item])),
  )

  async function load(force = false): Promise<void> {
    if (inflight) return inflight
    if (items.value.length && !force) return
    loading.value = true
    error.value = ''
    inflight = fetchServiceItems()
      .then((data) => {
        items.value = data
      })
      .catch((cause) => {
        error.value = describeApiError(cause)
      })
      .finally(() => {
        loading.value = false
        inflight = null
      })
    return inflight
  }

  /** 事项编码（S01）→ 事项名；查不到时回退为原始编码 */
  function titleForCode(code: string | null | undefined): string | null {
    const id = itemIdFromCode(code)
    if (!id) return null
    return byId.value[id]?.title ?? code ?? null
  }

  /** 记录页标签用：事项名，无法解析时给出兜底文案 */
  function labelForCode(code: string | null | undefined, fallback = '未识别事项'): string {
    return titleForCode(code) ?? fallback
  }

  return { items, loading, error, load, byId, titleForCode, labelForCode }
}
