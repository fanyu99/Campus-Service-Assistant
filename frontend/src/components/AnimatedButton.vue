<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

/**
 * 动效按钮（原范式里的 `animated-button`）：两根箭头（左右各一，悬停时互换）
 * + 文字 + 会膨胀的圆形色块。
 *
 * 静止：透明底 + 强调色描边环 + 强调色文字 + 右侧箭头。
 * 悬停 / 键盘聚焦：圆形色块放大填满按钮，文字与箭头切到 --page-bg，
 *                圆角由 100px 收成 12px，箭头从右滑出、左侧滑入。
 *
 * 两种形态：
 *   - 不传 `to`  → 渲染 `<button type="button">`（触发动作，如填充输入框）
 *   - 传了 `to`  → 渲染 `<RouterLink>`（导航，如「进入我的对话」）
 * 两种形态的视觉完全一致。
 *
 * 配色不写死（原范式用的是 greenyellow），全部走主题变量，深浅主题自动跟随：
 *   --accent    描边环 / 文字 / 膨胀色块
 *   --page-bg   色块填满后的文字与箭头（与 `.send` 按钮取色一致）
 *
 * 文案由默认插槽传入；父组件的事件监听、`data-*` 等属性会自动落到根元素上。
 */
const props = defineProps<{
  /** 传入后渲染成 <RouterLink>，用于页面内跳转 */
  to?: RouteLocationRaw
}>()

const rootProps = computed(() => (props.to ? { to: props.to } : { type: 'button' as const }))
</script>

<template>
  <component :is="props.to ? RouterLink : 'button'" class="animated-button" v-bind="rootProps">
    <svg class="arr arr-2" viewBox="0 0 24 24" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
      <path d="M16.1716 10.9999L10.8076 5.63589L12.2218 4.22168L20 11.9999L12.2218 19.778L10.8076 18.3638L16.1716 12.9999H4V10.9999H16.1716Z" />
    </svg>
    <span class="text"><slot /></span>
    <span class="circle" aria-hidden="true" />
    <svg class="arr arr-1" viewBox="0 0 24 24" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
      <path d="M16.1716 10.9999L10.8076 5.63589L12.2218 4.22168L20 11.9999L12.2218 19.778L10.8076 18.3638L16.1716 12.9999H4V10.9999H16.1716Z" />
    </svg>
  </component>
</template>

<style scoped>
.animated-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  /* flex:0 0 auto —— 按钮内是 overflow:hidden，若允许被压缩，窄屏（对话页 chips
     是 nowrap + 横向滚动）会把文字裁掉。保持原宽让容器滚动。 */
  flex: 0 0 auto;
  gap: 4px;
  padding: 7px 20px;
  border: 3px solid transparent;
  border-radius: 100px;
  background-color: transparent;
  color: var(--accent);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  white-space: nowrap;
  /* 渲染成 <RouterLink> 时是 <a>，要去掉默认下划线 */
  text-decoration: none;
  /* 原范式是 0 0 0 2px greenyellow；这里换成强调色描边环 */
  box-shadow: 0 0 0 2px var(--accent);
  cursor: pointer;
  overflow: hidden;
  transition: all .6s cubic-bezier(.23, 1, .32, 1);
}

.animated-button .arr {
  position: absolute;
  width: 13px;
  fill: var(--accent);
  z-index: 9;
  transition: all .8s cubic-bezier(.23, 1, .32, 1);
}

.animated-button .arr-1 { right: 8px; }
.animated-button .arr-2 { left: -25%; }

.animated-button .circle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 14px;
  height: 14px;
  background-color: var(--accent);
  border-radius: 50%;
  opacity: 0;
  transition: all .8s cubic-bezier(.23, 1, .32, 1);
}

.animated-button .text {
  position: relative;
  z-index: 1;
  transform: translateX(-9px);
  transition: all .8s cubic-bezier(.23, 1, .32, 1);
}

.animated-button:hover,
.animated-button:focus-visible {
  box-shadow: 0 0 0 12px transparent;
  color: var(--page-bg);
  border-radius: 12px;
}

.animated-button:hover .arr-1,
.animated-button:focus-visible .arr-1 { right: -25%; }

.animated-button:hover .arr-2,
.animated-button:focus-visible .arr-2 { left: 8px; }

.animated-button:hover .text,
.animated-button:focus-visible .text { transform: translateX(9px); }

.animated-button:hover .arr,
.animated-button:focus-visible .arr { fill: var(--page-bg); }

.animated-button:active {
  scale: .95;
  box-shadow: 0 0 0 4px var(--accent);
}

.animated-button:hover .circle,
.animated-button:focus-visible .circle {
  width: 200px;
  height: 200px;
  opacity: 1;
}

@media (max-width: 700px) {
  .animated-button {
    /* 触屏：统一到站内控件的触控目标下限（见 theme.css 的 --control-h） */
    min-height: var(--control-h);
    padding: 0 20px;
    font-size: 13.5px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .animated-button,
  .animated-button .arr,
  .animated-button .text,
  .animated-button .circle {
    transition: none;
  }
}
</style>
