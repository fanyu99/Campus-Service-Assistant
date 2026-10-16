<script setup lang="ts">
/**
 * 非 answered 状态（追问 / 暂不支持 / 依据不足 / 资料冲突 / 服务异常）的统一提示块。
 * 只负责呈现与可选操作按钮，具体文案由调用方按状态给出。
 */
defineProps<{
  tone: 'info' | 'warn' | 'error'
  title: string
  description?: string
  actionLabel?: string
}>()

const emit = defineEmits<{ (e: 'action'): void }>()
</script>

<template>
  <section class="state-notice" :class="`is-${tone}`" data-od-id="state-notice">
    <p class="notice-title">{{ title }}</p>
    <p v-if="description" class="notice-desc">{{ description }}</p>
    <button
      v-if="actionLabel"
      type="button"
      class="notice-action spark-button"
      data-od-id="state-notice-action"
      @click="emit('action')"
    >{{ actionLabel }}</button>
  </section>
</template>

<style scoped>
.state-notice {
  display: grid;
  gap: 7px;
  padding: 13px 15px;
  border: 1px solid var(--border);
  border-radius: 4px 16px 16px 16px;
  background: var(--surface);
  color: var(--fg);
}

.state-notice.is-warn {
  border-color: color-mix(in srgb, var(--danger) 32%, var(--border));
  background: color-mix(in srgb, var(--danger) 7%, var(--surface));
}

.state-notice.is-error {
  border-color: color-mix(in srgb, var(--danger) 45%, var(--border));
  background: color-mix(in srgb, var(--danger) 10%, var(--surface));
}

.notice-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.7;
}

.notice-desc {
  margin: 0;
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.75;
}

.notice-action {
  justify-self: start;
  min-height: 32px;
  margin-top: 2px;
  padding: 0 14px;
  border: 1px solid var(--border);
  border-radius: var(--control-radius-pill);
  color: var(--fg);
  font-size: 12.5px;
}

.notice-action:hover {
  border-color: var(--fg);
}

@media (max-width: 700px) {
  .notice-action {
    min-height: var(--control-h);
  }
}
</style>
