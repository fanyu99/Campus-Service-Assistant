# 输入框

## 设计思路

**解决的问题**：首页、对话页、搜索框、表单字段各写一套 `border + box-shadow +
:focus` 样式，四处的聚焦反馈长得都不一样，改一次要改四个文件。

**视觉与交互意图**：把"长什么样"抽成一个全局外壳 `.composer-shell`，复刻首页
composer 的四层结构：

| 层 | 元素 | 作用 |
| --- | --- | --- |
| 底 | 元素自身 `background` | 双层渐变：`padding-box` 填 `--surface`，`border-box` 画 110° 渐变描边 |
| 网格 | `::before` | 16×16 动态网格 + 135° 对角渐隐；hover 时开始漂移，focus 时加速 |
| 流光 | `::after` | 2px 宽的边框流光（`padding:2px` + xor 掩膜切出边带），focus 时提速 |
| 内容 | 子元素 | 自动 `position:relative; z-index:1` |

**关键约定**：页面 scoped 样式**只负责布局**（display / flex / gap / padding /
min-height），绝不重复写 border / background / border-radius / focus 样式。

**适用场景**：所有输入框、搜索框、表单字段，以及下拉选择的触发器。

## 完整代码

### 全局外壳（放 `theme.css`）

```css
/* ── 统一动态输入框外壳：完整复刻「首页 / 我的对话」composer 的
      渐变描边 + 动态网格 + 边框流光 + 主题色光晕 ── */
.composer-shell {
  --composer-shell-radius: 24px;
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border: 1px solid transparent;
  border-radius: var(--composer-shell-radius);
  background:
    linear-gradient(var(--surface), var(--surface)) padding-box,
    linear-gradient(110deg, var(--border), color-mix(in srgb, var(--accent) 42%, var(--border)), var(--border)) border-box;
  box-shadow: 0 7px 18px color-mix(in srgb, var(--fg) 4%, transparent);
  transition: box-shadow .24s ease, background .3s ease, transform .24s ease;
}

.composer-shell::before {
  content: '';
  position: absolute;
  z-index: 0;
  inset: 0;
  opacity: .74;
  pointer-events: none;
  background-image:
    linear-gradient(to right, var(--composer-grid-line) 1px, transparent 1px),
    linear-gradient(to bottom, var(--composer-grid-line) 1px, transparent 1px),
    linear-gradient(135deg, transparent 0 53%, var(--composer-grid-fade) 78%);
  background-size: 16px 16px, 16px 16px, 100% 100%;
  background-position: center;
  transition: opacity .24s ease, filter .3s ease;
}

.composer-shell::after {
  content: '';
  position: absolute;
  z-index: 2;
  inset: 0;
  padding: 2px;
  border-radius: inherit;
  opacity: 0;
  pointer-events: none;
  background: linear-gradient(105deg, transparent 15%, var(--composer-flow-hot) 40%, var(--composer-flow-bright) 50%, var(--accent) 60%, transparent 85%);
  background-size: 220% 100%;
  background-position: 100% 50%;
  filter: drop-shadow(0 0 6px var(--composer-hover-glow));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  transition: opacity .2s ease, filter .2s ease;
}

/* 子元素自动抬到网格之上（.sr-only 除外，它不能参与层叠） */
.composer-shell > *:not(.sr-only) { position: relative; z-index: 1; }

.composer-shell:hover {
  background:
    linear-gradient(var(--surface), var(--surface)) padding-box,
    linear-gradient(118deg, var(--accent-hover), var(--accent), var(--accent-hover)) border-box;
  box-shadow:
    0 0 0 2px var(--composer-hover-glow),
    0 0 22px var(--composer-hover-glow),
    0 14px 30px color-mix(in srgb, var(--composer-hover-glow) 60%, transparent);
}
.composer-shell:hover::before {
  opacity: 1;
  filter: saturate(1.25) contrast(1.08);
  animation: composer-shell-grid-drift 2.6s linear infinite;
}
.composer-shell:hover::after {
  opacity: .9;
  animation: composer-shell-border-flow 2s linear infinite;
}

.composer-shell:focus-within {
  background:
    linear-gradient(var(--surface), var(--surface)) padding-box,
    linear-gradient(125deg, var(--composer-flow-hot), var(--composer-flow-bright), var(--accent)) border-box;
  box-shadow:
    0 0 0 3px var(--composer-focus-glow),
    0 0 30px var(--composer-focus-glow),
    0 16px 38px color-mix(in srgb, var(--composer-focus-glow) 64%, transparent);
}
.composer-shell:focus-within::before {
  opacity: 1;
  filter: saturate(1.4) contrast(1.12);
  animation: composer-shell-grid-drift 1.35s linear infinite;
}
.composer-shell:focus-within::after {
  opacity: 1;
  filter: drop-shadow(0 0 10px var(--composer-focus-glow));
  animation: composer-shell-border-flow 1.05s linear infinite;
}

/* 校验失败：只换描边渐变色，圆角/间距/阴影不动 */
.composer-shell.is-invalid {
  background:
    linear-gradient(var(--surface), var(--surface)) padding-box,
    linear-gradient(125deg, var(--danger), color-mix(in srgb, var(--danger) 42%, var(--border)), var(--danger)) border-box;
}

@keyframes composer-shell-grid-drift {
  from { background-position: 0 0, 0 0, center; }
  to   { background-position: 32px 32px, 32px 32px, center; }
}
@keyframes composer-shell-border-flow {
  from { background-position: 100% 50%; }
  to   { background-position: -120% 50%; }
}

@media (prefers-reduced-motion: reduce) {
  .composer-shell,
  .composer-shell::before,
  .composer-shell::after { transition: none; animation: none; }
}
```

### 用法 A：主 composer（首页 / 对话页）

页面 scoped 只写布局与内部元素：

```css
.composer {
  position: relative;
  isolation: isolate;
  display: flex;
  flex-direction: column;
  gap: 9px;
  overflow: hidden;
  padding: 14px 14px 11px;
  /* 下面三行由 .composer-shell 提供，页面里不要再写：
     border / border-radius / background / box-shadow */
}

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

.composer-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-left: 4px;
}
.composer-hint {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
.composer-msg { margin: 0; min-height: 19px; font-size: 12px; line-height: 1.6; color: var(--fg); text-align: center; }
.composer-msg.is-error { color: var(--danger); }

/* 键盘焦点环：:has() 保证只在真正的键盘聚焦时出现，鼠标点击不触发 */
.composer:has(:focus-visible) { outline: 2.5px solid var(--fg); outline-offset: 2px; }

@media (max-width: 700px) {
  .composer { padding: 13px 13px 11px; border-radius: 22px; }
  .composer textarea { font-size: 16px; }   /* 低于 16px 会触发 iOS 自动缩放 */
}
@media (max-height: 660px) and (min-width: 701px) {
  .composer { padding: 10px 12px 8px; border-radius: 20px; }
  .composer-msg { min-height: 0; }
}
```

```vue
<form class="composer composer-shell" :class="{ 'is-invalid': isError }" novalidate @submit.prevent="submitQuestion">
  <label class="sr-only" for="askInput">输入你想咨询的校园事务</label>
  <textarea
    id="askInput" ref="inputEl" v-model="question" rows="1" maxlength="200"
    autocomplete="off" placeholder="试试问：学生证丢了怎么补办？"
    @input="onInput" @keydown="onKeydown"
  ></textarea>
  <div class="composer-foot">
    <p class="composer-hint">Enter 发送 · Shift + Enter 换行</p>
    <button type="submit" class="send spark-button"><span>开始咨询</span><svg class="i" aria-hidden="true"><use href="#i-arrow-up"/></svg></button>
  </div>
</form>
<p class="composer-msg" :class="{ 'is-error': isError }" role="status" aria-live="polite">{{ status }}</p>
```

自适应高度与输入法安全：

```ts
const MAX_H = 104
function autoGrow() {
  const el = inputEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, MAX_H) + 'px'
}

function onKeydown(e: KeyboardEvent) {
  // isComposing：中文输入法选词回车不应触发提交
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    submitQuestion()
  }
}
```

### 用法 B：搜索框（帮助页 / 事项页 / 记录页）

```vue
<label class="help-search composer-shell" data-od-id="help-search">
  <svg class="i" aria-hidden="true"><use href="#i-search" /></svg>
  <span class="sr-only">搜索帮助内容</span>
  <input v-model="query" type="search" placeholder="搜索问题或关键词" autocomplete="off" />
  <button v-if="query" type="button" class="clear-search" aria-label="清空" @click="query = ''">清空</button>
</label>
```

```css
.help-search,
.history-search,
.search-field {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 48px;              /* 帮助页 48 / 记录页 46 / 事项页 46 */
  padding: 0 13px;
}
.help-search .i { width: 16px; height: 16px; color: var(--muted); }
.help-search input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--fg);
  font: 400 13px/1.5 var(--font-body);
}
.help-search input::placeholder { color: var(--muted); }
.clear-search {
  flex: 0 0 auto;
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
}
.clear-search:hover { color: var(--fg); }
```

### 用法 C：设置页表单字段

```vue
<label class="field">
  <span>显示名称</span>
  <span class="composer-shell"><input v-model="displayName" type="text" autocomplete="name" /></span>
</label>
```

```css
.field {
  display: grid;
  gap: 7px;
  color: var(--fg);
  font-size: 12px;
  font-weight: 550;
}
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
```

## 变体说明

| 变体 | 规则 |
| --- | --- |
| **尺寸** | composer：padding `14px 14px 11px`，圆角 24px（移动端 22px、矮视口 20px），textarea `min-height:25px / max-height:104px`。搜索框：`min-height` 46~48px，圆角 24px（默认）。表单字段：`min-height` 44px。 |
| **状态 · rest** | 网格 `opacity:.74` 静止、流光 `opacity:0`、阴影 `0 7px 18px`。 |
| **状态 · hover** | 描边渐变转成 `118deg accent-hover→accent→accent-hover`；网格 `opacity:1` + 漂移 **2.6s**；流光 `opacity:.9` + 流动 **2s**；阴影三层。 |
| **状态 · focus-within** | 描边渐变转成 `125deg flow-hot→flow-bright→accent`；网格漂移提速到 **1.35s**；流光提速到 **1.05s** 且 `opacity:1`；阴影 `0 0 0 3px` 聚焦环。 |
| **状态 · invalid** | `.is-invalid`：描边渐变换成 `--danger` 系。**不改圆角与阴影。** |
| **状态 · disabled** | 目前未实现。需要时把 `--composer-shell-radius` 保持、`opacity:.6` + 移除 hover/focus 动画。 |
| **主题** | 全部走 `--surface` / `--border` / `--accent*` / `--composer-*`，明暗自动跟随。 |
| **移动端** | 圆角 22px、textarea 字号 16px（防 iOS 缩放）、按钮 44px。 |
| **圆角覆盖** | 用 `--composer-shell-radius`：`.composer-shell { --composer-shell-radius: 20px }`。 |

## 使用注意事项

**可访问性**
- **必须有可见或 `.sr-only` 的 `<label>`**。搜索框用 `<label>` 包住整个外壳 +
  内部 `<span class="sr-only">`，这样点击外壳任意位置都能聚焦输入框。
- 状态提示用 `role="status" aria-live="polite"`，错误文案同时把外壳标成
  `.is-invalid`（视觉）与文本（读屏）双通道。
- `.composer:has(:focus-visible)` 的 outline 是**给整个外壳**的键盘焦点环；
  不要写成 `:focus-within`（鼠标点击也会亮，很吵）。
- 清空按钮的 `aria-label` 与可见文本都写"清空"（"清除"留给设置页的破坏性动作）。

**性能**
- 网格漂移与流光都是 `background-position` 动画（会触发重绘）。**只在 hover /
  focus 时启动**，静止态完全不动——这是刻意的，避免页面上常驻多个重绘源。
- 外壳是 `overflow: hidden`，内部任何 `abs` 光效都会被裁。需要溢出光效就套到
  外层容器。

**常见误用**
1. **在页面 scoped 里重写 `border` / `background` / `border-radius`** —— 会盖掉
   双层渐变（`padding-box` + `border-box`），描边直接消失。
2. **给内部 input 加 `border: 1px solid`** —— 出现"框中框"。内部一律 `border: 0`。
3. **忘记 `isComposing` 判断** —— 中文输入法选词时按回车会误提交。
4. **max-height 不设** —— 长文本会把 composer 顶到屏幕外。首页 104px、
   对话页 132px，两者不同是有意的（对话页消息区更宽）。
5. **把 `.composer-shell` 用在非输入类容器上**（比如卡片）—— 它自带
   `overflow:hidden` 和双层背景，套在卡片上会把内部滚动条和光效都吃掉。
6. 旧类 `.dynamic-input-shell` **已废弃**，被 `.composer-shell` 取代，不要再用。
