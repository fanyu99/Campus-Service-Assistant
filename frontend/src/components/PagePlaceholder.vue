<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const title = computed(() => (route.meta.title as string | undefined) ?? '页面')


function dismissNotice(id: string) {
  const el = document.querySelector<HTMLElement>(`[data-od-id="${id}"]`)
  const dot = el?.querySelector('.dot-badge')
  if (dot) dot.remove()
  el?.setAttribute('aria-label', '通知（无未读）')
  el?.setAttribute('data-tip', '通知（无未读）')
}
</script>

<template>
  <main class="main" data-od-id="page-main">
    <header class="topbar" data-od-id="global-header">
      <nav class="crumb" aria-label="页面标题"><strong>{{ title }}</strong></nav>
      <div class="top-actions">
        <button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="notification-button" @click="dismissNotice('notification-button')"><svg class="i" aria-hidden="true"><use href="#i-bell"/></svg><span class="dot-badge"></span></button>
        <span class="avatar" role="img" aria-label="当前用户：林同学" data-od-id="profile-chip-top">林</span>
      </div>
    </header>

    <section class="placeholder" data-od-id="page-placeholder">
      <p class="ph-tag">待实现</p>
      <h1 class="ph-title">{{ title }}</h1>
      <p class="ph-desc">页面结构已就位，内容留空，等待后续开发。</p>
      <slot />
    </section>
  </main>
</template>

<style scoped>
.placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;
  flex:1;min-height:0;padding:clamp(24px,5vh,64px) 24px;text-align:center}
.ph-tag{margin:0;padding:4px 12px;border-radius:100px;background:var(--accent-soft);color:var(--accent);font-size:12px;font-weight:500}
.ph-title{margin:4px 0 0;font-family:var(--font-display);font-weight:900;font-size:clamp(24px,3.4vw,36px);letter-spacing:-.02em}
.ph-desc{margin:0;max-width:34ch;color:var(--muted);font-size:13.5px;line-height:1.7}

@media (max-width:700px){
  .placeholder{min-height:52vh;padding:40px 4px}
}
</style>