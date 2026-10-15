<!--
  常驻栏的主题快捷切换按钮。

  视觉完全复用全局 .icon-btn（与同栏的通知按钮同一套尺寸 / 圆角 / hover / tooltip），
  所以这里不写任何样式，只负责「图标 + 行为」。

  行为与设置页保持一致：同样走 composables/useTheme 的 setTheme(option, origin)，
  圆心取本按钮中心，因此切换时张开的就是那一圈「水波涟漪」圆形扩散过渡。
  快捷切换只在明暗之间翻转：跟随系统时按当前实际明暗落到对应的固定选项
  （当前是深色 → 浅色，当前是浅色 → 深色）。
-->
<script setup lang="ts">
import { useTemplateRef } from 'vue'
import { setTheme, useTheme, type ThemeOption } from '../composables/useTheme'

const { isDark } = useTheme()
const root = useTemplateRef<HTMLButtonElement>('root')

function toggleTheme() {
  const next: ThemeOption = isDark.value ? '浅色' : '深色'
  const rect = root.value?.getBoundingClientRect()
  setTheme(next, rect ? { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 } : undefined)
}
</script>

<template>
  <button
    ref="root"
    type="button"
    class="icon-btn"
    :aria-label="isDark ? '切换到浅色主题' : '切换到深色主题'"
    :data-tip="isDark ? '切换到浅色' : '切换到深色'"
    data-od-id="theme-toggle-button"
    @click="toggleTheme"
  >
    <svg class="i" aria-hidden="true"><use :href="isDark ? '#i-moon' : '#i-sun'" /></svg>
  </button>
</template>
