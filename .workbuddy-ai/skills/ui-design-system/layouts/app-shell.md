# 应用外壳：.app-shell / .main / .topbar

## 设计思路

**解决的问题**：`.app-shell` 被钉死成 `height: 100vh; overflow: hidden`，里面的 `.main`
因此**也只有一屏高**。任何超过一屏的页面内容都会被直接裁掉——滚轮滚不动、键盘也
够不到。这是本项目最容易踩、后果最严重的布局坑。

**视觉与交互意图**：桌面端是"一屏应用"（侧栏固定 + 主区滚动），移动端是"文档流"
（整体随页面滚）。两套行为的切换靠媒体查询完成，不靠 JS。

**核心规则（背下来）**：

> **页面级滚动必须由 `.main`（即各页的 `.X-page`）自己承担，绝不能写
> `overflow: hidden`。**
>
> 统一写法：
> ```css
> .X-page { min-height: 0; overflow-y: auto; overflow-x: hidden;
>           scrollbar-width: thin; scrollbar-color: var(--border) transparent }
> @media (max-width: 700px) { .X-page { min-height: auto; overflow: visible } }
> ```
> 例外：`ChatView` 是 `overflow: hidden` + 内部 `.message-list` 独立滚动（有意设计）。

**适用场景**：新增任何页面时的第一步。

## 完整代码

### 外壳与骨架（全局，放 `theme.css`）

```css
*,
*::before,
*::after { box-sizing: border-box; }

html { -webkit-text-size-adjust: 100%; }

.app-shell {
  position: relative;
  display: flex;
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;          /* 桌面端：整个应用不滚，交给内部容器 */
}

.main {
  position: relative;
  z-index: 2;                /* 压在粒子 canvas(z-index:0) 之上 */
  display: flex;
  flex-direction: column;
  min-width: 0;              /* flex 子项关键：否则长内容会把布局撑破 */
  flex: 1;
  padding: 0 clamp(20px, 2.8vw, 40px);
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 58px;
  flex: 0 0 auto;            /* 顶栏不参与伸缩 */
}

/* 矮视口兜底：窗口太矮时主区自己滚 */
@media (max-height: 620px) and (min-width: 701px) {
  .main { overflow-y: auto; }
}

/* ── 移动端：回到文档滚动 ──────────────────────────────────────────────── */
@media (max-width: 700px) {
  .app-shell {
    display: flex;
    flex-direction: column;
    height: auto;
    min-height: 100svh;
    overflow: visible;
  }
  .main {
    flex: none;
    width: 100%;
    height: auto;
    overflow: visible;
    padding: 6px 24px 0;
  }
  .topbar { display: none; }   /* 移动端由侧栏的 .bar-actions 顶上 */
}
```

### 页面骨架（每个页面都这样开头）

```vue
<template>
  <main class="main services-page" data-od-id="services-main">
    <header class="topbar" data-od-id="global-header">
      <nav class="crumb" aria-label="页面标题"><strong>支持事项</strong></nav>
      <div class="top-actions">
        <button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="notification-button">
          <svg class="i" aria-hidden="true"><use href="#i-bell" /></svg><span class="dot-badge"></span>
        </button>
        <span class="avatar" role="img" aria-label="当前用户：林同学" data-od-id="profile-chip-top">林</span>
      </div>
    </header>

    <section class="services-content">…</section>
  </main>
</template>

<style scoped>
/* .main 在 .app-shell（height:100vh + overflow:hidden）里被钉死高度，
   所以「页面级滚动」必须由 .main 自己承担：overflow-y:auto 建立滚动容器，
   否则内容超过一屏会被直接裁掉、滚轮和键盘都够不到。 */
.services-page {
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}
.services-content {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(250px, .82fr) minmax(0, 1.35fr);
  gap: clamp(34px, 6vw, 92px);
  width: min(1080px, 100%);
  margin: auto;
  padding: clamp(26px, 5vh, 70px) 0 clamp(30px, 5vh, 72px);
}

@media (max-width: 700px) {
  .services-page { min-height: auto; overflow: visible; }   /* 交给文档滚动 */
  .services-content { display: block; width: 100%; padding: 28px 0 40px; }
}
</style>
```

### 路由过渡（挂一次，App.vue）

```vue
<div class="app-shell">
  <AppSidebar />
  <Transition name="route" mode="out-in">
    <router-view v-slot="{ Component, route }">
      <component :is="Component" :key="route.fullPath" />
    </router-view>
  </Transition>
</div>
```

```css
.route-enter-active,
.route-leave-active {
  will-change: opacity, transform;
  transition: opacity 180ms cubic-bezier(.2, 0, 0, 1), transform 180ms cubic-bezier(.2, 0, 0, 1);
}
.route-enter-from { opacity: 0; transform: translateY(8px); }
.route-leave-to { opacity: 0; transform: translateY(-4px); }
@media (prefers-reduced-motion: reduce) {
  .route-enter-active,
  .route-leave-active { transition: none; }
  .route-enter-from,
  .route-leave-to { opacity: 1; transform: none; }
}
```

### App.vue 的最小挂载顺序

```vue
<template>
  <AppSprite />
  <ParticleBackground :particle-count="82" :petal-count="72" … />
  <!-- 主题切换的圆形扩散：两层平时全屏透明，只是 view-transition-name 的载体 -->
  <div class="theme-ripple-veil" aria-hidden="true" />
  <div class="theme-ripple-pond" aria-hidden="true" />
  <div class="app-shell">
    <AppSidebar />
    <Transition name="route" mode="out-in">…</Transition>
  </div>
  <!-- 弹窗挂在外壳之外，position:fixed + z-index:30 -->
</template>
```

## 变体说明

| 变体 | 规则 |
| --- | --- |
| **宽桌面（>1080px）** | 侧栏 200px + 主区 flex:1；主区内部自己滚。 |
| **窄桌面（≤1080px）** | 侧栏折成 74px 图标条；主区逻辑不变。 |
| **矮视口（≤620px 高，桌面）** | `.main { overflow-y: auto }` 兜底。 |
| **移动端（≤700px）** | `.app-shell` 变纵向、`height:auto; min-height:100svh; overflow:visible`；`.main` `overflow: visible`；**顶栏隐藏**，导航移到侧栏顶部条。 |
| **对话页** | **唯一例外**：`.chat-main { min-height: 0; overflow: hidden }` + `.message-list { overflow-y: auto }` 独立滚动；移动端再放开成 `min-height: 100svh; overflow: visible`。 |
| **主题** | 外壳不填背景（透明，让粒子渐变透上来）。 |

## 使用注意事项

**可访问性**
- 每个页面 `<main class="main X-page">` 只能有一个 `<main>`。
- 顶栏 `<nav class="crumb" aria-label="页面标题">` 给出当前页名称。
- 滚动容器要能被键盘滚动：纯 `overflow-y: auto` 的 `div` 默认不可聚焦，
  但因为页面里有可聚焦元素（按钮/链接），Tab 到它们时会自动滚入视野，可接受。
- 移动端用 `100svh` 而不是 `100vh`（避免 iOS 地址栏导致的高差）。

**性能**
- `overflow-x: hidden` 防横向溢出；`scrollbar-width: thin` +
  `scrollbar-color: var(--border) transparent` 统一滚动条观感（配 `color-scheme`）。
- 路由过渡只动 `opacity` + `transform`，`will-change` 只在 active 期间挂。

**常见误用**
1. **给 `.X-page` 写 `overflow: hidden`** —— 超过一屏的内容永久够不到，
   且不会报错，是最难查的一类 bug。**每个新页面都要检查这一行。**
2. **移动端媒体查询里忘记放开** （`min-height:auto; overflow:visible`）——
   手机上会出现一个内部滚动的小窗口，体验很差。
3. **给 `.topbar` 加 `position: sticky`** —— 用户明确要求过不要固定顶栏
   （试过并回滚）。顶栏随页面滚走是当前接受的状态，**不要再提议**。
4. **`.main` 忘了 `min-width: 0`** —— flex 子项默认 `min-width:auto`，
   长内容会把侧栏挤没。
5. **在 `.app-shell` 里再嵌一层 `height: 100vh` 的容器** —— 双重钉死，
   内部滚动彻底失效。
6. 弹窗（`.notification-modal`）必须挂在 `.app-shell` **之外**，否则会被
   `overflow: hidden` 裁掉。
