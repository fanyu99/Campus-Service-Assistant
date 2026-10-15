# 内容页布局：帮助 / 事项 / 记录 / 设置

## 设计思路

**解决的问题**：四个页面（使用帮助、支持事项、最近记录、设置）结构高度相似——
顶栏 + 大标题 + 搜索/筛选 + 列表 + 空态。各写一遍会产出四套间距。

**视觉与交互意图**：统一骨架，只有"内容区宽度"和"是否分栏"两处不同：

| 页面 | 内容区宽度 | 布局 | 特征 |
| --- | --- | --- | --- |
| 使用帮助 | `min(1020px, 100%)` | 单列（intro → FAQ → 联系卡片） | 搜索 + 分类 tab |
| 支持事项 | `min(1080px, 100%)` | **双列** `minmax(250px,.82fr) minmax(0,1.35fr)`（intro | list） | 搜索 + 分类 tab |
| 最近记录 | `min(1020px, 100%)` | 单列（head 横向 → list） | 搜索 + 筛选 tab 在标题右侧 |
| 设置 | `min(900px, 100%)` | 单列（分区堆叠） | 表单字段 + AppSelect |

**核心规则**：页面根元素承担滚动（见 `app-shell.md`）。

**适用场景**：任何新增的"内容型"页面。

## 完整代码

### 通用骨架

```vue
<main class="main X-page" data-od-id="X-main">
  <header class="topbar" data-od-id="X-header">
    <nav class="crumb" aria-label="页面标题"><strong>页面名</strong></nav>
    <div class="top-actions">
      <button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="X-notification-button">
        <svg class="i" aria-hidden="true"><use href="#i-bell" /></svg><span class="dot-badge" />
      </button>
      <span class="avatar" role="img" aria-label="当前用户：林同学" data-od-id="X-profile-chip">林</span>
    </div>
  </header>

  <section class="X-content" data-od-id="X-content">
    <div class="X-intro">
      <h1 data-od-id="X-heading">查找…</h1>
      <label class="X-search composer-shell">
        <svg class="i" aria-hidden="true"><use href="#i-search" /></svg>
        <span class="sr-only">搜索…</span>
        <input v-model="query" type="search" placeholder="…" autocomplete="off" />
        <button v-if="query" type="button" class="clear-search" aria-label="清空" @click="query = ''">清空</button>
      </label>
      <div class="X-categories" role="list" aria-label="…分类">
        <button v-for="c in categories" :key="c" type="button" class="category-tab"
                :class="{ 'is-active': activeCategory === c }" :aria-pressed="activeCategory === c"
                @click="activeCategory = c">{{ c }}</button>
      </div>
    </div>

    <section class="X-list-wrap" aria-labelledby="X-heading">
      <div class="list-heading"><span>全部…</span><span class="list-count">{{ items.length }} 项</span></div>
      <ul v-if="items.length" class="X-list">…</ul>
      <div v-else class="empty-state">…</div>
    </section>
  </section>
</main>
```

```css
/* 页面级滚动：必须有，否则内容超一屏被裁掉 */
.X-page {
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

.X-content {
  position: relative;
  z-index: 1;
  width: min(1020px, 100%);              /* 帮助/记录 1020；事项 1080；设置 900 */
  margin: auto;
  padding: clamp(26px, 5vh, 70px) 0 clamp(30px, 5vh, 72px);
}

h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(32px, 4.4vw, 54px);
  line-height: 1.28;                     /* 设置页 1.3 */
  font-weight: 900;
  letter-spacing: -.025em;
}

@media (max-width: 700px) {
  .X-page { min-height: auto; overflow: visible; }
  .X-content { width: 100%; padding: 28px 0 40px; }
}
```

### 事项页：双列

```css
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
.services-intro { align-self: start; padding-top: clamp(8px, 3vh, 42px); }
.service-list-wrap { min-width: 0; padding-top: clamp(8px, 3vh, 40px); }

@media (max-width: 900px) {
  .services-content { grid-template-columns: minmax(220px, .7fr) minmax(0, 1.3fr); gap: 30px; }
  .service-item { grid-template-columns: 34px minmax(0, 1fr) auto; }
  .service-category { display: none; }
}
@media (max-width: 700px) {
  .services-content { display: block; width: 100%; padding: 28px 0 40px; }
  .services-intro { padding-top: 0; }
  .service-list-wrap { padding-top: 42px; }
}
```

### 记录页：标题与筛选同行

```css
.history-content {
  position: relative;
  z-index: 1;
  width: min(1020px, 100%);
  margin: auto;
  padding: clamp(26px, 5vh, 70px) 0 clamp(30px, 5vh, 72px);
}
.history-title-block { display: grid; gap: 18px; min-width: min(430px, 100%); }
.history-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  padding: clamp(8px, 3vh, 40px) 0 30px;
}
.history-filters { display: flex; gap: 5px; padding-bottom: 2px; }

@media (max-width: 800px) {
  .history-title-block { width: 100%; min-width: 0; }
  .history-head { align-items: flex-start; flex-direction: column; gap: 22px; }
  .history-filters { width: 100%; overflow-x: auto; }
  .filter-tab { min-height: 40px; flex: 0 0 auto; }
  .history-item { grid-template-columns: 82px minmax(0, 1fr); gap: 12px; }
  .record-link { grid-column: 2; justify-self: start; }
}
@media (max-width: 700px) {
  .history-item { grid-template-columns: 1fr; gap: 7px; min-height: 0; padding: 17px 0; }
  .record-title-line { align-items: flex-start; }
  .record-title-line h2 { white-space: normal; overflow: visible; }
  .record-link { grid-column: auto; }
}
```

### 设置页：分区堆叠

```css
.settings-content {
  position: relative;
  z-index: 1;
  width: min(900px, 100%);
  margin: auto;
  padding: clamp(26px, 5vh, 70px) 0 clamp(30px, 5vh, 72px);
}
.settings-head { padding: clamp(8px, 3vh, 40px) 0 30px; }
.intro-copy { max-width: 48ch; margin: 16px 0 0; color: var(--muted); font-size: 14px; line-height: 1.8; }
.settings-layout { display: grid; gap: 14px; }
.settings-section { padding: 22px 0; border-top: 1px solid var(--border); }
.section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
.section-heading h2 { margin: 0; font-size: 16px; font-weight: 650; line-height: 1.45; }
.section-heading p { margin: 5px 0 0; color: var(--muted); font-size: 12px; line-height: 1.6; }

.profile-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 20px; }
.field { display: grid; gap: 7px; color: var(--fg); font-size: 12px; font-weight: 550; }
.field .composer-shell { display: block; width: 100%; min-height: 44px; }

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-height: 66px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}
.setting-row .select-shell { flex: 0 0 auto; width: 150px; }
.setting-row > div { display: grid; gap: 4px; min-width: 0; }
.setting-row strong { font-size: 13px; font-weight: 550; }
.setting-row span { color: var(--muted); font-size: 12px; line-height: 1.5; }

.data-actions { display: flex; align-items: center; gap: 12px; margin-top: 20px; }
.save-status { margin: 13px 0 0; color: var(--muted); font-size: 12px; }
.settings-section[data-od-id="appearance-settings"] .setting-row { border-bottom: 0; }
.data-section { padding-bottom: 0; }

@media (max-width: 700px) {
  .settings-content { width: 100%; padding: 28px 0 40px; }
  .settings-head { padding-top: 0; }
  .profile-grid { grid-template-columns: 1fr; }
  .setting-row { min-height: 70px; }
  .setting-row .select-shell { width: 132px; }
  .data-actions { align-items: flex-start; flex-direction: column; gap: 6px; }
  .secondary-button,
  .text-button { min-height: 44px; }
  .settings-section { padding: 20px 0; }
}
```

### 帮助页：FAQ + 联系卡片

```css
.help-intro { max-width: 680px; padding: clamp(8px, 3vh, 40px) 0 26px; }
.faq-section { max-width: 860px; }
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 0 0 13px;
  border-bottom: 1px solid var(--border);
  color: var(--fg);
  font-size: 13px;
  font-weight: 550;
}
.result-count { color: var(--muted); font-size: 12px; font-weight: 400; white-space: nowrap; }

@media (max-width: 700px) {
  .help-intro { padding-top: 0; }
  .faq-question { min-height: 60px; white-space: normal; }
  .faq-answer { padding-right: 22px; }
}
```

## 变体说明

| 变体 | 内容区宽度 | 列数 | 断点 |
| --- | --- | --- | --- |
| 使用帮助 | `min(1020px,100%)` | 1 | ≤700px 单列 + padding 收敛 |
| 支持事项 | `min(1080px,100%)` | 2（≤900px 变窄列并隐藏分类列；≤700px 变 1） | 900 / 700 |
| 最近记录 | `min(1020px,100%)` | 1（head 在 ≤800px 变纵向） | 800 / 700 |
| 设置 | `min(900px,100%)` | 1（表单网格 ≤700px 变 1 列） | 700 |

| 状态 | 规则 |
| --- | --- |
| **搜索中** | 列表实时过滤；有值才显示"清空"按钮。 |
| **筛选中** | `.category-tab.is-active` 反白；`aria-pressed` 同步。 |
| **空态** | `.empty-state`（标题 + 说明 + 重置/入口按钮）。 |
| **保存反馈**（设置页） | `.save-status` 显示"已保存"，1800ms 后消失（`aria-live="polite"`）。 |
| **主题** | 全变量，无额外处理。 |

## 使用注意事项

**可访问性**
- `aria-labelledby` 指向 `h1` 的 id，让列表区域有可访问名称。
- 搜索框 `<label>` 包住外壳 + `.sr-only` 文案；"清空"按钮有 `aria-label`。
- 空态里的按钮要能真正重置状态（清 query **和**分类）。
- 设置页的保存反馈用 `aria-live="polite"`。

**性能**
- 过滤全部是前端 computed，数据量小（<50 条）无需防抖。
- 页面滚动容器上的 `scrollbar-width/scrollbar-color` 让滚动条跟主题一致。

**常见误用**
1. **页面根元素写 `overflow: hidden`** —— 内容超一屏被裁。见 `app-shell.md`。
2. **`grid-template-columns` 用了 `1fr` 而不是 `minmax(0, 1fr)`** —— 长内容会把
   列撑破，省略号失效。**所有可伸缩列都要 `minmax(0, 1fr)`。**
3. **移动端忘记放开 `overflow`** —— 双滚动条。
4. **设置页 `.setting-row` 用 `justify-content: space-between` 但不给左侧
   `min-width: 0`** —— 长文案会把下拉挤出去。
5. **H1 的 `line-height` 不统一** —— 帮助/事项/记录用 1.28，设置页用 1.3，
   新增页面照这两个值取。
