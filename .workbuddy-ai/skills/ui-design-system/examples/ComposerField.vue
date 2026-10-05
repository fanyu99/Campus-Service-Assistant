<script setup lang="ts">
/**
 * 统一输入框外壳 `.composer-shell` 的三种用法，一个文件里跑通：
 *   ① 主 composer（自适应高度 + Enter 发送 / Shift+Enter 换行 + 校验失败态）
 *   ② 搜索框（带「清空」按钮）
 *   ③ 表单字段（设置页那种带标签的输入框）
 *
 * 视觉（渐变描边 / 动态网格 / 边框流光 / 光晕）全部来自全局 `.composer-shell`，
 * 这里的 scoped 样式**只写布局**，绝不重复 border / background / border-radius。
 *
 * 依赖：
 *   - src/styles/theme.css 里的 .composer-shell / .spark-button / .sr-only
 *   - components/AppSprite.vue 提供的 #i-search / #i-arrow-up
 */
import { computed, ref } from 'vue'

const MAX_H = 104

/* ── ① 主 composer ─────────────────────────────────────────────────── */
const question = ref('')
const status = ref('')
const isError = ref(false)
const isSending = ref(false)
const inputEl = ref<HTMLTextAreaElement | null>(null)

/** 还能输入多少字（maxlength=200 的可见计数器，可选） */
const remaining = computed(() => 200 - question.value.length)

function autoGrow() {
  const el = inputEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, MAX_H) + 'px'
}

function clearStatus() {
  status.value = ''
  isError.value = false
}

function onInput() {
  autoGrow()
  clearStatus()
}

function onKeydown(e: KeyboardEvent) {
  // isComposing：中文输入法选词回车不应触发提交
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    submit()
  }
}

const emit = defineEmits<{ (e: 'submit', text: string): void }>()

function submit() {
  const text = question.value.trim()
  if (!text) {
    status.value = '先写下你要咨询的事，再发送'
    isError.value = true
    inputEl.value?.focus()
    return
  }
  clearStatus()
  isSending.value = true
  emit('submit', text)
  window.setTimeout(() => {
    isSending.value = false
    question.value = ''
    autoGrow()
  }, 520)
}

/** 供父组件（如首页建议 chips）填充内容 */
function fill(text: string) {
  question.value = text
  clearStatus()
  autoGrow()
  requestAnimationFrame(() => {
    const el = inputEl.value
    if (!el) return
    el.focus()
    el.setSelectionRange(text.length, text.length)
  })
}

defineExpose({ fill })

/* ── ② 搜索框 ──────────────────────────────────────────────────────── */
const query = ref('')

/* ── ③ 表单字段 ────────────────────────────────────────────────────── */
const displayName = ref('林同学')
</script>

<template>
  <div class="composer-demo">
    <!-- ① 主 composer -->
    <form
      class="composer composer-shell"
      :class="{ 'is-invalid': isError }"
      novalidate
      @submit.prevent="submit"
    >
      <label class="sr-only" for="composerInput">输入你想咨询的校园事务</label>
      <textarea
        id="composerInput"
        ref="inputEl"
        v-model="question"
        rows="1"
        maxlength="200"
        autocomplete="off"
        placeholder="试试问：学生证丢了怎么补办？"
        @input="onInput"
        @keydown="onKeydown"
      ></textarea>
      <div class="composer-foot">
        <p class="composer-hint">Enter 发送 · Shift + Enter 换行 · 剩 {{ remaining }} 字</p>
        <button type="submit" class="send spark-button" :class="{ 'is-loading': isSending }" :disabled="isSending">
          <span v-if="isSending" class="sr-only">正在发送</span>
          <template v-else>
            <span>开始咨询</span><svg class="i" aria-hidden="true"><use href="#i-arrow-up" /></svg>
          </template>
        </button>
      </div>
    </form>
    <p class="composer-msg" :class="{ 'is-error': isError }" role="status" aria-live="polite">{{ status }}</p>

    <!-- ② 搜索框 -->
    <label class="search-field composer-shell">
      <svg class="i" aria-hidden="true"><use href="#i-search" /></svg>
      <span class="sr-only">搜索支持事项</span>
      <input v-model="query" type="search" placeholder="搜索事项名称或关键词" autocomplete="off" />
      <button v-if="query" type="button" class="clear-search" aria-label="清空" @click="query = ''">清空</button>
    </label>

    <!-- ③ 表单字段 -->
    <label class="field">
      <span>显示名称</span>
      <span class="composer-shell"><input v-model="displayName" type="text" autocomplete="name" /></span>
    </label>
  </div>
</template>

<style scoped>
.composer-demo { display: grid; gap: 16px; max-width: 660px; }

/* ── ① 主 composer：只写布局 ─────────────────────────────────────────── */
.composer { display: flex; flex-direction: column; gap: 9px; padding: 14px 14px 11px; }
.composer textarea,
.composer-foot { position: relative; z-index: 1; }
.composer textarea {
  width: 100%;
  min-height: 25px;
  max-height: 104px;
  padding: 0 4px;
  border: 0;
  background: transparent;
  color: var(--fg);
  font: 400 15px/1.6 var(--font-body);
  resize: none;
  overflow-y: auto;
  outline: 0;
}
.composer textarea::placeholder { color: var(--muted); }
.composer-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-left: 4px; }
.composer-hint {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* 键盘焦点环：:has() 保证只在真正的键盘聚焦时出现 */
.composer:has(:focus-visible) { outline: 2.5px solid var(--fg); outline-offset: 2px; }

.send {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  flex: 0 0 auto;
  height: 38px;
  padding: 0 16px;
}
.send:disabled { cursor: wait; opacity: .68; transform: none; }
.send.is-loading { gap: 0; min-width: 58px; padding-inline: 13px; }

.composer-msg { margin: 0; min-height: 19px; font-size: 12px; line-height: 1.6; color: var(--fg); text-align: center; }
.composer-msg.is-error { color: var(--danger); }

/* ── ② 搜索框 ────────────────────────────────────────────────────────── */
.search-field { display: flex; align-items: center; gap: 9px; min-height: 46px; padding: 0 12px; }
.search-field .i { width: 16px; height: 16px; color: var(--muted); }
.search-field input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--fg);
  font: 400 13px/1.5 var(--font-body);
}
.search-field input::placeholder { color: var(--muted); }
.clear-search { flex: 0 0 auto; color: var(--muted); font-size: 12px; white-space: nowrap; }
.clear-search:hover { color: var(--fg); }

/* ── ③ 表单字段 ──────────────────────────────────────────────────────── */
.field { display: grid; gap: 7px; color: var(--fg); font-size: 12px; font-weight: 550; }
.field .composer-shell { display: block; width: 100%; min-height: 44px; }
.field input {
  display: block;
  width: 100%;
  min-height: 42px;
  padding: 0 12px;
  border: 0;
  border-radius: inherit;      /* 跟随外壳圆角，避免内层再切一次角 */
  background: transparent;
  color: var(--fg);
  font: 400 13px/1.5 var(--font-body);
  outline: 0;
}

/* ── 移动端 ──────────────────────────────────────────────────────────── */
@media (max-width: 700px) {
  /* 圆角交给外壳的变量，不要在页面里重写 border-radius */
  .composer { --composer-shell-radius: 22px; padding: 13px 13px 11px; }
  .composer textarea { font-size: 16px; }   /* 低于 16px 会触发 iOS 自动缩放 */
  .send { height: 44px; padding: 0 18px; }
  .composer-hint { display: none; }
  .composer-foot { justify-content: flex-end; }
}
@media (max-height: 660px) and (min-width: 701px) {
  .composer { --composer-shell-radius: 20px; padding: 10px 12px 8px; }
  .composer-msg { min-height: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .send { transition: none; }
}
</style>
