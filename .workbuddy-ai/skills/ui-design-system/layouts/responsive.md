# 响应式断点与三档形态

## 设计思路

**解决的问题**：断点散落各处、每个组件自己挑数值，导致"同一个窗口宽度下侧栏已折叠
但页面还没变窄"的错位。

**视觉与交互意图**：全站只用**四个宽度断点 + 两个高度断点**，且**语义固定**：

| 断点 | 语义 | 主要变化 |
| --- | --- | --- |
| `≤1080px` | 窄桌面 | 侧栏 200→74px（图标条）；首页右面板 340→272px |
| `≤940px` | 更窄桌面 | 首页面板 →250px；列表行收回"破格" |
| `≤900px` | （仅事项页） | 双列变窄列 + 隐藏分类列 |
| `≤800px` | （仅记录页） | 标题区变纵向；历史行塌成两列 |
| **`≤700px`** | **移动端** | 外壳变纵向文档流；侧栏变顶部横向条；顶栏隐藏；所有交互元素 44px |
| `≤380px` | 超窄 | 侧栏品牌名隐藏 |

| 高度断点 | 语义 |
| --- | --- |
| `≤660px 高` | 首页：隐藏建议 chips、压缩 composer |
| `≤620px 高` | `.main` 自己滚（兜底） |
| `≤600px 高` | 侧栏自身可滚 |

**适用场景**：写任何媒体查询时——**从上表挑，不要自创数值**。

## 完整代码

### 断点速查（可直接复制的骨架）

```css
/* ── 窄桌面：侧栏折成图标条 ────────────────────────────────────────────── */
@media (max-width: 1080px) {
  .sidebar { flex-basis: 74px; width: 74px; padding-inline: 10px; align-items: center; }
  /* 文字用 .sr-only 隐藏（保留给读屏），不是 display:none */
  .brand strong,
  .nav-item > span { position: absolute; width: 1px; height: 1px; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  .nav-item { justify-content: center; gap: 0; padding: 0; }
  .side-status, .profile-meta { display: none; }
}

/* ── 移动端：外壳变纵向文档流 ──────────────────────────────────────────── */
@media (max-width: 700px) {
  .app-shell { display: flex; flex-direction: column; height: auto; min-height: 100svh; overflow: visible; }
  .main { flex: none; width: 100%; height: auto; overflow: visible; padding: 6px 24px 0; }
  .topbar { display: none; }
  .X-page { min-height: auto; overflow: visible; }      /* 每个页面都要写 */
}

/* ── 矮视口 ────────────────────────────────────────────────────────────── */
@media (max-height: 620px) and (min-width: 701px) { .main { overflow-y: auto; } }
@media (max-height: 660px) and (min-width: 701px) {
  .composer { padding: 10px 12px 8px; border-radius: 20px; }
  .chips { display: none; }
  .composer-msg { min-height: 0; }
}
@media (max-height: 600px) and (min-width: 701px) { .sidebar { overflow-y: auto; scrollbar-width: thin; } }

/* ── 触屏：关掉所有 hover 类反馈 ───────────────────────────────────────── */
@media (hover: none) {
  .nav-item::before, .nav-item::after,
  .icon-btn[data-tip]::before, .icon-btn[data-tip]::after { display: none; }
}

/* ── 动效降级（每个有动画的组件都要写）────────────────────────────────── */
@media (prefers-reduced-motion: reduce) { /* 见 motion/reduced-motion.md */ }
```

### 移动端必须做的六件事（新页面 checklist）

```css
@media (max-width: 700px) {
  /* 1. 页面放开滚动限制 */
  .X-page { min-height: auto; overflow: visible; }

  /* 2. 内容区宽度归 100% */
  .X-content { width: 100%; padding: 28px 0 40px; }

  /* 3. 交互元素顶到 44px */
  .btn, .tab, .select-trigger, .select-option, .animated-button, .send { min-height: 44px; }

  /* 4. 输入框字号 16px（低于 16px 会触发 iOS Safari 自动缩放） */
  .composer textarea, .X-search input { font-size: 16px; }

  /* 5. 横向滚动容器：子项 flex:0 0 auto + 容器 padding-bottom 留给焦点环 */
  .chips, .category-filter, .history-filters {
    overflow-x: auto; flex-wrap: nowrap; padding-bottom: 3px;
  }
  .chips > *, .category-tab, .filter-tab { flex: 0 0 auto; }

  /* 6. 隐藏桌面专属元素、显示移动端专属元素 */
  .topbar { display: none; }
  .mobile-note { display: block; }
}
```

## 变体说明

### 三档形态对照

| 维度 | 宽桌面 >1080px | 窄桌面 ≤1080px | 移动端 ≤700px |
| --- | --- | --- | --- |
| 侧栏 | 200px 竖列（图标+文字） | 74px 图标条 | 顶部 100% 横向条，`sticky` |
| 顶栏 | 58px 显示 | 58px 显示 | **隐藏**（侧栏 `.bar-actions` 顶上） |
| 导航项 | 40px 高、`gap:10px` | 40px 高、居中 | 44×44、圆角 12px |
| 主区 padding | `0 clamp(20px,2.8vw,40px)` | 同 | `6px 24px 0` |
| 首页面板 | 340px | 272px（≤940px 250px） | 100%，纵向 |
| 页面滚动 | `.X-page` 内部滚 | 同 | 文档滚 |
| 输入框圆角 | 24px | 24px | 22px |
| 按钮高度 | 38px | 38px | 44px |
| 字体 | 15px 基线 | 15px | 15px（输入框 16px） |
| tooltip | 右侧/下方 | 右侧/下方 | **隐藏**（`hover: none`） |

### 高度断点对照

| 断点 | 影响 | 做法 |
| --- | --- | --- |
| `≤660px 高` | 首页 composer 与 chips 打架 | **删内容**（隐藏 chips / hint / composer-msg 高度归零），不缩字号 |
| `≤620px 高` | 任何页面内容超一屏 | `.main { overflow-y: auto }` 兜底 |
| `≤600px 高` | 侧栏放不下 | 侧栏自身 `overflow-y: auto` |

### 尺寸断点

| 断点 | 页面 | 变化 |
| --- | --- | --- |
| `≤1080px` | 全站 + 首页 | 侧栏折叠、面板 272px |
| `≤940px` | 首页 | 面板 250px、gap 18px、列表行收回"破格" |
| `≤900px` | 事项页 | 双列变窄、隐藏 `.service-category` |
| `≤800px` | 记录页 | head 纵向、历史行两列 |
| `≤700px` | **全站** | 移动端形态 |
| `≤380px` | 侧栏 | 品牌名隐藏 |

## 使用注意事项

**可访问性**
- 折叠文字用 `.sr-only`（`clip: rect(0 0 0 0)`），**不要 `display: none`**——
  后者会把标签从无障碍树里删掉。
- 44px 是触摸目标下限：视觉上仍是 34px 图标按钮时，用 `width/height: 44px`
  撑开透明区域，不要靠放大字号。
- `@media (hover: none)` 下隐藏 tooltip：触屏没有 hover，留着会挡内容。
- `100svh` 而不是 `100vh`（iOS 地址栏）。

**性能**
- 移动端放开 `overflow` 后，页面滚动由文档承担——**更高效**（原生滚动，
  不需要内部滚动容器的额外层）。
- 横向滚动容器加 `scrollbar-width: none` 隐藏滚动条时，要保留
  `padding-bottom: 3px` 给焦点环留位置，否则 `focus-visible` 的 outline 会被裁。

**常见误用**
1. **自创断点**（如 `860px`、`1152px`）—— 会出现"侧栏折叠了但页面还是双列"的
   错位。只用上表的六个值。
2. **移动端忘记放开 `.X-page` 的 `overflow`** —— 双滚动条 + composer 被软键盘遮住。
3. **`display: none` 隐藏折叠文字** —— 读屏丢失标签。
4. **用 `100vh`** —— iOS 上会被地址栏吃掉一截。用 `100svh`。
5. **矮视口下缩字号而不是删内容** —— 字号体系会被破坏。项目里的做法是
   **隐藏非必要区块**（chips、hint）。
6. **横向滚动容器子项忘了 `flex: 0 0 auto`** —— 会被压扁、文字折行
   （`AnimatedButton` 内部已自带 `flex: 0 0 auto`，其他组件要自己加）。
