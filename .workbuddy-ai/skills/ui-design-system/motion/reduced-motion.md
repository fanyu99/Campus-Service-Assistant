# 无障碍降级：prefers-reduced-motion

## 设计思路

**解决的问题**：`prefers-reduced-motion` 分支最容易写成两种错法——① 完全不写，
前庭敏感用户被迫看动画；② 写成 `display: none` 把元素整个删掉，视觉缺失
（用户明确要求过：**降级后视觉仍完整，是"不动"，不是"消失"**）。

**核心原则**：

> **降级 = 停动画，保留视觉状态。**
> hover 颜色照样变、描边环照样在、加载指示器照样显示、光晕照样铺着——只是不动。

**适用场景**：每一个有 `transition` 或 `animation` 的组件。

## 完整代码

### 全站降级清单（照抄）

```css
/* ── ① 输入框外壳（全局 .composer-shell）────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .composer-shell,
  .composer-shell::before,
  .composer-shell::after,
  .spark-button,
  .spark-button::before { transition: none; animation: none; }
}

/* ── ② 动效按钮 ────────────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .animated-button,
  .animated-button .arr,
  .animated-button .text,
  .animated-button .circle { transition: none; }
}

/* ── ③ 首页入场 ────────────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .home-reveal .topbar,
  .home-reveal .stage,
  .home-reveal .panel { animation: none; }
}

/* ── ④ 路由切换（★ 必须复位初始态）────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .route-enter-active,
  .route-leave-active { transition: none; }
  .route-enter-from,
  .route-leave-to { opacity: 1; transform: none; }   /* 不复位会永久不可见 */
}

/* ── ⑤ 角色气泡与眼神 ──────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .character-bubble { animation: none; }
  .ch-iris { transform: none; }
}

/* ── ⑥ 下拉选择 ────────────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .select-panel,
  .select-chev { transition: none; }
  .select-pop-enter-active,
  .select-pop-leave-active { transition: none; }
}

/* ── ⑦ 加载指示器（★ 保留静态姿态，不是空白）─────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .send,
  .composer,
  .composer::before,
  .composer::after,
  .loading-ball,
  .loading-shadow { transition: none; animation: none; }
  .loading-ball {
    top: var(--loader-rest-top);          /* 固定在最高点 */
    height: var(--loader-ball-size);
    transform: none;
  }
  .loading-shadow { transform: scaleX(.7); opacity: .5; }
}

/* ── ⑧ 通知卡片三层光效（★ 保留静止的环与背光）───────────────────── */
@media (prefers-reduced-motion: reduce) {
  .notification-card-frame::before,
  .notification-card-frame::after,
  .notification-card-ring::before { animation: none; }
  .notification-card-frame::after { opacity: .6; filter: blur(28px); transform: none; }
}

/* ── ⑨ 主题切换扩散（★ CSS 与 JS 双重兜底）───────────────────────── */
@media (prefers-reduced-motion: reduce) {
  html.theme-rippling::view-transition-new(root),
  html.theme-rippling::view-transition-new(theme-ripple),
  html.theme-rippling::view-transition-group(theme-ripple),
  html.theme-rippling::view-transition-new(theme-ripple-pond),
  html.theme-rippling::view-transition-group(theme-ripple-pond) { animation: none; }
}

/* ── ⑩ 分类 tab / 列表行 / 链接 ────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .category-tab,
  .service-item,
  .service-link,
  .history-item,
  .record-link,
  .filter-tab { transition: none; }
}
```

### JS 侧兜底（两处）

```ts
// ① 主题切换：不支持减弱动效就直接切
export function canPlayThemeRipple(): boolean {
  const doc = document as Document & { startViewTransition?: unknown }
  return typeof doc.startViewTransition === 'function'
    && !window.matchMedia('(prefers-reduced-motion: reduce)').matches
}
```

```ts
// ② 粒子引擎：降配而不是关闭
if (reducedMotionPreference || config.reducedMotion) {
  config.count = Math.min(config.count, 32)
  config.petalCount = Math.min(config.petalCount, 32)
  config.trailLimit = 0
  config.trailStrength = 0
  config.repulsionStrength = 0
  config.rippleLimit = Math.min(config.rippleLimit, 16)
}
```

```ts
// ③ 眼神跟随：触屏环绕模式只在「未减弱动效」时启用
function syncMode() {
  idle = !fine.matches && !reduce.matches
  …
}
```

## 变体说明

### 三档降级对照

| 元素 | 正常 | 降级后 | 是否可见 |
| --- | --- | --- | --- |
| composer 网格 | 漂移 | 静止（opacity 由 hover/focus 给） | ✅ 可见（hover 时 opacity 1） |
| composer 流光 | 流动 | 静止（opacity 由 hover/focus 给） | ✅ 可见（focus 时 opacity 1） |
| 动效按钮 | 圆膨胀 + 圆角收拢 | 直接切到终态（hover 仍填色） | ✅ 可见 |
| spark 掠光 | 掠过 | 静止高光 | ✅ 可见 |
| 首页入场 | 上浮淡入 | 直接出现 | ✅ 可见 |
| 路由切换 | 180ms 淡入淡出 | 瞬切（**必须复位 opacity:1**） | ✅ 可见 |
| 角色气泡 | 弹出 | 直接出现 | ✅ 可见 |
| 眼神跟随 | 跟随指针 / 缓慢环绕 | 固定居中 | ✅ 可见 |
| 加载球 | 跳动 | 固定最高点 + 影子 scaleX(.7) | ✅ 可见（静态指示器） |
| 通知描边环 | 旋转 | 静止的渐变环 | ✅ 可见 |
| 通知背光 | 呼吸 | 固定 `opacity:.6; blur(28px)` | ✅ 可见 |
| 通知环境光 | 呼吸 | 固定 `opacity:.6` | ✅ 可见 |
| 主题切换 | 圆形扩散 | 直接换 | ✅ 可见 |
| 品牌标呼吸 | 呼吸 | 静止 | ✅ 可见 |
| 粒子背景 | 全参数 | ≤32 粒子、无拖尾、无排斥 | ✅ 可见（静态背景） |

### 未做降级 / 无需降级

| 项 | 说明 |
| --- | --- |
| hover 颜色过渡（.16s） | 纯颜色变化，不属于"运动"，**不降级也能接受**。当前项目里部分组件降了、部分没降，属历史差异；新增组件建议统一降级以保持一致。 |
| tooltip | 有 `opacity` + `transform`，**未降级**。它是 220ms 的小位移，可接受；若要补，加 `.icon-btn[data-tip]::before/::after { transition: none }`。 |

## 使用注意事项

**可访问性**
- **最危险的一处**：路由降级的 `enter-from` / `leave-to` 必须复位成
  `opacity: 1; transform: none`。忘了的话，开了"减弱动效"的用户会看到一个
  **永久空白的页面**（因为 `opacity: 0` 被保留但没有动画去改变它）。
- 加载指示器降级后要给出**明确的静态姿态**（球在最高点、影子缩小），
  不能是三个球堆在底部（那样看起来像坏了）。
- `prefers-reduced-motion` 是**用户系统级偏好**，不要提供"动画开关"去覆盖它
  （除非用户明确要求）。

**性能**
- 降级不只惠及前庭敏感用户：低端设备上停掉循环动画也能明显省电。
- 粒子引擎的降级是**降参数**而不是停 rAF——背景仍然存在（视觉完整），
  只是粒子少、无拖尾。

**常见误用**
1. **写成 `display: none`** —— 用户明确要求过"视觉仍完整，只是不动"。
   通知卡的三层光效、加载指示器都不能删掉。
2. **只写 `animation: none` 忘了 `transition: none`** —— hover 仍然是渐变的
   （虽然很短，但仍是动）。两个都要写。
3. **路由降级忘了复位初始态** —— 见上，最危险。
4. **只在 CSS 里降级，JS 里的 rAF 照跑** —— 粒子引擎和眼神跟随都有 JS 分支，
   新增的 JS 动画（rAF / Web Animations）也要判断
   `matchMedia('(prefers-reduced-motion: reduce)').matches`。
5. **用 `@media (prefers-reduced-motion: no-preference)` 反着写** ——
   老浏览器不支持 `no-preference` 查询时整段样式会失效。统一用
   `reduce` 正向覆盖。
