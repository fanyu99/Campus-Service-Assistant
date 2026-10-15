# 反馈：加载、空态、错误、徽标、气泡

## 三点跳动加载指示器

### 设计思路

**解决的问题**：转圈 spinner 在这套"暖色 + 手作感"的界面里太工业；纯文字"加载中"
又太弱。

**视觉与交互意图**：三个小球依次跳起、落地（附带模糊影子同步缩放），像水滴弹跳。
用**同一套结构 + 一组私有变量**同时产出两种尺寸——消息气泡里的大号（12px 球）和
按钮里的小号（6px 球），靠 `--loader-*` 变量切换，不写第二份 keyframes。

**适用场景**：助手正在生成回答、按钮正在提交。

### 完整代码

```css
.loading-animation {
  --loader-ball-size: 12px;
  --loader-track-width: 62px;
  --loader-height: 31px;
  --loader-rest-top: 0px;
  --loader-floor-top: 25px;
  --loader-shadow-width: 13px;
  --loader-shadow-top: 27px;
  position: relative;
  z-index: 1;
  width: var(--loader-track-width);
  height: var(--loader-height);
}

.loading-ball,
.loading-shadow {
  position: absolute;
  display: block;
  transform-origin: 50%;
}

.loading-ball {
  top: var(--loader-floor-top);
  left: 4px;
  width: var(--loader-ball-size);
  height: var(--loader-ball-size);
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 3px 8px color-mix(in srgb, var(--accent) 26%, transparent);
  animation: loader-ball .5s alternate infinite ease;
}
.loading-ball:nth-child(2) { left: 25px; animation-delay: .2s; }
.loading-ball:nth-child(3) { left: 46px; animation-delay: .3s; }

.loading-shadow {
  top: var(--loader-shadow-top);
  left: 3px;
  z-index: -1;
  width: var(--loader-shadow-width);
  height: 4px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 44%, transparent);
  filter: blur(1px);
  animation: loader-shadow .5s alternate infinite ease;
}
.loading-shadow:nth-child(5) { left: 24px; animation-delay: .2s; }
.loading-shadow:nth-child(6) { left: 45px; animation-delay: .3s; }

@keyframes loader-ball {
  0% {
    top: var(--loader-floor-top);
    height: 5px;
    border-radius: 50px 50px 25px 25px;
    transform: scaleX(1.7);      /* 落地压扁 */
  }
  40% {
    height: var(--loader-ball-size);
    border-radius: 50%;
    transform: scaleX(1);
  }
  100% { top: var(--loader-rest-top); }   /* 弹到最高点 */
}

@keyframes loader-shadow {
  0% { transform: scaleX(1.5); }
  40% { transform: scaleX(1); opacity: .7; }
  100% { transform: scaleX(.2); opacity: .4; }   /* 球飞高 → 影子变小变淡 */
}

/* ── 小号变体：按钮内 ──────────────────────────────────────────────── */
.loading-animation--button {
  --loader-ball-size: 6px;
  --loader-track-width: 30px;
  --loader-height: 17px;
  --loader-floor-top: 11px;
  --loader-shadow-top: 14px;
  --loader-shadow-width: 7px;
}
.loading-animation--button .loading-ball { left: 1px; }
.loading-animation--button .loading-ball:nth-child(2) { left: 12px; }
.loading-animation--button .loading-ball:nth-child(3) { left: 23px; }
.loading-animation--button .loading-shadow { left: 0; height: 2px; }
.loading-animation--button .loading-shadow:nth-child(5) { left: 11px; }
.loading-animation--button .loading-shadow:nth-child(6) { left: 22px; }
```

```vue
<!-- 气泡内（大号） -->
<div class="typing-bubble" role="status" aria-label="校园助手正在生成回答">
  <div class="loading-animation loading-animation--assistant" aria-hidden="true">
    <span class="loading-ball" /><span class="loading-ball" /><span class="loading-ball" />
    <span class="loading-shadow" /><span class="loading-shadow" /><span class="loading-shadow" />
  </div>
</div>

<!-- 按钮内（小号）：必须配 .sr-only 文本 + disabled -->
<button type="submit" class="send spark-button" :class="{ 'is-loading': isSending }" :disabled="isSending">
  <span v-if="isSending" class="sr-only">正在发送</span>
  <span v-if="isSending" class="loading-animation loading-animation--button" aria-hidden="true">
    <span class="loading-ball" /><span class="loading-ball" /><span class="loading-ball" />
    <span class="loading-shadow" /><span class="loading-shadow" /><span class="loading-shadow" />
  </span>
  <template v-else>
    <span>开始咨询</span><svg class="i" aria-hidden="true"><use href="#i-arrow-up" /></svg>
  </template>
</button>
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| **尺寸** | `--assistant`（默认）：球 12px、轨道 62×31；`--button`：球 6px、轨道 30×17。**只改变量，不改 keyframes。** |
| **节奏** | `.5s alternate infinite ease`，三球延迟 `0 / .2s / .3s`。`alternate` 让它弹上去再落回来，形成完整一跳。 |
| **主题** | 球 `--accent`、影子 `--accent` 44%，自动跟随。 |
| **禁用/暂停** | 不用禁用态——它只在"正在发生"时出现，结束即卸载。 |
| **reduced-motion** | `animation: none`，球固定在最高点（`top: var(--loader-rest-top)`、恢复原尺寸），影子 `scaleX(.7) opacity:.5`。**是"不动的静态指示器"，不是空白。** |

### 使用注意事项

**可访问性**
- 外层容器要有 `role="status"` + `aria-label`（如"校园助手正在生成回答"）；
  内部动画 `aria-hidden="true"`。
- 按钮内必须配 `.sr-only` 文本（"正在发送"）。

**性能**
- 动的是 `top` / `height` / `transform`——**会触发布局**。元素极小（3 个球），
  可接受；**不要在长列表里每一行都放一个**。
- `filter: blur(1px)` 的影子有 3 个，若同屏出现十几个实例会明显掉帧。当前只有
  1~2 处，OK。

**常见误用**
1. 写第二份 keyframes 做小号 —— 用变量。
2. 只放动画不加 `role="status"` —— 读屏用户完全不知道在加载。
3. `isSending` 时不加 `disabled` —— 连点重复提交。

---

## 空态

### 设计思路

空态不是"什么都没有"，而是**给下一步动作**：一句话说明现状 + 一句解释 +
一个入口按钮。三个页面（事项 / 记录 / 帮助）共用同一结构，只有文案不同。

### 完整代码

```css
.empty-state {
  padding: 46px 0;                    /* 帮助页 44px */
  border-bottom: 1px solid var(--border);
}
.empty-state h2 { margin: 0; font-size: 16px; font-weight: 550; }
.empty-state p { margin: 8px 0 16px; color: var(--muted); font-size: 13px; line-height: 1.7; }
```

```vue
<div v-else class="empty-state" data-od-id="services-empty">
  <h2>没有匹配的事项</h2>
  <p>换个更短的关键词，或把分类切回“全部”。</p>
  <button type="button" class="text-action spark-button" @click="query = ''; activeCategory = '全部'">重置筛选</button>
</div>
```

对话页的空态是另一种（撑满消息区居中）：

```css
.empty-state {                        /* 对话页变体 */
  display: grid;
  place-items: center;
  align-content: center;
  flex: 1;
  min-height: 230px;
  color: var(--muted);
  text-align: center;
}
.empty-state p { margin: 0; color: var(--muted); font-size: 13px; }
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| **列表型**（事项/记录/帮助） | 左对齐，`padding: 46px 0` + 底部分隔线；标题 16px + 说明 13px + 动作按钮。 |
| **撑满型**（对话页） | `flex:1` + 居中，`min-height:230px`，两行文字，无按钮（下方就有输入框）。 |
| **主题** | `--fg` 标题 + `--muted` 说明，自动跟随。 |

### 使用注意事项

- 空态的**动作按钮一定要能真正改变状态**（"重置筛选"要把 query 和分类都清掉），
  否则是假出口。
- 文案写"下一步能做什么"，不要只写"暂无数据"。

---

## 错误提示

### 设计思路

错误用**两个通道**同时表达：① 输入框外壳 `.is-invalid`（描边转 `--danger`）；
② 输入框下方一行 `role="status"` 文本。只做视觉或只做文本都不够。

### 完整代码

```css
.composer-msg {
  margin: 0;
  min-height: 19px;          /* 预留一行高度，出现/消失时不抖动 */
  font-size: 12px;
  line-height: 1.6;
  color: var(--fg);
  text-align: center;
}
.composer-msg.is-error { color: var(--danger); }
```

```vue
<form class="composer composer-shell" :class="{ 'is-invalid': isError }" novalidate @submit.prevent="submitQuestion">…</form>
<p class="composer-msg" :class="{ 'is-error': isError }" role="status" aria-live="polite">{{ status }}</p>
```

```ts
function submitQuestion() {
  const text = question.value.trim()
  if (!text || isSending.value) {
    if (!text) {
      status.value = '先写下你要咨询的事，再发送'
      isError.value = true
      inputEl.value?.focus()
    }
    return
  }
  isError.value = false
  …
}
function onInput() { autoGrow(); clearStatus() }   // 一输入就清掉错误
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| **触发** | 提交空内容、提交被拒绝。 |
| **清除** | 用户一开始输入就清（`onInput` → `clearStatus()`），不要等下次提交。 |
| **尺寸** | `min-height: 19px` 保底，避免文案出现时把下方内容顶动。矮视口下可降到 0。 |
| **主题** | `--danger` 明暗两套已定义。 |

### 使用注意事项

- `min-height` 保底是防抖动的**关键**，别省。
- 错误文本用 `role="status" aria-live="polite"`；**不要**用 `aria-live="assertive"`
  （会打断读屏）。
- 错误发生后把焦点送回输入框（`inputEl.focus()`）。

---

## 徽标与状态点

### 完整代码

```css
/* 未读小红点（顶铃铛 / 侧栏铃铛） */
.dot-badge {
  position: absolute;
  top: 7px;
  right: 8px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
}

/* 侧栏状态点（绿色：在线/已更新） */
.status-dot {
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: oklch(60% .13 148);
}

/* 记录状态标签 */
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

/* kicker 小标签 */
.notification-kicker {
  display: inline-flex;
  padding: 5px 9px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .14em;
}
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| 尺寸 | 圆点 6px；状态标签 `padding: 4px 7px` / 11px / 圆角 6px；kicker `padding: 5px 9px` / 10px / 999px。 |
| 颜色 | 未读 `--accent`；状态点语义绿 `oklch(60% .13 148)`；待处理 `--accent-soft` 底 + `--accent` 字。 |
| 主题 | 语义绿是唯一没做 token 的颜色（只有一处用）。若要复用请补一个 `--success`。 |

### 使用注意事项

- 未读点消失时**必须同步改 `aria-label` 与 `data-tip`**（"通知" → "通知（无未读）"），
  否则读屏用户不知道状态变了。
- 圆点是纯视觉的，**信息必须在文字里也能读到**。

---

## Tooltip（CSS-only）

### 设计思路

不引组件、不写 JS：用 `data-tip` 属性 + 两个伪元素（箭头 + 气泡）实现，hover
与 focus-visible 都触发。用在图标按钮和侧栏导航上。

### 完整代码

```css
.icon-btn[data-tip]::before,
.icon-btn[data-tip]::after {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  transition: opacity .22s ease, transform .22s cubic-bezier(.2, .8, .2, 1);
  z-index: 20;
}

.icon-btn[data-tip]::before {            /* 箭头 */
  content: '';
  top: calc(100% + 4px);
  right: 12px;
  width: 9px;
  height: 9px;
  border-top: 1px solid var(--tooltip-border);
  border-left: 1px solid var(--tooltip-border);
  background: var(--tooltip-bg);
  transform: translateY(5px) rotate(45deg);
}

.icon-btn[data-tip]::after {             /* 气泡 */
  content: attr(data-tip);
  top: calc(100% + 8px);
  right: 0;
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
  transform: translateY(5px) scale(.96);
}

.icon-btn[data-tip]:hover::before,
.icon-btn[data-tip]:focus-visible::before { opacity: 1; transform: translateY(0) rotate(45deg); }
.icon-btn[data-tip]:hover::after,
.icon-btn[data-tip]:focus-visible::after { opacity: 1; transform: translateY(0) scale(1); }

@media (hover: none) {
  .icon-btn[data-tip]::before,
  .icon-btn[data-tip]::after { display: none; }
}
```

侧栏导航的版本把气泡放在**右侧居中**（`left: calc(100% + 10px)`），移动端改成
**下方居中**——见 `components/navigation.md`。

### 变体说明

| 变体 | 规则 |
| --- | --- |
| 位置 | 图标按钮：下方右对齐；侧栏导航：右侧居中；侧栏导航（移动端）：下方居中。 |
| 动画 | `opacity` + `transform`（`translateY(5px)` → 0，`scale(.96)` → 1），220ms，曲线 `cubic-bezier(.2,.8,.2,1)`。 |
| 触屏 | `@media (hover: none)` 下 `display: none`。 |
| 主题 | `--tooltip-*` 全套，自动跟随。 |

### 使用注意事项

- `content: attr(data-tip)` 决定了**文案只能通过 `data-tip` 属性传**，不能放插槽。
- **`aria-label` 与 `data-tip` 必须一致**，否则鼠标用户和读屏用户看到两种说法。
- tooltip 不能承载"必要信息"（触屏上会消失），只能是对已有标签的补充。

---

## 角色消息气泡

### 设计思路

首页角色与通知弹窗角色共用**同一个视觉**（底色 / 描边 / 圆角 / 小箭头 / 弹出动画），
但摆放位置完全不同。解决办法：视觉放全局 `.character-bubble`，位置交给使用方通过
两个自定义属性声明。

### 完整代码

```css
/* ── 角色消息气泡（首页「托腮角色」与通知弹窗角色共用）───────────────────
   视觉样式（底色 / 描边 / 圆角 / 小箭头 / 弹出动画）在此统一，
   摆放位置由使用方决定，通过两个自定义属性传入：
     --bubble-rest     静止时的 transform（如 translateX(-18%) / translateX(-50%)）
     --bubble-arrow-x  小箭头在气泡内的水平位置，默认 50%（居中）            */
.character-bubble {
  position: absolute;
  z-index: 3;
  width: max-content;
  max-width: min(300px, 76vw);
  padding: 10px 15px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--surface);
  color: var(--fg);
  font-size: 13px;
  line-height: 1.5;
  text-align: center;
  box-shadow: 0 10px 24px color-mix(in srgb, var(--fg) 8%, transparent);
  transform: var(--bubble-rest, translateX(0));
  animation: bubble-pop .24s ease both;
}

.character-bubble::after {
  content: "";
  position: absolute;
  left: var(--bubble-arrow-x, 50%);
  bottom: -7px;
  width: 12px;
  height: 12px;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  transform: translateX(-50%) rotate(45deg);
}

@keyframes bubble-pop {
  from { opacity: 0; transform: var(--bubble-rest, translateX(0)) translateY(4px) scale(.98); }
  to   { opacity: 1; transform: var(--bubble-rest, translateX(0)); }
}

@media (prefers-reduced-motion: reduce) { .character-bubble { animation: none; } }
```

```css
/* 首页：贴在角色左上偏右，箭头指向角色头部 */
.character-bubble {
  left: 72%;
  bottom: calc(100% - 4px);
  --bubble-rest: translateX(-18%);
  --bubble-arrow-x: 22%;
}

/* 通知弹窗：居中对齐角色，贴在角色头顶上方 6px，箭头垂直向下 */
.notification-bubble { --bubble-rest: translateX(-50%); left: 50%; bottom: calc(100% + 6px); }
```

跨组件共享台词状态：

```ts
// composables/useCharacterBubble.ts
import { ref } from 'vue'
const hoverMessage = ref<string | null>(null)

export function useCharacterBubble() {
  function setHoverMessage(message: string) { hoverMessage.value = message }
  function clearHoverMessage() { hoverMessage.value = null }
  return { hoverMessage, setHoverMessage, clearHoverMessage }
}
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| **位置** | 用 `--bubble-rest`（静止 transform）与 `--bubble-arrow-x`（箭头横向位置）声明。 |
| **尺寸** | `max-width: min(300px, 76vw)`；`padding: 10px 15px`；圆角 18px。 |
| **动画** | `bubble-pop .24s ease both`（`opacity` + `translateY(4px) scale(.98)` → 静止态）。**注意 keyframes 里也要带上 `--bubble-rest`**，否则动画结束时会跳到 `translateX(0)`。 |
| **移动端** | 首页要把 `.home-reveal` 提到 `z-index: 7`、气泡 `z-index: 8`，否则会被移动端 sticky 导航栏遮住。 |
| **主题** | `--surface` / `--border` / `--fg`，自动跟随。 |
| **reduced-motion** | `animation: none`（直接显示，不弹出）。 |

### 使用注意事项

- **文案保持 ≤15 字**。气泡 `max-width` 有限，超了会换行并把气泡顶出容器。
- 台词统一"傲娇可爱"语气；首页 `hoverMessages` 与通知的 `noticeGreetings` 各自维护。
- `role="status" aria-live="polite"`（**不要 assertive**：hover 时台词会频繁变化）。
- 气泡是 `position: absolute`，父级必须 `position: relative`。
