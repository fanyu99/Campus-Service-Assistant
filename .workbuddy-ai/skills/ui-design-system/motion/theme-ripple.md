# 主题切换：圆形扩散（水波涟漪）

## 设计思路

**解决的问题**：换主题如果只是瞬间变色，用户会怀疑"是不是点错了"。需要一个
能把"变化发生的位置"和"变化本身"连起来的过渡。

**视觉与交互意图**：从触点按钮（用户刚点的地方）张开一个圆铺满整页——圆内是新主题，
圆外是旧主题，圆走到哪儿就换到哪儿。圆的前沿带一圈**波峰环**，触点周围另有一簇
**水滴涟漪**（比大圆更快、只荡一波），两者叠加成"一滴水落进水里"的层次。

**实现方式**：View Transitions API。新旧主题各被拍成一张全屏快照：

- `::view-transition-new(root)` 新主题 → `clip-path` 的圆从触点向外张开
- `::view-transition-old(root)` 旧主题 → 原地不动，被圆慢慢盖住

两层都是 `fixed` 快照，真实 DOM 只换颜色、不动布局，所以**动画全程布局不变**。

**四条实测逼出来的硬约束**（踩过，别改回去）：

1. **波峰环的颜色只能由实元素提供** —— 伪元素自身的 `background`/`border`
   不会绘制，快照会整块盖住元素自身的绘制。所以 `.theme-ripple-veil` 在扩散期间
   必须是**一块纯色**，环由 `mask` 现场切出来。
2. **环不能画在实元素上** —— 元素绘制会被裁在自己的盒子里，"最远角落半径"上的
   环进不了快照，缩放到前沿时只剩远角一小段弧。所以环交给 `mask`，半径想多大都行。
3. **半径必须注册成 `<length>`**（`@property`）才能逐帧插值。未注册的自定义属性
   是离散的，帧与帧之间只会跳变。
4. **淡出必须挂在 `::view-transition-group` 上、半径挂在 `new` 上** —— 若把
   `opacity` 和半径塞进同一组 keyframes，中间那几档会把半径插值切成多段、每段
   各走一次缓动，环就和圆脱节了。

## 完整代码

### CSS（`theme.css` 的「主题切换：圆形扩散」一节）

```css
:root {
  /* 慢一档：让「渐变铺开」这件事本身被看见，而不是一闪而过 */
  --theme-ripple-duration: 1200ms;
  /* 拟合一圈水面涟漪的真实规律 r ∝ √t（实测进度 25%→.49、50%→.71、75%→.86）：
     全程都在走、越走越慢，没有前段猛冲后段拖沓的断层 */
  --theme-ripple-ease: cubic-bezier(.2, .7, .7, .8);
  /* 水滴涟漪：比大圆短、起步更冲，才有一滴水砸进水面的利落感；只荡一波 */
  --theme-ripple-pond-duration: 800ms;
  --theme-ripple-pond-ease: cubic-bezier(.18, .8, .42, .92);
}

/* 波峰环的半径：注册成 <length> 才能逐帧插值 */
@property --theme-ripple-r {
  syntax: '<length>';
  inherits: true;
  initial-value: 0px;
}

/* 两个实元素：平时全屏透明，只是 view-transition-name 的载体 */
.theme-ripple-veil { position: fixed; inset: 0; pointer-events: none; view-transition-name: theme-ripple; }
.theme-ripple-pond { position: fixed; inset: 0; pointer-events: none; view-transition-name: theme-ripple-pond; }

/* 绘制只在「扩散回调里」挂上（见 themeRipple.ts）：新快照拍的就是这一帧。
   绝不能提前挂 —— 那时页面还没被旧快照盖住，整屏纯色会闪一下。 */
html.theme-rippling-paint .theme-ripple-veil { background: var(--theme-ripple-crest); }

/* 水滴涟漪：以触点为圆心的一小簇同心波，画幅收到 130px 内，只在按钮周边。
   由内到外三层：中心柔光 → 内圈亮波 → 中/外圈淡波，靠 alpha 拉开层次。
   三层都是 3px 实心线 + 两侧 5~8px 过渡，是「细线」而不是宽带 ——
   再叠上低 alpha，整簇只留隐约一圈水痕。 */
html.theme-rippling-paint .theme-ripple-pond {
  background: radial-gradient(circle at var(--theme-ripple-x) var(--theme-ripple-y),
    var(--theme-ripple-drop-soft) 0 3px,
    transparent 14px,
    transparent 35px,
    var(--theme-ripple-drop) 38px,
    var(--theme-ripple-drop) 41px,
    transparent 47px,
    transparent 75px,
    var(--theme-ripple-drop-soft) 78px,
    var(--theme-ripple-drop-soft) 81px,
    transparent 88px,
    transparent 115px,
    var(--theme-ripple-drop-soft) 118px,
    var(--theme-ripple-drop-soft) 121px,
    transparent 129px);
}

/* 层序：两层装饰都要压在两个 root 快照之上，水滴涟漪再压在大波峰之上 */
html.theme-rippling::view-transition-group(root) { z-index: 1; }
html.theme-rippling::view-transition-group(theme-ripple) { z-index: 2; }
html.theme-rippling::view-transition-group(theme-ripple-pond) { z-index: 3; }

/* 关掉默认的淡入淡出，并强制 normal 混合：
   UA 给 ::view-transition-new 的是 plus-lighter，两层不透明快照相加会冲白整屏 */
html.theme-rippling::view-transition-old(root),
html.theme-rippling::view-transition-new(root),
html.theme-rippling::view-transition-old(theme-ripple),
html.theme-rippling::view-transition-new(theme-ripple),
html.theme-rippling::view-transition-old(theme-ripple-pond),
html.theme-rippling::view-transition-new(theme-ripple-pond) {
  mix-blend-mode: normal;
  animation: none;
}

/* 扩散圆：半径从 0 张到「触点 → 最远角落」，到 100% 时刚好盖满整页 */
html.theme-rippling::view-transition-new(root) {
  animation: theme-ripple-reveal var(--theme-ripple-duration) var(--theme-ripple-ease) both;
}
@keyframes theme-ripple-reveal {
  from { clip-path: circle(0px at var(--theme-ripple-x) var(--theme-ripple-y)); }
  to   { clip-path: circle(var(--theme-ripple-radius) at var(--theme-ripple-x) var(--theme-ripple-y)); }
}

html.theme-rippling::view-transition-old(theme-ripple) { opacity: 0; }
html.theme-rippling::view-transition-group(theme-ripple) {
  z-index: 2;
  animation: theme-ripple-crest-fade var(--theme-ripple-duration) linear both;
}
html.theme-rippling::view-transition-new(theme-ripple) {
  /* 波峰剖面：内侧一段薄雾 → 2px 实心亮带（正好盖住 clip-path 的硬边）→ 外侧拖尾光。
     位置全部以 --theme-ripple-r 为基准，随环半径一起走；
     薄雾/拖尾只用 alpha（颜色统一由实元素那块纯色决定）。 */
  -webkit-mask-image: radial-gradient(circle at var(--theme-ripple-x) var(--theme-ripple-y),
    transparent 0 calc(var(--theme-ripple-r) - 24px),
    rgb(0 0 0 / .30) calc(var(--theme-ripple-r) - 12px),
    #000 calc(var(--theme-ripple-r) - 2px),
    #000 calc(var(--theme-ripple-r) + 2px),
    rgb(0 0 0 / .24) calc(var(--theme-ripple-r) + 12px),
    transparent calc(var(--theme-ripple-r) + 32px));
  mask-image: radial-gradient(circle at var(--theme-ripple-x) var(--theme-ripple-y),
    transparent 0 calc(var(--theme-ripple-r) - 24px),
    rgb(0 0 0 / .30) calc(var(--theme-ripple-r) - 12px),
    #000 calc(var(--theme-ripple-r) - 2px),
    #000 calc(var(--theme-ripple-r) + 2px),
    rgb(0 0 0 / .24) calc(var(--theme-ripple-r) + 12px),
    transparent calc(var(--theme-ripple-r) + 32px));
  animation: theme-ripple-crest-r var(--theme-ripple-duration) var(--theme-ripple-ease) both;
}
@keyframes theme-ripple-crest-r {
  from { --theme-ripple-r: 0px; }
  to   { --theme-ripple-r: var(--theme-ripple-radius); }
}
@keyframes theme-ripple-crest-fade {
  /* 收尾淡出：此时半径已越过最远角落，环基本都在视口外了 */
  from { opacity: 1; }
  76% { opacity: 1; }
  to { opacity: 0; }
}

/* ── 水滴涟漪：整簇同心波一起 scale 放大 ────────────────────────────────
   环画在实元素上（画幅只有 140px，整个装得进元素盒子），所以这层能纯靠
   transform 放大 —— 半径与环宽同步增长，正是水波扩散的质感，而且走合成器。
   transform-origin 锁在触点上，缩放中心就是落水点。 */
html.theme-rippling::view-transition-old(theme-ripple-pond) { opacity: 0; }
html.theme-rippling::view-transition-group(theme-ripple-pond) {
  animation: theme-ripple-pond-fade var(--theme-ripple-pond-duration) linear both;
}
html.theme-rippling::view-transition-new(theme-ripple-pond) {
  transform-origin: var(--theme-ripple-x) var(--theme-ripple-y);
  animation: theme-ripple-pond-r var(--theme-ripple-pond-duration) var(--theme-ripple-pond-ease) both;
}
@keyframes theme-ripple-pond-r {
  from { transform: scale(0); }
  to   { transform: scale(1); }
}
@keyframes theme-ripple-pond-fade {
  /* 起点 scale 为 0（整簇缩成一个点，本来就看不见），所以不需要淡入；
     底色 alpha 已经很低，这里就不再额外衰减，免得叠成看不见。 */
  from { opacity: 1; }
  40% { opacity: .8; }
  to { opacity: 0; }
}

/* 无障碍：不留动画，直接换主题（JS 侧也会跳过扩散，这里兜底） */
@media (prefers-reduced-motion: reduce) {
  html.theme-rippling::view-transition-new(root),
  html.theme-rippling::view-transition-new(theme-ripple),
  html.theme-rippling::view-transition-group(theme-ripple),
  html.theme-rippling::view-transition-new(theme-ripple-pond),
  html.theme-rippling::view-transition-group(theme-ripple-pond) { animation: none; }
}
```

### JS（`composables/themeRipple.ts`）

```ts
export type RippleOrigin = { x: number; y: number }

const RIPPLE_CLASS = 'theme-rippling'      // ::view-transition-* 规则的前缀
const PAINT_CLASS = 'theme-rippling-paint' // 让实元素开始绘制

let rippleSeq = 0                          // 连续切换时只让最后一次收尾

/** 浏览器支持 + 用户没有要求减弱动效，才值得扩散 */
export function canPlayThemeRipple(): boolean {
  const doc = document as Document & { startViewTransition?: unknown }
  return typeof doc.startViewTransition === 'function'
    && !window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function playThemeRipple(commit: () => void, origin: RippleOrigin): void {
  const doc = document as Document & {
    startViewTransition?: (cb: () => void) => { finished: Promise<void> }
  }
  const startViewTransition = doc.startViewTransition
  if (!startViewTransition) { commit(); return }

  const { innerWidth: width, innerHeight: height } = window
  // 最远角落 = 水平、垂直方向都最远的那个角，所以两个方向各取 max 再合成。
  // +8px 是安全余量，保证圆一定盖过角落（否则可能留下一线没被铺到的像素）。
  const radius = Math.hypot(
    Math.max(origin.x, width - origin.x),
    Math.max(origin.y, height - origin.y),
  ) + 8

  const root = document.documentElement
  const token = (rippleSeq += 1)
  root.style.setProperty('--theme-ripple-x', `${origin.x}px`)
  root.style.setProperty('--theme-ripple-y', `${origin.y}px`)
  root.style.setProperty('--theme-ripple-radius', `${radius}px`)
  root.classList.add(RIPPLE_CLASS)

  const transition = startViewTransition.call(doc, () => {
    // 两层的颜色都跟着新主题走，所以要等 commit 之后才挂（其实两者同帧生效）
    root.classList.add(PAINT_CLASS)
    commit()
  })

  // finished 在伪元素树被拆掉之后兑现，此时收尾不会有可见的一帧
  void transition.finished.finally(() => {
    if (token !== rippleSeq) return
    root.classList.remove(RIPPLE_CLASS, PAINT_CLASS)
    root.style.removeProperty('--theme-ripple-x')
    root.style.removeProperty('--theme-ripple-y')
    root.style.removeProperty('--theme-ripple-radius')
  })
}
```

### 调用（`composables/useTheme.ts`）

```ts
export function setTheme(option: ThemeOption, origin?: RippleOrigin): void {
  if (option === theme.value) return          // 选中当前项：什么都不做，连 DOM 都不碰

  // 主题必须等扩散动画的回调再落，否则旧快照拍到的是新配色，圆就没东西可铺了
  const commit = () => { theme.value = option; paint(option) }

  if (!origin || resolveDark(option) === resolveDark(theme.value) || !canPlayThemeRipple()) {
    commit()
    return
  }
  playThemeRipple(commit, origin)
}
```

```vue
<!-- App.vue：两个载体元素，平时全屏透明 -->
<div class="theme-ripple-veil" aria-hidden="true" />
<div class="theme-ripple-pond" aria-hidden="true" />
```

```ts
// 设置页：量出按钮中心当圆心
const themeSelect = useTemplateRef<{ triggerEl: HTMLButtonElement | null }>('themeSelect')
function onThemeChange(next: ThemeOption) {
  const rect = themeSelect.value?.triggerEl?.getBoundingClientRect()
  setTheme(next, rect ? { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 } : undefined)
}
```

## 变体说明

| 变体 | 行为 |
| --- | --- |
| **选中当前项** | 直接 `return`，连 DOM 都不碰。 |
| **明暗没变**（浅色 ↔ 跟随系统且系统正好浅色） | 只更新选项，**不播动画**——不值得为"没变的样子"播动画。 |
| **有圆心 + 浏览器支持 + 未减弱动效** | 完整扩散（1200ms 大圆 + 800ms 水滴涟漪）。 |
| **无圆心**（系统主题变化） | 直接切换，不扩散。 |
| **浏览器不支持 `startViewTransition`** | 直接切换（降级）。 |
| **`prefers-reduced-motion: reduce`** | 直接切换（CSS 与 JS 双重兜底）。 |
| **连续切换** | `rippleSeq` 保证只有最后一次负责清理，前一次不会打断后一次。 |
| **主题** | `--theme-ripple-crest` / `--theme-ripple-drop*` 明暗两套：深色把亮端推到 L 84%（L70 在深底上看不见）。 |

### 波峰剖面参数

| 段落 | 位置（相对 `--theme-ripple-r`） | alpha |
| --- | --- | --- |
| 内侧透明 | `0` → `r-24px` | 0 |
| 内侧薄雾 | `r-12px` | .30 |
| **实心亮带** | `r-2px` → `r+2px` | 1（**必须不透明**：要盖住 clip-path 的硬边） |
| 外侧拖尾 | `r+12px` | .24 |
| 外侧透明 | `r+32px` | 0 |

### 水滴涟漪参数

| 圈 | 半径 | 线宽 | 颜色 |
| --- | --- | --- | --- |
| 中心柔光 | 0–3px | — | `--theme-ripple-drop-soft` |
| 内圈 | 38–41px | 3px | `--theme-ripple-drop` |
| 中圈 | 78–81px | 3px | `--theme-ripple-drop-soft` |
| 外圈 | 118–121px | 3px | `--theme-ripple-drop-soft` |

> **强度已被要求降过两轮，不要往回调**：第一版 `oklch(66% .17 40 / .82)` →
> 降到 `.36/.17` → 再降到 `.22/.10` + 3px 细线。它就是"隐约一圈水痕"。

## 使用注意事项

**可访问性**
- `prefers-reduced-motion` 下**直接换主题**（JS 侧 `canPlayThemeRipple()` 返回
  false，CSS 侧再兜一层）。
- 两个载体元素都要 `aria-hidden="true"` + `pointer-events: none`。

**性能**
- 波峰环用 `transform`-free 的 `mask` + 注册过的 `@property` 插值，
  **不重绘渐变**（颜色是纯色块，变的只是遮罩半径）。
- 水滴涟漪是纯 `transform: scale`，走合成器。
- 扩散期间**布局完全不动**（快照是 fixed 的），不会有重排。
- `finished.finally` 里做清理：此时伪元素树已拆掉，不会有可见的一帧。

**常见误用**
1. **把 `PAINT_CLASS` 提前挂** —— 页面还没被旧快照盖住，整屏纯色会闪一下。
   必须挂在 `startViewTransition` 的**回调里**。
2. **去掉 `mix-blend-mode: normal`** —— UA 默认给 `plus-lighter`，两层不透明
   快照相加会把整屏冲白。
3. **把 `opacity` 和半径写进同一组 keyframes** —— 半径插值被切成多段，
   环与圆脱节。淡出挂 `group`，半径挂 `new`。
4. **用 `circle(150%)` 之类的百分比当终点** —— 需求要的是"触点 → 最远角落"的
   真实距离，JS 里按视口算准（两个方向各取 max 再 `hypot`，+8 余量）。
5. **把 `--theme-ripple-crest` 调成半透明** —— 它要盖住 clip-path 硬边，
   半透明会在接缝处漏出旧主题一线。
6. **忘记在 `finished` 里清理三个 `--theme-ripple-*` 变量** —— 下次不扩散时
   会残留旧值（虽然不可见，但会污染 DOM）。
7. 后续若新增带 `view-transition-name` 的元素，注意这些规则都以
   `html.theme-rippling` 为前缀，**不会误伤别的过渡**——但反过来，别的过渡
   也不要复用 `theme-ripple` / `theme-ripple-pond` 这两个名字。
