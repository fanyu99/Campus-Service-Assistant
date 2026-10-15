# 按钮

## 总览：什么时候用哪一类

| 类 | 类名 | 用途 | 出现位置 |
| --- | --- | --- | --- |
| 实心主按钮 | `.send` | 表单提交、对话发送 | 首页 / 对话页 composer |
| 光扫主按钮 | `.spark-button` | 强调色实心 + 掠光，用于"开始咨询""保存修改"等 | 事项行、记录行、设置页、空态 |
| 动效描边按钮 | `.animated-button` | 次要/引导动作、建议 chips、导航 CTA | 首页建议、对话页建议、帮助页 |
| 次级按钮 | `.secondary-button` | 与实心主按钮并列的次要动作 | 设置页"保存修改" |
| 文本按钮 | `.text-button` / `.text-action` | 低优先级或危险动作 | 设置页"清除…"、空态"重置筛选" |
| 图标按钮 | `.icon-btn` | 顶栏 / 侧栏的纯图标操作 | 通知铃铛 |
| 分类 tab | `.category-tab` / `.filter-tab` | 筛选组（不是按钮，是切换组） | 帮助页、事项页、记录页 |

**选择原则**：一个视图里**最多一个实心/光扫主按钮**；其余全部降级为描边或文本。

---

## `.spark-button` —— 光扫强调按钮（全局类）

### 设计思路

**解决的问题**：实心强调按钮在静止时太"死"，需要一个低成本的、不依赖 JS 的
活跃感。

**视觉与交互意图**：静止是强调色胶囊；hover / focus 时一道白色高光从左侧掠到右侧
（`::before` 的 `translateX(-65%) → 65%`），同时整体上浮 2px、阴影加深并长出
4px 的同色聚焦环。掠光只有一次，不循环——它是"响应"，不是"招手"。

**适用场景**：任何需要强调的实心动作。它是**全局类**，定义在 `theme.css`，
任何组件直接加 class 即可。

### 完整代码

```css
/* ── 输入框内部旋转射线：覆盖网格但位于文字与操作区之后 ────────────────── */
.spark-button {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border: 1px solid transparent !important;
  border-radius: 999px !important;
  background:
    linear-gradient(var(--accent), var(--accent)) padding-box,
    linear-gradient(120deg, var(--accent-hover), var(--composer-flow-bright), var(--accent)) border-box !important;
  color: var(--page-bg) !important;
  box-shadow: 0 8px 18px color-mix(in srgb, var(--accent) 24%, transparent);
  transition: transform .22s ease, box-shadow .22s ease, filter .22s ease;
}

.spark-button::before {
  content: '';
  position: absolute;
  z-index: -1;
  inset: 0;
  background:
    radial-gradient(circle at 22% 0%, color-mix(in srgb, #fff 36%, transparent), transparent 42%),
    linear-gradient(110deg, transparent 15%, color-mix(in srgb, #fff 26%, transparent) 50%, transparent 85%);
  opacity: 0;
  transform: translateX(-65%);
  transition: opacity .22s ease, transform .55s ease;
}

.spark-button:hover,
.spark-button:focus-visible {
  transform: translateY(-2px);
  filter: saturate(1.12);
  box-shadow:
    0 11px 28px color-mix(in srgb, var(--accent) 35%, transparent),
    0 0 0 4px color-mix(in srgb, var(--accent) 15%, transparent);
}

.spark-button:hover::before,
.spark-button:focus-visible::before {
  opacity: 1;
  transform: translateX(65%);
}

.spark-button:active { transform: translateY(0) scale(.98); }

@media (prefers-reduced-motion: reduce) {
  .spark-button, .spark-button::before { transition: none; animation: none; }
}
```

用法（可以是 `<button>` 也可以是 `<RouterLink>`）：

```vue
<button type="submit" class="send spark-button" data-od-id="ask-submit">
  <span>开始咨询</span><svg class="i" aria-hidden="true"><use href="#i-arrow-up" /></svg>
</button>

<RouterLink class="service-link spark-button" :to="{ name: 'chat', query: { q: item.prompt } }">
  开始咨询<svg class="i" aria-hidden="true"><use href="#i-chev" /></svg>
</RouterLink>
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| **尺寸** | 高度由使用方给：`.send` 38px（移动端 44px）、设置页按钮 `min-height:42px`、链接型 12px 字号 + 13px 图标。圆角恒为 999px。 |
| **状态** | hover/focus-visible：上浮 2px + 掠光 + 4px 同色环；active：回位并 `scale(.98)`；disabled（对话页发送中）：`cursor: wait; opacity: .68; transform: none`，内部换成加载指示器。 |
| **加载** | 加 `.is-loading`：`gap: 0; min-width: 58px; padding-inline: 13px`，内容替换为 `.loading-animation--button`。**用 min-width 保底，不要靠改 padding 让按钮宽度跳变。** |
| **主题** | 全走 `--accent` / `--accent-hover` / `--page-bg`，明暗自动跟随。 |
| **移动端** | 高度顶到 44px。 |

### 使用注意事项

**可访问性**
- 渲染成 `<a>` / `<RouterLink>` 时必须带 `text-decoration: none`（项目里没有全局
  `a` 重置，忘了会留下下划线）。
- 加载态要把"正在发送"用 `.sr-only` 文本说出来，图标部分 `aria-hidden`。
- `!important` 是**故意的**：`.spark-button` 会被加在已经有自身样式的元素上
  （如 `.send`、`.text-action`），不用 `!important` 压不住。新增同类全局类照抄。

**性能**
- 掠光是 `transform` + `opacity`，走合成层，不影响布局。

**常见误用**
1. 在 `.spark-button` 上再写 `border-radius: 13px` —— 会被 `!important` 压回
   999px，看到的是"我明明写了却不生效"。想要方角就别用这个类。
2. 一个视图里放三个 spark 按钮 —— 强调失效。
3. 加载态只把文字换成"…"，不加 `disabled` —— 连点会重复提交。

---

## `.animated-button` —— 描边环 + 圆形填色（组件）

### 设计思路

**解决的问题**：次要动作如果用实心按钮会抢主按钮的戏，用纯文字又太弱。

**视觉与交互意图**：静止态是**透明底 + 2px 强调色描边环 + 强调色文字 + 右侧箭头**；
hover / focus-visible 时，中心一个 14px 的强调色圆点膨胀到 200px 填满整个按钮，
文字与箭头切到 `--page-bg`，圆角从 100px 收成 12px，右侧箭头滑出、左侧箭头滑入。
**圆角参与动画**（胶囊→方块）是这一类的签名动作。

**适用场景**：建议 chips、引导性 CTA（"进入我的对话"）。组件文件
`components/AnimatedButton.vue`（完整副本见 `examples/AnimatedButton.vue`）。

### 完整代码

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

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
  /* 描边环用 box-shadow 而不是 border：border 会挤压内容盒，圆角动画会跳 */
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
    /* 触屏：把高度顶到 44px 的可点区域下限 */
    min-height: 44px;
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
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| **形态** | 不传 `to` → `<button type="button">`（触发动作）；传 `to` → `<RouterLink>`（导航）。两种视觉完全一致。 |
| **尺寸** | 桌面 `padding: 7px 20px` / 13px / 600；移动端 `min-height: 44px` / `padding: 0 20px` / 13.5px。箭头 13px。 |
| **状态** | hover 与 focus-visible **共用同一套样式**（键盘用户必须看到同样的反馈）；active `scale(.95)` + 4px 环。 |
| **主题** | 描边环与文字走 `--accent`，填满后的文字走 `--page-bg`。实测对比度：浅色 5.59:1、深色 4.94:1，均过 AA。 |
| **禁用 / 加载** | 当前组件未实现。需要时加 `:disabled` 并把 `--accent` 降到 `color-mix(in srgb, var(--accent) 45%, transparent)`，同时移除 hover 规则。 |

### 使用注意事项

**可访问性**
- `text-decoration: none` 必须保留：渲染成 `<RouterLink>` 时是 `<a>`。
- 两个箭头都 `aria-hidden="true"`，可读文本只在 `.text` 里。
- hover 与 focus-visible 并列写，不要只写 hover。

**性能**
- 圆点膨胀动的是 `width/height`（会触发布局）。这是**刻意接受**的：元素很小、
  数量少（一行最多 3~4 个）。若要放到长列表里，改成 `transform: scale()` 版本。

**常见误用**
1. **去掉 `flex: 0 0 auto`** —— 按钮是 `overflow:hidden`，被 flex 压缩后窄屏上
   文字会被裁掉。对话页 chips 是 `nowrap` + 横向滚动，必须让按钮保持原宽。
2. **把文字写长** —— 实测容器 ≥587px 时一行放下（1440/1366/1280/1080/1024 均
   一行）；1200/1152/960/940/860 会折成两行。这是刻意接受的（压到 11px 以下才
   能避免，得不偿失），但**别再往上加字**。
3. **在组件里覆盖 stroke-width** —— 全站图标统一 1.7（见 `icon.md`）。
4. 旧名 `SuggestionChip.vue` 已删除，**不要再引用**。

---

## `.send` —— composer 内的实心发送按钮

### 设计思路

composer 内已经有一个强视觉的外壳（渐变描边 + 网格 + 流光），按钮必须**收敛**：
纯色实心、小圆角、只在 hover 时轻微上浮 1px。它不能跟外壳抢注意力。

### 完整代码

```css
.send {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  flex: 0 0 auto;
  height: 38px;
  padding: 0 16px;
  border-radius: 13px;
  background: var(--accent);
  color: var(--page-bg);
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  transition: background .18s ease, transform .18s ease;
}

.send .i { width: 15px; height: 15px; }   /* 不要在这里覆盖 stroke-width */

.send:hover { background: var(--accent-hover); transform: translateY(-1px); }
.send:active { transform: translateY(0); }
.send:disabled { cursor: wait; opacity: .68; transform: none; }
.send.is-loading { gap: 0; min-width: 58px; padding-inline: 13px; }

@media (max-width: 700px) {
  .send { height: 44px; padding: 0 18px; }
}
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| 尺寸 | 38px（移动端 44px） |
| 组合 | 与 `.spark-button` 叠加时（`class="send spark-button"`）掠光与上浮取 spark 的更强版本 |
| 加载 | 内部替换成 `.loading-animation--button`，`disabled` + `cursor: wait` |
| 主题 | `--accent` / `--page-bg`，自动跟随 |

### 使用注意事项

- `disabled` 时 `transform: none`——否则按压动画会在禁用态残留。
- 不要把 `.send` 单独用到 composer 之外；其他地方用 `.spark-button`。

---

## `.secondary-button` / `.text-button` / `.text-action` —— 次级与文本按钮

### 设计思路

次级按钮是"实心中性色"（`--fg` 底 + `--page-bg` 字），比强调色低一级；
文本按钮是最低优先级，hover 才变色，危险动作 hover 到 `--danger`。

### 完整代码

```css
.secondary-button {
  min-height: 42px;
  padding: 0 16px;
  border: 1px solid var(--fg);
  border-radius: 11px;
  background: var(--fg);
  color: var(--page-bg);
  font-size: 13px;
  font-weight: 550;
  white-space: nowrap;
}
.secondary-button:hover { background: var(--accent-hover); }

.text-button {
  min-height: 42px;
  padding: 0 3px;
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
}
.text-button:hover { color: var(--danger); }   /* 危险动作：hover 变红是唯一预警 */

.text-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--fg);
  font-size: 13px;
  font-weight: 550;
  text-decoration: none;
  white-space: nowrap;
}
.text-action:hover { color: var(--accent); }
.text-action .i { width: 14px; height: 14px; }

@media (max-width: 700px) {
  .secondary-button,
  .text-button { min-height: 44px; }
}
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| 尺寸 | 42px（移动端 44px） |
| 危险 | `.text-button` hover → `--danger`；设置页"清除本机保存的设置"用这个 |
| 移动端 | 设置页 `.data-actions` 在 ≤700px 变纵向排列 |

### 使用注意事项

- `.secondary-button` hover 到 `--accent-hover` 而不是 `--accent`：中性按钮变强调色
  会让人误以为它是主按钮。
- 危险动作**只靠 hover 变色是不够的**，最好配合二次确认；当前实现只是文案明确。

---

## `.icon-btn` —— 图标按钮（全局类）

### 设计思路

顶栏/侧栏的操作没有文字空间，用 34px 圆角方块 + 17px 图标，hover 时填
`--row-hover`。它自带 `data-tip` tooltip（纯 CSS，见 `navigation.md`）。

### 完整代码

```css
.icon-btn {
  position: relative;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 11px;
  color: var(--muted);
  transition: background .16s ease, color .16s ease;
}

.icon-btn .i { width: 17px; height: 17px; }

.icon-btn:hover {
  background: var(--row-hover);
  color: var(--fg);
}

/* 未读小红点 */
.dot-badge {
  position: absolute;
  top: 7px;
  right: 8px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
}
```

用法：

```vue
<button
  type="button"
  class="icon-btn"
  :aria-label="noticeRead ? '通知（无未读）' : '通知'"
  :data-tip="noticeRead ? '通知（无未读）' : '通知'"
  @click="dismissNotice"
>
  <svg class="i" aria-hidden="true"><use href="#i-bell" /></svg>
  <span v-if="!noticeRead" class="dot-badge" />
</button>
```

### 变体说明

| 变体 | 规则 |
| --- | --- |
| 尺寸 | 34×34（移动端侧栏 44×44） |
| 未读 | `.dot-badge`，点击后 `v-if` 移除并把 `aria-label` / `data-tip` 一起改成"通知（无未读）" |
| 主题 | `--muted` → hover `--fg`；底色 `--row-hover` |

### 使用注意事项

**可访问性**
- **必须有 `aria-label`**，且未读状态变化时要同步改 label（"通知" → "通知（无未读）"），
  否则读屏用户不知道红点没了。
- tooltip 在 `@media (hover: none)` 下 `display: none`——触屏没有 hover 态。

**常见误用**
- 用 `.icon-btn` 承载"重要"操作。它是**低视觉权重**的，重要操作要带文字。
