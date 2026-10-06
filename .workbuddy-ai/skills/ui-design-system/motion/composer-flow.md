# 输入框流光与动态网格

## 设计思路

**解决的问题**：输入框是页面的核心交互区，静止时需要一点"活着"的感觉，但又不能
常驻动画拖累性能。

**视觉与交互意图**：**静止完全不动，hover 才启动，focus 再提速**——形成一条
"越专注越活跃"的梯度：

| 状态 | 网格漂移 | 边框流光 | 阴影 |
| --- | --- | --- | --- |
| rest | 不动，opacity .74 | 不可见 | `0 7px 18px` |
| hover | 2.6s 一圈 | 2s 一圈，opacity .9 | +2px 光晕环 |
| focus-within | **1.35s** 一圈 | **1.05s** 一圈，opacity 1 | +3px 光晕环 |

这个"提速"是整套设计里最有效的一处反馈：用户不用看颜色，光流动变快就知道
输入框已激活。

**边界描边怎么画的**：`::after` 用 `padding: 2px` + 双层 `mask` + `mask-composite:
exclude`（xor）把中间挖掉，只留 2px 宽的边带。这是全站统一写法（描边环、
通知卡环都用它）。

## 完整代码

```css
.composer-shell::before {          /* 动态网格 */
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

.composer-shell::after {           /* 边框流光：2px 边带 */
  content: '';
  position: absolute;
  z-index: 2;
  inset: 0;
  padding: 2px;                    /* 边带宽度 = 2px */
  border-radius: inherit;
  opacity: 0;
  pointer-events: none;
  background: linear-gradient(105deg,
    transparent 15%,
    var(--composer-flow-hot) 40%,
    var(--composer-flow-bright) 50%,
    var(--accent) 60%,
    transparent 85%);
  background-size: 220% 100%;
  background-position: 100% 50%;
  filter: drop-shadow(0 0 6px var(--composer-hover-glow));
  /* 掩膜：只留 padding 那一圈（content-box 挖掉） */
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  transition: opacity .2s ease, filter .2s ease;
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

@keyframes composer-shell-grid-drift {
  from { background-position: 0 0, 0 0, center; }
  to   { background-position: 32px 32px, 32px 32px, center; }   /* 2×16px = 两个网格周期 */
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

### 依赖的 token

```css
--composer-grid-line: oklch(47% .08 36 / .10);    /* 浅色 */
--composer-grid-fade: oklch(98% .008 55 / .78);   /* = 表面色 alpha，对角渐隐 */
--composer-hover-glow: oklch(60% .23 32 / .34);
--composer-focus-glow: oklch(58% .25 34 / .48);
--composer-flow-hot: oklch(69% .20 48);
--composer-flow-bright: oklch(76% .16 72);
```

## 变体说明

| 变体 | 网格漂移 | 边框流光 | 备注 |
| --- | --- | --- | --- |
| rest | — | — | 网格 opacity .74，静态 |
| hover | 2.6s | 2s（opacity .9） | 描边渐变换成 `118deg accent-hover→accent→accent-hover` |
| focus-within | **1.35s** | **1.05s**（opacity 1） | 描边渐变换成 `125deg flow-hot→flow-bright→accent` |
| invalid | 跟随当前状态 | 跟随当前状态 | 描边渐变换成 `--danger` 系，动画不变 |
| disabled | 无 | 无 | 需要时移除 hover/focus 规则 |
| 移动端 | 同（触屏无 hover，靠 focus-within 触发） | 同 | 圆角 22px 不影响动画 |
| 矮视口 | 同 | 同 | padding 收紧不影响动画 |
| reduced-motion | 停 | 停 | 网格与流光**保持可见**（opacity 由 hover/focus 规则给），只是不动 |

### 掩膜边带写法（可复用到任何"渐变描边"）

```css
.ring {
  position: absolute;
  inset: -2px;                 /* 想让环在元素外就把 inset 取负 */
  padding: 2px;                /* 环宽 */
  border-radius: inherit;      /* 跟随元素圆角 */
  pointer-events: none;
  background: <你的渐变>;
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  mask-composite: exclude;
}
```

> `-webkit-mask-composite: xor` 与标准 `mask-composite: exclude` 必须**两个都写**，
> Safari 只认前者。

## 使用注意事项

**可访问性**
- 流光的提速是**辅助**反馈，不是唯一反馈——focus 时还必须有 focus 环与描边变色。
- reduced-motion 下网格与流光**保留可见**（它们不是装饰性闪烁，是状态指示），
  只停动画。

**性能**
- 两个动画都动 `background-position`——**会重绘**，不是合成层。这是刻意接受
  的：只在 hover/focus 期间跑，且全站同一时刻最多一个输入框处于 focus。
- 静止态**零动画**（opacity 由 `transition` 控制，不是 `animation`）。不要改成
  常驻循环。
- `filter: drop-shadow` 在流光上是常驻的（即使 opacity 0 也会计算）——
  如果输入框很多（比如表单页有 10 个字段），考虑把 `drop-shadow` 也放到
  hover/focus 规则里。当前设置页有 3 个字段 + 1 个下拉，实测无问题。
- 网格的第三层渐变 `linear-gradient(135deg, transparent 0 53%, var(--composer-grid-fade) 78%)`
  是**静态的**（keyframes 里它的位置恒为 `center`），所以只有前两层在动。

**常见误用**
1. **把动画改成常驻循环** —— 页面静止时也在重绘，明显掉帧。
2. **`background-size` 与 keyframes 的距离不匹配** —— 网格 16px，`to` 必须写
   `32px`（整数倍周期）才能无缝循环。改网格尺寸时两边一起改。
3. **只写 `-webkit-mask-composite` 不写 `mask-composite`** —— Chrome/Edge 不认
   前者，边带会变成一整块（中间不挖空）。
4. **给 `.composer-shell::after` 加 `z-index: 2` 但忘了内容层 `z-index: 1`** ——
   流光会盖在文字上。全局规则 `.composer-shell > *:not(.sr-only) { position:
   relative; z-index: 1 }` 已处理，不要删。
5. **复制这套动画到一个常驻的装饰元素上** —— 见第 1 条。
