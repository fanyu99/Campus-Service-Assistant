<script setup lang="ts" generic="T extends string">
import { nextTick, onBeforeUnmount, ref, useId, watch } from 'vue'

/**
 * 自绘下拉选择器。
 *
 * 为什么不用原生 <select>：下拉弹层由浏览器绘制，弹层里「当前选中项」的高亮色
 * 完全无法用 CSS 定制（`option:checked` / `option:hover` / `accent-color` 实测均被忽略），
 * 深色主题下会出现「浅色文字压在浅蓝高亮上」的低对比度问题（实测仅 2.96:1）。
 * 所以这里自绘，配色统一走主题变量。
 *
 * 触发器外面套全局 `.composer-shell`，与设置页的输入框视觉完全一致。
 */
const props = defineProps<{
  modelValue: T
  options: readonly T[]
  /** 无障碍名称，同时用于 listbox 的 aria-label */
  label: string
}>()

const emit = defineEmits<{ (e: 'update:modelValue', value: T): void }>()

const uid = useId()
const listId = `select-list-${uid}`
const optionId = (index: number) => `select-option-${uid}-${index}`

const rootEl = ref<HTMLElement | null>(null)
const triggerEl = ref<HTMLButtonElement | null>(null)
const listEl = ref<HTMLElement | null>(null)
const open = ref(false)
const activeIndex = ref(0)

function openList() {
  const current = props.options.indexOf(props.modelValue)
  activeIndex.value = current < 0 ? 0 : current
  open.value = true
}

function closeList(returnFocus = false) {
  if (!open.value) return
  open.value = false
  if (returnFocus) triggerEl.value?.focus()
}

function toggle() {
  open.value ? closeList() : openList()
}

function choose(option: T) {
  emit('update:modelValue', option)
  closeList(true)
}

function moveActive(step: number) {
  const count = props.options.length
  if (!count) return
  activeIndex.value = (activeIndex.value + step + count) % count
}

function onTriggerKeydown(event: KeyboardEvent) {
  const key = event.key
  if (!open.value) {
    if (key === 'ArrowDown' || key === 'ArrowUp' || key === 'Enter' || key === ' ') {
      event.preventDefault()
      openList()
    }
    return
  }

  switch (key) {
    case 'ArrowDown':
      event.preventDefault()
      moveActive(1)
      break
    case 'ArrowUp':
      event.preventDefault()
      moveActive(-1)
      break
    case 'Home':
      event.preventDefault()
      activeIndex.value = 0
      break
    case 'End':
      event.preventDefault()
      activeIndex.value = props.options.length - 1
      break
    case 'Enter':
    case ' ':
      event.preventDefault()
      choose(props.options[activeIndex.value])
      break
    case 'Escape':
      event.preventDefault()
      closeList()
      break
    case 'Tab':
      closeList()
      break
  }
}

/** 点面板外部关闭；用 pointerdown 以便早于 click，避免「点触发器先被关掉再被打开」 */
function onDocumentPointerDown(event: PointerEvent) {
  if (!rootEl.value?.contains(event.target as Node)) closeList()
}

watch(open, (isOpen) => {
  if (isOpen) {
    document.addEventListener('pointerdown', onDocumentPointerDown)
    nextTick(() => {
      listEl.value?.querySelector<HTMLElement>('.is-active')?.scrollIntoView({ block: 'nearest' })
    })
  } else {
    document.removeEventListener('pointerdown', onDocumentPointerDown)
  }
})

onBeforeUnmount(() => document.removeEventListener('pointerdown', onDocumentPointerDown))
</script>

<template>
  <div ref="rootEl" class="app-select">
    <span class="composer-shell select-shell">
      <button
        ref="triggerEl"
        type="button"
        class="select-trigger"
        role="combobox"
        aria-haspopup="listbox"
        :aria-label="label"
        :aria-expanded="open"
        :aria-controls="listId"
        :aria-activedescendant="open ? optionId(activeIndex) : undefined"
        @click="toggle"
        @keydown="onTriggerKeydown"
      >
        <span class="select-value">{{ modelValue }}</span>
        <svg class="i select-chev" :class="{ 'is-open': open }" aria-hidden="true"><use href="#i-chev"/></svg>
      </button>
    </span>

    <Transition name="select-pop">
      <ul v-if="open" :id="listId" ref="listEl" class="select-panel" role="listbox" :aria-label="label">
        <li
          v-for="(option, index) in options"
          :id="optionId(index)"
          :key="option"
          role="option"
          :aria-selected="option === modelValue"
          class="select-option"
          :class="{ 'is-active': index === activeIndex, 'is-selected': option === modelValue }"
          @click="choose(option)"
          @mouseenter="activeIndex = index"
        >
          <span class="select-option-text">{{ option }}</span>
          <svg v-if="option === modelValue" class="i select-check" aria-hidden="true"><use href="#i-check"/></svg>
        </li>
      </ul>
    </Transition>
  </div>
</template>

<style scoped>
.app-select{position:relative;display:block}
.app-select .composer-shell{display:block;width:100%}

.select-trigger{display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;min-height:42px;padding:0 12px;
  border:0;background:transparent;color:var(--fg);font:400 13px/1.5 var(--font-body);text-align:left;cursor:pointer}
/* 触发器被 .composer-shell 的 overflow:hidden 包着，外描边会被裁掉，所以用负 offset 画在内侧 */
.select-trigger:focus-visible{outline:2px solid var(--fg);outline-offset:-3px;border-radius:20px}
.select-value{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.select-chev{width:15px;height:15px;color:var(--muted);transform:rotate(90deg);transition:transform .2s ease,color .2s ease}
.select-trigger[aria-expanded='true'] .select-chev{transform:rotate(-90deg);color:var(--accent)}

/* 弹层：与全站浮层（tooltip）同一套变量，深浅色主题自动跟随 */
.select-panel{position:absolute;z-index:30;top:calc(100% + 6px);right:0;min-width:100%;max-height:min(280px,50vh);
  overflow-y:auto;margin:0;padding:5px;border:1px solid var(--border);border-radius:14px;background:var(--tooltip-bg);
  box-shadow:var(--tooltip-shadow);list-style:none;backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px)}
.select-option{display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:36px;padding:8px 11px;
  border-radius:10px;color:var(--fg);font-size:13px;white-space:nowrap;cursor:pointer;transition:background .14s ease,color .14s ease}
/* 选中项靠「accent-soft 底色 + 强调色对勾」区分；文字仍用 --fg 而不是 --accent，
   因为 accent 压在 accent-soft 上深色主题只有 3.58:1，低于正文 4.5:1 的 AA 门槛，
   改用 --fg 后是 11.3:1（深色）/ 15.7:1（浅色）。 */
.select-option.is-selected{background:var(--accent-soft);color:var(--fg);font-weight:600}
.select-option.is-active{background:var(--row-hover)}
/* 选中项同时是光标项时保持 accent-soft，别被 row-hover 盖掉选中感 */
.select-option.is-selected.is-active{background:var(--accent-soft)}
.select-check{width:14px;height:14px;flex:0 0 auto;color:var(--accent)}

.select-pop-enter-active,.select-pop-leave-active{transition:opacity .16s ease,transform .16s ease}
.select-pop-enter-from,.select-pop-leave-to{opacity:0;transform:translateY(-6px) scale(.98)}
/* 触屏尺寸：与站内其他移动端控件统一到 44px 点击目标 */
@media (max-width:700px){
  .select-trigger,.select-option{min-height:44px}
}
@media (prefers-reduced-motion:reduce){
  .select-panel,.select-chev{transition:none}
  .select-pop-enter-active,.select-pop-leave-active{transition:none}
}
</style>
