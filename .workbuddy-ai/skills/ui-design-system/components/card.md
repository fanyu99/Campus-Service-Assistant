# 卡片与列表行

## 设计思路

**解决的问题**："卡片"在本项目里其实是三种完全不同的东西，混用会互相破坏：

| 类型 | 特征 | 例子 |
| --- | --- | --- |
| **大卡片（发光型）** | 有独立 frame 承载外发光，自身 `overflow:auto` | 通知中心卡片 |
| **面板卡片（静态型）** | 半透明表面 + 边框，无光效 | 帮助页联系卡片 |
| **列表行（行型）** | 无边框，靠分隔线，hover 填 `--row-hover` | 事务行、记录行、FAQ 行 |

**视觉与交互意图**：层级靠**圆角序列 + 分隔线 + 底色**表达，不靠阴影堆叠。
列表行刻意"不像卡片"——它们是一张长表的一部分，用分隔线比用卡片边框更透气。

**适用场景**：任何容器型 UI、任何列表。

---

## 列表行 —— 事务行 / 记录行 / FAQ 行

### 设计思路

一行 = 「图标 / 标识 + 主标题 + 次信息 + 尾随动作」。整行可点（`<button>` 或
`<RouterLink>`），hover 只变底色到 `--row-hover`，尾随箭头从 `--muted` 变 `--fg`
——这是唯一的 hover 反馈，不加阴影、不加位移，避免长列表滚动时满屏抖动。

### 完整代码

```css
/* ── 首页右面板：事务行 ────────────────────────────────────────────── */
.list { display: grid; gap: 2px; margin-top: 9px; }

.row,
.recent-row {
  display: flex;
  align-items: center;
  gap: 11px;
  /* 「破格」：让 hover 底色铺满比容器更宽一点，视觉上不被窄列挤住。
     只在首页右面板这种窄列里用，其他页面不要复制。 */
  width: calc(100% + 20px);
  margin-inline: -10px;
  padding: 6px 10px;
  border-radius: 12px;
  color: var(--fg);
  text-align: left;
  transition: background .16s ease;
}
.row { min-height: 46px; }
.recent-row { min-height: 48px; padding: 7px 10px; }

.row:hover,
.recent-row:hover { background: var(--row-hover); }
.row:hover .row-chev,
.recent-row:hover .row-chev { color: var(--fg); }

.row-icon {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  border-radius: 9px;
  background: var(--surface);
  color: var(--fg);
}
.row-icon .i { width: 15px; height: 15px; }

.row-title {
  font-weight: 500;
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}
.row-cat { flex: 0 0 auto; color: var(--muted); font-size: 12px; white-space: nowrap; }
.row-chev { width: 14px; height: 14px; flex: 0 0 auto; color: var(--muted); transition: color .16s ease; }

/* 记录行：小圆点 + 两行文字 */
.recent-dot { width: 5px; height: 5px; flex: 0 0 auto; border-radius: 50%; background: var(--muted); }
.recent-body { min-width: 0; flex: 1; }
.recent-body strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13.5px;
  font-weight: 400;
}
.recent-body span { display: block; margin-top: 3px; color: var(--muted); font-size: 11.5px; }
.recent-body i { margin: 0 5px; font-style: normal; opacity: .6; }

/* ── 事项页 / 记录页：grid 型列表行 ────────────────────────────────── */
.service-list,
.history-list { display: grid; }

.service-item {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 13px;
  min-height: 84px;
  padding: 15px 0;
  border-bottom: 1px solid var(--border);
  transition: background .16s ease;
}
/* 半透明 hover：整行铺满 --row-hover 在长列表里太重，降到 55% */
.service-item:hover { background: color-mix(in oklch, var(--row-hover) 55%, transparent); }

.service-mark {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  color: var(--accent);
  font-size: 14px;
  font-weight: 600;
}
.service-mark .i { width: 16px; height: 16px; }

.service-copy { min-width: 0; }
.service-copy h2 { margin: 0; font-size: 14px; font-weight: 550; line-height: 1.45; }
.service-copy p { margin: 4px 0 0; color: var(--muted); font-size: 12px; line-height: 1.5; }
.service-category { color: var(--muted); font-size: 11px; white-space: nowrap; }

.history-item {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr) auto;
  align-items: center;
  gap: 22px;
  min-height: 92px;
  padding: 18px 0;
  border-bottom: 1px solid var(--border);
  transition: background .16s ease;
}
.history-item:hover { background: color-mix(in oklch, var(--row-hover) 55%, transparent); }

.record-time { color: var(--muted); font-size: 12px; white-space: nowrap; }
.record-body { min-width: 0; user-select: text; -webkit-user-select: text; }
.record-title-line { display: flex; align-items: center; gap: 10px; min-width: 0; }
.record-title-line h2 {
  min-width: 0;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 550;
  line-height: 1.5;
}
.record-status {
  flex: 0 0 auto;
  padding: 4px 7px;
  border-radius: 6px;
  background: var(--surface);
  color: var(--muted);
  font-size: 11px;
  white-space: nowrap;
}
.record-status.is-pending { background: var(--accent-soft); color: var(--accent); }
.record-body p { margin: 5px 0 0; color: var(--muted); font-size: 12px; line-height: 1.55; }
.record-tag { margin-left: 10px; color: var(--fg); white-space: nowrap; }
.record-tag::before { content: '·'; margin-right: 10px; color: var(--border); }

/* ── FAQ 行（帮助页）：可展开 ──────────────────────────────────────── */
.faq-item { border-bottom: 1px solid var(--border); }
.faq-question {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  min-height: 64px;
  padding: 0;
  text-align: left;
  color: var(--fg);
  font-size: 14px;
  font-weight: 550;
  white-space: nowrap;
}
.faq-question .i {
  flex: 0 0 auto;
  width: 15px;
  height: 15px;
  transform: rotate(90deg);
  transition: transform .18s ease;
}
.faq-item.is-open .faq-question .i { transform: rotate(-90deg); }
.faq-answer {
  max-width: 72ch;
  margin: 0;
  padding: 0 32px 18px 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.8;
  user-select: text;
  -webkit-user-select: text;
}
```

```vue
<!-- FAQ：aria-expanded 必须跟展开状态同步 -->
<article class="faq-item" :class="{ 'is-open': openId === item.id }">
  <button type="button" class="faq-question" :aria-expanded="openId === item.id" @click="openId = openId === item.id ? '' : item.id">
    <span>{{ item.question }}</span>
    <svg class="i" aria-hidden="true"><use href="#i-chev" /></svg>
  </button>
  <p v-if="openId === item.id" class="faq-answer">{{ item.answer }}</p>
</article>
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| **尺寸** | 事务行 46px / 记录行 48px / 事项行 84px / 历史行 92px / FAQ 行 64px；移动端分别提到 52 / 52 / 78 / auto / 60。 |
| **状态 · hover** | 面板内列表 `--row-hover` 铺满；长列表用 `color-mix(in oklch, var(--row-hover) 55%, transparent)` 半透明。 |
| **状态 · focus-visible** | 走全局 `outline: 2.5px solid var(--fg)`，**不要单独给行写焦点样式**。 |
| **状态 · 选中** | 列表没有"选中"态；筛选是分类 tab 的事。记录状态用 `.record-status` / `.is-pending`。 |
| **主题** | 全部走 `--fg` / `--muted` / `--border` / `--row-hover` / `--surface` / `--accent`。 |
| **移动端** | 事项行去掉分类列（`grid-template-columns: 34px minmax(0,1fr) auto`）；历史行塌成单列（`1fr`，`gap:7px`），链接 `grid-column` 归位；FAQ 问题 `white-space: normal`。 |
| **窄桌面** | 首页右面板 340→272（≤940px 再 250px）；"破格"写法回到 `width:100%; margin-inline:0`。 |

### 使用注意事项

**可访问性**
- 整行可点时，用 `<button type="button">` 或 `<RouterLink>`，**不要**在外层 `<li>`
  上挂 `@click`（键盘够不到）。
- FAQ 的 `aria-expanded` 必须绑定展开状态；答案区不需要额外 `role`。
- 长文本（记录详情、FAQ 答案）要显式 `user-select: text`——`body` 全局禁选了。
- 图标列 `aria-hidden="true"`，可读信息在文字里。

**性能**
- hover 只动 `background`（合成层友好）。**不要给行加 `transform: translateY`**，
  长列表滚动时会持续重绘。
- 长列表的半透明 hover 用 `color-mix(in oklch, ...)`：oklch 插值不会出现
  sRGB 中途发灰的问题。

**常见误用**
1. **复制"破格"写法**（`width: calc(100% + 20px); margin-inline: -10px`）到宽页面
   —— 会让可点区超出容器，移动端触发横向滚动。只在窄列里用。
2. **给列表行加阴影** —— 层级错乱，且滚动时掉帧。
3. **行内文字不设 `min-width: 0`** —— flex/grid 子项默认 `min-width:auto`，
   长文本会把行撑破、省略号失效。**每个可伸缩列都要 `min-width: 0`**。

---

## 面板卡片 —— 静态型

### 设计思路

不需要发光的容器：半透明 `--surface` 底 + `--border` 边框 + 18px 圆角。
半透明是刻意的——让背后的粒子渐变透上来，跟"页面不是纯色"的事实一致。

### 完整代码

```css
.help-contact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  margin-top: 40px;
  padding: 24px 26px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: color-mix(in oklch, var(--surface) 78%, transparent);
}
.contact-label {
  margin: 0 0 8px;
  color: var(--accent);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .06em;
}
.help-contact h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 800;
  line-height: 1.35;
}
.help-contact p:last-child {
  max-width: 48ch;
  margin: 7px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.7;
}

@media (max-width: 700px) {
  .help-contact {
    align-items: flex-start;
    flex-direction: column;
    margin-top: 32px;
    padding: 20px;
  }
}
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| 尺寸 | padding `24px 26px`，圆角 18px；移动端纵向排列 + `padding: 20px` |
| 主题 | `--surface` 半透明 + `--border`，明暗自动跟随 |
| 无光效 | 这一类**不加**任何 box-shadow

### 使用注意事项

- 半透明底用 `color-mix(in oklch, ...)`，不要用 `rgba()` 写死——后者在深色主题下
  会变成一块突兀的亮斑。
- 面板卡片里**不要**放需要滚动的长内容（没有 `overflow` 处理）。

---

## 大卡片（发光型）—— 要点速记

通知中心卡片是本项目唯一"发光型"卡片，它的结构有一条硬约束：

> **光效绝不能挂在 `.notification-card` 内部** —— 卡片是 `overflow:auto` 的滚动
> 容器，挂在里面会被裁掉，而且 `abs` 子元素会跟着内容一起滚走。

正确做法是**在外面包一层 frame**，三层光效全部挂在 frame 上：

```css
.notification-card-frame { position: relative; z-index: 1; width: 100%; isolation: isolate; }
/* ::before      环境弥散光（只呼吸 opacity，不旋转）*/
/* ::after       底部呼吸背光（径向渐变，opacity+scale+blur 三联动）*/
/* .…-ring       旋转渐变描边环（叠在卡片之上，mask 只留 2px 边）*/
```

完整代码与参数见 `components/dialog.md`（弹窗与卡片是一体的）与
`motion/notice-glow.md`（三层光效的实现细节）。

### 使用注意事项

- 新增发光型卡片时照抄 frame 三层结构，不要简化成"给卡片加个 box-shadow"。
- 所有光效层都要 `pointer-events: none`（实测否则会挡住关闭按钮与列表 hover）。
- 窄屏要收敛光效（`inset` 收窄、`blur` 减小），避免糊满整屏。
