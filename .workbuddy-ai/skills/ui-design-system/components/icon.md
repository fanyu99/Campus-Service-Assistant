# 图标

## 设计思路

**解决的问题**：图标来源混乱（Unicode 字符、emoji、随手画的 SVG），同一层级的图标
视觉重量不一致——有的撑满 24×24，有的缩在中间一小团。

**视觉与交互意图**：全部内联到一个 SVG sprite（`AppSprite.vue`），用
`<use href="#i-*">` 引用。统一基线：

| 维度 | 规则 |
| --- | --- |
| 画布 | `viewBox="0 0 24 24"` |
| **安全框** | 主体图形收进 **3.8–20.2**（16.4×16.4 居中于 12,12）——**同层级图标视觉重量一致靠这个框，不靠眼睛估** |
| 描边 | `fill:none; stroke:currentColor; stroke-width:1.7; stroke-linecap/linejoin:round` |
| 圆角 | 矩形一律 `rx="2.5"`（**不准混 2 和 2.6**） |
| 例外 | 箭头类（`i-chev` / `i-arrow-up`）与勾（`i-check`）形状天然窄扁，**只对齐高度**，不硬撑到 16.4 宽 |
| 尺寸 | 由使用方给 `.i { width/height }`（默认 `1em`，各组件覆盖成 13~19px） |

**适用场景**：全站所有图标。

## 完整代码

### Sprite 定义（`components/AppSprite.vue`，完整副本见 `examples/AppSprite.vue`）

```vue
<!--
  图标库统一基线（改图标前先看这里）：
    画布      viewBox 0 0 24 24
    安全框    主体图形收进 3.8–20.2（16.4×16.4，居中于 12,12）
              —— 同层级图标视觉重量一致，靠的就是这个框，不是靠眼睛估
    描边      fill:none + stroke:currentColor + stroke-width:1.7
              （定义在 theme.css 的 .i；任何组件都不要再单独覆盖 stroke-width）
    端点      stroke-linecap / stroke-linejoin 均为 round
    圆角      矩形一律 rx=2.5
    例外      箭头类（i-chev / i-arrow-up）与勾（i-check）形状本身窄扁，
              只对齐高度，不硬撑到 16.4 宽
-->
<template>
  <svg class="sprite" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg">
    <!-- ── 导航 ─────────────────────────────────────────────────────────── -->
    <symbol id="i-home" viewBox="0 0 24 24"><path d="M3.8 10.6L12 3.9l8.2 6.7V19a1.4 1.4 0 0 1-1.4 1.4h-4v-6.1H9.2v6.1H5.2A1.4 1.4 0 0 1 3.8 19z" /></symbol>
    <symbol id="i-chat" viewBox="0 0 24 24"><path d="M20.2 14.6a2 2 0 0 1-2 2H8.3L4.4 20.2V5.8a2 2 0 0 1 2-2h11.8a2 2 0 0 1 2 2z" /><path d="M8.6 9.8h6.8M8.6 13h4.2" /></symbol>
    <symbol id="i-list" viewBox="0 0 24 24"><path d="M8.8 5.6h11.4M8.8 12h11.4M8.8 18.4h11.4" /><path d="M4.4 5.6h.01M4.4 12h.01M4.4 18.4h.01" /></symbol>
    <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.2" /><path d="M12 7.6V12l3.2 1.9" /></symbol>
    <symbol id="i-help" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.2" /><path d="M9.7 9.5a2.4 2.4 0 1 1 3.3 2.3c-.7.3-1 .8-1 1.5v.3" /><path d="M12 16.6h.01" /></symbol>
    <symbol id="i-sliders" viewBox="0 0 24 24"><path d="M3.9 6.4h8.6M17.7 6.4h2.5M3.9 17.6h2M10.9 17.6h9.3" /><circle cx="15.2" cy="6.4" r="2.5" /><circle cx="8.4" cy="17.6" r="2.5" /></symbol>

    <!-- ── 通知（按类型区分，不再一律用铃铛）─────────────────────────────── -->
    <symbol id="i-bell" viewBox="0 0 24 24"><path d="M18.5 16.4V11.2a6.5 6.5 0 1 0-13 0v5.2L3.9 19h16.2z" /><path d="M9.9 21.2a2.4 2.4 0 0 0 4.2 0" /></symbol>
    <symbol id="i-megaphone" viewBox="0 0 24 24"><path d="M4.2 11.1L19.8 6.6v10.8L4.2 13.9z" /><path d="M11.4 16a2.7 2.7 0 1 1-5.2-1.4" /></symbol>
    <symbol id="i-doc" viewBox="0 0 24 24"><path d="M13.6 4.2H7.6a2.6 2.6 0 0 0-2.6 2.6v10.4a2.6 2.6 0 0 0 2.6 2.6h8.8a2.6 2.6 0 0 0 2.6-2.6V9.6z" /><path d="M13.6 4.2v5.4h5.4" /><path d="M9.4 13.6h5.2M9.4 16.4h5.2" /></symbol>
    <symbol id="i-wrench" viewBox="0 0 24 24"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" /></symbol>

    <!-- ── 事务（首页服务行与事项列表共用同一套映射）──────────────────────── -->
    <symbol id="i-id" viewBox="0 0 24 24"><rect x="3.8" y="4.8" width="16.4" height="14.4" rx="2.5" /><circle cx="8.8" cy="11.4" r="2.1" /><path d="M6.2 16.6a3 3 0 0 1 5.2 0M13.6 10.4h4.4M13.6 13.6h4.4" /></symbol>
    <symbol id="i-card" viewBox="0 0 24 24"><rect x="3.8" y="4.8" width="16.4" height="14.4" rx="2.5" /><path d="M3.8 9.6h16.4M6.8 14.4h3.2" /></symbol>
    <symbol id="i-calendar" viewBox="0 0 24 24"><rect x="3.8" y="5.4" width="16.4" height="14.4" rx="2.5" /><path d="M3.8 10.4h16.4M8.4 3.9v3.2M15.6 3.9v3.2" /></symbol>
    <symbol id="i-award" viewBox="0 0 24 24"><circle cx="12" cy="9.4" r="6.4" /><path d="M8.8 14.8L7.2 20.4l4.8-2.3 4.8 2.3-1.6-5.6" /></symbol>
    <symbol id="i-wifi" viewBox="0 0 24 24"><path d="M4.2 8.7a11.6 11.6 0 0 1 15.6 0" /><path d="M7.2 11.9a7.4 7.4 0 0 1 9.6 0" /><path d="M10.2 15.1a3.2 3.2 0 0 1 3.6 0" /><path d="M12 18.3h.01" /></symbol>

    <!-- ── 通用 ─────────────────────────────────────────────────────────── -->
    <symbol id="i-search" viewBox="0 0 24 24"><circle cx="10.4" cy="10.4" r="6.4" /><path d="M15.1 15.1l4.8 4.8" /></symbol>
    <symbol id="i-chev" viewBox="0 0 24 24"><path d="M9.5 5.5l6.5 6.5-6.5 6.5" /></symbol>
    <symbol id="i-arrow-up" viewBox="0 0 24 24"><path d="M12 19.5V5" /><path d="M5.8 11.2L12 5l6.2 6.2" /></symbol>
    <symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12.8l4.6 4.6L19 7.6" /></symbol>
  </svg>
</template>
```

### 全局 `.i` 类（`theme.css`）

```css
.sprite {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
}

.i {
  width: 1em;
  height: 1em;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex: 0 0 auto;
}
```

### 用法

```vue
<!-- 1. App.vue 顶部挂一次 sprite（全站只挂一次） -->
<AppSprite />

<!-- 2. 任意位置引用 -->
<svg class="i" aria-hidden="true"><use href="#i-bell" /></svg>

<!-- 3. 覆盖尺寸（在 scoped 里只改 width/height，不改 stroke-width） -->
.send .i { width: 15px; height: 15px; }
```

### 事务图标映射（首页服务行 + 事项列表共用）

```ts
/** 事务图标：按 id 映射到内联 sprite，与首页服务行同一套映射。
    不再用 mock 里的 Unicode 字符（▣ ⌁ ◷ ¥ @）—— 那些符号在多数中文字体里
    缺字或回退成别的字形，粗细也跟全站的线性图标对不上。 */
const SERVICE_ICON: Record<string, string> = {
  'student-card': 'i-id',
  'campus-card': 'i-card',
  repair: 'i-wrench',
  leave: 'i-calendar',
  scholarship: 'i-award',
  network: 'i-wifi',
}
```

## 变体说明

### 19 个 symbol 清单

| 分组 | id | 用途 |
| --- | --- | --- |
| 导航 | `i-home` `i-chat` `i-list` `i-clock` `i-help` `i-sliders` | 侧栏主/辅导航 |
| 通知 | `i-bell` `i-megaphone` `i-doc` `i-wrench` | 通知按类型区分 |
| 事务 | `i-id` `i-card` `i-calendar` `i-award` `i-wifi` | 首页服务行 + 事项列表 |
| 通用 | `i-search` `i-chev` `i-arrow-up` `i-check` | 搜索 / 右箭头 / 发送 / 选中 |

**已删除**：`i-grid`（侧栏 services 换 `i-list`）、`i-drop`（首页 repair 换
`i-wrench`）、`i-spark`（零引用）。**不要再引用**。

### 尺寸档位（实测）

| 位置 | 尺寸 |
| --- | --- |
| 侧栏导航（桌面） | 16px |
| 侧栏导航（移动端） | 19px |
| 顶栏 `.icon-btn` | 17px |
| 搜索框 / 事务行图标块 | 16px / 15px |
| 发送按钮 / 动效按钮箭头 | 15px / 13px |
| 列表行尾随 chev | 14px |
| 下拉对勾 / 通知项 | 14px / 16px |
| 链接型按钮 chev | 13px |

### 状态与主题

| 变体 | 规则 |
| --- | --- |
| 颜色 | `stroke: currentColor` → 跟随父级 `color`。要变色就改父级 `color`（如 hover 时 `color: var(--fg)`）。 |
| hover | 由父元素控制（`.icon-btn:hover { color: var(--fg) }`）。 |
| 旋转 | 需要方向时用 `transform`（下拉箭头 `rotate(90deg)` ↔ `-90deg`；FAQ `rotate(90deg)` ↔ `-90deg`），**不要用第二个图标**。 |
| 主题 | 自动跟随，无需额外处理。 |
| 禁用 | 父级 `color` 降到 `color-mix(in srgb, var(--muted) 60%, transparent)`。 |

## 使用注意事项

**可访问性**
- 装饰性图标一律 `aria-hidden="true"`。只有当图标是**唯一**信息载体时才加
  `aria-label`（如头像 `role="img" aria-label="当前用户：林同学"`）。
- sprite 根元素 `aria-hidden="true" focusable="false"`（防止 IE/旧 Edge 把 svg
  纳入 Tab 序列）。

**性能**
- 内联 sprite 意味着**零额外网络请求**；代价是每个页面都带上约 4KB 的 symbol。
  20 个图标以内保持内联，超过 40 个再考虑外部文件。

**常见误用**
1. **在组件里覆盖 `stroke-width`** —— 全站统一 1.7。历史上 `.send .i` 曾单独覆盖过，
   是明确的出血点，已删。**包括 `.send .i` 也不要写。**
2. **引入第二套图标库**（如 element-plus 的 icons-vue）—— 画风与 stroke-width
   都不一样，会立刻看出两套。
3. **用 Unicode 字符当图标**（`▣` `⌁` `◷` `¥` `@`）—— 中文字体里缺字或回退成别的
   字形，粗细也对不上。`home.mock.ts` 里的 `icon` 字段是历史遗留，**UI 不引用它**。
4. **新增 symbol 不进安全框** —— 主体必须收进 3.8–20.2，否则同层级里会显得
   忽大忽小。
5. **矩形圆角混用 2 和 2.6** —— 统一 `rx="2.5"`。
6. **圆形半径随意取** —— `i-clock` / `i-help` 的 `r` 是 8.2（与安全框一致），
   `i-search` 的 `r` 是 6.4（配合斜线把手）。新增圆形图标照这两个档取。
