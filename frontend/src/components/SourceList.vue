<script setup lang="ts">
import { isSafeSourceUrl } from '../api/client'
import type { Source } from '../api/client'

/**
 * 来源列表（契约 §3.2）。
 * 链接渲染前必须经 `isSafeSourceUrl()` 过滤协议——后端返回值不可直接信任（OWASP A08）；
 * 协议不合法的来源降级为纯文本展示，不丢信息也不给出可点击的危险链接。
 */
defineProps<{ sources: Source[]; heading?: string }>()

const STATUS_LABEL: Record<string, string> = {
  verified: '已核验',
  expired: '已过期',
  draft: '未核验',
  conflict: '存在冲突',
}

function statusLabel(status?: string | null): string {
  if (!status) return ''
  return STATUS_LABEL[status] ?? status
}
</script>

<template>
  <section v-if="sources.length" class="source-block" data-od-id="source-list">
    <h4>{{ heading ?? '来源' }}</h4>
    <ul>
      <li v-for="(source, index) in sources" :key="`${source.title}-${index}`">
        <div class="source-line">
          <a
            v-if="isSafeSourceUrl(source.url)"
            class="source-title"
            :href="source.url"
            target="_blank"
            rel="noopener noreferrer"
          >{{ source.title }}</a>
          <span v-else class="source-title is-plain">{{ source.title }}</span>
          <span v-if="statusLabel(source.status)" class="source-status" :class="`is-${source.status}`">
            {{ statusLabel(source.status) }}
          </span>
        </div>
        <p class="source-meta">
          {{ source.department }}<template v-if="source.published_at"> · {{ source.published_at }}</template>
        </p>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.source-block {
  display: grid;
  gap: 9px;
  margin-top: 12px;
}

.source-block h4 {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
}

.source-block ul {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.source-block li {
  display: grid;
  gap: 3px;
  padding-left: 11px;
  border-left: 2px solid var(--border);
}

.source-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.source-title {
  color: var(--fg);
  font-size: 13px;
  line-height: 1.6;
  text-decoration: underline;
  text-decoration-color: color-mix(in srgb, var(--muted) 55%, transparent);
  text-underline-offset: 3px;
}

.source-title:hover {
  color: var(--accent);
  text-decoration-color: currentColor;
}

.source-title.is-plain {
  color: var(--muted);
  text-decoration: none;
}

.source-status {
  flex: 0 0 auto;
  padding: 1px 7px;
  border: 1px solid var(--border);
  border-radius: var(--control-radius-pill);
  color: var(--muted);
  font-size: 11px;
  white-space: nowrap;
}

.source-status.is-verified {
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
  color: var(--accent);
}

.source-status.is-expired,
.source-status.is-conflict {
  border-color: color-mix(in srgb, var(--danger) 45%, var(--border));
  color: var(--danger);
}

.source-meta {
  margin: 0;
  color: var(--muted);
  font-size: 11.5px;
}

@media (max-width: 700px) {
  .source-title {
    font-size: 13.5px;
  }
}
</style>
