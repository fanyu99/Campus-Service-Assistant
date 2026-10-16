# 校园办事小秘书 · 前后端接口文档

> **版本：** v1.3（定稿）
> **编制日期：** 2026-10-07
> **依据：** 《校园办事小秘书实施方案》第五章「技术架构」、第八章「对话和输出设计」、第九章「数据库设计」、第十章「接口规划」
> **定位：** 本文件是**前后端唯一的权威契约**。`frontend/docs/api.md` 已改为指向本文件，避免两份来源各自漂移。
> **变更规则：** 任何字段增删必须同步更新本文档并写入文末「变更记录」（团队协作规则第 3 条）。

---

## 0. 当前落地状态（重要）

| 侧 | 状态 | 说明 |
|---|---|---|
| 前端 | ✅ 契约已实现 | `frontend/src/api/client.ts` 已按本文档定义全部类型与调用函数：`checkHealth` / `fetchServiceItems` / `sendChatMessage` / `fetchChatMessages` / `submitFeedback` / `fetchConversations` |
| 后端 | ✅ 已实现 | `backend/` 已按本文档实现全部 7 个端点（含 `POST /api/chat/messages`、`GET /api/chat/messages` 与 `GET /api/knowledge/sources`），并补录 §1.2 的 `X-Session-Token` |
| 页面接线 | ✅ 已接线 | 六个页面已切换到真实接口：首页/支持事项用 `fetchServiceItems`、对话页用 `sendChatMessage` + `submitFeedback` + `fetchChatMessages`（`?id=` 查看/续接历史）、最近记录用 `fetchConversations`；`frontend/src/data/home.mock.ts` 已移除；七态渲染由 `AnswerCard` / `SourceList` / `FeedbackBar` / `StateNotice` / 普通气泡（smalltalk）承担 |

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
X-Session-Token: <匿名会话标识>   # 问答与历史记录接口使用，见下方说明
```

> **`X-Session-Token`（匿名会话标识，v1.1 补录）：** 由前端首次访问时生成
> （`crypto.randomUUID()`）并持久化到本机，随 `POST /api/chat/messages`、
> `GET /api/chat/messages` 与 `GET /api/conversations` 一起发送。后端据此隔离
> 会话，**禁止跨标识读取**；缺失或空白时 `GET /api/conversations` 直接返回空
> 列表而不做全量查询（OWASP A01）。它不是登录态，不承载任何身份信息，也不得
> 用于识别自然人。写入与读取使用同一套规范化规则（去空白 + 截断到 64 字符）。

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
| `smalltalk` | 寒暄 / 引导对话 | `null` | 展示 `text` 普通聊天气泡，不展示卡片（v1.3 新增） |

> **定稿约定：** 非 `answered` 状态下 `answer` 一律为 `null`（显式返回，不省略字段）；`sources` 一律为数组（可为空数组）。

> **实现说明（v1.1 补录）：**
> 1. **`intent` 在非 `answered` 状态下不保证为 `null`**：已识别到事项时会回传事项编码
>    （如 `need_clarification` 回传 `S04`、`insufficient_evidence` 回传 `S01`），便于前端展示与埋点。
>    前端请按 `status` 分支渲染，不要依赖 `intent` 判空。
> 2. **拒答时可能回带来源**：若事项只有过期/草稿来源，状态为 `insufficient_evidence`、`answer` 为 `null`，
>    但 `sources` 会回带这些来源（`status` 为 `expired` / `draft`），供前端提示「资料可能已失效」；
>    完全无来源时 `sources` 为 `[]`。

> **smalltalk 分类规则（v1.3 补录）：** 意图关键词未命中且不在「追问补参」链上时，后端先做分流：
> ① 问候 / 寒暄 / 感谢 / 告别命中问候规则 → `smalltalk` **规则直答，不调模型**（零延迟）；
> ② 接着上文正在讨论的事项继续追问（如「那费用呢」）→ **沿用该事项**走检索与生成，给出正式回答；
> ③ 与事务沾边但表述不清 → `smalltalk` + 模型生成的引导语；
> ④ 明确库外（食堂、选课等）→ `unsupported`（保持现状，不编造）。
> **红线：`smalltalk` 的 `text` 不得包含政策、时间、地点、电话与办理流程**，只做寒暄与引导。

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

> ✅ 前端 `ServicesView.vue` 原有的演示项 `network`（校园网与账号）**不在实施方案的 8 项事务内**、无 `item_code`，已于 v1.2 **移出支持事项列表**；如后续正式纳入范围，需先补 `service_items` 数据与知识来源，再更新本表。

### 3.6 FeedbackReasonCode（反馈原因码，定稿）

| 值 | 含义 |
|---|---|
| `SOURCE_ERROR` | 来源错误 |
| `INCOMPLETE_STEPS` | 流程不完整 |
| `OUTDATED_CONTENT` | 内容过期 |
| `OTHER` | 其他 |

### 3.7 ConversationMessage（消息明细，v1.3 新增）

对应 `conversation_messages` 表（迁移 `0005`），一问一答成对落库，用于「查看历史 / 续接会话 / 多轮上下文」。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | String(36) | 主键，uuid4 |
| `conversation_id` | String(36) FK | 关联 `conversations.id`，级联删除 |
| `role` | String(16) | `question` / `assistant` |
| `content` | Text | question 轮 = 用户原文；assistant 轮 = 回复文本（answered 时为卡片 summary） |
| `status` | String(24) | 该轮 §3.3 状态 |
| `answer_json` | Text / JSON | assistant 轮的结构化卡片快照；非 answered 为 `NULL` |
| `sources_json` | Text / JSON | assistant 轮的来源快照（仍由数据库映射生成，不采信模型输出） |
| `created_at` | DateTime(tz) | 入库时间（单调递增，保证问 → 答的先后） |

索引：`(conversation_id, created_at)`。

> **动机：** `conversations` 是「一行 = 一个问题」的单轮摘要，AI 的回答从未落库；
> 本表补齐后历史可查看（§4.7）、可续接（后续轮次沿用同一 `conversation_id`）、
> 可作上下文（生成提示词注入最近 4 轮对话历史）。

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

**响应 200（`smalltalk`，v1.3 新增）：**

```json
{
  "conversation_id": "demo-004",
  "status": "smalltalk",
  "intent": null,
  "answer": null,
  "sources": [],
  "need_clarification": false,
  "clarifying_question": null,
  "text": "你是在问学生证补办吗？我可以帮你查办理流程。"
}
```

> **`text`（v1.3 新增，可选）：** 纯文本对话内容，仅 `smalltalk` 状态非空，前端渲染为普通
> 聊天气泡；其余状态省略或为 `null`。`smalltalk` 响应语义固定为
> `answer=null`、`sources=[]`、`need_clarification=false`（见 §3.3）。

**前端：** `sendChatMessage()`。**每轮必须携带上一轮返回的 `conversation_id`**；刷新页面视为新会话。
从「最近记录」进入时先经 `GET /api/chat/messages` 加载历史（§4.7），
后续轮次携带同一 `conversation_id` 即完成续接。

> **会话归属校验（v1.1）：** 续写已存在的 `conversation_id` 时，后端校验该会话的
> `session_token` 与请求头 `X-Session-Token` 是否一致；不一致一律按 404
> `CONVERSATION_NOT_FOUND` 处理（含请求未带标识的情况），避免跨标识续写（§4.4）。
> 会话创建时未带标识的，首次带标识访问即完成「认领」，之后按标识隔离。

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

### 4.7 查询会话消息明细（v1.3 新增）

```text
GET /api/chat/messages?conversation_id=<会话id>
X-Session-Token: <匿名会话标识>
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `conversation_id` | string | 是 | 会话标识（`conversations.id`，即问答接口回传的 `conversation_id`） |

**响应 200：**

```json
{
  "messages": [
    {
      "role": "question",
      "content": "学生证丢了怎么补办？",
      "status": "answered",
      "answer": null,
      "sources": [],
      "created_at": "2026-10-16T09:42:00+08:00"
    },
    {
      "role": "assistant",
      "content": "需要提交补办申请，审核通过后按通知领取新证。",
      "status": "answered",
      "answer": { "title": "学生证补办", "summary": "……", "steps": ["……"] },
      "sources": [
        { "title": "关于学生证补办工作的通知", "department": "学生工作处", "published_at": "2026-09-01", "url": "https://example.edu.cn/notice/001", "item_code": "S01", "status": "verified" }
      ],
      "created_at": "2026-10-16T09:42:03+08:00"
    }
  ],
  "total": 2
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `messages` | ChatMessageItem[] | 按时间正序，一问一答成对；单次最多返回最近 200 条 |
| `messages[].role` | string | `question` / `assistant` |
| `messages[].content` | string | question 轮 = 用户原文；assistant 轮 = 回复文本（answered 时为卡片 summary） |
| `messages[].status` | string | 该轮回答状态（§3.3 枚举） |
| `messages[].answer` | AnswerCard \| null | assistant 且 answered 轮的结构化卡片快照，其余为 `null` |
| `messages[].sources` | Source[] | assistant 轮的来源快照（仍由数据库映射生成，不采信模型输出） |
| `messages[].created_at` | string | 入库时间，ISO 8601 带时区 |
| `total` | integer | 本次返回的条数 |

**归属校验（与 §4.3 一致）：** 会话不存在、或不属于当前 `X-Session-Token`
→ 404 `CONVERSATION_NOT_FOUND`（契约 §4.4 匿名隔离）。会话存在但尚无消息
（如升级前创建的旧会话）→ 200 + 空 `messages`，前端展示「暂无对话内容」。

**前端：** `fetchChatMessages(conversationId)`。用途：「最近记录 → 查看 / 续接」
（入口语义见 §5 与 §6.1）与续接时的历史渲染。

> 实现说明：接口形态按 `docs/问题修复方案-对话体验三项-2026-10-16.md` §2.6
> 定为 `/api/chat/messages?conversation_id=`（与问答 POST 同路径、按方法区分），
> 与 v1.3 规划稿中的路径式写法等价。

## 5. 页面与接口映射

| 页面 | 前端文件 | 当前数据来源 | 目标接口 | 前端函数 |
|---|---|---|---|---|
| 首页 | `views/HomeView.vue` | ✅ 真实接口（事项 + 最近 3 条会话） | `GET /api/service-items`、`GET /api/conversations` | `fetchServiceItems()`、`fetchConversations()` |
| 我的对话 | `views/ChatView.vue` | ✅ 真实接口（七态渲染与反馈闭环；`?id=` 加载历史可续接） | `POST /api/chat/messages`、`GET /api/chat/messages`、`POST /api/feedback` | `sendChatMessage()`、`fetchChatMessages()`、`submitFeedback()` |
| 支持事项 | `views/ServicesView.vue` | ✅ 真实接口（分类取自后端 `category`） | `GET /api/service-items` | `fetchServiceItems()` |
| 最近记录 | `views/HistoryView.vue` | ✅ 真实接口（状态由 `result_status` 推导；主点击查看、继续咨询续接，均走 `?id=`） | `GET /api/conversations` | `fetchConversations()` |
| 使用帮助 | `views/HelpView.vue` | 组件内常量 | 无（FAQ 静态） | — |
| 设置 | `views/SettingsView.vue` | `localStorage` | 无（偏好仅存本机） | — |

---

## 6. 联调注意事项

1. **会话衔接：** `ChatView` 每轮请求携带上一轮响应的 `conversation_id`；刷新页面视为新会话。
   从「最近记录」进入（`/chat?id=<会话id>`）时先经 `GET /api/chat/messages` 加载历史，
   后续轮次携带同一 `conversation_id` 即续接原会话（v1.3）。
2. **状态分支：** 前端需实现 §3.3 的 7 种 `status` 渲染；`smalltalk` 渲染为普通聊天气泡（`text`），
   其余状态见 `ChatView` 现有分支。
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
| 2026-10-16 | v1.1 | 补录与落地说明 | ① §1.2 补录 `X-Session-Token` 请求头（后端 `GET /api/conversations` 已按其隔离，前端此前未发送，本次对齐）② §3.1 的 `icon` / `tone` / `prompt` 由「选返」转为**实际返回**（`service_items` 新增同名列，为空时回退后端缺省表）③ 明确 `POST /api/chat/messages` 的错误映射：传输层失败 503 `UPSTREAM_TIMEOUT` / `UPSTREAM_ERROR`、上游限流 429 `RATE_LIMITED`、模型输出不可用 200 `status=service_error` ④ 明确生成依据口径：仅「已核验 + 有效期内 + 有正文」的来源可产出 `answered`；过期/草稿一律拒答（`insufficient_evidence`，并在 `sources` 中回带这些来源供前端提示「资料可能已失效」）；存在冲突来源时返回 `conflict` |
| 2026-10-16 | v1.2 | 六页接线与范围收敛 | ① §0 落地状态更新为「后端已实现 + 页面已接线」② §5 六个页面的数据来源改为真实接口（`home.mock.ts` 已移除）③ §3.5 前端演示项 `network`（校园网与账号）**移出支持事项列表**（不在 S01–S08 范围内）④ 补充实现约定：记录页「待继续/已完成」由 `result_status` 推导（§3.4），事项编码→UI key 映射见 §3.5，前端 `src/data/service-codes.ts` 与本表保持一致 |
| 2026-10-16 | v1.3 | 对话体验三项修复落地 | ① `GET /api/chat/messages` 上线，新增表 `conversation_messages`（迁移 0005）：AI 回答与来源快照落库，历史可查看、可续接，生成提示词注入最近 4 轮对话历史 ② 新状态 `smalltalk` 与响应字段 `text` 上线（迁移 0006）：问候/寒暄规则直答，接着上文事项的追问沿用该事项给出回答，表述不清给引导语，明确库外仍 `unsupported`；`smalltalk` 文案不得含政策内容 ③ 前端入口语义：`/chat?q=` 提问、`/chat?id=` 查看/续接（记录页主点击与「继续咨询」均走 `?id=`，查看历史不再重新提问）。详见 `docs/问题修复方案-对话体验三项-2026-10-16.md` |
