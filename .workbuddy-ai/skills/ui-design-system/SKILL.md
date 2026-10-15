---
name: ui-design-system
description: 校园办事小秘书（Campus-Service-Assistant）前端的 UI 设计与动效体系。This skill should be used when 新增或改动本项目的任意前端界面——写新页面、新组件、改配色、改圆角/间距/阴影、加动效、调响应式断点、做深浅主题适配时。它给出完整的 token 命名表、组件级可复制代码、页面布局骨架、统一的缓动曲线与时长，以及无障碍/性能红线；也适用于审查现有界面是否符合体系（如是否误用原生 select、是否漏了 prefers-reduced-motion、是否踩了页面级滚动的坑）。触发词：UI 规范、设计规范、设计体系、配色 token、主题切换、动效、圆角阴影、页面布局、组件样式、composer-shell、character-bubble、AnimatedButton。
agent_created: true
---

# 校园办事小秘书 · UI 设计与动效体系

## 1. 这份 skill 解决什么

本项目的前端视觉不是"想到哪写到哪"，而是一套已经跑通的体系：颜色全部走 CSS 变量、
边框/光效统一走掩膜写法、动效共用同一批缓动曲线与时长、深浅主题靠 `html[data-theme]`
整体切换。零散改动最容易破坏的就是这套一致性——比如新写一个输入框却自带一套
`border/box-shadow`，或加一个下拉框时用了原生 `<select>` 导致深色主题下对比度崩掉。

本 skill 把这套体系固化成可查、可复制的条目，保证**新组件能基于同一套 token 与
同一套写法扩展**，而不是另起一套。

## 2. 技术栈（沿用，不要替换）

| 项 | 值 |
| --- | --- |
| 框架 | Vue 3.5（`<script setup lang="ts">`）+ vue-router 4 |
| 构建 | Vite 6 + `vue-tsc`（`npm run build` 含类型检查） |
| 样式 | 原生 CSS，**无预处理器、无 Tailwind、无 CSS Modules** |
| 全局样式 | `src/styles/theme.css`（唯一的设计变量来源） |
| 组件样式 | 每个 SFC 的 `<style scoped>`，只写布局，不重复写全局外壳 |
| 图标 | 内联 SVG sprite（`components/AppSprite.vue` + `<use href="#i-*">`） |
| 背景 | 全屏 `<canvas>` 粒子引擎（`components/particle-background/`） |

已有 UI 库：项目依赖里挂了 element-plus，但**界面不依赖它的组件**，不要引入
`el-*` 组件以免出现第二套视觉语言。

## 3. 全局设计原则（改动前先过一遍）

1. **变量优先，字面值例外。** 任何颜色、阴影、光效颜色必须来自 `theme.css` 的
   `--*` 变量。唯一允许写死的是纯装饰性 alpha 数值（如 `color-mix(... 4% ...)`）。
   `color-scheme` 一行不要删——它负责滚动条、光标、拼写下划线等浏览器自带 UI 的明暗。
2. **外壳与布局分离。** 全局类（`.composer-shell` / `.character-bubble` /
   `.animated-button` / `.spark-button`）负责"长什么样"，页面 scoped 样式只负责
   "放哪儿、多大"。**不要在页面里重写 border / background / border-radius /
   focus 样式**，否则会盖掉统一外壳。
3. **光效挂在容器外层。** 任何溢出型光晕 / 描边环 / 背光都不能挂在
   `overflow:auto` 或 `overflow:hidden` 的滚动容器内部（会被裁掉，abs 子元素还会
   跟着内容滚走）。统一在外面包一层 frame。
4. **一条动效 = 一条曲线 + 一个时长 + 一个触发条件。** 曲线只能从
   `motion/motion-tokens.md` 的清单里选，不要自创 cubic-bezier。
5. **每个动画都要有 `prefers-reduced-motion` 分支**，且降级后视觉仍完整
   （是"不动"，不是"消失"）。
6. **真机上肉眼可见的对比度是硬指标。** 正文 ≥ 4.5:1，大字/非文本 ≥ 3:1。
   实测过的关键组合见 `foundations/color-system.md`，不要凭感觉换色。
7. **文案统一**：中文弯引号 “”，不用感叹号，中英混排两侧留半角空格，同一对象
   在全站用同一个词（侧栏叫"支持事项"，面板标题就写"事项"不写"服务"）。
   "清除"是设置页的 destructive 动作；搜索框右侧的按钮统一叫"清空"。

## 4. 目录与调用方式

按需读取，不要一次全读：

```
SKILL.md                          本文件（原则 + 索引）
foundations/
  color-system.md                 ★ 完整色板 token 与明暗主题映射（改动颜色必读）
  typography.md                   字体层级、字号/字重/行高对照
  spacing-radius-shadow.md        间距 / 圆角 / 阴影的取值表与推荐 token
  page-background.md              页面底色与全屏粒子 canvas（含"不能填 --page-bg"的坑）
components/
  button.md                       四类按钮（实心 / spark / 动效描边 / 文本 / 图标）
  input.md                        ★ .composer-shell 统一输入框外壳 + 搜索框 + 表单字段
  card.md                         卡片与列表行（事务行、记录行、FAQ 行、空态）
  navigation.md                   侧栏、顶栏、面包屑、分类 tab、tooltip
  dialog.md                       通知中心弹窗（含角色"趴"在卡片上的定位算法）
  select.md                       自绘下拉 AppSelect（为什么不能用原生 select）
  icon.md                         sprite 基线与 19 个 symbol 清单
  feedback.md                     加载指示器、空态、错误提示、徽标、tooltip
layouts/
  app-shell.md                    ★ .app-shell / .main / .topbar 骨架（含滚动的坑）
  home-layout.md                  首页：角色层 + composer + 右侧面板
  chat-layout.md                  对话页：内部消息流独立滚动
  content-page-layout.md          内容页：帮助 / 事项 / 记录 / 设置 的通用骨架
  responsive.md                   断点表与三档形态（宽桌面 / 窄桌面 / 移动端）
motion/
  motion-tokens.md                ★ 缓动曲线 / 时长 / 触发条件总表（加动效必读）
  composer-flow.md                输入框动态网格 + 边框流光
  theme-ripple.md                 主题切换圆形扩散（View Transitions）
  notice-glow.md                  通知卡片三层光效
  entrance-route.md               入场、路由切换、气泡弹出
  loading.md                      三点跳动加载指示器
  reduced-motion.md               无障碍降级清单
examples/
  README.md                       怎么跑起来
  theme.css                       ★ 可直接复制进项目的完整 token 文件
  design-system.html              单文件演示页（浏览器直接打开，全组件一览）
  AnimatedButton.vue / AppSelect.vue / ComposerField.vue / NoticeCard.vue / AppSprite.vue
```

### 典型调用路径

- **写新页面** → `layouts/content-page-layout.md`（骨架）+ 对应 `components/*.md`
  （零件）+ `foundations/typography.md`（字号）。
- **加一个新组件** → 先查 `components/` 有没有同类；有就复用外壳（`.composer-shell`
  等），没有则按"四部分"模板新增一个条目，命名沿用 `--xx-yy` 与 `.xx-yy`。
- **改配色 / 加主题变量** → `foundations/color-system.md`，**明暗两套必须同时给**，
  并补上 `color-scheme` 影响不到的说明。
- **加动效** → `motion/motion-tokens.md` 选曲线，再抄对应条目的 keyframes，
  最后补 `prefers-reduced-motion` 分支（照 `motion/reduced-motion.md`）。
- **审查现有界面** → 按 `SKILL.md` 第 3 节七条原则逐条过。

## 5. 条目的统一写法

每个条目（一个组件 / 一类动效）固定四部分，标题层级如下：

```
## <组件名>
### 设计思路      —— 解决什么问题、视觉与交互意图、适用场景
### 完整代码      —— 可直接复制，关键参数全部用 token / CSS 变量表示，不省略
### 变体说明      —— 尺寸 / 状态（hover, focus, active, disabled, loading, invalid）
                     / 主题（浅、深）/ 窄屏
### 使用注意事项  —— 可访问性、性能、常见误用
```

写新条目时**照抄这个结构**，变量命名与既有条目保持同一套（见下）。

## 6. 命名约定（全篇一致，扩展时沿用）

| 类别 | 规则 | 示例 |
| --- | --- | --- |
| 颜色 token | `--<域>-<角色>` | `--accent` `--accent-soft` `--accent-hover` `--surface` `--fg` `--muted` `--border` `--danger` `--row-hover` |
| 浮层 token | `--tooltip-*` | `--tooltip-bg` `--tooltip-text` `--tooltip-muted` `--tooltip-border` `--tooltip-shadow` |
| 输入框 token | `--composer-*` | `--composer-grid-line` `--composer-hover-glow` `--composer-flow-hot` |
| 通知光效 token | `--notice-*` | `--notice-ring-hot` `--notice-aura-a` `--notice-glow-core` |
| 动效 token | `--theme-ripple-*` | `--theme-ripple-crest` `--theme-ripple-x` `--theme-ripple-radius` |
| 粒子 token | `--fx-*` | `--fx-particle` `--fx-petal` `--fx-water` |
| 组件内私有变量 | `--<组件>-<属性>` | `--composer-shell-radius` `--bubble-rest` `--bubble-arrow-x` `--loader-ball-size` |
| 全局类 | `.kebab-case` | `.composer-shell` `.character-bubble` `.animated-button` `.spark-button` |
| 状态类 | `.is-*` | `.is-invalid` `.is-active` `.is-selected` `.is-open` `.is-loading` `.is-pending` |
| 图标 id | `i-<name>` | `i-home` `i-chev` `i-arrow-up` |
| 埋点 | `data-od-id="kebab-case"` | `data-od-id="ask-submit"` `data-od-id="nav-home"` |

CSS 注释风格统一为「`/* ── 标题 ── */` + 说明性正文」，说明**为什么**（这条约束是
怎么踩出来的），而不是复述代码在做什么。

## 7. 交付前自检

改动前端后，逐项确认：

- [ ] `npm run build` 通过（含 `vue-tsc` 类型检查）。
- [ ] 新增颜色变量在 `:root` 与 `html[data-theme='dark']` 两处都定义了。
- [ ] 没有在页面 scoped 样式里重写全局外壳的 border / background / 圆角。
- [ ] 新增动画都配了 `prefers-reduced-motion: reduce` 分支。
- [ ] 页面容器按 `layouts/app-shell.md` 的规则处理了滚动（内容超一屏能滚到）。
- [ ] 移动端（≤700px）交互元素 ≥ 44px。
- [ ] 图标来自 sprite，没有引入第二套图标库。
