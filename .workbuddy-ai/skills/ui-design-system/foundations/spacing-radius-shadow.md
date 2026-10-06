# 间距、圆角与阴影

## 设计思路

**解决的问题**：项目里这三个维度目前是**字面值**，没有 token 化。这本身不构成
bug，但每次新增组件都要"照着隔壁抄一个差不多的值"，时间一长就出现
`12px / 13px / 14px` 三种圆角并存、阴影深浅不一的碎片化。

**视觉与交互意图**：
- **间距**：4px 基准栅格。栅格内允许 2px 的半步（用于紧凑对齐，如 `gap: 10px`、
  `padding: 14px`），但**不要出现 3px / 7px 这种非栅格值**做外间距。
- **圆角**：跟"容器层级"绑定——越大的容器圆角越大（卡片 32px > 面板 18px >
  列表行 12px > 按钮 13px > 图标块 9~11px），形成可辨识的层级序列。
- **阴影**：**只用两种手法**——① `0 <y> <blur> color-mix(in srgb, var(--fg) N%, transparent)`
  做"离地感"；② `0 0 0 Npx <glow-token>` + `0 0 <blur> <glow-token>` 做"发光感"。
  不写第三种。

**适用场景**：新增任何容器 / 列表 / 浮层时取圆角与阴影；排版时取间距。

## 完整代码

### 推荐 token（新代码照此写；既有字面值逐步迁移）

把这段加到 `:root`（与 `color-system.md` 的变量同文件）：

```css
:root {
  /* ── 间距：4px 栅格，允许 2px 半步 ─────────────────────────────────── */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-14: 56px;
  /* 语义化间距：改布局时改语义值，不动栅格 */
  --gap-tight: 6px;        /* 图标与文字 */
  --gap-inline: 10px;      /* 行内元素默认间距 */
  --gap-block: 14px;       /* 区块之间 */
  --pad-card: clamp(30px, 4vw, 44px) clamp(22px, 5vw, 48px) 28px;
  --pad-row: 6px 10px;     /* 列表行内边距 */
  --pad-shell: 0 clamp(20px, 2.8vw, 40px);   /* .main 左右 */

  /* ── 圆角：按容器层级递增 ─────────────────────────────────────────── */
  --radius-icon: 9px;      /* 头像、图标块（30px 级） */
  --radius-control: 11px;  /* 图标按钮、次要按钮（34~42px 级） */
  --radius-chip: 999px;    /* pill：分类 tab、kicker、spark 按钮 */
  --radius-row: 12px;      /* 列表行、面板内选项 */
  --radius-btn: 13px;      /* 实心按钮 */
  --radius-panel: 18px;    /* 面板、联系卡片、字符气泡 */
  --radius-composer: 24px; /* 输入框外壳（--composer-shell-radius 覆盖） */
  --radius-card: 32px;     /* 大卡片（通知卡，窄屏 25px） */

  /* ── 阴影：只有「离地」与「发光」两种 ─────────────────────────────── */
  --shadow-rest: 0 7px 18px color-mix(in srgb, var(--fg) 4%, transparent);
  --shadow-raise: 0 14px 30px color-mix(in srgb, var(--fg) 9%, transparent);
  --shadow-card: 0 26px 64px color-mix(in srgb, #172033 24%, transparent),
                 0 8px 26px color-mix(in srgb, var(--fg) 9%, transparent);
  --shadow-bubble: 0 10px 24px color-mix(in srgb, var(--fg) 8%, transparent);
  --shadow-accent-btn: 0 8px 18px color-mix(in srgb, var(--accent) 24%, transparent);
  --shadow-accent-btn-hover: 0 11px 28px color-mix(in srgb, var(--accent) 35%, transparent),
                             0 0 0 4px color-mix(in srgb, var(--accent) 15%, transparent);
  /* 浮层阴影已存在同名 token：--tooltip-shadow，不要重复定义 */
}
```

### 圆角取值表（实测归纳，新组件按容器大小取）

| 元素 | 圆角 | 备注 |
| --- | --- | --- |
| 头像 `.avatar`（30px） | 9px | |
| 图标块 `.row-icon`（30px）/ `.notification-item-icon`（34px） | 9px / 11px | |
| 图标按钮 `.icon-btn`（34px） | 11px | |
| 侧栏导航项（40px 高） | 11px | 移动端 12px |
| 次要按钮 `.secondary-button` | 11px | |
| 下拉弹层 `.select-panel` | 14px | 选项 10px |
| 实心按钮 `.send` | 13px | 高度 38px |
| 列表行 `.row` / `.recent-row` | 12px | |
| 通知列表项 | 17px | |
| 角色气泡 `.character-bubble` | 18px | 小箭头 12px 方块转 45° |
| 联系卡片 `.help-contact` | 18px | |
| 输入框 `.composer-shell` | 24px（默认） | 移动端 22px / 矮视口 20px |
| 动效按钮 `.animated-button` | 100px → 悬停 12px | 圆角本身参与动画 |
| 通知卡片 | 32px（窄屏 25px） | 走 `--notice-card-radius` |
| pill / 圆形 | 999px / 50% | 分类 tab、kicker、spark 按钮、头像圆 |

### 阴影取值表（实测归纳）

| 元素 / 状态 | 阴影 |
| --- | --- |
| 输入框静止 | `0 7px 18px color-mix(in srgb, var(--fg) 4%, transparent)` |
| 输入框 hover | `0 0 0 2px var(--composer-hover-glow), 0 0 22px var(--composer-hover-glow), 0 14px 30px color-mix(in srgb, var(--composer-hover-glow) 60%, transparent)` |
| 输入框 focus | `0 0 0 3px var(--composer-focus-glow), 0 0 30px var(--composer-focus-glow), 0 16px 38px color-mix(in srgb, var(--composer-focus-glow) 64%, transparent)` |
| spark 按钮静止 | `0 8px 18px color-mix(in srgb, var(--accent) 24%, transparent)` |
| spark 按钮 hover | `0 11px 28px color-mix(in srgb, var(--accent) 35%, transparent), 0 0 0 4px color-mix(in srgb, var(--accent) 15%, transparent)` |
| 角色气泡 | `0 10px 24px color-mix(in srgb, var(--fg) 8%, transparent)` |
| 通知卡片 | `0 26px 64px color-mix(in srgb, #172033 24%, transparent), 0 8px 26px color-mix(in srgb, var(--fg) 9%, transparent)` |
| 品牌圆标 / 消息头像 | `0 0 0 1px color-mix(in srgb, var(--accent) 45%, transparent), 0 0 16px color-mix(in srgb, var(--accent) 38%, transparent), 0 1px 3px rgba(80,30,10,.14)` |
| 加载球 | `0 3px 8px color-mix(in srgb, var(--accent) 26%, transparent)` |
| 浮层（tooltip / 下拉） | `var(--tooltip-shadow)` |

### 间距速查（实测归纳）

| 场景 | 值 |
| --- | --- |
| 图标 ↔ 文字 | 6~10px（侧栏 10px、按钮 7px、搜索框 9px） |
| 列表行内边距 | `6px 10px`（首页事务行）/ `7px 10px`（记录行）/ `14px`（通知项） |
| 列表行间距 | `gap: 2px`（首页）/ `gap: 10px`（通知） |
| 卡片内边距 | `clamp(30px,4vw,44px) clamp(22px,5vw,48px) 28px` |
| 页面内容区 | `width: min(1020px,100%); margin:auto; padding: clamp(26px,5vh,70px) 0 clamp(30px,5vh,72px)` |
| 顶栏 | 高 58px，`gap:16px` |
| 侧栏 | 宽 200px，`padding: 22px 14px 16px` |
| 主区左右 | `padding: 0 clamp(20px, 2.8vw, 40px)` |
| 首页工作区 | `gap: clamp(20px, 2.4vw, 38px)` |

## 变体说明

| 变体 | 规则 |
| --- | --- |
| **移动端（≤700px）** | 输入框圆角 24→22px；通知卡 32→25px；列表行 `min-height` 提到 52px、`padding: 8px`；主区 padding 变成 `6px 24px 0`。 |
| **矮视口（≤660px 高）** | 输入框圆角 → 20px、`padding: 10px 12px 8px`；靠压缩 padding 而不是改圆角数值体系。 |
| **窄桌面（≤1080px）** | 侧栏 200→74px；首页右面板 340→272px（≤940px 再降到 250px）。 |
| **hover / focus / active / disabled** | 圆角与间距**永远不变**；只有阴影与颜色变。`active` 用 `transform`（`translateY` 回位或 `scale(.95~.98)`）表达按压，不改阴影。 |
| **invalid** | 只换描边渐变色到 `--danger`，圆角/间距/阴影不动。 |
| **loading** | 按钮变 `min-width` 保底 + 内部换加载指示器；不要改 padding 让按钮抖动。 |
| **深色主题** | 圆角与间距完全不变。阴影里写死的 `#172033` 与 `rgba(80,30,10,.14)` 是**深浅共用**的（它们模拟的是"环境光"而非"底色"），实测两套主题下都成立，不要改成变量。 |

## 使用注意事项

**可访问性**
- 44px 是移动端的**最小可点区域**，不是视觉尺寸。视觉上仍是 34px 图标按钮时，
  移动端用 `width/height: 44px` 或 `min-height: 44px` 撑开透明区域。
- 焦点环全局统一：`:where(button,[href],input,textarea,[tabindex]):focus-visible {
  outline: 2.5px solid var(--fg); outline-offset: 2px }`。**不要在组件里改 outline 宽度**，
  只有被 `overflow:hidden` 裁掉时才用负 offset 画到内侧（见 AppSelect 触发器）。

**性能**
- 阴影里用 `color-mix(in srgb, var(--fg) 4%, transparent)` 而不是 `rgba(0,0,0,.04)`：
  前者在深色主题下会自动变成"深色投影"，后者在深底上完全看不见。
- `box-shadow` 的大 blur（>40px）+ `filter: blur()` 同时用会明显掉帧。通知卡的
  背光已经用了 `will-change: opacity,transform,filter`，新增同类效果照抄这个组合。
- 不要在滚动容器的直接子元素上挂大面积 blur 光效——滚动时每帧重绘。

**常见误用**
1. **用 `padding` 制造层级** —— 层级靠圆角序列和分隔线，不靠 padding 大小。
2. **圆角超过容器短边的一半** —— 会出现"胶囊化"的意外形状；pill 请显式用 999px。
3. **在 `overflow:auto` 容器内部放外发光** —— 一定被裁掉。见 `components/dialog.md`
   的 frame 分层写法。
4. **给 `box-shadow` 写第三层"中间调"** —— 两种手法之外的第三种会让阴影风格漂移；
   需要更立体就调 `--shadow-raise` 的 alpha 档位。
5. **`margin-inline: -10px; width: calc(100% + 20px)`**（列表行"破格"写法）只用于
   首页右面板的窄列，其他页面不要复制——它会让行的可点区超出容器，在移动端
   容易触发横向滚动。
