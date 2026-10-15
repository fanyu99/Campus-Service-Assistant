# 校园办事小秘书 · 前端代码审查 + 前后端架构一致性审查 + API 文档修正

**日期**：2026-10-07
**场景**：代码审查 + 架构审查 + API 契约修正（含落地调整）
**评审依据**：`plans/校园办事小秘书实施方案.md`
**参与成员**：产品官（产品评审员）+ 排障手（调查员）+ 安全卫士（安全官）+ 质量门神（QA 与发布）+ 设计师（设计顾问）

---

## 📌 TL;DR（执行摘要）

- **整体结论：🔴 不通过**（作为「可演示、可答辩的完整作品」）；若仅作为**纯前端 UI 原型**评审则为 🟢 通过。
- 根因高度集中：**实施方案承诺的「可信闭环」实体 100% 缺失**——无 `backend/`、无知识库、无 AgentArts 适配层、无测试；六个页面全部跑在 mock 上，`api/client.ts` 写好了但零调用。
- 本次已落地 **9 项修复**：跨页资料失效、API 契约与计划不符、Element Plus 空引入（主 chunk 1,084 kB → 136 kB）、清数据遗漏、部署编排不自洽、API 文档过期等。
- 阻塞项数量：**4 个 P0**（均为「后端 + 接线 + 测试」三类，本次无法在纯前端范围内闭环）。
- 下一步：先补 `backend/`（健康检查 / 事项 / 问答 / 反馈）+ 4 个 P0 事项知识库 + 前端接线与 6 态渲染，再谈验收指标。

---

## 🎯 核心结论卡片

| 项目 | 内容 |
|------|------|
| Go / No-Go | 🔴 **No-Go**（完整作品）／ 🟢 Go（仅前端原型） |
| 严重度分布 | 🔴 6 / 🟠 9 / 🟡 13 |
| 关键行动项 | 12 条（其中 P0 4 条） |
| 本次已修复 | 9 项（详见「本次已落地的调整」） |
| 建议负责人 | 后端/适配层 → 成员三；知识库 → 成员一；接线与 6 态 UI → 成员二；契约维护 → 全员 |

---

## 1. 各成员核心结论

### 🔍 产品官（产品与架构一致性）
- 核心判断：**No-Go**。架构分层表显示后端 FastAPI、MySQL+Alembic、AgentArts 适配层、知识库（raw/processed/faq/metadata）、测试**五层全部为 ❌**；实施方案第二章 4 节的 7 项验收指标**完成度 0%、不可测**，仅「前端构建成功」可达成。
- 关键建议：先做 P0-1~P0-4（FastAPI 服务 / 4 个 P0 事项知识库与结构化 `answer` 契约 / 前端接线与 6 态渲染 / 核心接口自动化测试）；Element Plus、P1 事项、知识维护页、Alembic 可降级。

### 🔧 排障手（前端代码根因）
- 核心判断：根因是**缺少共享的 profile / conversation 状态源**——设置、身份、会话三处各写各的、互不读取，叠加「API 层写好却未接线」「Element Plus 全量空引入」，属典型「貌似完整、实则未联通」的演示态代码。
- 关键建议：抽 `useProfile` 统一键与字段（设置页写 `campus-service-assistant-settings`，首页却读 `campus-assistant.user` 等四个键）；接线 `client.ts`；删 Element Plus；`clearLocalData` 补删草稿键。

### 🛡️ 安全卫士（OWASP + STRIDE）
- 核心判断：当前仅前端静态原型，**无后端、无鉴权、无 TLS**，攻击面小，但**接口契约已埋下隐患**：`/api/conversations` 匿名全量返回可枚举他人咨询（A01 🔴）、`message` 直达 LLM 无注入过滤（A03 🟠）、无限流/长度上限（DoS 🟠）、错误体直出可能泄露内部信息。
- 关键建议：后端实现时按 A01 / A03 / 限流 / HTTPS 先行加固；隐私侧 ✅ 未触碰红线（localStorage 仅存偏好与草稿，无学号/身份证/密码）。

### ✅ 质量门神（QA 与发布）
- 核心判断：**No-Go**。前端构建成功（39s，无 TS 错误）但主 chunk **1,084 kB** 触发警告；测试链路**整体缺失**（无 `test` 脚本、无 vitest、无后端 pytest），验收硬指标「核心接口自动化测试 100%」**不可判定**。
- 关键建议：`docker-compose.yml` 补 `backend` 服务（现仅 frontend，而 `nginx.conf` 反代到 `http://backend:8000` → `/api/*` 必然 502）；补前端 test 脚本与后端测试；`manualChunks` 拆包 / 图片转 WebP。

### 🎨 设计师（页面视觉与交互）
- 核心判断：页面外壳（topbar / 侧栏 / 主题 / composer）工艺精良、a11y 底子扎实，但**核心业务 UI 尚未落地**——6 种状态、结构化答案卡片、来源列表、反馈栏**全部缺失**，`ChatView` 本质是静态 mock，产品最核心卖点「有来源、可核验、能执行」**在 UI 上无法演示**，属 Critical 级差距。
- 关键建议：优先补 `AnswerCard` / `SourceList` / `FeedbackBar` 三组件与 6 态视觉；统一搜索/筛选范式与 `SERVICE_ICON`；补 `theme-color` 随主题变化。

---

## 2. 综合审查发现（去重合并，按严重度排序）

| # | 严重度 | 类别 | 位置 | 问题 | 建议 | 来源 | 本次状态 |
|---|--------|------|------|------|------|------|---------|
| 1 | 🔴 | 架构 | 仓库根 | 无 `backend/`、`knowledge/`、`scripts/`；无 FastAPI / MySQL / AgentArts 适配层 | 按实施方案第六章补齐后端与知识库 | 产品官 | 待办 |
| 2 | 🔴 | 契约 | `api/client.ts:30`（原） | `answer` 定义为 `string \| null`，实施方案 §8.1 要求结构化对象 | 定义 `AnswerCard` 类型 | 产品官 / 排障手 | ✅ 已修复 |
| 3 | 🔴 | 功能 | `views/ChatView.vue:104-113` | 6 种 `status` + 结构化答案卡片 + 来源 + 反馈栏前端零覆盖 | 建 `AnswerCard`/`SourceList`/`FeedbackBar` 与 6 态渲染 | 设计师 / 产品官 | 待办 |
| 4 | 🔴 | 功能 | `ChatView.vue` / `HomeView.vue` / `ServicesView.vue` / `HistoryView.vue` | 全部使用 mock，`client.ts` 三函数零调用 | 逐页接真实接口 | 产品官 / 质量门神 | 待办 |
| 5 | 🔴 | 测试 | `package.json` | 无 `test` 脚本、无 vitest；后端无 pytest | 补测试链路 | 质量门神 | 🟡 部分修复（前端已补 6 个用例） |
| 6 | 🔴 | 功能 | `HomeView.vue:50-64` vs `SettingsView.vue:42-44` | 资料键名/字段不匹配，设置页改名全站不生效 | 抽 `useProfile` 单一数据源 | 排障手 / 设计师 | ✅ 已修复 |
| 7 | 🔴 | 安全 | `docs/api.md` §4.4（原） | `GET /api/conversations` 匿名全量返回，可枚举他人会话（A01） | 按匿名 token 隔离，禁全量 | 安全卫士 | ✅ 已写入契约硬性要求 |
| 8 | 🟠 | 部署 | `docker-compose.yml` ↔ `nginx.conf:23-33` | compose 无 `backend` 服务，反代目标不存在 → `/api/*` 必然 502 | 补 backend 服务 | 质量门神 / 安全卫士 | ✅ 已补编排意图 + 明确阻塞 |
| 9 | 🟠 | 包体 | `main.ts:2-3,8`、`package.json` | Element Plus 全量引入 + 全量 CSS，全站零使用，主 chunk 1,084 kB | 删除引入与依赖 | 产品官 / 排障手 / 质量门神 | ✅ 已修复（→136 kB） |
| 10 | 🟠 | 安全 | `client.ts` / 提示词 | `message` 直达 AgentArts，无输入清洗落地（A03 提示词注入） | 后端做注入过滤 + 输出白名单 | 安全卫士 | ✅ 已写入契约要求 |
| 11 | 🟠 | 安全 | — | 无速率限制 / 无 `message` 长度上限 → LLM 成本放大（DoS） | 限流 + 长度上限 + 熔断 | 安全卫士 | ✅ 已写入契约要求 |
| 12 | 🟠 | 安全 | `nginx.conf:2` | 仅 `listen 80`，无 HTTPS/HSTS 约定 | 生产 HTTPS 终结 + TLS1.2+ | 安全卫士 | 待办 |
| 13 | 🟠 | 身份 | `AppSidebar.vue:91-92,96`、各页 topbar | 用户身份硬编码「林/林同学」 | 消费 `useProfile` | 排障手 / 设计师 | ✅ 已修复 |
| 14 | 🟠 | 功能 | `SettingsView.vue:36-40` | `clearLocalData` 只删设置键，未删首页草稿键 | 一并清除 | 排障手 | ✅ 已修复 |
| 15 | 🟠 | 范围 | `plans/` vs 实现 | 计划要求 Vitest/Pytest、目录规划、Element Plus 均未落实 | 对齐计划或修订计划 | 产品官 | 部分修复 |
| 16 | 🟠 | 文档 | `frontend/docs/api.md` | 称「client.ts 没有定义问答响应接口」，与实现不符 | 重写为指向权威文档 | 产品官 | ✅ 已修复 |
| 17 | 🟡 | 维护 | `HomeView.vue:26` / `ServicesView.vue:22` | `SERVICE_ICON` 双份维护，Services 多两项 → 漂移风险 | 抽共享模块 | 设计师 / 排障手 | ✅ 已修复 |
| 18 | 🟡 | 维护 | `ServicesView.vue:14-18`、`HistoryView.vue:9` | mock 数据源重复；`HistoryView` 按下标伪造 `status/detail` | 统一数据源，接 `GET /api/conversations` | 排障手 | 待办 |
| 19 | 🟡 | 交互 | `ChatView.vue:116-124`、`App.vue:149` | 已有消息时二次 `route.query.q` 被忽略；`key=route.fullPath` 使 query 变即整页重挂 | 明确会话生命周期设计 | 排障手 | 待办（已记录） |
| 20 | 🟡 | 一致性 | `ServicesView.vue:50` | 搜索框缺放大镜图标（History/Help 有） | 补 `#i-search` | 设计师 | ✅ 已修复 |
| 21 | 🟡 | 一致性 | `HistoryView.vue` vs `ServicesView`/`HelpView` | 筛选范式分叉（`filter-tab` vs `category-tab`） | 抽统一范式 | 设计师 | 待办 |
| 22 | 🟡 | 一致性 | `index.html:6` | `theme-color` 固定浅色 `#f4f2ed`，不随主题变化 | 随主题动态更新 | 设计师 | ✅ 已修复 |
| 23 | 🟡 | a11y | `AppSidebar.vue:107`、`ServicesView.vue:51`、`HelpView.vue:57` | `brand-mark-glow` 无 reduced-motion 兜底；`role=list` 缺 `listitem`；FAQ 缺 `aria-controls/id` | 逐项补齐 | 设计师 | 待办 |
| 24 | 🟡 | a11y | `theme.css:426` | ≤700px topbar 隐藏 → 移动端无主题快捷切换 | 评估移动端入口 | 设计师 | 待办（已知取舍） |
| 25 | 🟡 | 范围 | `ServicesView.vue:17` | 演示项 `network` 不在实施方案 8 项事务内 | 移除或正式纳入 | 设计师 | ✅ 已在契约中标注 |
| 26 | 🟡 | 范围 | 仓库根 | 缺 `README.md`、`.env.example`、`docs/requirements|architecture|knowledge-governance|test-report|demo-script.md` | 按计划补齐 | 产品官 | 待办 |
| 27 | 🟡 | 性能 | `dist/assets/character.png` 等 | 图片合计 ~4 MB（`character.png` 1.59 MB） | 转 WebP / 压缩 | 质量门神 | 待办 |
| 28 | 🟡 | 健壮性 | `client.ts:75`（原） | 非 JSON 的 2xx 被误判为「网络异常」 | 区分解析失败 | 排障手 | ✅ 已修复 |

---

## ✅ 本次已落地的调整（交付清单）

### 代码变更

| 文件 | 变更 |
|---|---|
| `frontend/src/composables/useProfile.ts` | **新增**：个人资料单一数据源，统一存储键与字段；`setProfile` 与 `useTheme` 的 `theme` 字段 merge；`clearLocalData` 一并清设置与草稿 |
| `frontend/src/data/service-icons.ts` | **新增**：`SERVICE_ICON` + `FALLBACK_SERVICE_ICON` 共享模块 |
| `frontend/src/api/client.ts` | **重写**：`answer` 改为结构化 `AnswerCard`；补 `intent` / `need_clarification`；补 `checkHealth()` / `fetchConversations()`；错误处理区分 204/空响应/非法 JSON；`Headers` 正确合并；新增 `isSafeSourceUrl()` |
| `frontend/src/main.ts` | 移除 Element Plus 全局引入与全量 CSS |
| `frontend/package.json` | 移除 `element-plus` / `@element-plus/icons-vue`；新增 `vitest` / `jsdom` 与 `test` 脚本 |
| `frontend/src/composables/useTheme.ts` | `paint()` 同步 `<meta name="theme-color">` |
| `frontend/src/views/HomeView.vue` | 删除 4 个错误 localStorage 键的读取；改用 `useProfile`；修复「林同学同学」重复拼接；共用 `SERVICE_ICON` |
| `frontend/src/views/SettingsView.vue` | 改用 `useProfile` 的 computed 双向绑定；`clearLocalData` 一并清草稿 |
| `frontend/src/components/AppSidebar.vue` | 侧栏身份改为消费 `useProfile`（不再硬编码） |
| `frontend/src/views/ChatView.vue` / `ServicesView.vue` / `HistoryView.vue` / `HelpView.vue` | topbar 头像与 aria-label 改为消费 `useProfile`；Services 搜索框补放大镜图标 |
| `frontend/tests/client.spec.ts`、`frontend/tests/useProfile.spec.ts`、`frontend/vitest.config.ts` | **新增**：6 个单元测试 |
| `frontend/tsconfig.json` | `include` 加入 `tests/**/*.ts` |
| `docker-compose.yml` | 补齐「计划中的另一半」编排（backend / db / volumes，注释态）并写明现状与启用步骤 |
| `docs/api.md` | **新增（权威契约 v1.0）**：定稿错误结构、错误码、6 态语义、标识符规范、字段映射、变更记录 |
| `frontend/docs/api.md` | 重写为指向权威文档 + 前端侧要点，消除双份来源 |

### 验证结果

| 项目 | 结果 |
|---|---|
| `npm run build`（含 `vue-tsc` 类型检查） | ✅ 通过，77 modules，5.41s |
| 主 chunk 体积 | ✅ **1,084.54 kB → 135.90 kB**（gzip 356.72 kB → 51.77 kB，↓ 87%） |
| `npm run test` | ✅ 2 文件 / 6 用例全部通过 |
| 残留检查 | ✅ 无 `element-plus` 引用、无硬编码「林同学」头像、`SERVICE_ICON` 仅一处定义 |

### 发布检查清单

- [x] 类型检查通过
- [x] 构建通过、产物体积下降
- [x] 前端单元测试可运行且通过
- [x] 接口契约文档与实际类型一致
- [ ] 后端服务（`/api/health`、`/api/service-items`、`/api/chat/messages`、`/api/feedback`）——**阻塞**
- [ ] 4 个 P0 事项知识库与结构化 `answer` 数据——**阻塞**
- [ ] 前端六页接线 + 6 态渲染 + 来源 + 反馈闭环——**阻塞**
- [ ] 接口级自动化测试（验收硬指标 100%）——**阻塞**

### 回滚预案

本次改动均为前端源码与配置，**未触碰任何后端或数据**。如需回滚：
`git checkout -- frontend/ docs/ docker-compose.yml`（新增文件用 `git clean -f` 清理），
依赖恢复 `npm install`。建议先 `git stash` 再验证。

---

## ⚠️ 待完善 / 已知局限

1. **后端整体缺失**是本次审查最重要的结论，也是唯一无法在「前端代码审查」范围内闭环的 P0；本报告只能把它标为阻塞项并给出实现规格。
2. 本次修复的**接口契约是「按实施方案推导的定稿」**，后端尚未实现，仍存在落地时调整的可能——调整必须走 `docs/api.md` §8 变更记录。
3. `docs/api.md` §3.5 对「`S01` vs `student_card_reissue`」做了统一裁定（取 `S01`），这与实施方案 §8.1 的示例不一致，**建议同步修订实施方案**。
4. `ChatView` 的会话生命周期（`App.vue` 的 `key=route.fullPath` 重挂 vs 页面内 query 变化）未做行为改动，仅记录——它依赖后端会话模型定型后再决定。
5. 未做视觉回归截图（遵循用户既有偏好：不留自生成校验图，效果由用户自行在浏览器确认）。
6. 安全审计中的 A02/A05/A09/A10 等条目依赖后端实现，已列入「待后端复评清单」。

---

## 📚 成员产出索引

- **产品官（gstack-product-reviewer）**：架构分层落地表、计划-实现偏差清单（7 条）、验收指标可达成性评估、P0 阻塞项 P0-1~P0-4。
- **排障手（gstack-investigator）**：根因 R1–R7、代码异味与健壮性扫描、P0/P1/P2 分级。
- **安全卫士（gstack-security-officer）**：STRIDE 威胁表（6 类）、OWASP Top 10 检查表（A01–A10）、隐私最小化结论、8 项待后端复评清单。
- **质量门神（gstack-qa-lead）**：测试缺口表、部署链路不一致分析与失败表现、构建健康度实测、上线前检查清单与 Go/No-Go。
- **设计师（gstack-designer）**：一致性问题 C1–C8、状态与组件覆盖缺口表、可访问性结论、响应式结论。

---

> 本报告由软件工坊 AI 协作生成，关键决策请由工程负责人复核。
