# 配色体系

## 设计思路

**解决的问题**：颜色散落在各个组件里，改一处漏三处；深色主题靠临时加 `filter` 或直接
写第二套值，很快就会跟浅色脱节。

**视觉与交互意图**：整套色板从一个来源推导——角色图的真实像素。强调色取角色发色的
色相（`oklch(74% .154 36)`），再按用途下压明度到可承载白字的档位；中性色（页面 /
表面 / 前景 / 弱化 / 边框）沿同一暖色相（H 38~55）排布，保证任意两个相邻层级之间
既能拉开层次又不发灰。**所有颜色用 `oklch()` 表达**，因为它是感知均匀的：同一 L 值
在不同色相下的观感亮度一致，改 hue 时不会顺手把明暗改掉。

**适用场景**：任何需要取色的场合——新增组件、改状态色、加深色主题、调对比度。

**核心约束**：
1. 颜色**只**来自本节列出的 token。模板里不要出现 `#xxx` / `rgb()` 硬编码
   （唯一的例外是纯装饰性的 `rgba(80,30,10,.14)` 这类投影，它们不承载信息）。
2. 新增 token 必须**明暗两套一起给**，且命名一一对应。
3. 渐变端点必须用**同色相 alpha=0** 的版本（如 `--notice-ring-fade`），
   不能用 `transparent`——后者是 `rgba(0,0,0,0)`，插值途中会出现灰边。

## 完整代码

把下面两块放进 `src/styles/theme.css`（完整可运行副本见 `examples/theme.css`）。
注释里标了实测对比度，改值前先看一眼会被拖下水的是哪一组。

```css
/* ── 字体：自托管真实字体文件（Epilogue Black 标题 / DM Sans 正文）───────── */
@font-face {
  font-family: 'DM Sans';
  src: url('/assets/fonts/DMSans-Regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Epilogue';
  src: url('/assets/fonts/Epilogue-Black.woff2') format('woff2');
  font-weight: 900;
  font-style: normal;
  font-display: swap;
}

:root {
  /* 告诉浏览器用浅色渲染「原生控件与浏览器自带 UI」：滚动条、输入框光标、
     日期选择器、拼写下划线等。它们由浏览器绘制，不受 --surface 等变量影响，
     只能靠 color-scheme 切换。深色主题在 html[data-theme='dark'] 里覆盖成 dark。 */
  color-scheme: light;

  /* ── 中性色：页面 → 表面 → 边框，弱化文字夹在前景与边框之间 ────────── */
  --page-bg: #fdfdfd;                        /* 角色图顶边 4px 带实测均值 */
  --surface: oklch(98% .008 55);             /* #fdf7f3 输入框 / 卡片表面 */
  --fg: oklch(19% .018 40);                  /* #1b110e 对页面 18.2:1 */
  --muted: oklch(50% .035 38);               /* #765d55 对页面 5.96:1 / 对表面 5.70:1 */
  --border: oklch(90% .018 45);              /* #e9dbd4 */
  --row-hover: oklch(94% .016 45);           /* 列表行悬停底，L 相对页面下移 .06 */

  /* ── 强调色：取自角色发色 oklch(74% .154 36)，压到能承载白字的明度 ──── */
  --accent: oklch(53% .16 36);               /* #b53f1d 对页面 5.59:1，其上白字 5.69:1 */
  --accent-hover: oklch(45% .16 34);         /* #9a2202 白字对比度升至 8.07:1 */
  --accent-soft: oklch(95% .035 40);         /* #ffe7dd 选中底；与强调色 4.80:1 */

  --danger: oklch(47% .17 27);               /* #a51f1e 对页面 7.34:1 */

  /* ── 浮层（tooltip / 下拉弹层 / 任何飘在内容之上的面板）───────────── */
  --tooltip-bg: oklch(99% .007 55 / .98);
  --tooltip-text: var(--fg);
  --tooltip-muted: var(--muted);
  --tooltip-border: oklch(83% .055 36 / .8);
  --tooltip-shadow: 0 16px 34px oklch(24% .025 38 / .16), inset 0 1px 0 oklch(100% 0 0 / .76);

  /* ── 输入框外壳 .composer-shell 的专用分层色 ───────────────────────── */
  --composer-grid-line: oklch(47% .08 36 / .10);     /* 动态网格线 */
  --composer-grid-fade: oklch(98% .008 55 / .78);    /* 网格对角渐隐（= 表面色 alpha） */
  --composer-hover-glow: oklch(60% .23 32 / .34);    /* hover 光晕 */
  --composer-focus-glow: oklch(58% .25 34 / .48);    /* focus 光晕（比 hover 更实） */
  --composer-flow-hot: oklch(69% .20 48);            /* 边框流光：热端 */
  --composer-flow-bright: oklch(76% .16 72);         /* 边框流光：高光端 */

  /* ── 通知卡片光效：旋转渐变描边环 + 环境弥散光 + 底部呼吸背光 ────────
     浅色底下「亮端」不能用高 L 值（会糊进白底），所以取中亮高饱和暖橙；
     深色底才把亮端推到 L 89%。所有端点都带同色相 alpha=0 版本，
     避免渐变插值到 transparent（黑色透明）时出现灰边。 */
  --notice-ring-fade: oklch(56% .18 34 / 0);         /* 环的渐隐端（同色相 alpha=0）*/
  --notice-ring-tail: oklch(56% .18 34 / .32);       /* 环的拖尾 */
  --notice-ring-hot: oklch(56% .20 32 / .96);        /* 环的热端 */
  --notice-ring-bright: oklch(70% .18 52 / 1);       /* 环的高光（彗星头）*/
  --notice-aura-a: oklch(60% .17 36 / .28);          /* 环境弥散光 · 瓣 A */
  --notice-aura-b: oklch(78% .13 62 / .20);          /* 环境弥散光 · 瓣 B */
  --notice-glow-core: oklch(58% .18 34 / .55);       /* 底部背光 · 亮芯 */
  --notice-glow-halo: oklch(70% .14 48 / .32);       /* 底部背光 · 外晕 */
  --notice-glow-fade: oklch(74% .12 52 / 0);         /* 底部背光 · 渐隐端 */

  /* ── 主题切换的圆形扩散（见 motion/theme-ripple.md）──────────────────
     波峰环压在「新主题内侧 / 旧主题外侧」的交界上，色值要在两种底色上都立得住：
     浅色取中亮高饱和暖橙（L 太高会糊进浅底），深色把亮端推到 L 84%。
     必须不透明：它还得盖住 clip-path 那条硬边，带 alpha 会在接缝处漏出旧主题一线。 */
  --theme-ripple-crest: oklch(70% .17 42);
  /* 水滴涟漪（触点周围那几圈同心波）：内圈略亮、外圈更淡，靠 alpha 拉开层次。
     这一层只覆盖按钮周边，多数时间落在已经铺好的新主题上，所以按新主题底色配色。
     压在「隐约可见」的区间——它是氛围点缀，不是主体：用户看过第一版
     oklch(66% .17 40 / .82) 后明确要求降两档，不要往回调。 */
  --theme-ripple-drop: oklch(66% .10 42 / .22);
  --theme-ripple-drop-soft: oklch(70% .08 46 / .10);

  /* ── 全屏粒子背景（canvas 读取，不是 CSS 直接用）──────────────────── */
  --fx-orb-1: oklch(74% .154 36 / .20);
  --fx-orb-2: oklch(84% .10 40 / .21);
  --fx-dot: oklch(70% .14 36 / .17);
  --fx-particle: oklch(52% .17 27);
  --fx-particle-bright: oklch(62% .18 28);
  --fx-particle-trail: oklch(100% 0 0);
  --fx-particle-glow: 213, 70, 56;                   /* RGB 三元组，引擎里拼 rgba() */
  --fx-petal: oklch(61% .16 28 / .9);
  --fx-petal-highlight: oklch(82% .13 30 / .92);
  --fx-ripple: oklch(56% .19 28);
  --fx-water: 27, 49, 65;                            /* RGB 三元组 */
  --fx-water-highlight: oklch(68% .14 28 / .48);
  /* 樱花排斥力场仅保留物理交互，不绘制轮廓或光晕。 */
  --fx-field-outline-alpha: 0;
  --fx-field-glow-strength: 0;

  /* ── 字体栈 ─────────────────────────────────────────────────────── */
  --font-display: 'Epilogue', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
  --font-body: 'DM Sans', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
}

/* ── 深色主题（设置页「页面外观 > 主题」切换；跟随系统由 useTheme 处理）────── */
html[data-theme='dark'] {
  color-scheme: dark;
  --page-bg: oklch(17% .012 40);
  --surface: oklch(22% .016 42);
  --fg: oklch(93% .012 55);
  --muted: oklch(70% .03 45);
  --border: oklch(32% .02 45);
  --accent: oklch(62% .15 38);
  --accent-hover: oklch(68% .15 38);
  --accent-soft: oklch(30% .05 40);
  --danger: oklch(65% .16 27);
  --row-hover: oklch(27% .02 45);
  --tooltip-bg: oklch(24% .018 42 / .98);
  --tooltip-text: oklch(96% .008 55);
  --tooltip-muted: oklch(76% .025 48);
  --tooltip-border: oklch(68% .11 38 / .68);
  --tooltip-shadow: 0 18px 38px oklch(5% .01 40 / .46), inset 0 1px 0 oklch(100% 0 0 / .08);
  --composer-grid-line: oklch(78% .08 38 / .13);
  --composer-grid-fade: oklch(22% .016 42 / .80);
  --composer-hover-glow: oklch(75% .22 40 / .40);
  --composer-focus-glow: oklch(78% .20 46 / .56);
  --composer-flow-hot: oklch(80% .18 48);
  --composer-flow-bright: oklch(88% .13 78);
  /* 通知卡片光效：深色底把亮端提到 L 89%，描边环与背光整体降一点 alpha，
     因为深底上同样的 alpha 观感更「糊」。 */
  --notice-ring-fade: oklch(70% .15 38 / 0);
  --notice-ring-tail: oklch(70% .15 38 / .36);
  --notice-ring-hot: oklch(70% .17 38 / .98);
  --notice-ring-bright: oklch(89% .12 76 / 1);
  --notice-aura-a: oklch(64% .16 36 / .24);
  --notice-aura-b: oklch(56% .13 44 / .20);
  --notice-glow-core: oklch(66% .17 38 / .60);
  --notice-glow-halo: oklch(58% .14 40 / .34);
  --notice-glow-fade: oklch(56% .12 42 / 0);
  /* 主题切换：深底上把波峰推到 L 84% 才看得见 */
  --theme-ripple-crest: oklch(84% .13 62);
  --theme-ripple-drop: oklch(85% .07 58 / .21);
  --theme-ripple-drop-soft: oklch(78% .06 54 / .09);
  --fx-orb-1: oklch(55% .13 36 / .16);
  --fx-orb-2: oklch(42% .09 40 / .18);
  --fx-dot: oklch(50% .12 36 / .14);
  --fx-particle: oklch(70% .16 28);
  --fx-particle-bright: oklch(78% .17 28);
  --fx-particle-trail: oklch(100% 0 0);
  --fx-particle-glow: 246, 105, 82;
  --fx-petal: oklch(77% .13 28 / .82);
  --fx-petal-highlight: oklch(93% .07 34 / .9);
  --fx-ripple: oklch(80% .14 28 / .8);
  --fx-water: 38, 55, 69;
  --fx-water-highlight: oklch(79% .11 30 / .38);
  --fx-field-outline-alpha: 0;
  --fx-field-glow-strength: 0;
}
```

### 主题落地的两条规则（不要绕过）

```ts
// composables/useTheme.ts —— 写入 <html data-theme>，幂等（值没变就不写）
function paint(option: ThemeOption): void {
  const next = resolveDark(option) ? 'dark' : 'light'
  if (document.documentElement.dataset.theme !== next) document.documentElement.dataset.theme = next
}
```

```ts
// 换主题一律走 setTheme(option, origin)，不要直接改 theme.value
// origin = 触点按钮中心，用于张开圆形扩散（见 motion/theme-ripple.md）
const rect = triggerEl.getBoundingClientRect()
setTheme(next, { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 })
```

## 变体说明

### 明暗映射总表（改动时两列一起改）

| Token | 浅色 | 深色 | 语义 |
| --- | --- | --- | --- |
| `--page-bg` | `#fdfdfd` | `oklch(17% .012 40)` | 页面底（**注意：可见底色实际由粒子 canvas 绘制，见 page-background.md**） |
| `--surface` | `oklch(98% .008 55)` | `oklch(22% .016 42)` | 卡片 / 输入框 / 气泡表面 |
| `--fg` | `oklch(19% .018 40)` | `oklch(93% .012 55)` | 正文与标题 |
| `--muted` | `oklch(50% .035 38)` | `oklch(70% .03 45)` | 次要文字、占位符、元信息 |
| `--border` | `oklch(90% .018 45)` | `oklch(32% .02 45)` | 分隔线、描边 |
| `--row-hover` | `oklch(94% .016 45)` | `oklch(27% .02 45)` | 列表行 / 图标按钮悬停底 |
| `--accent` | `oklch(53% .16 36)` | `oklch(62% .15 38)` | 强调色：链接、选中、主按钮底 |
| `--accent-hover` | `oklch(45% .16 34)` | `oklch(68% .15 38)` | 强调色按下 / 悬停 |
| `--accent-soft` | `oklch(95% .035 40)` | `oklch(30% .05 40)` | 选中项底、图标底、kicker 底 |
| `--danger` | `oklch(47% .17 27)` | `oklch(65% .16 27)` | 错误文案、危险动作 |
| `--tooltip-bg` | `oklch(99% .007 55 / .98)` | `oklch(24% .018 42 / .98)` | 浮层底 |
| `--tooltip-border` | `oklch(83% .055 36 / .8)` | `oklch(68% .11 38 / .68)` | 浮层描边 |
| `--theme-ripple-crest` | `oklch(70% .17 42)` | `oklch(84% .13 62)` | 主题扩散波峰（**必须不透明**） |
| `--theme-ripple-drop` | `oklch(66% .10 42 / .22)` | `oklch(85% .07 58 / .21)` | 水滴涟漪内圈（**细线隐约档**） |
| `--theme-ripple-drop-soft` | `oklch(70% .08 46 / .10)` | `oklch(78% .06 54 / .09)` | 水滴涟漪外圈 |

### 已实测的关键对比度（换值前对照，别把已过关的组合改崩）

| 组合 | 浅色 | 深色 | 门槛 |
| --- | --- | --- | --- |
| `--fg` / `--page-bg` | 18.2:1 | — | 正文 4.5 |
| `--muted` / `--page-bg` | 5.96:1 | — | 正文 4.5 |
| `--muted` / `--surface` | 5.70:1 | — | 正文 4.5 |
| `--accent` / `--page-bg` | 5.59:1 | 4.94:1（动效按钮实测） | 正文 4.5 |
| 白字 / `--accent` | 5.69:1 | — | 正文 4.5 |
| 白字 / `--accent-hover` | 8.07:1 | — | 正文 4.5 |
| `--accent` / `--accent-soft` | 4.80:1 | **3.58:1 ✗** | 正文 4.5 |
| `--danger` / `--page-bg` | 7.34:1 | — | 正文 4.5 |
| `--fg` / `--accent-soft` | 15.7:1 | 11.3:1 | 正文 4.5 |

> 深色主题下 **`--accent` 压在 `--accent-soft` 上只有 3.58:1**，这是下拉选中项文字
> 必须用 `--fg` 而不是 `--accent` 的原因（见 `components/select.md`）。

### 主题的三档状态

| 状态 | 取值 | 行为 |
| --- | --- | --- |
| 跟随系统 | `跟随系统` | 监听 `prefers-color-scheme`，系统变则跟着变，**不播扩散动画**（没有触点） |
| 浅色 | `浅色` | 固定 `data-theme="light"` |
| 深色 | `深色` | 固定 `data-theme="dark"` |

`setTheme` 的三条分支：选中当前项 → 什么都不做（连 DOM 都不碰）；明暗没变
（浅色 ↔ 跟随系统且系统正好浅色）→ 只更新选项不播动画；其余 → 圆形扩散。

## 使用注意事项

**可访问性**
- 对比度是硬门槛，不是建议值。正文 ≥ 4.5:1，≥18.66px 或 ≥14px 粗体的大字 ≥ 3:1，
  图标 / 边框等非文本 ≥ 3:1。
- `color-scheme` 一行**不能删**：它管的是浏览器绘制的滚动条、输入框光标、拼写
  下划线。删掉后深色主题下滚动条会是浅色的。
- 不要同时用 `data-theme` 与 `class` 两套主题开关，`ParticleBackground` 的
  MutationObserver 只监听 `data-theme` 属性。

**性能**
- `paint()` 必须幂等：重复写同一个 `data-theme` 值也会惊动 MutationObserver，
  导致粒子引擎白重建一次（82 粒子 + 72 花瓣全量重算）。
- 渐变端点用同色相 alpha=0 变量而非 `transparent`，否则插值出现灰边——这是视觉
  问题，不是性能问题，但很容易被误判成"渲染 bug"去查半天。

**常见误用**
1. **在组件里写 `background: #fff`** —— 深色主题立刻破功。用 `var(--surface)`。
2. **只用 `color-mix(in srgb, var(--fg) 4%, transparent)` 做阴影** —— 这类写法是
   允许的（装饰性 alpha），但要写成 `transparent` 而不是 `rgba(0,0,0,0)` 吗？两者
   等价，保持既有风格即可；关键是**不要把阴影色也写成新变量**去膨胀 token 表。
3. **深色主题忘了同步新增 token** —— 深色下该变量会回落到浅色值，出现半明半暗。
   新增变量后立即在 `html[data-theme='dark']` 里补一行。
4. **以为 `--page-bg` 就是用户看到的底色** —— 实际观感由粒子 canvas 画的竖向渐变
   主导（比 `--page-bg` 暗约 37 级）。详见 `page-background.md`。
5. **把 `--theme-ripple-crest` 调成半透明** —— 它要盖住 clip-path 的硬边，半透明
   会在接缝处漏出旧主题一线。
