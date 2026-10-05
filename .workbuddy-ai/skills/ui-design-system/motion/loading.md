# 加载指示器动效

> 组件结构与用法见 `components/feedback.md`；本文件聚焦**动画本身**的参数与节奏。

## 设计思路

**解决的问题**：转圈 spinner 太工业，纯文字太弱。需要一个和这套"暖色手作感"
界面匹配、且能同时产出两种尺寸的等待指示。

**视觉与交互意图**：三个球依次弹起、落地，影子同步缩放——像水滴弹跳。
节奏上用 **`.5s alternate`**（弹上去再落回来 = 完整一跳），三球错峰
`0 / .2s / .3s`，形成"连续的水滴"而不是齐步走。

**关键实现**：**一套结构 + 一组私有变量**同时产出大号（气泡内 12px）和小号
（按钮内 6px）——只改 `--loader-*`，不写第二份 keyframes。

## 完整代码

```css
.loading-animation {
  --loader-ball-size: 12px;
  --loader-track-width: 62px;
  --loader-height: 31px;
  --loader-rest-top: 0px;        /* 弹到最高点时球的 top */
  --loader-floor-top: 25px;      /* 落地时球的 top */
  --loader-shadow-width: 13px;
  --loader-shadow-top: 27px;
  position: relative;
  z-index: 1;
  width: var(--loader-track-width);
  height: var(--loader-height);
}

.loading-ball,
.loading-shadow { position: absolute; display: block; transform-origin: 50%; }

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

/* 一跳：落地压扁 → 恢复圆形 → 弹到最高点 */
@keyframes loader-ball {
  0% {
    top: var(--loader-floor-top);
    height: 5px;                          /* 压扁 */
    border-radius: 50px 50px 25px 25px;   /* 下半更圆，像被压的球 */
    transform: scaleX(1.7);               /* 横向铺开 */
  }
  40% {
    height: var(--loader-ball-size);
    border-radius: 50%;
    transform: scaleX(1);
  }
  100% { top: var(--loader-rest-top); }
}

/* 影子：球飞得越高，影子越小越淡 */
@keyframes loader-shadow {
  0% { transform: scaleX(1.5); }
  40% { transform: scaleX(1); opacity: .7; }
  100% { transform: scaleX(.2); opacity: .4; }
}

/* ── 小号变体：只改变量 ──────────────────────────────────────────────── */
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

/* ── 降级：固定在最高点，是「不动的静态指示器」而不是空白 ────────────── */
@media (prefers-reduced-motion: reduce) {
  .loading-ball,
  .loading-shadow { transition: none; animation: none; }
  .loading-ball { top: var(--loader-rest-top); height: var(--loader-ball-size); transform: none; }
  .loading-shadow { transform: scaleX(.7); opacity: .5; }
}
```

## 变体说明

### 两套尺寸参数

| 变量 | 大号（气泡内） | 小号（按钮内） |
| --- | --- | --- |
| `--loader-ball-size` | 12px | 6px |
| `--loader-track-width` | 62px | 30px |
| `--loader-height` | 31px | 17px |
| `--loader-rest-top` | 0px | 0px（继承） |
| `--loader-floor-top` | 25px | 11px |
| `--loader-shadow-top` | 27px | 14px |
| `--loader-shadow-width` | 13px | 7px |
| 三球 left | 4 / 25 / 46px | 1 / 12 / 23px |
| 三影 left | 3 / 24 / 45px | 0 / 11 / 22px |
| 影子 height | 4px | 2px |

### 节奏

| 项 | 值 |
| --- | --- |
| 单跳时长 | `.5s` |
| 方向 | `alternate`（弹上去、落回来，一次 `alternate` 循环 = 一跳 + 一落） |
| 曲线 | `ease` |
| 错峰 | 球 `0 / .2s / .3s`；影子同样 `0 / .2s / .3s`（**影子必须与对应球同延迟**） |
| 压扁段 | 0%（`height:5px; scaleX(1.7)`）→ 40%（恢复圆形）→ 100%（最高点） |

### 状态

| 状态 | 行为 |
| --- | --- |
| 加载中 | 动画常驻（`infinite`）；按钮同时 `disabled` + `cursor: wait` + `opacity:.68`。 |
| 结束 | 元素随 `v-if` 卸载，**不需要收尾动画**。 |
| 主题 | 球与影子都走 `--accent`，自动跟随。 |
| 移动端 | 尺寸不变（跟随大/小号变体）。 |
| reduced-motion | 球固定最高点、影子 `scaleX(.7) opacity:.5`——**静态指示器，不是空白**。 |

## 使用注意事项

**可访问性**
- 外层容器 `role="status"` + `aria-label`（如"校园助手正在生成回答"）；
  动画本身 `aria-hidden="true"`。
- 按钮内要配 `.sr-only` 文本（"正在发送"），因为按钮里的可见文字被替换掉了。
- 降级后的静态姿态必须**看起来像"在等待"而不是"坏了"**——球要在最高点
  （有腾空感），不能堆在底部。

**性能**
- 动的是 `top` / `height` / `transform` —— **会触发布局**。元素极小（3 个球 + 3 个
  影子），可接受；**不要在长列表里每一行都放一个**。
- 影子有 `filter: blur(1px)` ×3。同屏 1~2 个实例没问题，十几个会掉帧。
- 结束即卸载，不留常驻 rAF（它纯 CSS，不走 JS）。

**常见误用**
1. **写第二份 keyframes 做小号** —— 用 `--loader-*` 变量。
2. **影子延迟与球不一致** —— 球飞起来时影子没跟上，看起来像错位。
3. **只放动画不加 `role="status"`** —— 读屏用户完全不知道在加载。
4. **`isSending` 时不加 `disabled`** —— 连点重复提交（对话页实测过）。
5. **降级时只写 `animation: none`** —— 球会停在 `top: var(--loader-floor-top)`
   且 `height: 5px`（压扁态），像三个扁饼。必须显式复位到最高点。
