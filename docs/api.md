# 校园办事小秘书 · 前后端接口文档

> **版本：** v1.0（定稿）
> **编制日期：** 2026-10-07
> **依据：** 《校园办事小秘书实施方案》第五章「技术架构」、第八章「对话和输出设计」、第九章「数据库设计」、第十章「接口规划」
> **定位：** 本文件是**前后端唯一的权威契约**。`frontend/docs/api.md` 已改为指向本文件，避免两份来源各自漂移。
> **变更规则：** 任何字段增删必须同步更新本文档并写入文末「变更记录」（团队协作规则第 3 条）。

---

## 0. 当前落地状态（重要）

| 侧 | 状态 | 说明 |
|---|---|---|
| 前端 | ✅ 契约已实现 | `frontend/src/api/client.ts` 已按本文档定义全部类型与调用函数：`checkHealth` / `fetchServiceItems` / `sendChatMessage` / `submitFeedback` / `fetchConversations` |
| 后端 | ❌ **尚未实现** | 仓库当前无 `backend/` 目录。**本文档同时是后端的实现规格** |
| 页面接线 | 🟡 未接线 | 六个页面目前仍使用 `frontend/src/data/home.mock.ts` 与 `setTimeout` 模拟，尚未调用上述函数 |

> 阅读顺序建议：先看 §1 通用约定与 §2 错误处理，再看 §3 数据模型，最后按需查 §4 接口详情。

---

## 1. 通用约定

### 1.1 基础信息

| 项目 | 约定 |
|---|---|
| 协议 | 生产 HTTPS；本地开发 HTTP |
| Base URL | **同域 `/api`**（生产由 Nginx 反代到 `http://backend:8000`；开发由 Vite 代理到 `http://localhost:8000`） |
| 前端配置 | `VITE_API_BASE_URL`，缺省 `/api`（`client.ts` 内置兜底） |
| 数据格式 | 请求与响应均为 `application/json; charset=utf-8` |
| 字符编码 | UTF-8 |
| 日期格式 | 纯日期 `YYYY-MM-DD`（如 `published_at`）；时间戳 ISO 8601 带时区（如 `2026-09-27T09:42:00+08:00`） |
| 认证 | 原型阶段无登录态，全部接口匿名访问。**不采集、不传输、不记录学号 / 身份证号 / 银行卡号 / 账号密码**（实施方案第十四章） |
| 超时 | 前端请求超时 **8 秒**（对应验收指标「典型回答时间 8 秒以内」）；超时不自动重试，由用户手动重试 |

### 1.2 请求头

```text
Content-Type: application/json   # 仅带 body 的请求需要
Accept: application/json
```

### 1.3 CORS

| 环境 | 策略 |
|---|---|
| 生产 | 前端与后端同域（`/api` 由 Nginx 反代），**无需开启 CORS** |
| 开发 | 前端 `http://localhost:5173` 经 Vite 代理访问，**同样无需 CORS** |

> 若某环境确需直连跨域，仅允许显式白名单来源，禁止 `Access-Control-Allow-Origin: *` 与 `Allow-Credentials` 同时出现。

---

## 2. 错误处理（定稿）

### 2.1 错误响应体

所有 4xx / 5xx 响应统一为：

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "message 字段不能为空"
  }
}
```

- `code`：稳定的机器可读错误码（见 §2.3），前端据此分支；
- `message`：**面向用户的安全文案**，不得包含堆栈、SQL、内部主机名或密钥；
- 前端 `client.ts` 读取 `error.message` 与 `error.code`，构造 `ApiError(status, code)`。

### 2.2 HTTP 状态码

| 状态码 | 含义 | 前端处理 |
|---|---|---|
| 200 | 成功（业务级状态另见 §3.3 的 `status`） | 按 `status` 分支渲染 |
| 204 | 成功且无响应体 | 视为成功，不解析 JSON |
| 400 | 请求参数错误 | 提示用户修改输入 |
| 404 | 资源不存在（如会话不存在） | 提示后重置会话 |
| 422 | 字段校验失败（FastAPI 默认） | 提示用户修改输入 |
| 429 | 触发限流 | 提示稍后重试 |
| 500 | 服务内部错误 | 展示重试提示 |
| 503 | 云服务（AgentArts）异常或超时 | 展示重试提示，**不白屏** |

### 2.3 业务错误码（`error.code`）

| code | 触发场景 |
|---|---|
| `INVALID_REQUEST` | 参数缺失或格式错误 |
| `MESSAGE_TOO_LONG` | `message` 超出长度上限（建议 200 字符，与前端 `maxlength` 一致） |
| `CONVERSATION_NOT_FOUND` | `conversation_id` 不存在或已过期 |
| `RATE_LIMITED` | 触发速率限制 |
| `UPSTREAM_TIMEOUT` | AgentArts 超时 |
| `UPSTREAM_ERROR` | AgentArts 返回异常 |
| `INTERNAL_ERROR` | 其它未预期错误 |

### 2.4 前端本地错误（不来自后端）

| `ApiError.code` | 触发条件 |
|---|---|
| `TIMEOUT` | 请求超过 8 秒被中止 |
| `NETWORK_ERROR` | 网络不可达 / DNS 失败 |
| `INVALID_RESPONSE` | 2xx 但响应体不是合法 JSON |

---

## 3. 数据模型

### 3.1 ServiceItem（支持事项）

`GET /api/service-items` 的数组元素。**直接返回数组**，不使用 `{ items, total }` 包装。

| 字段 | 类型 | 必返回 | 说明 |
|---|---|---:|---|
| `id` | string | 是 | 前端 UI 稳定标识（kebab-case，如 `student-card`），用作列表 key |
| `title` | string | 是 | 事项名称 |
| `description` | string | 是 | 一句话说明 |
| `category` | string | 是 | 分类，用于筛选 |
| `icon` | string | 否 | 图标标识；前端已有本地兜底（`src/data/service-icons.ts`） |
| `tone` | `orange` \| `blue` \| `green` \| `purple` | 否 | 卡片主题色 |
| `prompt` | string | 否 | 点击后预填到对话输入框的问题 |

**与数据库 `service_items` 表的字段映射（实施方案 9.1）：**

| 响应字段 | DB 字段 | 说明 |
|---|---|---|
| `title` | `name` | 事项名称 |
| `description` | `description` | 简要说明 |
| `category` | `category` | 类别 |
| `id` | — | 由后端从 `code` 派生的前端 UI key，或前端本地映射 |
| — | `code` | 事项编码（S01…），**业务主键，见 §3.5** |
| — | `enabled` | 仅返回 `enabled = true` 的事项 |

### 3.2 Source（来源）

| 字段 | 类型 | 必返回 | 说明 |
|---|---|---:|---|
| `title` | string | 是 | 原始通知名称 |
| `department` | string | 是 | 发布部门 |
| `published_at` | string | 是 | 发布日期 `YYYY-MM-DD` |
| `url` | string | 是 | 学校官方来源地址，**必须为 http/https 绝对地址** |
| `item_code` | string \| null | 否 | 事项编码，如 `S01` |
| `status` | string \| null | 否 | 知识状态：`draft` / `verified` / `expired` / `conflict` |

> 前端渲染 `url` 前必须经 `isSafeSourceUrl()` 校验协议，禁止直接信任后端返回值（OWASP A08）。

### 3.3 AnswerCard 与回答状态

**`answer` 是结构化对象，不是字符串**（对应实施方案 8.1）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `title` | string | 事项标题 |
| `summary` | string | 一句话概述 |
| `eligibility` | string[] | 办理条件 |
| `materials` | string[] | 所需材料 |
| `steps` | string[] | 办理步骤（有序） |
| `location` | string \| null | 办理地点；不确定时为 `null`，前端显示「以来源通知为准」 |
| `deadline` | string \| null | 截止日期 `YYYY-MM-DD`；无截止时为 `null` |
| `contacts` | string[] | 联系方式 |
| `warnings` | string[] | 风险提示（过期、冲突、需线下确认等） |

**`status` 枚举（对应实施方案 8.2）：**

| status | 含义 | `answer` | 前端表现 |
|---|---|---|---|
| `answered` | 已找到可靠依据 | **结构化对象** | 展示完整办事卡片 + 来源列表 + 反馈栏 |
| `need_clarification` | 信息不足 | `null` | 展示 `clarifying_question`，输入框继续追问 |
| `unsupported` | 暂不支持 | `null` | 展示支持事项列表 |
| `insufficient_evidence` | 依据不足 | `null` | 展示不确定提示与咨询建议，不编造流程 |
| `conflict` | 知识存在冲突 | `null` | 不给确定结论，提示联系责任部门确认 |
| `service_error` | 云服务异常 | `null` | 展示重试提示 |

> **定稿约定：** 非 `answered` 状态下 `answer` 一律为 `null`（显式返回，不省略字段）；`sources` 一律为数组（可为空数组）。

### 3.4 ConversationSummary（会话摘要）

`GET /api/conversations` 的数组元素，对应实施方案 9.3 `conversations` 表。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 随机会话标识（建议 `crypto.randomUUID`，不可预测） |
| `question` | string | 该会话最近一次用户提问 |
| `last_intent` | string \| null | 最近识别到的事项编码（§3.5） |
| `result_status` | string | 最近一次回答状态（§3.3 枚举） |
| `started_at` | string | 会话开始时间，ISO 8601 |
| `last_message_at` | string | 最近一条消息时间，ISO 8601 |

> **「待继续 / 已完成」推导规则（定稿）：** `result_status === 'need_clarification'` → 待继续；其余 → 已完成。

### 3.5 标识符规范（定稿）

实施方案存在两套编码：第二章用 `S01`–`S08`，第八章示例用 `student_card_reissue`。

**本契约统一采用 `item_code`（`S01`–`S08`）作为业务标识**，理由是知识库元数据（7.2 `item_code`）、来源文档与数据库均以它为主键。

| 用途 | 采用值 |
|---|---|
| `intent` / `last_intent` / `sources.item_code` | `S01`–`S08` |
| `ServiceItem.id`（前端 UI key） | kebab-case，如 `student-card` |

**映射表（前端 `SERVICE_ICON` / `home.mock.ts` 已按此维护）：**

| item_code | ServiceItem.id | 事项 |
|---|---|---|
| `S01` | `student-card` | 学生证补办 |
| `S02` | `campus-card` | 校园卡补办 |
| `S03` | `repair` | 宿舍报修 |
| `S04` | `leave` | 请假办理 |
| `S05` | `scholarship` | 奖学金申请 |
| `S06` | `grant` | 助学金申请 |
| `S07` | `major-transfer` | 转专业咨询 |
| `S08` | `graduation` | 毕业手续 |

> ⚠️ 前端 `ServicesView.vue` 的演示项 `network`（校园网与账号）**不在实施方案的 8 项事务内**，属原型演示项，无 `item_code`；建议答辩前移除或正式纳入范围。

### 3.6 FeedbackReasonCode（反馈原因码，定稿）

| 值 | 含义 |
|---|---|
| `SOURCE_ERROR` | 来源错误 |
| `INCOMPLETE_STEPS` | 流程不完整 |
| `OUTDATED_CONTENT` | 内容过期 |
| `OTHER` | 其他 |

---

## 4. 接口详情

### 4.1 健康检查

```text
GET /api/health
```

**响应 200：**

```json
{ "status": "ok" }
```

**前端：** `checkHealth()`。用途：联调探测、部署自测（`frontend/docs/deploy.md` §6）。

---

### 4.2 查询支持事项

```text
GET /api/service-items
```

**查询参数：** 无（仅返回 `enabled = true`）。

**响应 200：** `ServiceItem[]`（直接数组，见 §3.1）

```json
[
  {
    "id": "student-card",
    "title": "学生证补办",
    "description": "材料、流程与办理地点",
    "category": "证件",
    "icon": "i-id",
    "tone": "orange",
    "prompt": "学生证丢了怎么补办？"
  }
]
```

**前端：** `fetchServiceItems()`。

---

### 4.3 发起问答

```text
POST /api/chat/messages
Content-Type: application/json
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `conversation_id` | string \| null | 是 | 首轮传 `null`，后端创建新会话并返回；后续轮次回传同一 id |
| `message` | string | 是 | 用户问题，≤ 200 字符 |
| `context.campus` | string \| null | 否 | 校区，用于缩小检索范围 |
| `context.student_type` | string \| null | 否 | 学生类型，如 `undergraduate` |

**请求示例：**

```json
{
  "conversation_id": null,
  "message": "学生证丢了怎么补办？",
  "context": { "campus": null, "student_type": "undergraduate" }
}
```

**响应 200（`answered`，完整示例）：**

```json
{
  "conversation_id": "demo-001",
  "status": "answered",
  "intent": "S01",
  "answer": {
    "title": "学生证补办",
    "summary": "需要提交补办申请，审核通过后按通知领取新证。",
    "eligibility": ["学生证遗失", "学生证损坏"],
    "materials": ["有效身份证明", "补办申请", "证件照片"],
    "steps": ["确认当前有效的补办通知", "准备并提交材料", "等待审核", "按通知领取新证"],
    "location": "以最新通知为准",
    "deadline": null,
    "contacts": [],
    "warnings": ["具体要求以来源通知为准"]
  },
  "sources": [
    {
      "title": "关于学生证补办工作的通知",
      "department": "学生工作处",
      "published_at": "2026-09-01",
      "url": "https://example.edu.cn/notice/001",
      "item_code": "S01",
      "status": "verified"
    }
  ],
  "need_clarification": false,
  "clarifying_question": null
}
```

**响应 200（`need_clarification`）：**

```json
{
  "conversation_id": "demo-002",
  "status": "need_clarification",
  "intent": "S04",
  "answer": null,
  "sources": [],
  "need_clarification": true,
  "clarifying_question": "你的请假类型是事假、病假还是公假？"
}
```

**响应 200（`insufficient_evidence`）：**

```json
{
  "conversation_id": "demo-003",
  "status": "insufficient_evidence",
  "intent": null,
  "answer": null,
  "sources": [],
  "need_clarification": false,
  "clarifying_question": null
}
```

**前端：** `sendChatMessage()`。**每轮必须携带上一轮返回的 `conversation_id`**；刷新页面视为新会话。

---

### 4.4 查询最近会话

```text
GET /api/conversations
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | integer | 否 | 返回条数，默认 `10`，最大 `50` |

**响应 200：**

```json
{
  "conversations": [
    {
      "id": "c-1001",
      "question": "学生证丢了怎么补办？",
      "last_intent": "S01",
      "result_status": "answered",
      "started_at": "2026-09-27T09:42:00+08:00",
      "last_message_at": "2026-09-27T09:43:10+08:00"
    }
  ],
  "total": 1
}
```

> ⚠️ **隐私要求：** 匿名阶段该接口**不得返回全量会话**，必须按匿名标识（会话签名 / 匿名 token）隔离，禁止可枚举他人咨询（OWASP A01）。实施方案第十章未规划此接口，但它由 `HistoryView` 的数据需求驱动，建议正式纳入范围。

**前端：** `fetchConversations(limit)`。

---

### 4.5 提交反馈

```text
POST /api/feedback
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `conversation_id` | string | 是 | 关联会话 |
| `helpful` | boolean | 是 | 是否有帮助 |
| `reason_code` | string \| null | 否 | `helpful = false` 时建议提供，取值见 §3.6 |
| `comment` | string \| null | 否 | 可选短评，≤ 200 字 |

**请求示例：**

```json
{
  "conversation_id": "demo-001",
  "helpful": false,
  "reason_code": "OUTDATED_CONTENT",
  "comment": "办理地点似乎已经发生变化"
}
```

**响应 200：**

```json
{ "status": "ok" }
```

**前端：** `submitFeedback()`。

---

### 4.6 查询知识来源状态

```text
GET /api/knowledge/sources
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `status` | string | 否 | `draft` / `verified` / `expired` / `conflict`，缺省返回全部 |
| `item_code` | string | 否 | 按事项编码过滤，如 `S01` |

**响应 200：**

```json
{
  "sources": [
    {
      "id": "1",
      "service_item_id": "1",
      "item_code": "S01",
      "title": "关于学生证补办工作的通知",
      "department": "学生工作处",
      "official_url": "https://example.edu.cn/notice/001",
      "publish_date": "2026-09-01",
      "effective_from": "2026-09-01",
      "effective_to": "2027-08-31",
      "audience": "全日制在校本科生",
      "campus": "主校区",
      "status": "verified",
      "version": "v1.0",
      "reviewed_at": "2026-09-15"
    }
  ],
  "total": 1
}
```

> 对应实施方案第十章第 5 节与第七章「必要元数据」。前端暂无消费方（知识来源页未实现），**建议按需实现，不阻塞 P0**。

---

## 5. 页面与接口映射

| 页面 | 前端文件 | 当前数据来源 | 目标接口 | 前端函数 |
|---|---|---|---|---|
| 首页 | `views/HomeView.vue` | `home.mock.ts` | `GET /api/service-items` | `fetchServiceItems()` |
| 我的对话 | `views/ChatView.vue` | `setTimeout` 模拟 | `POST /api/chat/messages`、`POST /api/feedback` | `sendChatMessage()`、`submitFeedback()` |
| 支持事项 | `views/ServicesView.vue` | `home.mock.ts` + 本地扩展 | `GET /api/service-items` | `fetchServiceItems()` |
| 最近记录 | `views/HistoryView.vue` | `home.mock.ts`（本地伪造 status） | `GET /api/conversations` | `fetchConversations()` |
| 使用帮助 | `views/HelpView.vue` | 组件内常量 | 无（FAQ 静态） | — |
| 设置 | `views/SettingsView.vue` | `localStorage` | 无（偏好仅存本机） | — |

---

## 6. 联调注意事项

1. **会话衔接：** `ChatView` 每轮请求携带上一轮响应的 `conversation_id`；刷新页面视为新会话。
2. **状态分支：** 前端需实现 §3.3 的 6 种 `status` 渲染；当前 `ChatView` 仅有纯文本气泡，未实现任何分支。
3. **来源展示：** 渲染 `sources[].url` 前必须经 `isSafeSourceUrl()` 校验协议。
4. **追问交互：** `need_clarification` 时把 `clarifying_question` 作为助手消息展示，用户下一条消息继续携带同一 `conversation_id`。
5. **敏感信息：** 前后端均不传输、不记录学号 / 身份证号 / 账号密码；提示词已禁止索取敏感信息（实施方案第八章第 3 节）。
6. **提示词注入：** `message` 会直达 AgentArts / LLM，后端必须做输入清洗与输出白名单校验（OWASP A03），不能只依赖提示词软约束。
7. **限流与熔断：** 建议对 `/api/chat/messages` 加速率限制与单条长度上限，避免 LLM 成本被放大（OWASP A04 / DoS）。
8. **错误脱敏：** 4xx / 5xx 的 `error.message` 必须是安全文案，不得回传堆栈或内部主机名。
9. **接口变更：** 任何字段增删必须同步更新本文档并写入变更记录。

---

## 7. 与实施方案的对应关系

| 实施方案位置 | 本文件章节 | 一致性 |
|---|---|---|
| 8.1 统一响应结构 | §3.3、§4.3 | ✅ 已对齐（`answer` 为结构化对象） |
| 8.2 回答状态 | §3.3 | ✅ 6 态完整 |
| 9.1 service_items | §3.1 | ✅ 含字段映射 |
| 9.3 conversations | §3.4 | ✅ 含状态推导规则 |
| 9.4 feedback | §3.6、§4.5 | ✅ reason_code 定稿 |
| 10.1–10.5 接口规划 | §4.1–§4.6 | ✅ 全部覆盖，另新增 §4.4 |
| 7.2 知识元数据 | §3.2、§4.6 | ✅ |
| 2.2 事务编码 S01–S08 | §3.5 | ⚠️ 实施方案 8.1 示例使用 `student_card_reissue`，与第二章的 `S01` 不一致；**本契约统一取 `S01`**，建议同步修订实施方案示例 |

---

## 8. 变更记录

| 日期 | 版本 | 变更 | 说明 |
|---|---|---|---|
| 2026-09-27 | v0.1 | 初稿（联调草案） | 由前端编制，含 6 项「待确认」 |
| 2026-10-07 | v1.0 | 定稿并修正 | ① `answer` 由 string 改为结构化对象（对齐实施方案 8.1）② 补齐 `intent` / `need_clarification` 字段 ③ 统一错误结构与业务错误码（原「待确认」Q1）④ 定稿 `reason_code` 枚举（Q5）⑤ 定稿 `answer` 空值语义（Q3）⑥ 定稿「待继续/已完成」推导规则（Q4）⑦ 定稿 CORS 策略（Q6）⑧ 新增 §3.5 标识符规范与 §0 落地状态 ⑨ 明确 §4.4 匿名隔离与 §6.6 提示词注入要求 |
