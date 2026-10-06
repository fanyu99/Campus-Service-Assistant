# 下拉选择（AppSelect）

## 设计思路

**解决的问题**：原生 `<select>` 的**弹层由浏览器绘制**，弹层里"当前选中项"的高亮色
完全无法用 CSS 定制——`option:checked`、`option:hover`、`accent-color` 实测全部被
忽略。深色主题下会出现"浅色文字压在浅蓝高亮上"的低对比度问题（**实测 2.96:1**，
远低于 AA 的 4.5:1）。

**视觉与交互意图**：
- 触发器外套全局 `.composer-shell` → 与页面其他输入框**视觉完全一致**。
- 弹层复用浮层变量（`--tooltip-bg` / `--tooltip-border` / `--tooltip-shadow`）→ 与
  tooltip 同一套玻璃质感，深浅主题自动跟随。
- 选中项靠"`--accent-soft` 底 + 强调色对勾"区分，**文字仍用 `--fg`**（因为
  `--accent` 压在 `--accent-soft` 上深色主题只有 3.58:1；改用 `--fg` 后是
  深色 11.3:1 / 浅色 15.7:1）。

**适用场景**：设置页主题选择，以及任何需要在受限空间里做单选的场合。

## 完整代码

完整 SFC 见 `examples/AppSelect.vue`，核心如下。

### 模板

```vue
<div ref="rootEl" class="app-select">
  <span class="composer-shell select-shell">
    <button
      ref="triggerEl" type="button" class="select-trigger"
      role="combobox" aria-haspopup="listbox" :aria-label="label"
      :aria-expanded="open" :aria-controls="listId"
      :aria-activedescendant="open ? optionId(activeIndex) : undefined"
      @click="toggle" @keydown="onTriggerKeydown"
    >
      <span class="select-value">{{ modelValue }}</span>
      <svg class="i select-chev" :class="{ 'is-open': open }" aria-hidden="true"><use href="#i-chev" /></svg>
    </button>
  </span>

  <Transition name="select-pop">
    <ul v-if="open" :id="listId" ref="listEl" class="select-panel" role="listbox" :aria-label="label">
      <li
        v-for="(option, index) in options" :id="optionId(index)" :key="option"
        role="option" :aria-selected="option === modelValue"
        class="select-option"
        :class="{ 'is-active': index === activeIndex, 'is-selected': option === modelValue }"
        @click="choose(option)" @mouseenter="activeIndex = index"
      >
        <span class="select-option-text">{{ option }}</span>
        <svg v-if="option === modelValue" class="i select-check" aria-hidden="true"><use href="#i-check" /></svg>
      </li>
    </ul>
  </Transition>
</div>
```

### 脚本（含完整键盘操作）

```ts
const props = defineProps<{
  modelValue: T
  options: readonly T[]
  /** 无障碍名称，同时用于 listbox 的 aria-label */
  label: string
}>()
const emit = defineEmits<{ (e: 'update:modelValue', value: T): void }>()

const uid = useId()
const listId = `select-list-${uid}`
const optionId = (index: number) => `select-option-${uid}-${index}`

const rootEl = ref<HTMLElement | null>(null)
const triggerEl = ref<HTMLButtonElement | null>(null)
const listEl = ref<HTMLElement | null>(null)
const open = ref(false)
const activeIndex = ref(0)

function openList() {
  const current = props.options.indexOf(props.modelValue)
  activeIndex.value = current < 0 ? 0 : current
  open.value = true
}
function closeList(returnFocus = false) {
  if (!open.value) return
  open.value = false
  if (returnFocus) triggerEl.value?.focus()
}
function toggle() { open.value ? closeList() : openList() }
function choose(option: T) { emit('update:modelValue', option); closeList(true) }
function moveActive(step: number) {
  const count = props.options.length
  if (!count) return
  activeIndex.value = (activeIndex.value + step + count) % count
}

function onTriggerKeydown(event: KeyboardEvent) {
  const key = event.key
  if (!open.value) {
    if (key === 'ArrowDown' || key === 'ArrowUp' || key === 'Enter' || key === ' ') {
      event.preventDefault()
      openList()
    }
    return
  }
  switch (key) {
    case 'ArrowDown': event.preventDefault(); moveActive(1); break
    case 'ArrowUp':   event.preventDefault(); moveActive(-1); break
    case 'Home':      event.preventDefault(); activeIndex.value = 0; break
    case 'End':       event.preventDefault(); activeIndex.value = props.options.length - 1; break
    case 'Enter':
    case ' ':         event.preventDefault(); choose(props.options[activeIndex.value]); break
    case 'Escape':    event.preventDefault(); closeList(); break
    case 'Tab':       closeList(); break
  }
}

/** 点面板外部关闭；用 pointerdown 以便早于 click，避免「点触发器先被关掉再被打开」 */
function onDocumentPointerDown(event: PointerEvent) {
  if (!rootEl.value?.contains(event.target as Node)) closeList()
}

watch(open, (isOpen) => {
  if (isOpen) {
    document.addEventListener('pointerdown', onDocumentPointerDown)
    nextTick(() => {
      listEl.value?.querySelector<HTMLElement>('.is-active')?.scrollIntoView({ block: 'nearest' })
    })
  } else {
    document.removeEventListener('pointerdown', onDocumentPointerDown)
  }
})

onBeforeUnmount(() => document.removeEventListener('pointerdown', onDocumentPointerDown))

/** 给父组件留个抓手：主题切换的圆形扩散要以这个触发器按钮为圆心 */
defineExpose({ triggerEl })
```

### 样式

```css
.app-select { position: relative; display: block; }
.app-select .composer-shell { display: block; width: 100%; }

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  min-height: 42px;
  padding: 0 12px;
  border: 0;
  background: transparent;
  color: var(--fg);
  font: 400 13px/1.5 var(--font-body);
  text-align: left;
  cursor: pointer;
}
/* 触发器被 .composer-shell 的 overflow:hidden 包着，外描边会被裁掉，
   所以用负 offset 画在内侧 */
.select-trigger:focus-visible { outline: 2px solid var(--fg); outline-offset: -3px; border-radius: 20px; }

.select-value { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.select-chev { width: 15px; height: 15px; color: var(--muted); transform: rotate(90deg); transition: transform .2s ease, color .2s ease; }
.select-trigger[aria-expanded='true'] .select-chev { transform: rotate(-90deg); color: var(--accent); }

/* 弹层：与全站浮层（tooltip）同一套变量，深浅色主题自动跟随 */
.select-panel {
  position: absolute;
  z-index: 30;
  top: calc(100% + 6px);
  right: 0;
  min-width: 100%;
  max-height: min(280px, 50vh);
  overflow-y: auto;
  margin: 0;
  padding: 5px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--tooltip-bg);
  box-shadow: var(--tooltip-shadow);
  list-style: none;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

.select-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 36px;
  padding: 8px 11px;
  border-radius: 10px;
  color: var(--fg);
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
  transition: background .14s ease, color .14s ease;
}
/* 选中项靠「accent-soft 底色 + 强调色对勾」区分；文字仍用 --fg 而不是 --accent，
   因为 accent 压在 accent-soft 上深色主题只有 3.58:1，低于正文 4.5:1 的 AA 门槛。 */
.select-option.is-selected { background: var(--accent-soft); color: var(--fg); font-weight: 600; }
.select-option.is-active { background: var(--row-hover); }
/* 选中项同时是光标项时保持 accent-soft，别被 row-hover 盖掉选中感 */
.select-option.is-selected.is-active { background: var(--accent-soft); }
.select-check { width: 14px; height: 14px; flex: 0 0 auto; color: var(--accent); }

.select-pop-enter-active,
.select-pop-leave-active { transition: opacity .16s ease, transform .16s ease; }
.select-pop-enter-from,
.select-pop-leave-to { opacity: 0; transform: translateY(-6px) scale(.98); }

/* 触屏尺寸：与站内其他移动端控件统一到 44px 点击目标 */
@media (max-width: 700px) {
  .select-trigger,
  .select-option { min-height: 44px; }
}
@media (prefers-reduced-motion: reduce) {
  .select-panel, .select-chev { transition: none; }
  .select-pop-enter-active, .select-pop-leave-active { transition: none; }
}
```

### 调用（设置页主题）

```vue
<AppSelect
  ref="themeSelect" :model-value="theme" :options="themeOptions"
  label="选择主题" class="select-shell" data-od-id="theme-select"
  @update:model-value="onThemeChange"
/>
```

```ts
const themeOptions: readonly ThemeOption[] = ['跟随系统', '浅色', '深色']
const themeSelect = useTemplateRef<{ triggerEl: HTMLButtonElement | null }>('themeSelect')

/**
 * 主题不能直接 v-model 到 theme 上：切换要从触点按钮张开一个圆扩散铺满整页，
 * 所以先量出按钮中心当圆心，再交给 setTheme（见 motion/theme-ripple.md）。
 */
function onThemeChange(next: ThemeOption) {
  const rect = themeSelect.value?.triggerEl?.getBoundingClientRect()
  setTheme(next, rect ? { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 } : undefined)
}
```

## 变体说明

| 变体 | 规则 |
| --- | --- |
| **尺寸** | 触发器 `min-height: 42px`（设置页用 44px 外壳）；选项 36px；移动端两者都到 44px。宽度由使用方给（设置页 `.setting-row .select-shell { width: 150px }`，窄屏 132px）。 |
| **状态 · 关闭** | 触发器显示当前值 + 右箭头（`rotate(90deg)` 指向下）。 |
| **状态 · 展开** | 箭头 `rotate(-90deg)` + 变 `--accent`；弹层从上往下 6px 处淡入下滑（`opacity + translateY(-6px) scale(.98)`，160ms）。 |
| **状态 · 键盘光标** | `.is-active`（`--row-hover`）；与 `.is-selected` 同时成立时**保持 accent-soft**。 |
| **状态 · 选中** | `.is-selected`（`--accent-soft` 底 + 600 字重 + 对勾）。 |
| **状态 · 禁用/加载** | 组件未实现。需要时在触发器上加 `disabled` 并移除 hover 动画。 |
| **主题** | 触发器走 `--fg`；弹层走 `--tooltip-*`；选中底走 `--accent-soft`。明暗自动跟随，**深色下不再有原生 select 的对比度问题**。 |
| **移动端** | 44px 点击目标；弹层方向仍向下（选项少，不需要翻转）。 |

## 使用注意事项

**可访问性**
- 完整 combobox / listbox 语义：`role="combobox"` + `aria-haspopup="listbox"` +
  `aria-expanded` + `aria-controls` + `aria-activedescendant`；选项 `role="option"` +
  `aria-selected`。
- 键盘：`↓/↑` 移动、`Home/End` 跳首尾、`Enter/Space` 选中、`Esc` 关闭、`Tab` 关闭并
  移焦。**关闭态按 `↓/↑/Enter/Space` 都要能打开**。
- 选中后要 `triggerEl.focus()` 把焦点还回触发器。
- 组件是 `generic="T extends string"`——**选项必须是字符串**。需要对象选项时另写
  一个组件，不要改成 `any`。

**性能**
- 外部点击用 `pointerdown` 而不是 `click`：早于 click 触发，避免"点触发器时被
  document 的 handler 关掉、又被自身 click 打开"的抖动。
- 监听必须在 `onBeforeUnmount` 里解绑（当前实现已做）。

**常见误用**
1. **改回原生 `<select>`** —— 深色主题下选中项对比度 2.96:1，必崩。
2. **给 `.select-trigger` 用正的 `outline-offset`** —— 触发器在
   `overflow:hidden` 的外壳里，外描边会被裁掉。用 `outline-offset: -3px`。
3. **选中项文字用 `--accent`** —— 深色下 3.58:1 不过 AA。用 `--fg` + 对勾。
4. **忘了 `defineExpose({ triggerEl })`** —— 主题切换拿不到圆心，扩散动画会退化成
   直接切换（不报错，但效果没了）。
5. 弹层 `max-height` 写死 px —— 小屏上会顶出视口。用 `min(280px, 50vh)`。
