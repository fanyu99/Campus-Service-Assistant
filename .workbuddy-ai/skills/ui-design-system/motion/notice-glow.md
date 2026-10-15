# 通知卡片三层光效

## 设计思路

**解决的问题**：想让卡片"发光"，但卡片自己是 `overflow: auto` 的滚动容器——
光效挂在里面一定被裁掉，而且 `abs` 子元素会跟着内容一起滚走。

**视觉与交互意图**：在卡片**外面**包一层 `.notification-card-frame`，三层光效
全挂 frame 上（从下往上）：

```
.notification-card-ring   旋转渐变描边环（z-index:2，压在卡片之上，mask 只留 2px 边）
.notification-card        ← 不透明卡片（z-index:1），盖住光的中心
  frame::after            底部呼吸背光（径向渐变，opacity+scale+blur 三联动）
  frame::before           环境弥散光（conic 双瓣，只呼吸 opacity）
```

背光与环境光在卡片**之下**，卡片不透明底自然盖住中心，只露出外圈 →
形成"光晕从卡片后面扩散出来"的观感。

**适用边界**：这套东西只在通知弹窗用。**不要复制到普通卡片上**——它很贵。

## 完整代码

```css
.notification-card-frame { position: relative; z-index: 1; width: 100%; isolation: isolate; }

/* ── ① 环境弥散光 ──────────────────────────────────────────────────────
   内容恒定不变（没有随时间的渐变角度变化），
   所以 blur 只会被栅格化一次，动画只走 opacity → 全程合成层，不重绘。 */
.notification-card-frame::before {
  content: '';
  position: absolute;
  z-index: 0;
  inset: -18px;
  border-radius: calc(var(--notice-card-radius) + 18px);
  background: conic-gradient(from 208deg,
    transparent 0deg,
    var(--notice-aura-a) 58deg,
    transparent 148deg,
    var(--notice-aura-b) 232deg,
    transparent 322deg);
  filter: blur(26px);
  opacity: .6;
  pointer-events: none;
  animation: notice-aura-breathe 7.6s ease-in-out infinite;
}

/* ── ② 底部呼吸背光 ────────────────────────────────────────────────────
   盒子比卡片宽 4%，向下溢出 70px，
   亮芯落在卡片下沿附近（渐变 66% 处），只有露在卡片外的部分可见。
   --notice-glow-fade 是同色相 alpha=0，避免插值出灰边。 */
.notification-card-frame::after {
  content: '';
  position: absolute;
  z-index: 0;
  left: -4%;
  right: -4%;
  bottom: -70px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(62% 100% at 50% 66%,
    var(--notice-glow-core) 0%,
    var(--notice-glow-halo) 42%,
    var(--notice-glow-fade) 76%);
  filter: blur(30px);
  opacity: .72;
  pointer-events: none;
  transform-origin: 50% 100%;
  animation: notice-glow-breathe 6.4s ease-in-out infinite;
  will-change: opacity, transform, filter;
}

/* ── ③ 旋转渐变描边环 ──────────────────────────────────────────────────
   外层 inset:-2px / padding:2px + xor 掩膜 = 只保留 2px 宽的边带
   （与 .composer-shell::after 同一套掩膜写法）。
   内层 ::before 是一个 300% 见方的 conic 渐变方块，用 transform:rotate 旋转 ——
   纯合成层动画，不重绘渐变；旋转的是方块而不是渐变角度，
   所以掩膜（在父层坐标系里）不会跟着转，边带形状始终贴合卡片圆角。
   300% 是安全余量：只要卡片高宽比 < 2.83，方块任意角度都能盖满父层。
   overflow:hidden 把栅格范围收在卡片尺寸内，避免按 9 倍面积去栅格。 */
.notification-card-ring {
  position: absolute;
  z-index: 2;
  inset: -2px;
  padding: 2px;
  border-radius: calc(var(--notice-card-radius) + 2px);
  overflow: hidden;
  pointer-events: none;
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  mask-composite: exclude;
}
.notification-card-ring::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 300%;
  aspect-ratio: 1;
  background:
    conic-gradient(from 0deg,                       /* 拖尾瓣 */
      var(--notice-ring-fade) 0deg,
      var(--notice-ring-tail) 30deg,
      var(--notice-ring-fade) 118deg,
      var(--notice-ring-fade) 360deg),
    conic-gradient(from 0deg,                       /* 彗星头瓣 */
      var(--notice-ring-fade) 0deg,
      var(--notice-ring-hot) 50deg,
      var(--notice-ring-bright) 68deg,
      var(--notice-ring-hot) 88deg,
      var(--notice-ring-fade) 132deg,
      var(--notice-ring-fade) 360deg);
  transform: translate(-50%, -50%) rotate(0deg);
  will-change: transform;
  animation: notice-ring-spin 6.5s linear infinite;
}

@keyframes notice-ring-spin {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to   { transform: translate(-50%, -50%) rotate(360deg); }
}
@keyframes notice-aura-breathe {
  0%, 100% { opacity: .44; }
  50% { opacity: .76; }
}
@keyframes notice-glow-breathe {
  0%, 100% { opacity: .52; filter: blur(24px); transform: scale(.94, 1); }
  50%      { opacity: .88; filter: blur(38px); transform: scale(1.04, 1.12); }
}

/* ── 窄屏收敛：避免糊满整屏，也省掉不必要的模糊面积 ───────────────────── */
@media (max-width: 700px) {
  .notification-card-frame::before { inset: -12px; border-radius: calc(var(--notice-card-radius) + 12px); filter: blur(18px); }
  .notification-card-frame::after { left: -2%; right: -2%; bottom: -52px; height: 160px; filter: blur(24px); }
  @keyframes notice-glow-breathe {
    0%, 100% { opacity: .52; filter: blur(20px); transform: scale(.94, 1); }
    50%      { opacity: .86; filter: blur(30px); transform: scale(1.03, 1.1); }
  }
}

/* ── 无障碍：关闭全部光效动画，但保留静止的描边环与背光 ────────────────── */
@media (prefers-reduced-motion: reduce) {
  .notification-card-frame::before,
  .notification-card-frame::after,
  .notification-card-ring::before { animation: none; }
  .notification-card-frame::after { opacity: .6; filter: blur(28px); transform: none; }
}
```

### 依赖的 token

```css
/* 浅色 */
--notice-ring-fade: oklch(56% .18 34 / 0);      /* 同色相 alpha=0，不是 transparent */
--notice-ring-tail: oklch(56% .18 34 / .32);
--notice-ring-hot: oklch(56% .20 32 / .96);
--notice-ring-bright: oklch(70% .18 52 / 1);    /* 彗星头；浅色底不能用高 L，会糊进白底 */
--notice-aura-a: oklch(60% .17 36 / .28);
--notice-aura-b: oklch(78% .13 62 / .20);
--notice-glow-core: oklch(58% .18 34 / .55);
--notice-glow-halo: oklch(70% .14 48 / .32);
--notice-glow-fade: oklch(74% .12 52 / 0);
/* 深色：亮端提到 L 89%，环与背光整体降 alpha（深底上同样 alpha 观感更糊） */
```

## 变体说明

| 变体 | 规则 |
| --- | --- |
| **尺寸** | 卡片圆角 `--notice-card-radius: 32px`（窄屏 25px）；环 `inset:-2px` + `padding:2px` + 圆角 = 卡片半径 + 2px；环境光 `inset:-18px` + 圆角 = 半径 + 18px（窄屏 -12px）；背光左右各溢出 4%（窄屏 2%）、向下 70px（窄屏 52px）、高 200px（窄屏 160px）。 |
| **状态** | 只有"弹窗可见"一种状态——打开即播，关闭即卸载（三层随 DOM 一起消失，无退出动画）。 |
| **主题** | 明暗各一套 `--notice-*`；深色把环的亮端推到 `L 89%`，并降整体 alpha。 |
| **窄屏** | 见上：`inset` 收窄、`blur` 减小、呼吸幅度同步减小（`scale(1.03,1.1)` 而非 `1.04,1.12`）。 |
| **禁用/加载** | 不适用（光效不承载状态）。 |
| **reduced-motion** | 三条动画全 `none`，但**环与背光仍可见**（背光固定 `opacity:.6; blur(28px); transform:none`）。是"不动"，不是"消失"。 |

### 三条动画的参数

| 层 | 时长 | 曲线 | 动的属性 |
| --- | --- | --- | --- |
| 描边环 | 6.5s | `linear` | `transform: rotate` |
| 底部背光 | 6.4s | `ease-in-out` | `opacity` + `filter: blur` + `transform: scale` |
| 环境弥散光 | 7.6s | `ease-in-out` | 仅 `opacity` |

**实测过的观感**（改参数时对照）：
- 彗星头屏幕角度随 rotate 线性推进：0→68°、90→158°、180→248°、247→315°。
- 环带最饱和像素：浅色 `(235,108,6)` / 深色 `(238,112,72)`。
- 底部背光从卡片下沿 `(212,68,23)` 向外 60px 衰减到 `(210,182,176)`。
- 窄屏 390px 无横向溢出。

## 使用注意事项

**可访问性**
- reduced-motion 下**保留静止的光效**——用户明确要求"视觉仍完整，只是不动"。
- 三层都要 `pointer-events: none`：实测否则会挡住关闭按钮与列表 hover。
- 光效不承载任何信息，纯装饰，不需要 `aria`。

**性能（这套东西很贵，别滥用）**
- 环境弥散光 `::before` 的 conic-gradient **内容恒定** → blur 只栅格化一次，
  动画只走 `opacity`（合成层）。**不要改成动态渐变角度**，否则每帧重绘。
- 描边环转的是 `transform: rotate`（合成层），**不是** conic 的角度。用
  `@property` 动角度会逐帧重绘渐变，实测明显掉帧。
- 描边环的 `300%` 见方是安全余量（卡片高宽比 < 2.83 都盖得住），必须配
  `overflow: hidden` 把栅格范围收在卡片尺寸内——**否则会按 9 倍面积去栅格**。
- 底部背光是三层里最贵的（`opacity` + `blur` + `scale` 三联动 + 大面积模糊）。
  它带了 `will-change: opacity, transform, filter`，窄屏下把 blur 从 30px 降到 24px。
- **只在一个元素上跑**。不要给列表里的每张卡片都加这套。

**常见误用**
1. **把光效挂进 `.notification-card` 内部** —— 一定被 `overflow: auto` 裁掉，
   abs 子元素还会跟着内容滚走。
2. **用 `@property` 动 conic 的 `from` 角度** —— 逐帧重绘，掉帧。转
   `transform: rotate`。
3. **渐变端点用 `transparent`** —— 它是 `rgba(0,0,0,0)`，插值途中出现灰边。
   必须用同色相 alpha=0 的 `--notice-ring-fade` / `--notice-glow-fade`。
4. **浅色底把 `--notice-ring-bright` 提到高 L** —— 会糊进白底看不见。取 L70
   （深色才推到 L89）。
5. **去掉 `overflow: hidden`** —— 300% 的方块会按 9 倍面积栅格，内存和帧率都崩。
6. **reduced-motion 下 `display: none`** —— 用户要求保留视觉。
