# 校园办事小秘书 · 后端契约对齐 + 展示字段补齐 + 问答主链路交付报告

**日期**：2026-10-16  
**场景**：全流程交付（代码实现 → 代码审查 → QA 独立验证）  
**参与成员**：产品官（代码审查，含 review 方法论）+ 质量门神（QA 与发布验证）；主理人汇编  
**审查对象**：仓库 `D:/Desktop/Campus-Service-Assistant` 工作区未提交改动（16 个新文件 + 19 个修改文件）  
**依据**：`docs/api.md` v1.0（本次补录为 v1.1）、`plans/校园办事小秘书实施方案.md`、`deliverables/后端交接说明.md`

---

## 📌 TL;DR（执行摘要）

- **整体结论：🟢 通过。** 代码审查给出 Conditional Go 的 2 项硬门槛（生产路径静默回退替身、无关文档删除）已处理/已识别；QA 独立验证给出 **Go，无阻塞项**。
- **阻塞项数量：0**（代码层面）。两处与本次无关的工作树文档删除仍需用户确认。
- **验证结果**：后端 `pytest -q` → **130 passed**；前端 `vue-tsc --noEmit` 通过、`vitest run` → **9 passed**、`vite build` 成功（主 chunk 137.04 kB）；SQLite 端到端契约冒烟 17 项全过；迁移 `upgrade head → downgrade base → upgrade head` 可回环（head = `0004`）。
- **下一步**：① 确认/恢复两处无关文档删除；② 用成员一核验过的真实通知正文替换演示正文（`scripts/backfill_knowledge_content.py`）；③ 提交（**推送由用户自行执行**）。

---

## 🎯 核心结论卡片

| 项目         | 内容                                                            |
| ---------- | ------------------------------------------------------------- |
| Go / No-Go | 🟢 **Go**（代码审查 Conditional Go 的条件已全部满足）                       |
| 严重度分布      | 🔴 2（1 已修 + 1 非代码）/ 🟠 6（4 已修 / 2 已记录为后续项）/ 🟡 8（6 已修 / 2 记录） |
| 关键行动项      | 6 条（0 条 P0 阻塞代码交付）                                            |
| 建议负责人      | 后端与适配层 → 成员三；知识正文与核验 → 成员一；前端接线与六态渲染 → 成员二                    |
| 变更规模       | 新增 16 文件（约 1735 行，含 4 组测试 804 行）/ 修改 19 文件                    |



---

## 1. 各成员核心结论

### 🔍 产品官（代码审查）

- **核心判断**：**Conditional Go**。六态链路与契约 §3.3 / §4.3 对齐良好，`sources` 由数据库映射而非采信模型输出、输出经 `AnswerCard` 强校验，是有效的反幻觉设计；未发现破坏契约或既有接口的缺陷。回归风险逐项核对为「无破坏性回归」（迁移 head 同步、加列可空、`health.py` 去重行为不变）。
- **关键建议**：
  1. **🔴 生产路径不得静默回退替身**——原 `get_llm_client()` 在无 Key 时无条件返回 `MockLLMClient`，其缺省输出恒为「学生证补办」卡片，会出现「问转专业却答学生证、还挂着 S07 真实来源」的假答案，且无日志提示。**已修**。
  2. **🟠 回填脚本写入的是虚构正文**，会削弱反幻觉保证（挂真实来源却输出杜撰流程）。**保留但显式标注为演示占位**，需成员一替换。
  3. **🟠 存量数据升级后问答会整体拒答**（`content` 为空即无依据）。**已在迁移 0004 注释中写死「必须回填」**。
  4. **🟡 图标双来源漂移**：后端 `DISPLAY_DEFAULTS` 与前端 `service-icons.ts` 存在不一致（S06）。**已对齐为前端实际渲染结果并加一致性测试**。
  5. 判断点结论（逐条）：① 六态全部可达、非 answered 的 `answer` 显式 null ✅；② **「过期/草稿一律拒答」比原计划「过期→answered+warning」更正确**（依据实施方案 4.1 原则 1、7.5、8.3 规则 5 与用例 4）；③ 新增 `source_documents.content` **属必要支撑改动、非 scope creep**；④ 多轮承接误判有界（不编造）；⑤ 无输入清洗/限流属计划 F3，已记待办。

### ✅ 质量门神（QA 与发布）

- **核心判断**：**Go，无阻塞项。** 17 项验证全部通过，含真实进程端到端契约冒烟（SQLite + uvicorn）、边界反例（非法 `conversation_id`、纯空白 message、200 字边界、超长 token、campus 不匹配、conflict 与 verified 并存、事项表缺行时外键降级）与迁移回环，**未发现任何 500 或契约不符**。
- **关键建议**：
  1. **工作树在验证期间是移动靶**——已冻结快照指纹 `d33c9f86…` 并前后两次复验一致；建议后续改动后按同一指纹复验。
  2. **契约示例与实现不一致（O2）**：`§4.3` 的 `insufficient_evidence` 示例 `intent: null`，实现对已识别意图回传事项码。**已在契约补「实现说明」**。
  3. **会话续写未绑定标识（O3）**：用不同 `X-Session-Token` 也能续写同一会话，弱于 §4.4「禁止跨标识读取」。**已修（跨标识续写一律 404）并补测试**。
  4. **本地无 Key 返回 answered 占位卡（O4）**：本地联调可接受（卡片已显式标注替身来源），**生产已被 503 挡住**；提示不要用 `APP_ENV=local` 部署。
  5. **前端标识注入缺单测（O5）**：**已补 3 个 vitest 用例**（生成/持久化/复用/沿用）。
  6. **环境陷阱记录**：沙箱 `HTTP_PROXY` 会让 httpx 把绝对 URL 当路径发给代理，冒烟脚本需 `trust_env=False`——属测试夹具问题，不是产品缺陷。

---

## 2. 综合审查发现（去重合并，按严重度排序）

| #  | 严重度 | 类别     | 位置                                                                      | 问题描述                                                       | 建议 / 处置                                                                                                             | 来源         | 状态          |
| -- | --- | ------ | ----------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ---------- | ----------- |
| 1  | 🔴  | 安全/正确性 | `app/services/llm_client.py`（原 `get_llm_client`）                        | 无 Key 时无条件回退替身，其缺省输出恒为固定「学生证补办」卡片 → 任何事项都可能返回张冠李戴的假答案且无提示  | 按环境分流：有 Key→MaaS；无 Key 且 local→替身（warning 日志 + 占位卡显式标注）；无 Key 且非 local→`UnavailableLLMClient`（503 `UPSTREAM_ERROR`） | 产品官        | ✅ 已修        |
| 2  | 🔴  | 仓库卫生   | `frontend/docs/home-design.md`、`plans/UI图标与文案微调方案.md`                   | 工作树存在与本次无关的删除，整体提交会永久删除文档（其中含图标映射的书面依据）                    | 提交前 `git checkout -- frontend/docs plans`，或明确排除                                                                     | 产品官 / 质量门神 | ⏳ 待用户确认     |
| 3  | 🟠  | 安全/隐私  | `app/services/chat_service.py` `_resolve_conversation`                  | 续写已存在会话时不校验标识归属，不同 token 可续写同一会话                           | 校验 `session_token` 一致，不一致按 404 处理；未带标识的会话首次带标识访问即认领                                                                 | 质量门神（O3）   | ✅ 已修 + 补测试  |
| 4  | 🟠  | 正确性    | `app/services/retrieval.py` + `chat_service.py`                         | 仅过期/草稿来源时拒答但丢弃来源，无法提示「资料可能已失效」（实施方案用例 4 要求提示）              | 拒答时回带 `status=expired/draft` 的 sources；无来源时仍为 `[]`                                                                  | 产品官（🟡-6）  | ✅ 已修 + 补测试  |
| 5  | 🟠  | 一致性    | `app/services/conversations.py` vs `chat_service.py`                    | 会话标识写入截断 64、读取不截断 → 超长 token「写得进查不出」                       | 抽 `app/services/session_token.py` 统一规范化，两处复用                                                                        | 产品官（🟡-3）  | ✅ 已修 + 补测试  |
| 6  | 🟠  | 一致性    | `app/services/retrieval.py` `_apply_context`                            | `student_type` 用英文（`undergraduate`）比对中文 `audience`，软过滤形同虚设 | 增加中英口径映射（undergraduate→本科、graduate→研究生…）                                                                            | 产品官（🟡-4）  | ✅ 已修 + 补测试  |
| 7  | 🟠  | 类型契约   | `frontend/src/types/home.ts`                                            | `icon/tone/prompt` 声明为非空必填，与契约「选返」及后端 `str \| None` 不符     | 改为可选可空，调用点补 `?? undefined`                                                                                          | 产品官（🟠-4）  | ✅ 已修        |
| 8  | 🟠  | 数据质量   | `scripts/backfill_knowledge_content.py`                                 | 回填的是演示用虚构正文，挂真实来源会削弱「来源可追溯」                                | 已显式标注为演示占位；验收前必须替换为核验过的真实通知                                                                                         | 产品官（🟠-1）  | ⏳ 待成员一      |
| 9  | 🟠  | 部署陷阱   | `alembic/versions/0004_*.py`                                            | 注释暗示「历史行无需回填」，实际 `content` 为空会导致问答整体拒答                     | 注释改为明确「必须回填」，并写明启用问答前先跑回填脚本                                                                                         | 产品官（🟠-2）  | ✅ 已修        |
| 10 | 🟠  | 安全     | `app/api/chat.py`                                                       | 新端点无限流、无输入清洗（提示词注入 / 成本放大）                                 | 属计划 F3，明确记入待办；答辩前至少加单标识速率限制                                                                                         | 产品官（🟠-3）  | ⏳ 计划 F3     |
| 11 | 🟡  | 一致性    | `app/services/service_items.py` vs `frontend/src/data/service-icons.ts` | 图标双来源，S06 不一致（后端 `i-award`、前端回退 `i-doc`）                   | 后端缺省 icon 对齐前端实际渲染结果，并加一致性测试                                                                                        | 产品官（🟡-1）  | ✅ 已修 + 补测试  |
| 12 | 🟡  | 健壮性    | `app/services/chat_service.py` `_parse_answer`                          | 「首个 `{` 到末个 `}`」启发式在模型夹带文字时会截出非法片段                         | 改为按花括号深度 + 字符串状态的配平扫描                                                                                               | 产品官（🟡-7）  | ✅ 已修        |
| 13 | 🟡  | 类型约束   | `app/models/service_item.py` `tone`                                     | `String(16)` 无枚举约束，脏数据会违反前端联合类型                            | 加 tone 枚举测试；DB 层约束留待后续（SQLite 不支持 `ALTER ADD CONSTRAINT`）                                                           | 产品官（🟡-2）  | 🟡 部分（测试已加） |
| 14 | 🟡  | 契约示例   | `docs/api.md §4.3`                                                      | 非 answered 示例写 `intent: null`，实现对已识别意图回传事项码                | 契约补「实现说明」：非 answered 时 `intent` 不保证为 null，前端按 `status` 分支                                                           | 质量门神（O2）   | ✅ 已修（文档）    |
| 15 | 🟡  | 测试覆盖   | `frontend/tests/client.spec.ts`                                         | 新增的标识注入逻辑无单测                                               | 补 3 个用例（生成/持久化/复用/沿用）                                                                                               | 质量门神（O5）   | ✅ 已修        |
| 16 | 🟡  | 多轮边界   | `chat_service._inherited_intent`                                        | 仅上一轮为 `need_clarification` 时承接事项；库外追问会被多问一轮                | 可接受（不编造、影响有界），已记录                                                                                                   | 产品官（🟡-5）  | 🟡 已知取舍     |
| 17 | 🟡  | 契约选择   | `chat_service._run_pipeline`                                            | `conflict` 状态回带冲突来源，其余非 answered 返回 `[]`（契约示例均为 `[]`）      | 有意设计（信息量更大），前端未接线，后续按需调整                                                                                            | 产品官（🟡-8）  | 🟡 已知取舍     |

---

## ✅ 行动清单

| # | 行动                                                                                    | 负责方      | 紧急度     | 期望完成 |
| - | ------------------------------------------------------------------------------------- | -------- | ------- | ---- |
| 1 | 确认/恢复两处与本次无关的文档删除（`frontend/docs/home-design.md`、`plans/UI图标与文案微调方案.md`）              | 用户 / 成员二 | P0（提交前） | 提交前  |
| 2 | 用成员一核验过的真实通知正文替换 `scripts/backfill_knowledge_content.py` 的演示正文，并执行回填                  | 成员一      | P0（演示前） | 验收前  |
| 3 | 前端接线：六页切换到真实接口 + 六态渲染（`AnswerCard`/`SourceList`/`FeedbackBar`），并消费 `icon/tone/prompt` | 成员二      | P1      | 联调周  |
| 4 | 补 `/api/chat/messages` 限流与输入清洗（计划 F3），配置 `MAAS_API_KEY` 后做真实 MaaS 联调与 20 次计时          | 成员三      | P1      | 联调周  |
| 5 | 部署流程写入「先 `alembic upgrade head` → 跑回填脚本 → 再启用问答」，并明确禁止用 `APP_ENV=local` 部署            | 成员三      | P1      | 部署前  |
| 6 | 按冻结指纹（`d33c9f86…`）在提交后复验一次，避免移动靶                                                      | 质量门神     | P2      | 提交后  |

---

## 📦 交付清单（全流程交付专属）

### 代码变更

**新增 16 个文件**

| 文件                                                                 | 作用                                                                                                           |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `backend/app/schemas/chat.py`                                      | 问答请求/响应、`AnswerCard`（九字段）、`ChatSource`                                                                       |
| `backend/app/services/llm_client.py`                               | `LLMClient` 协议 + `MaaSClient`（华为云 MaaS，OpenAI 兼容）+ `MockLLMClient`（替身）+ `UnavailableLLMClient`（生产明确失败）+ 环境分流 |
| `backend/app/services/intent.py`                                   | 规则意图识别（S01–S08 关键词表）+ 追问规则（S04 请假类型、S05 奖项类型）                                                                |
| `backend/app/services/retrieval.py`                                | 知识检索与依据判断（元数据软过滤、有效期校验、top 5 召回、verified/expired/conflict 分流）                                                |
| `backend/app/services/chat_service.py`                             | 六段流水线编排、会话落库、多轮承接、模型输出解析与校验                                                                                  |
| `backend/app/services/fallback_service.py`                         | LLM 异常 → 契约错误码映射 + 降级响应构造                                                                                    |
| `backend/app/services/session_token.py`                            | 匿名会话标识统一规范化（写入/读取共用）                                                                                         |
| `backend/app/api/chat.py`                                          | `POST /api/chat/messages` 路由                                                                                 |
| `backend/alembic/versions/0003_add_service_item_display_fields.py` | `service_items` 增加 `icon/tone/prompt`（可空）                                                                    |
| `backend/alembic/versions/0004_add_source_document_content.py`     | `source_documents` 增加 `content`（问答可依据正文，必须回填）                                                                |
| `backend/tests/test_chat_api.py`（407 行）                            | 六态、多轮、错误映射、隔离、边界                                                                                             |
| `backend/tests/test_llm_client.py`（约 190 行）                        | 请求构造、超时/401/429/畸形响应映射、替身与生产分流                                                                               |
| `backend/tests/test_retrieval.py`（约 180 行）                         | 依据判断全分支 + 软过滤口径                                                                                              |
| `backend/tests/test_fallback.py`（约 90 行）                           | 错误码映射 + 降级响应                                                                                                 |
| `scripts/backfill_knowledge_content.py`                            | 幂等回填 8 项展示字段与演示正文（**正文待替换为真实资料**）                                                                            |

**修改 19 个文件**：`backend/app/models/service_item.py`、`models/source_document.py`、`schemas/service_item.py`、`services/service_items.py`（新增 `DISPLAY_DEFAULTS` 缺省表 + `ALLOWED_TONES`）、`services/conversations.py`（标识规范化）、`core/config.py`（`maas_*` 配置）、`main.py`（注册 chat 路由）、`api/health.py`（去重共享 `UTF8JSONResponse`）、`requirements.txt`（+`httpx`）、`tests/{test_models,test_migrations,test_service_items,test_conversations}.py`、`frontend/src/api/client.ts`（`getSessionToken()` + 统一注入 `X-Session-Token`）、`frontend/src/types/home.ts`、`frontend/src/views/HomeView.vue`、`frontend/tests/client.spec.ts`、`docs/api.md`（v1.1）、`.env.example`（`MAAS_*`）

### 测试覆盖

| 层       | 命令                                                                                        | 结果                                                                                                     |
| ------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 后端单测/接口 | `pytest -q`（SQLite 内存库 + 真实迁移）                                                            | **130 passed**（本次新增 72 个用例，原 58 个全部保持通过）                                                               |
| 前端类型    | `vue-tsc --noEmit`                                                                        | 退出码 0                                                                                                  |
| 前端单测    | `vitest run`                                                                              | **9 passed**（2 文件）                                                                                     |
| 前端构建    | `vite build`                                                                              | 成功，主 chunk 137.04 kB（gzip 52.22 kB）                                                                    |
| 端到端冒烟   | SQLite + uvicorn 真实进程（QA 独立执行）                                                            | 17 项全过：health / service-items（空库与 8 项）/ chat 六态与错误码 / conversations 隔离 / feedback / 多轮承接 / 生产无 Key 503 |
| 迁移      | `upgrade head → downgrade base → upgrade head`                                            | 可回环，`alembic current = 0004 (head)`                                                                    |
| 边界反例    | 非法/空 `conversation_id`、纯空白 message、200 字边界、超长 token、campus 不匹配、conflict+verified 并存、事项表缺行 | 无 500、无契约不符                                                                                            |

### 发布检查清单

- [x] 契约文档同步（`docs/api.md` v1.1：`X-Session-Token`、展示字段转实返、错误映射、依据口径、会话归属）
- [x] 迁移可升可降、单一 head（`0004`）、模型-迁移零漂移
- [x] 生产环境缺 Key 明确失败（503），不静默编造
- [x] 无密钥入库；`MAAS_API_KEY` 仅经环境变量/`.env`（`.env` 已被忽略）
- [x] 非 answered 时 `answer` 显式 null；`sources` 恒为数组
- [ ] 两处无关文档删除已确认/恢复
- [ ] 真实知识正文已替换并回填
- [ ] 前端六页接线 + 六态渲染（成员二）
- [ ] 限流与输入清洗（F3）

### 回滚预案

1. **代码**：本次改动全部在工作区未提交，`git checkout -- .` + `git clean -fd` 即可整体回到 `556f3d9`（注意会一并丢弃本次新增文件；`git clean` 前先确认无其他未跟踪产物）。
2. **数据库**：`alembic downgrade 0002` 可退回本次两版迁移之前（0003 删 3 列、0004 删 `content`），均有 `downgrade()` 实现；SQLite 与 MySQL 均验证过升级路径。
3. **配置**：`maas_*` 配置项与 `.env.example` 为纯追加，缺省即旧行为（无 Key + local → 替身）。
4. **前端**：`client.ts` 新增的请求头对后端旧版本无副作用（未知头被忽略）；`types/home.ts` 放宽为可选可空不改变运行时代码。

---

## ⚠️ 待完善 / 已知局限

1. **与计划文本的有意偏离**：计划曾写「过期来源 → `answered` + warnings」，实现改为**一律拒答**（`insufficient_evidence`），理由是实施方案 4.1 原则 1、7.5「过期和冲突文档不得作为唯一正式依据」、8.3 规则 5 与用例 4，以及验收指标「库外拒答率 ≥90%」。代价是「关键字段完整率」需靠真实数据补齐；如需改为「带 warnings 的答案」，只需放宽 `retrieval.py` 的 `grounded` 判定一处。
2. **知识正文仍是演示占位**：`content` 用虚构内容回填，与「来源可追溯」存在张力；替换前不建议对外演示「answered」链路。**（已在下方「补记」中完成：改用 `scripts/real_knowledge.py` 的核验版正文）**
3. **意图识别为规则实现**：关键词表覆盖 8 事项，口语/错别字/跨事项仍会走追问或拒答；接入 AgentArts 工作流后可整体替换（`LLMClient` 协议已为切换预留）。


4. **无向量检索**：依赖元数据标签 + 关键词，数据量增大后需演进（`retrieval.py` 已留接口）。
5. **限流与输入清洗未做**（计划 F3）：当前依赖 200 字上限 + 来源不采信模型 + 输出强校验缓解。
6. **QA 提示的环境陷阱**：沙箱 `HTTP_PROXY` 会让 httpx 走代理导致全 404 假阳性，冒烟脚本需 `trust_env=False`（测试夹具问题，非产品缺陷）。
7. **移动靶风险**：QA 验证期间代码仍在变，其冻结指纹为 `d33c9f86a896e934c21df7e96c40b61254c08eb6`（`git diff HEAD` + 未跟踪文件内容 sha1 汇总）；本次报告所述为**其后最终状态**（又修了会话归属校验与前端标识单测），建议提交后按其指纹复验一次。
8. 未做视觉回归截图（遵循用户既有偏好：不留自生成校验图）。

---

## 🔄 补记（同日 13:56）：真实知识接入与内容校正

**用户确认**：工作树中两处文档删除（`frontend/docs/home-design.md`、`plans/UI图标与文案微调方案.md`）为**有意删除**，不恢复 → 行动清单第 1 条关闭。

**新增资产（用户提供）**：`scripts/real_knowledge.py`（S01–S08 核验来源与正文）、`scripts/load_real_knowledge.py`（幂等导入器）、`docs/suda-affairs-research-2026-10.md`（逐页复核的调研清单）。

**发现并修正的内容矛盾（重要）**：调研清单对 S01 / S07 明确标注旧口径「已废止 / 不适用现行流程」，但 `real_knowledge.py` 的正文与来源 URL 用的正是旧口径；另有 3 处口径混用。已按调研清单校正：

| 项 | 原状（与调研清单冲突） | 修正后 |
|---|---|---|
| S01 | 正文写「学院开证明 → 教务处综合科办理」，含申请表与银行缴费；来源指向官网**旧版**页 | 改为教务部**现行说明**口径（报社挂失 → jwyy 网上预约 → 预约日次月 10 号后到学院教务办领取；工本费 5 元、在校期间只能补办一次）；来源换成教务部现行说明文件 |
| S07 | 正文写「3 月中下旬申请、4 月中旬考核」；来源为 2016 年**已废止**办法页 | 改为现行时间线（6 月中下旬申请 → 6 月下旬资格审核 → 7 月初考核 → 7 月上旬报教务部）；来源换成数学科学学院 2025 年实施细则 |
| S02 | 正文混入 `teccard.suda.edu.cn` 口径（属**苏州大学应用技术学院**，独立学院） | 删除该口径，仅保留数信处本部渠道；补充「页面时间戳不作为时效依据」 |
| S04 | 沿用已更名的「师生网上事务中心」 | 改为「苏州大学一网通办（my.suda.edu.cn）」；补充请假上限规定与审核链时效提示 |
| S05 | 把个别学院的「学院公示 5 个工作日」写成统一要求 | 改为「学院初评后上报学校，校内公示不少于 5 个工作日（部分学院另设初评公示）」 |
| S08 | 账号保留期与照片房号未标注口径冲突 | 补「数信处另称保留至当年 8 月 31 日，两处官方表述不一致」与照片环节时效提示 |

**为降低「模型照抄旧口径」的风险**：正文不再复述已废止的具体流程与日期，只保留「官网该页为旧版、已取消环节不得作为依据」的通用提示——正文会进入提示词，复述旧细节存在被模型照抄进答案的风险。

**导入器修正（幂等性缺口）**：原实现按 `official_url` 覆盖写 → 来源 URL 变更时会再插一条、同事项出现两条来源。改为**以「事项 + 标题」为身份**覆盖写，并保留按「（核验版）」标记清理改名后的旧条目；报告字段 `demo_removed` → `stale_removed`。

**演示正文脚本退役**：`scripts/backfill_knowledge_content.py`（含虚构演示正文）删除，替换为 `scripts/backfill_service_display_fields.py`（只回填 `icon/tone/prompt`，正文交给真实知识导入器）。

**新增守卫测试** `backend/tests/test_real_knowledge.py`（20 个用例）：数据完整性（8 项全覆盖、来源必须为 `*.suda.edu.cn` 绝对地址、状态一律 `verified`、有效期未过、正文 ≥100 字）、**已废止口径不得回流**（S01 不含「综合科」、S07 不含「3 月中下旬 / 4 月中旬」）、独立学院口径不得混入 S02、导入器行为（缺事项报错 / 替换演示占位 / 幂等 / 改名清理 / URL 变更原地更新）、**8 项端到端接地**（每项都能 `answered` 且挂上对应真实来源）。

**验证结果**：
- 后端 `pytest -q` → **150 passed**（较上一版 +20）
- 真实链路冒烟（文件型 SQLite + `alembic upgrade head` + 导入脚本 CLI + uvicorn + curl）：
  - `load_real_knowledge.py` 首次「新增 8 / 更新 0 / 清理 0」，复跑「新增 0 / 更新 8 / 清理 0」→ 幂等成立
  - `backfill_service_display_fields.py` → 更新 8 项
  - `GET /api/service-items` → 8 项且含 `icon/tone/prompt`
  - S01 → `answered`，来源为教务部现行说明（`jwc.suda.edu.cn`）；S07 → `answered`，来源为数学科学学院 2025 细则
  - 库外问题 → `unsupported`；`GET /api/conversations`（带 token）可见 3 条会话
  - 说明：无 `MAAS_API_KEY` 时答案为**显式标注的本地替身占位卡**（正文需真实模型生成）；`sources` 始终来自数据库

**行动清单状态**：第 1 条（文档删除）**关闭**；第 2 条（真实正文替换与回填）**完成**；剩余第 3–6 条（前端接线、F3 限流、部署流程、提交后复验）。

---

## 🔄 补记二（同日 15:17 起）：F3 限流与清洗、F4 知识来源接口、F6 Docker 化

**同期由用户完成的 AgentArts 集成（本提交一并纳入）**：`backend/app/services/agentarts_client.py`
（实现 `LLMClient` 协议：超时/连接异常按 `max_attempts` 重试，4xx 与 429 不重试，输出结构容错解析）、
`get_llm_client()` 优先级分流（**AgentArts（key + agent_id）→ MaaS → 本地替身 → 生产明确 503**）、
`docs/AgentArts工作流配置说明.md`（六节点配置 + 统一 JSON 输出规范 + 20 条全链路测试方案）、
`docs/AgentArts知识库文档-学生事务核验版.md`（与 `scripts/real_knowledge.py` 同源），
新增 `backend/tests/test_agentarts_client.py`。当前接线为**生成委托模式**：后端保留规则意图识别与
MySQL 可信检索，把系统提示词与知识片段交给工作流生成。

### F3 · 限流 + 输入清洗 + 输出白名单（P0，契约 §6.6 / §6.7）

- `app/core/rate_limit.py`：进程内滑动窗口限流（时钟可注入，便于测试）；限流器**随应用实例创建**，
  测试可为每个实例单独设阈值；计数键为匿名会话标识（缺失时退化为主机地址）；超限 → 429 `RATE_LIMITED`。
- `app/core/sanitize.py`：控制字符清洗（保留 `\n\t`）；敏感数据**取值**（身份证 / 手机号 / 16–19 位卡号）
  与凭据赋值一律 400 拒绝；提示词注入 8 条模式（中英双语、忽略大小写）拒绝；
  `is_safe_source_url()` 提供来源链接白名单。
- **接入顺序**：先限流（保护 LLM / 智能体成本），再清洗，最后进入编排层。
- 检索侧接入链接白名单：不可引用的来源既不能作为生成依据，也不会出现在 `sources` 里。
- **误伤防护**：只对「敏感数据的取值」判罚，不对「提到敏感字段的合法提问」判罚
  （「补办学生证需要身份证号吗？」必须放行，已加断言守住）。英文注入模式曾因大小写敏感漏判
  （`Ignore all previous instructions` 未被拦截），由测试发现并加 `re.IGNORECASE` 修正。

### F4 · `GET /api/knowledge/sources`（P1，契约 §4.6）

- 新增 `app/schemas/knowledge.py` + `app/services/knowledge.py` + `app/api/knowledge.py`：
  按 `status` / `item_code` 过滤，`publish_date` 倒序；`id` / `service_item_id` 按契约示例以字符串返回；
  非法 `status` 由枚举校验直接 422；空库返回 `{sources: [], total: 0}`；纯只读、无 PII。

### F6 · Docker 化与 compose 启用（P1）

- 新增 `backend/Dockerfile`（`python:3.12-slim`、非 root、依赖分层缓存、内置 `HEALTHCHECK`）与 `backend/.dockerignore`。
- `docker-compose.yml` 由「注释态」改为可用：backend 启动时 `alembic upgrade head`（带等待数据库重试）
  → 启动 uvicorn；`depends_on: service_healthy`（db 用 `mysqladmin ping`）；**`APP_ENV` 固定 `production`**
  （杜绝部署环境误用本地替身）；db 端口仅绑定 `127.0.0.1`；限流阈值可经环境变量调整。
- 新增 `backend/docs/deploy.md`：部署运行手册（环境变量必填项、一键启动、**首次部署知识库导入顺序**、
  验收自测命令、运维要点、常见问题排查表）。
- 导入脚本的路径引导改为同时兼容宿主机与容器工作目录。
- **验证边界**：`docker compose config` 通过（语法与变量插值正确）；**镜像构建与容器运行未验证**——
  本会话 Docker 守护进程未启动（需手动启动 Docker Desktop 后再执行 `docker compose up -d --build`）。

**验证结果**：后端 `pytest -q` → **225 passed**（本次新增 30 例：限流 9 / 清洗 13 / 知识来源 8）；
导入脚本在「仓库根为 cwd」与「绝对路径调用」两种方式下均正常（幂等：首次新增 8 并清理 8 条演示来源，
复跑更新 8 条）。

---

## 📚 成员产出索引

- **产品官（gstack-product-reviewer）**：完整代码审查报告——7 个判断点逐条结论、按严重度排序的 2 🔴 / 4 🟠 / 8 🟡 发现、Go/No-Go 前置条件 5 条；明确裁定「过期/草稿拒答」比原计划更正确、`content` 列为必要支撑改动。
- **质量门神（gstack-qa-lead）**：独立 QA 报告——17 项验证项 → 实测结果表格、8 类边界反例、7 条观察项（O1–O7）、Go/No-Go；证据文件位于仓库外 `%TEMP%/csa_qa/`（smoke 脚本、uvicorn 日志、临时 SQLite 库），仓库内零临时文件。
- **主理人（team-lead）**：实现三步改动、按审查意见完成 8 项修复、汇编本报告。

---

> 本报告由软件工坊 AI 协作生成，关键决策请由工程负责人复核。
