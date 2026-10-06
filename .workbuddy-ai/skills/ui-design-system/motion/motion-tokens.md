# 动效 Token 总表

## 设计思路

**解决的问题**：缓动曲线和时长随手取，同一个"hover 反馈"在不同组件上是
160ms / 180ms / 220ms / 240ms 四种速度，整体节奏散掉。

**视觉与交互意图**：动效分**三类职责**，各自的时长区间与曲线族不同：

| 职责 | 时长区间 | 曲线族 | 触发条件 |
| --- | --- | --- | --- |
| **微反馈**（hover / 颜色 / 焦点） | 140–240ms | `ease` 或 `cubic-bezier(.2,0,0,1)` | 指针 / 键盘 |
| **转场**（入场 / 路由 / 弹层） | 160–460ms | `cubic-bezier(.2,0,0,1)` | 挂载 / 卸载 |
| **氛围**（循环光效 / 呼吸 / 流动） | 1.05s–7.6s | `linear` 或 `ease-in-out` | 常驻（或 hover/focus 期间） |

**核心规则**：
1. 曲线只能从下表选。**不要自创 cubic-bezier。**
2. 每一条动画都要有 `prefers-reduced-motion` 分支（见 `reduced-motion.md`）。
3. 循环动画**只在需要时启动**（hover / focus / 可见），静止态不留常驻重绘源。

## 完整代码

### 曲线清单（四选一）

```css
:root {
  /* ① 标准减速：微反馈与转场的主力。起步快、尾部极缓，
        适合「元素到达目标位置后稳定停下」的一切场合 */
  --ease-standard: cubic-bezier(.2, 0, 0, 1);

  /* ② 强调回弹：动效按钮专用。尾部略带回弹感（1 超过终点再回来），
        用于「圆形膨胀 + 圆角收拢」这种需要弹性的形变 */
  --ease-emphasis: cubic-bezier(.23, 1, .32, 1);

  /* ③ 浮层弹出：tooltip / 下拉弹层。比 ① 多一点过冲，
        让气泡有「顶出来」的手感 */
  --ease-pop: cubic-bezier(.2, .8, .2, 1);

  /* ④ 水面涟漪：主题切换专用，拟合 r ∝ √t
        （实测进度 25%→.49、50%→.71、75%→.86：全程都在走、越走越慢，
        没有前段猛冲后段拖沓的断层） */
  --ease-ripple: cubic-bezier(.2, .7, .7, .8);
  --ease-ripple-pond: cubic-bezier(.18, .8, .42, .92);

  /* 最简单的线性：只有「匀速旋转 / 匀速流动」用 */
  --ease-linear: linear;
  --ease-breathe: ease-in-out;
}
```

> 注意：项目当前**还没有**把这些曲线抽成变量（散落在各组件的字面值里）。
> 新代码优先用变量；改到旧组件时顺手替换。

### 时长清单

```css
:root {
  /* ── 微反馈 ─────────────────────────────────────────────────────── */
  --dur-instant: .14s;    /* 下拉选项 hover */
  --dur-fast: .16s;       /* ★ 主力：背景/颜色/边框类 hover（列表行、导航、tab、图标按钮） */
  --dur-control: .18s;    /* 实心按钮背景与位移、FAQ 箭头旋转 */
  --dur-feedback: .22s;   /* tooltip 弹出、spark 按钮掠光位移 */
  --dur-shell: .24s;      /* composer 外壳的 box-shadow / background / transform */
  --dur-glow: .3s;        /* composer 网格的 filter 过渡 */

  /* ── 转场 ───────────────────────────────────────────────────────── */
  --dur-popover: .16s;    /* 下拉弹层进出 */
  --dur-route: 180ms;     /* 路由切换 */
  --dur-bubble: .24s;     /* 角色气泡弹出 */
  --dur-entrance: 460ms;  /* 首页三区块入场 */

  /* ── 氛围（循环）───────────────────────────────────────────────── */
  --dur-border-flow-focus: 1.05s;   /* composer 边框流光 · focus */
  --dur-grid-drift-focus: 1.35s;    /* composer 网格漂移 · focus */
  --dur-border-flow-hover: 2s;      /* composer 边框流光 · hover */
  --dur-grid-drift-hover: 2.6s;     /* composer 网格漂移 · hover；品牌标呼吸 */
  --dur-ring-spin: 6.5s;            /* 通知卡描边环旋转 */
  --dur-glow-breathe: 6.4s;         /* 通知卡底部背光呼吸 */
  --dur-aura-breathe: 7.6s;         /* 通知卡环境弥散光呼吸 */
  --dur-loader: .5s;                /* 加载球一跳（alternate） */

  /* ── 主题切换 ───────────────────────────────────────────────────── */
  --theme-ripple-duration: 1200ms;        /* 大圆扩散 */
  --theme-ripple-pond-duration: 800ms;    /* 触点水滴涟漪（比大圆短、起步更冲） */
}
```

### 全站动效索引（改哪一条之前先看它属于哪一类）

| 动效 | 元素 | 属性 | 时长 | 曲线 | 触发 | 循环 |
| --- | --- | --- | --- | --- | --- | --- |
| 列表行 hover | `.row` / `.recent-row` / `.service-item` | `background` | .16s | `ease` | hover | ✗ |
| 导航项 hover | `.nav-item` | `background,color,transform` | .16s | `ease` | hover | ✗ |
| 图标按钮 hover | `.icon-btn` | `background,color` | .16s | `ease` | hover | ✗ |
| 分类 tab | `.category-tab` | `background,color,border-color` | .16s | `ease` | hover | ✗ |
| 链接按钮 | `.link-btn` / `.text-action` | `color` | .16s | `ease` | hover | ✗ |
| 下拉选项 hover | `.select-option` | `background,color` | .14s | `ease` | hover | ✗ |
| 实心按钮 | `.send` | `background,transform` | .18s | `ease` | hover/active | ✗ |
| FAQ 箭头 | `.faq-question .i` | `transform` | .18s | `ease` | 展开 | ✗ |
| 下拉箭头 | `.select-chev` | `transform,color` | .2s | `ease` | 展开 | ✗ |
| spark 掠光位移 | `.spark-button::before` | `transform` | .55s | `ease` | hover/focus | ✗ |
| spark 其余 | `.spark-button` | `transform,box-shadow,filter` | .22s | `ease` | hover/focus/active | ✗ |
| tooltip | `[data-tip]::before/::after` | `opacity,transform` | .22s | `.2,.8,.2,1` | hover/focus-visible | ✗ |
| 下拉弹层 | `.select-pop-*` | `opacity,transform` | .16s | `ease` | 挂载/卸载 | ✗ |
| composer 外壳 | `.composer-shell` | `box-shadow,background,transform` | .24s | `ease` | hover/focus | ✗ |
| composer 网格 filter | `.composer-shell::before` | `opacity,filter` | .24s / .3s | `ease` | hover/focus | ✗ |
| composer 流光 | `.composer-shell::after` | `opacity,filter` | .2s | `ease` | hover/focus | ✗ |
| **网格漂移** | `.composer-shell::before` | `background-position` | 2.6s / 1.35s | `linear` | hover / focus | ✓ |
| **边框流光** | `.composer-shell::after` | `background-position` | 2s / 1.05s | `linear` | hover / focus | ✓ |
| 角色气泡弹出 | `.character-bubble` | `opacity,transform` | .24s | `ease` | 挂载 | ✗ |
| 路由切换 | `.route-*` | `opacity,transform` | 180ms | `.2,0,0,1` | 路由变更 | ✗ |
| 首页入场 | `.home-reveal *` | `opacity,transform` | 460ms（+55/105ms 错峰） | `.2,0,0,1` | 挂载 | ✗ |
| 品牌标呼吸 | `.brand-mark` | `filter,transform` | 2.6s | `ease-in-out` | 常驻 | ✓ |
| 加载球 | `.loading-ball` | `top,height,transform` | .5s alternate | `ease` | 加载中 | ✓ |
| 加载影 | `.loading-shadow` | `transform,opacity` | .5s alternate | `ease` | 加载中 | ✓ |
| 描边环旋转 | `.notification-card-ring::before` | `transform` | 6.5s | `linear` | 弹窗可见 | ✓ |
| 底部背光呼吸 | `.notification-card-frame::after` | `opacity,filter,transform` | 6.4s | `ease-in-out` | 弹窗可见 | ✓ |
| 环境光呼吸 | `.notification-card-frame::before` | `opacity` | 7.6s | `ease-in-out` | 弹窗可见 | ✓ |
| **主题扩散（大圆）** | `::view-transition-new(root)` | `clip-path` | 1200ms | `.2,.7,.7,.8` | 换主题 | ✗ |
| **主题波峰环** | `::view-transition-new(theme-ripple)` | `--theme-ripple-r` | 1200ms | `.2,.7,.7,.8` | 换主题 | ✗ |
| **主题水滴涟漪** | `::view-transition-new(theme-ripple-pond)` | `transform: scale` | 800ms | `.18,.8,.42,.92` | 换主题 | ✗ |
| 眼神跟随 | `.ch-iris` | `--gx/--gy`（JS 写） | 帧级 ×0.15 | 线性插值 | 指针移动 / 触屏环绕 | ✓ |

## 变体说明

### 触发条件矩阵

| 触发 | 允许的动效 | 禁止 |
| --- | --- | --- |
| **hover** | 颜色/背景（.16s）、composer 的循环流光（只在 hover 期间） | 位移超过 4px、缩放超过 1.05 |
| **focus-visible** | 与 hover **完全相同**的反馈 + 全局 outline | 只写 hover 不写 focus |
| **active** | `transform`（`translateY` 回位 / `scale(.95~.98)`） | 改阴影（会和 hover 叠出怪效果） |
| **挂载 / 卸载** | `opacity` + `transform`（≤460ms） | `height` / `margin` 动画（会抖） |
| **常驻氛围** | 只动 `transform` / `opacity`；渐变内容必须恒定 | 动态渐变角度、`width/height`、大面积 `filter: blur` 变化 |
| **换主题** | View Transitions 圆形扩散 | 直接切换（除非不可扩散） |

### 三档降级

| 环境 | 行为 |
| --- | --- |
| `prefers-reduced-motion: reduce` | 所有**微反馈与转场** `transition: none`；所有**循环** `animation: none`；但视觉状态保留（hover 颜色照样变、环照样在，只是不动）。 |
| `document.hidden` | 粒子引擎停 rAF（见 `foundations/page-background.md`）。 |
| 触屏（`hover: none`） | tooltip 隐藏；眼神跟随改成缓慢环绕。 |

### 主题

动效参数**不随主题变化**（时长与曲线在明暗下完全一致），只有颜色 token 变。

## 使用注意事项

**可访问性**
- 任何新增动画都要配 `prefers-reduced-motion: reduce` 分支，且降级后**视觉完整**
  （是"不动"，不是"消失"）。
- 循环动画超过 5s 一轮才不会让人分心（当前最快的是 2.6s 的品牌标呼吸，它是
  32px 的小元素，可接受）。
- 闪烁类动画（频率 >3Hz）会诱发光敏癫痫——全站没有，新增也不要加。

**性能**
- **能用 `transform` / `opacity` 就不用别的**。当前有三处刻意的例外，都有注释：
  - `.animated-button .circle` 动 `width/height`（元素小、数量少）
  - `.loading-ball` 动 `top/height`（只有 3 个球）
  - `.composer-shell` 的循环动 `background-position`（只在 hover/focus 期间）
- **不要用 `@property` 动渐变角度** —— 逐帧重绘渐变。旋转请用
  `transform: rotate` 转整个方块（见 `notice-glow.md`）。
- `will-change` 只加在真正长动画的三层上（描边环、背光、路由过渡的 active 期）。

**常见误用**
1. **自创缓动曲线** —— 从上表挑。
2. **hover 规则只写 `:hover` 不写 `:focus-visible`** —— 键盘用户拿不到反馈。
   全站现有组件都是两者并列，新增必须照做。
3. **把 `opacity` 和半径塞进同一组 keyframes** —— 中间那几档会把半径插值切成
   多段、每段各走一次缓动，两层会脱节（见 `theme-ripple.md`）。
4. **`transition: all`** —— 会连带动画掉不该动的属性。`.animated-button` 用了
   `all` 是因为它要动圆角 + 阴影 + 颜色，属有意；其他地方写具体属性。
5. **循环动画在静止态也跑** —— 页面上常驻多个重绘源会整体掉帧。
