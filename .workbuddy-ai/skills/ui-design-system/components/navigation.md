# 导航

## 设计思路

**解决的问题**：导航有三处（侧栏主导航、侧栏辅助导航、顶栏），加上分类筛选 tab，
容易出现"同一个'当前页'状态在两处长得不一样"。

**视觉与交互意图**：
- **当前页**：`.active` = `--accent-soft` 底 + `--accent` 文字 + 500 字重。
- **非当前**：`--muted` 文字、透明底，hover 填 `--row-hover` 并把文字提到 `--fg`。
- 侧栏 hover 有 **2px 右移**（`translateX(2px)`）——这是唯一的位移反馈，幅度刻意
  很小，避免整列跳动。
- 每个导航项都带 **CSS-only tooltip**（`data-tip`），在图标折叠/移动端隐藏。

**适用场景**：侧栏、顶栏、面包屑、分类筛选组。

---

## 侧栏

### 完整代码

```vue
<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useCharacterBubble } from '../composables/useCharacterBubble'

interface NavItem { name: string; to: string; icon: string; label: string }

const route = useRoute()
const { setHoverMessage, clearHoverMessage } = useCharacterBubble()

const primaryNav: NavItem[] = [
  { name: 'home', to: '/', icon: 'i-home', label: '首页' },
  { name: 'chat', to: '/chat', icon: 'i-chat', label: '我的对话' },
  { name: 'services', to: '/services', icon: 'i-list', label: '支持事项' },
  { name: 'history', to: '/history', icon: 'i-clock', label: '最近记录' },
]
const secondaryNav: NavItem[] = [
  { name: 'help', to: '/help', icon: 'i-help', label: '使用帮助' },
  { name: 'settings', to: '/settings', icon: 'i-sliders', label: '设置' },
]

function isActive(name: string) { return route.name === name }

const navMessages: Record<string, string> = {
  home: '回首页找我吗？我就知道你会想我。',
  chat: '你要问我问题吗？',
  services: '校园事务，问我就对了。',
  history: '想看看我们之前聊过什么吗？',
  help: '遇到不会的就看这里，别害羞嘛。',
  settings: '要调整一下设置？我陪你。',
}
function showNavMessage(name: string) {
  setHoverMessage(navMessages[name] ?? '有什么问题尽管问我。')
}
</script>

<template>
  <aside class="sidebar" data-od-id="app-sidebar">
    <div class="brand" data-od-id="brand-lockup">
      <img class="brand-mark" src="/assets/brand-mark.png" alt="校园办事小秘书">
      <strong>校园办事小秘书</strong>
    </div>

    <nav class="primary-nav" aria-label="主导航">
      <router-link
        v-for="item in primaryNav" :key="item.name" :to="item.to"
        class="nav-item" :class="{ active: isActive(item.name) }"
        :data-od-id="`nav-${item.name}`" :data-tip="item.label"
        :aria-current="isActive(item.name) ? 'page' : undefined"
        @mouseenter="showNavMessage(item.name)" @mouseleave="clearHoverMessage"
        @focus="showNavMessage(item.name)" @blur="clearHoverMessage"
      >
        <svg class="i" aria-hidden="true"><use :href="`#${item.icon}`" /></svg><span>{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-spacer"></div>
    <div class="side-status" data-od-id="kb-status">
      <span class="status-dot" aria-hidden="true"></span><span>办事指南已更新</span>
    </div>

    <nav class="secondary-nav" aria-label="辅助导航">
      <router-link
        v-for="item in secondaryNav" :key="item.name" :to="item.to"
        class="nav-item" :class="{ active: isActive(item.name) }"
        :data-od-id="`nav-${item.name}`" :data-tip="item.label"
        :aria-current="isActive(item.name) ? 'page' : undefined"
        @mouseenter="showNavMessage(item.name)" @mouseleave="clearHoverMessage"
        @focus="showNavMessage(item.name)" @blur="clearHoverMessage"
      >
        <svg class="i" aria-hidden="true"><use :href="`#${item.icon}`" /></svg><span>{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="profile" data-od-id="profile-chip">
      <span class="avatar" aria-hidden="true">林</span>
      <span class="profile-meta"><strong>林同学</strong><span>本科生 · 一校区</span></span>
    </div>

    <div class="bar-actions">
      <button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="notification-button-mobile">
        <svg class="i" aria-hidden="true"><use href="#i-bell" /></svg><span class="dot-badge"></span>
      </button>
      <span class="avatar" role="img" aria-label="当前用户：林同学">林</span>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  position: relative;
  z-index: 3;
  flex: 0 0 200px;
  width: 200px;
  display: flex;
  flex-direction: column;
  padding: 22px 14px 16px;
}

.brand { display: flex; align-items: center; gap: 10px; padding: 0 6px 22px; }
.brand-mark {
  position: relative;
  display: block;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #fff;
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--accent) 45%, transparent),
    0 0 16px color-mix(in srgb, var(--accent) 38%, transparent),
    0 1px 3px rgba(80, 30, 10, .14);
  animation: brand-mark-glow 2.6s ease-in-out infinite;
}
.brand strong {
  font-family: var(--font-display);
  font-weight: 900;
  font-size: 15px;
  letter-spacing: -.01em;
  white-space: nowrap;
}
@keyframes brand-mark-glow {
  0%, 100% { filter: drop-shadow(0 0 0 color-mix(in srgb, var(--accent) 0%, transparent)); transform: scale(1); }
  50% { filter: drop-shadow(0 0 9px color-mix(in srgb, var(--accent) 72%, transparent)); transform: scale(1.04); }
}

.primary-nav,
.secondary-nav { display: grid; gap: 3px; }
.secondary-nav { padding-top: 12px; border-top: 1px solid var(--border); margin-top: 12px; }

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 40px;
  padding: 0 10px;
  border-radius: 11px;
  color: var(--muted);
  font-size: 13.5px;
  text-align: left;
  text-decoration: none;
  transition: background .16s ease, color .16s ease, transform .16s ease;
}
.nav-item .i { width: 16px; height: 16px; }
.nav-item > span { white-space: nowrap; }

.nav-item:hover { background: var(--row-hover); color: var(--fg); transform: translateX(2px); }
.nav-item.active { background: var(--accent-soft); color: var(--accent); font-weight: 500; }
.nav-item.active:hover { color: var(--accent); }

/* tooltip：悬停或键盘聚焦时显示对应页面名 */
.nav-item::before,
.nav-item::after {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  z-index: 20;
  transition: opacity .22s ease, transform .22s cubic-bezier(.2, .8, .2, 1);
}
.nav-item::before {                 /* 小箭头 */
  content: '';
  left: calc(100% + 6px);
  top: calc(50% - 4px);
  width: 9px;
  height: 9px;
  border-bottom: 1px solid var(--tooltip-border);
  border-left: 1px solid var(--tooltip-border);
  background: var(--tooltip-bg);
  transform: translateX(-5px) rotate(45deg);
}
.nav-item::after {                  /* 气泡 */
  content: attr(data-tip);
  left: calc(100% + 10px);
  top: 50%;
  transform: translate(-5px, -50%) scale(.96);
  transform-origin: left center;
  padding: 9px 12px;
  border: 1px solid var(--tooltip-border);
  border-radius: 10px 14px;
  background: var(--tooltip-bg);
  box-shadow: var(--tooltip-shadow);
  color: var(--tooltip-text);
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
  letter-spacing: .01em;
  white-space: nowrap;
}
.nav-item:hover::before,
.nav-item:focus-visible::before { opacity: 1; transform: translateX(0) rotate(45deg); }
.nav-item:hover::after,
.nav-item:focus-visible::after { opacity: 1; transform: translate(0, -50%) scale(1); }
@media (hover: none) { .nav-item::before, .nav-item::after { display: none; } }

.sidebar-spacer { flex: 1; min-height: 16px; }
.side-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 11px;
  background: var(--row-hover);
  color: var(--muted);
  font-size: 11.5px;
  line-height: 1.45;
}
.status-dot { width: 6px; height: 6px; flex: 0 0 auto; border-radius: 50%; background: oklch(60% .13 148); }

.profile { display: flex; align-items: center; gap: 9px; margin-top: 14px; padding: 6px 6px 0; }
.profile-meta { min-width: 0; }
.profile-meta strong { display: block; font-size: 12.5px; font-weight: 500; }
.profile-meta span { display: block; margin-top: 2px; color: var(--muted); font-size: 11px; }
.bar-actions { display: none; }

/* ── 窄桌面（≤1080px）：折叠成 74px 图标条 ────────────────────────────── */
@media (max-width: 1080px) {
  .sidebar { flex-basis: 74px; width: 74px; padding-inline: 10px; align-items: center; }
  .brand { padding: 0 0 20px; justify-content: center; }
  /* 文字用 .sr-only 的方式隐藏：保留给读屏，视觉上收起 */
  .brand strong,
  .nav-item > span {
    position: absolute; width: 1px; height: 1px; margin: -1px;
    overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
  }
  .nav-item { justify-content: center; gap: 0; padding: 0; }
  .side-status,
  .profile-meta { display: none; }
  .profile { justify-content: center; }
}
@media (max-height: 600px) and (min-width: 701px) {
  .sidebar { overflow-y: auto; scrollbar-width: thin; }
  .sidebar-spacer { min-height: 8px; }
}

/* ── 移动端（≤700px）：变成顶部横向条 ─────────────────────────────────── */
@media (max-width: 700px) {
  .sidebar {
    flex: none;
    width: 100%;
    flex-direction: row;
    align-items: center;
    gap: 4px;
    padding: 10px 18px;
    position: sticky;
    top: 0;
    z-index: 6;
    background: var(--page-bg);
  }
  .brand { padding: 0; margin-right: auto; min-width: 0; }
  .brand strong {
    position: static; width: auto; height: auto; margin: 0;
    overflow: hidden; clip: auto; display: block;
    font-size: 14px; min-width: 0;
    white-space: nowrap; text-overflow: ellipsis;
  }
  .brand-mark { width: 34px; height: 34px; }
  .sidebar-spacer,
  .side-status,
  .profile { display: none; }
  .primary-nav,
  .secondary-nav { display: flex; gap: 2px; padding: 0; margin: 0; border: 0; }
  .secondary-nav { border-left: 1px solid var(--border); padding-left: 6px; margin-left: 2px; }
  .nav-item { width: 44px; height: 44px; min-height: 44px; justify-content: center; padding: 0; border-radius: 12px; }
  .nav-item .i { width: 19px; height: 19px; }
  /* tooltip 改为出现在下方居中 */
  .nav-item::before { left: calc(50% - 4px); top: calc(100% + 4px); transform: translateY(5px) rotate(45deg); }
  .nav-item::after { left: 50%; top: calc(100% + 8px); transform: translate(-50%, 5px) scale(.96); transform-origin: center top; }
  .nav-item:hover::before,
  .nav-item:focus-visible::before { transform: translateY(0) rotate(45deg); }
  .nav-item:hover::after,
  .nav-item:focus-visible::after { transform: translate(-50%, 0) scale(1); }
  .bar-actions { display: flex; align-items: center; gap: 2px; padding-left: 6px; border-left: 1px solid var(--border); }
  .bar-actions .icon-btn { width: 44px; height: 44px; }
  .bar-actions .avatar { display: none; }
}
@media (max-width: 380px) { .brand strong { display: none; } }
</style>
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| **宽桌面（>1080px）** | 200px 宽，图标 + 文字，含状态条与个人卡片。 |
| **窄桌面（≤1080px）** | 74px 图标条；品牌名与导航文字用 `.sr-only` 隐藏（**不是 `display:none`**，读屏仍可读）；隐藏状态条与个人资料文字。 |
| **移动端（≤700px）** | 顶部 `position: sticky` 横向条，`background: var(--page-bg)`（这里是**唯一允许**填 page-bg 的地方——因为移动端 canvas 渐变在顶部已被内容覆盖，且顶栏需要挡住滚上来的内容）；导航项 44×44；主/辅导航之间加竖分隔线。 |
| **超窄（≤380px）** | 品牌名隐藏。 |
| **矮视口（≤600px 高）** | 侧栏自身 `overflow-y: auto`。 |
| **状态** | rest / hover（`--row-hover` + `translateX(2px)`）/ `.active`（`--accent-soft` + `--accent`）/ focus-visible（全局 outline + tooltip 同时出现）。 |
| **主题** | 全走变量；`.status-dot` 的绿色 `oklch(60% .13 148)` 是语义色，没做 token（只有一处用）。 |

### 使用注意事项

**可访问性**
- 两个 `<nav>` 都要有 `aria-label`（"主导航" / "辅助导航"）。
- 当前页用 `aria-current="page"`，**不要**只靠 `.active` 的视觉。
- 折叠态的文字必须用 `.sr-only` 隐藏，不能用 `display: none`（后者会把标签一起
  从无障碍树里删掉，读屏用户只剩 6 个无名字的链接）。
- tooltip 在 `@media (hover: none)` 下隐藏——触屏没有 hover，留着会挡内容。

**性能**
- `.brand-mark` 的呼吸用的是 `filter: drop-shadow` + `transform`，**会逐帧重绘**。
  只有一个元素，可接受；不要在列表里复制这种写法。
- 侧栏在移动端是 `position: sticky`，会建立新的滚动上下文；不要在它内部放
  `position: fixed` 子元素。

**常见误用**
1. **移动端顶栏填 `--page-bg` 这条规则不要外推** —— 桌面端顶栏**必须透明**
   （见 `foundations/page-background.md`）。只有移动端这条 sticky 顶栏例外。
2. 用户明确要求过：**不要给桌面端 `.topbar` 加 `position: sticky`**（试过，被要求
   回滚）。顶栏随页面滚走是当前接受的状态。
3. 导航文字用 `display: none` 而不是 `.sr-only`。
4. hover 位移超过 2px —— 整列会跟着抖。

---

## 顶栏与面包屑

### 完整代码

```css
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 58px;
  flex: 0 0 auto;
  /* 桌面端不写 background：让粒子渐变透上来 */
}

.crumb { display: flex; align-items: center; gap: 9px; font-size: 12.5px; color: var(--muted); }
.crumb strong { color: var(--fg); font-weight: 500; }

.top-actions { display: flex; align-items: center; gap: 10px; }

.avatar {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  border-radius: 9px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12.5px;
  font-weight: 500;
}

@media (max-width: 700px) {
  .topbar { display: none; }   /* 移动端由侧栏的 .bar-actions 顶上 */
}
```

```vue
<header class="topbar" data-od-id="global-header">
  <nav class="crumb" aria-label="页面标题"><strong>支持事项</strong></nav>
  <div class="top-actions">
    <button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="notification-button">
      <svg class="i" aria-hidden="true"><use href="#i-bell" /></svg><span class="dot-badge"></span>
    </button>
    <span class="avatar" role="img" aria-label="当前用户：林同学" data-od-id="profile-chip-top">林</span>
  </div>
</header>
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| 高度 | 58px，`gap: 16px` |
| 移动端 | `display: none`（侧栏 `.bar-actions` 里有一套同样的图标按钮 + 头像） |
| 头像 | `.avatar` 30px、`--accent-soft` 底 + `--accent` 字；带 `role="img"` + `aria-label` |
| 主题 | 透明底，不填 `--page-bg` |

### 使用注意事项

- 头像要有 `role="img" aria-label="当前用户：林同学"`，否则读屏读出来的是一个
  孤零零的"林"字。
- 顶栏里的图标按钮必须同时写 `aria-label` 与 `data-tip`，且两者文案一致。

---

## 分类筛选 tab

### 设计思路

不是按钮，是**切换组**：`.is-active` 用"反白"（`--fg` 底 + `--page-bg` 字）表示
选中，跟导航的 `--accent-soft` 选中态区分开——筛选是"当前视图的过滤条件"，
比"当前所在页面"更轻。

### 完整代码

```css
.category-filter { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 14px; }

.category-tab {
  min-height: 36px;                     /* 记录页 .filter-tab 是 34px */
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
  transition: background .16s ease, color .16s ease, border-color .16s ease;
}
.category-tab:hover { border-color: var(--fg); color: var(--fg); }
.category-tab.is-active { border-color: var(--fg); background: var(--fg); color: var(--page-bg); }

@media (max-width: 700px) {
  .category-filter { overflow-x: auto; flex-wrap: nowrap; padding-bottom: 3px; }
  .category-tab { flex: 0 0 auto; min-height: 40px; }
}
@media (prefers-reduced-motion: reduce) {
  .category-tab { transition: none; }
}
```

```vue
<div class="category-filter" role="list" aria-label="事项分类" data-od-id="service-categories">
  <button
    v-for="category in categories" :key="category" type="button"
    class="category-tab" :class="{ 'is-active': activeCategory === category }"
    :aria-pressed="activeCategory === category" @click="activeCategory = category"
  >{{ category }}</button>
</div>
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| 尺寸 | 帮助页 36px / 事项页 34px / 记录页 36px（`.filter-tab`，无边框、transparent 边框） |
| 状态 | rest（透明 + `--muted`）/ hover（`--fg` 边框与文字）/ `.is-active`（反白）/ focus-visible（全局 outline） |
| 移动端 | 容器改横向滚动 `overflow-x:auto; flex-wrap:nowrap`，tab `flex: 0 0 auto` + 40px |
| 主题 | `--fg` / `--page-bg` 自动反相 |

### 使用注意事项

**可访问性**
- 用 `aria-pressed` 表达"这是一个切换按钮的按下状态"。不要用 `aria-selected`
  （那是 tab/option 的语义）。
- 分组容器要有 `aria-label`。

**常见误用**
1. 用 `role="tablist"` / `<button role="tab">` —— 需要配套 `tabpanel` 与方向键
   管理，这里没有，用 `aria-pressed` 更简单且正确。
2. 移动端忘记 `flex: 0 0 auto` —— tab 会被压扁、文字折行。
3. 横向滚动容器忘记 `padding-bottom: 3px` —— 焦点环会被裁掉。
