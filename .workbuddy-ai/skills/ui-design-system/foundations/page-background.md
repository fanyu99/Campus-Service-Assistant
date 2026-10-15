# 页面背景设计

## 设计思路

**解决的问题**：页面底色看起来"不是 `--page-bg`"——顶栏、工具条明明填的是
`--page-bg`，却和周围切出一条可见色带。

**根因**：用户真正看到的底色**不是 CSS 画的**，而是 `<canvas>` 粒子引擎绘制的
**竖向渐变**（顶部 ≈ `#d8d8da`、底部 ≈ `#e7e7e8`，比 `--page-bg` 暗约 37 级）。
canvas 是 `position: fixed; inset: 0`，铺满视口且始终在内容之下。所以任何
**铺满宽度的不透明条**（顶栏、工具条）如果填 `--page-bg`，就会在渐变上切出一条
明显更亮的带。

**视觉与交互意图**：背景是"氛围层"——竖向渐变打底 + 缓慢漂移的粒子 + 樱花花瓣 +
底部水线与涟漪 + 鼠标附近的排斥力场。它**只提供氛围，不承载信息**，因此
`aria-hidden="true"`、`pointer-events: none`、`z-index: 0`（内容层 `z-index: 1~2`）。

**适用场景**：任何整页背景、任何"要不要给顶栏加背景色"的决定、任何新页面接入。

## 完整代码

### canvas 容器（组件已封装，新页面不要重复挂载）

```vue
<!-- App.vue：全局只挂一次，放在 .app-shell 之外 -->
<ParticleBackground
  :particle-count="82"
  :petal-count="72"
  :heart-scale="62"
  :repulsion-strength="0.86"
  :heart-force-radius="1.22"
  :gravity="0.012"
  :wind-strength="0.022"
  :drift-strength="0.28"
  :trail-strength="0.26"
  :trail-limit="120"
  :waterline-ratio="0.88"
  :water-depth="0.06"
  :ripple-limit="54"
  :opacity="0.82"
/>
```

```css
.particle-background {
  position: fixed;
  inset: 0;
  display: block;
  width: 100vw;
  height: 100vh;
  pointer-events: none;   /* 永远不吃事件 */
  overflow: hidden;
}
```

### 颜色从 CSS 变量读（引擎侧，保证主题切换同步）

```ts
function readThemeColors() {
  const styles = getComputedStyle(document.documentElement)
  const readNumberVar = (name: string) => {
    const value = Number.parseFloat(styles.getPropertyValue(name).trim())
    return Number.isFinite(value) ? value : undefined
  }
  return {
    particleColor: styles.getPropertyValue('--fx-particle').trim(),
    accentColor: styles.getPropertyValue('--fx-particle-bright').trim(),
    trailColor: styles.getPropertyValue('--fx-particle-trail').trim(),
    glowColor: styles.getPropertyValue('--fx-particle-glow').trim(),
    petalColor: styles.getPropertyValue('--fx-petal').trim(),
    petalHighlight: styles.getPropertyValue('--fx-petal-highlight').trim(),
    waterColor: styles.getPropertyValue('--fx-water').trim(),
    waterHighlight: styles.getPropertyValue('--fx-water-highlight').trim(),
    rippleColor: styles.getPropertyValue('--fx-ripple').trim(),
    fieldOutlineAlpha: readNumberVar('--fx-field-outline-alpha'),
    fieldGlowStrength: readNumberVar('--fx-field-glow-strength'),
  }
}
```

### 主题切换时立刻补画一帧（否则快照里留着旧配色）

```ts
themeObserver = new MutationObserver(() => {
  createEngine()
  // 立刻补画一帧：换主题可能正被 View Transitions 拍快照，只靠 rAF 会让
  // 新快照里留着旧配色（粒子颜色与底色渐变都会滞后一拍）。
  engine?.draw(1)
})
themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
```

### 页面层：绝不能用 --page-bg 铺满宽度

```css
/* ✅ 正确：顶栏完全透明，让粒子渐变透上来 */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 58px;
  flex: 0 0 auto;
  /* 不写 background */
}

/* ❌ 错误：铺满宽度的不透明条会在渐变上切出可见色带 */
.topbar { background: var(--page-bg); }

/* ✅ 需要"浮起来"时用半透明表面色 + 毛玻璃，而不是纯 --page-bg */
.topbar-float {
  background: color-mix(in srgb, var(--surface) 72%, transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
```

### 内容层压在 canvas 之上

```css
.main {
  position: relative;   /* 建立层叠上下文 */
  z-index: 2;           /* 内容永远在 canvas(z-index:0) 之上 */
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
  padding: 0 clamp(20px, 2.8vw, 40px);
}
```

## 变体说明

### 引擎参数表（改氛围时调这些，不要改 CSS）

| 参数 | 默认值 | 含义 | 调大的效果 |
| --- | --- | --- | --- |
| `particle-count` | 82 | 粒子数量 | 更密、更热闹（性能线性下降） |
| `petal-count` | 72 | 樱花花瓣数量 | 花瓣飘落更密 |
| `heart-scale` | 62 | 心形排斥力场尺寸 | 力场更大，鼠标"推开"范围更大 |
| `repulsion-strength` | 0.86 | 排斥强度 | 粒子被推得更远 |
| `heart-force-radius` | 1.22 | 力场作用半径系数 | 影响范围更广 |
| `gravity` | 0.012 | 重力 | 粒子下沉更快 |
| `wind-strength` | 0.022 | 风力 | 横向漂移更明显 |
| `drift-strength` | 0.28 | 随机漂移 | 运动更"活" |
| `trail-strength` | 0.26 | 拖尾强度 | 拖尾更明显 |
| `trail-limit` | 120 | 拖尾长度上限 | 拖尾更长（**最贵的一项**） |
| `waterline-ratio` | 0.88 | 水线在视口高度的占比 | 水线更靠上 |
| `water-depth` | 0.06 | 水面厚度 | 水带更厚 |
| `ripple-limit` | 54 | 涟漪数量上限 | 涟漪更多 |
| `opacity` | 0.82 | 整层不透明度 | 背景更实 |
| `z-index` | 0 | 层级 | — |

### 三档环境

| 环境 | 行为 |
| --- | --- |
| **正常** | 全参数运行，rAF 常驻循环，指针移动/按下会 `startLoop()` 唤醒。 |
| **`prefers-reduced-motion: reduce`** | 粒子 ≤32、花瓣 ≤32、`trailLimit=0`、`trailStrength=0`、`repulsionStrength=0`、涟漪 ≤16。**保留静态背景**，不是变空白。 |
| **`document.hidden`** | `stopLoop()` 停 rAF；回到前台 `startLoop()`。**必须做**，否则后台标签页持续占 CPU。 |

### 主题

| 主题 | 粒子 | 花瓣 | 水线 |
| --- | --- | --- | --- |
| 浅色 | `--fx-particle: oklch(52% .17 27)`（暗红） | `--fx-petal: oklch(61% .16 28 / .9)` | `--fx-water: 27,49,65` |
| 深色 | `--fx-particle: oklch(70% .16 28)`（提亮到 L70） | `--fx-petal: oklch(77% .13 28 / .82)` | `--fx-water: 38,55,69` |

深色主题下所有粒子色整体提亮约 18 个 L 级——深底上同样色值会"沉"进去看不见。

## 使用注意事项

**可访问性**
- canvas 必须 `aria-hidden="true"`（纯装饰，不应进入无障碍树）。
- `prefers-reduced-motion` 下**降配而不是关闭**：静态背景仍在，视觉完整。

**性能**
- **DPR 上限 2**：`Math.min(window.devicePixelRatio || 1, 2)`。不设上限的话
  3x 屏上画布面积翻 2.25 倍，掉帧明显。
- 引擎在 `data-theme` 变化时会**整体重建**（`createEngine()`）。这正是 `paint()`
  必须幂等的原因——重复写同一个值会白重建一次。
- 所有窗口监听都要 `{ passive: true }`；`onBeforeUnmount` 里**全部解绑**
  （resize / pointerdown / pointermove / pointerleave / touchmove / touchend /
  touchcancel / visibilitychange）+ `ResizeObserver` / `MutationObserver` disconnect
  + `engine.destroy()`。
- 不要在页面组件里再挂第二个 `ParticleBackground`。`useHeroField()` 是遗留兼容
  钩子，**故意什么都不做**，不要"修好"它。

**常见误用**
1. **给顶栏 / 工具条填 `--page-bg`** —— 这是本项目最经典的坑，会在渐变上切出
   亮色带。要背景就用半透明 `--surface` + blur，或者干脆透明。
2. **以为 `--page-bg` 决定观感** —— 决定观感的是 canvas 渐变。改 `--page-bg`
   只影响 body（被 canvas 完全遮住），几乎看不出区别。
3. **给 canvas 加 `z-index: -1`** —— 会掉到 body 背景之下被 `--page-bg` 盖住。
   用 `z-index: 0` + 内容层 `z-index: 1~2`。
4. **`backdrop-filter: blur()` 大面积铺** —— 铺满视口的毛玻璃每帧重算，很贵。
   只在弹窗遮罩、小面积工具条上用。
5. **忘了 `document.hidden` 停循环** —— 后台标签页持续跑 rAF，耗电被用户感知。
