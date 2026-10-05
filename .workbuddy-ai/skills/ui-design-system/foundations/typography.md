# 字体层级

## 设计思路

**解决的问题**：标题和正文混用一套字体、字号随手取，页面一多就出现"同一个层级
三种字号"的情况。

**视觉与交互意图**：只保留**两条字体栈**——标题用 Epilogue Black（900 字重、紧字距），
正文用 DM Sans（400）。两条都挂了中文回退（PingFang SC → Microsoft YaHei →
Noto Sans SC），因为界面文案以中文为主，西文字体只覆盖拉丁字母与数字。
层级靠**字号 + 字重 + 字距**三件事拉开，而不是靠换字体。

**适用场景**：写任何标题、正文、标签、元信息时取字号；新增页面时定 H1/H2 层级。

## 完整代码

```css
/* ── 字体栈（定义在 :root，明暗主题共用）───────────────────────────────── */
:root {
  --font-display: 'Epilogue', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
  --font-body: 'DM Sans', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
}

/* ── 全局基线 ────────────────────────────────────────────────────────── */
body {
  margin: 0;
  min-height: 100vh;
  background: var(--page-bg);
  color: var(--fg);
  font: 400 15px/1.5 var(--font-body);   /* 正文基线：15px / 行高 1.5 */
  font-synthesis: none;                  /* 不允许浏览器合成假粗体 */
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  /* 双击粒子爆发与文本选区冲突：默认禁选，仅内容区与输入框恢复 */
  user-select: none;
  -webkit-user-select: none;
}

input,
textarea {
  user-select: text;
  -webkit-user-select: text;
}
```

### 层级取值表（直接抄，不要自创）

```css
/* ── 页面主标题 H1：帮助 / 事项 / 记录 / 设置 四页共用 ────────────────── */
.page-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(32px, 4.4vw, 54px);
  font-weight: 900;
  line-height: 1.28;          /* 设置页用 1.3 */
  letter-spacing: -.025em;    /* 大字号必须收紧，否则中文看着散 */
}

/* ── 对话页 H1（比首页系页面小一档）─────────────────────────────────── */
.chat-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(24px, 3vw, 32px);
  font-weight: 900;
  line-height: 1.35;
  letter-spacing: 0;
}

/* ── 通知中心标题 ──────────────────────────────────────────────────── */
.dialog-title {
  margin: 12px 0 7px;
  font-family: var(--font-display);
  font-size: clamp(25px, 4vw, 34px);
  font-weight: 900;
  letter-spacing: -.03em;
}

/* ── 卡片内小标题（联系卡片、面板标题）──────────────────────────────── */
.card-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 800;
  line-height: 1.35;
}

.panel-title {                 /* 首页右侧面板 h2 */
  margin: 0;
  font-family: var(--font-display);
  font-size: 16.5px;
  font-weight: 900;
  letter-spacing: -.012em;
}

/* ── 分区标题（设置页 / 帮助页的 section h2）───────────────────────── */
.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 650;
  line-height: 1.45;
}

/* ── 列表项标题 ────────────────────────────────────────────────────── */
.item-title {
  margin: 0;
  font-size: 14px;
  font-weight: 550;
  line-height: 1.45;
}

/* ── 列表小标题（列表头、section-heading）───────────────────────────── */
.list-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding-bottom: 13px;
  border-bottom: 1px solid var(--border);
  color: var(--fg);
  font-size: 13px;
  font-weight: 550;
}

/* ── 元信息 / 次要说明 ─────────────────────────────────────────────── */
.meta {
  color: var(--muted);
  font-size: 11px;             /* 时间戳 */
}
.meta-strong {
  color: var(--fg);
  font-size: 12px;
  font-weight: 600;
}
.muted-copy {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}
.body-copy {
  max-width: 48ch;             /* 正文/说明的舒适行宽 */
  margin: 16px 0 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.8;
}
.long-copy {
  max-width: 72ch;
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.8;
}

/* ── 标签 / kicker ─────────────────────────────────────────────────── */
.kicker {
  display: inline-flex;
  padding: 5px 9px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .14em;       /* 小字号全大写感，靠字距撑开 */
}

/* ── 面包屑 ────────────────────────────────────────────────────────── */
.crumb {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 12.5px;
  color: var(--muted);
}
.crumb strong {
  color: var(--fg);
  font-weight: 500;
}

/* ── 输入框文字 ────────────────────────────────────────────────────── */
.field-text {
  font: 400 13px/1.5 var(--font-body);     /* 搜索框 / 下拉触发器 / 表单字段 */
}
.composer-text {
  font: 400 15px/1.6 var(--font-body);     /* 主输入区 */
}
.composer-hint {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

### 字号阶梯（从实测值归纳，新组件按档取）

| 档 | 字号 | 字重 | 字体栈 | 典型用途 |
| --- | --- | --- | --- | --- |
| Display-1 | `clamp(32px, 4.4vw, 54px)` | 900 | display | 页面 H1 |
| Display-2 | `clamp(24px, 3vw, 32px)` | 900 | display | 对话页 H1 |
| Display-3 | `clamp(25px, 4vw, 34px)` | 900 | display | 弹窗标题 |
| Title | 20px | 800 | display | 卡片内标题 |
| Section | 16.5px / 16px | 900 / 650 | display / body | 面板 h2、分区 h2 |
| Item | 14px | 550 | body | 列表项标题、FAQ 问题 |
| Body | 15px | 400 | body | 正文基线、消息气泡 |
| Control | 13px | 500 / 600 | body | 按钮、输入框、下拉 |
| Meta | 12px | 400 / 550 | body | 元信息、提示文案、表头 |
| Caption | 11.5 / 11px | 400 | body | 时间戳、分类标签 |
| Kicker | 10px | 700 | body | 全站小标签 |

## 变体说明

| 变体 | 规则 |
| --- | --- |
| **移动端（≤700px）** | H1 沿用 clamp 下限，不再单独降；输入框字号提到 **16px**（低于 16px 会触发 iOS Safari 自动缩放）；`.panel h2` 提到 `clamp(22px, 6.3vw, 30px)` 并加 `line-height:1.25`；FAQ 问题 `white-space` 从 `nowrap` 放开为 `normal`。 |
| **窄桌面（≤1080px）** | 字号不变；侧栏文字用 `.sr-only` 隐藏（图标仍可读）。 |
| **矮视口（≤660px 高）** | 首页 `.composer-hint` 隐藏、`.chips` 隐藏，靠删内容而非缩字号。 |
| **禁用 / 加载** | 字号永远不变；`font-synthesis: none` 保证 fake bold 不会出现。 |
| **深色主题** | 字重与字号完全不变，只换 `--fg` / `--muted`。深色下 `--muted` 提到 L70%（浅色 50%）以维持同等观感对比。 |

## 使用注意事项

**可访问性**
- 字号最小到 10px（kicker），且必须加 `letter-spacing` 撑开；**不要再做更小的字**。
- `font-synthesis: none` 不要删：DM Sans 只有 400 一个字重文件，界面里出现的
  550 / 600 / 650 若允许合成，中文会被拉成假粗体、糊成一团。
- 标题用 `clamp()` 而非媒体查询，保证任意视口宽度下都是连续过渡。
- 触摸目标 ≥ 44px 是尺寸问题不是字号问题——**不要靠放大字号去凑点击区域**。

**性能**
- 只加载两个字重的 woff2（DM Sans 400 / Epilogue 900），`font-display: swap`。
  不要为了 550/650 再拉一份字体文件。
- 中文字体走系统回退（PingFang SC / Microsoft YaHei / Noto Sans SC），
  **不要自托管中文 webfont**（体积大且画风跟西文不搭）。

**常见误用**
1. 给正文加 `font-weight: 500` 想"稍微强调一下" —— 会被 `font-synthesis: none`
   拦掉，正确做法是换 `--fg` 或换层级。
2. 在 scoped 样式里写 `font-family: system-ui` —— 破坏统一栈，中文回退链丢失。
3. 用 `letter-spacing` 去修大标题的松散感之外的用途 —— 中文正文加正字距会显脏。
4. 忘记 `user-select`：`body` 全局禁选，新加的可读长文（FAQ 答案、记录详情）
   必须显式恢复 `user-select: text`，否则用户选不中文字。
