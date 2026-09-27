# 校园办事小秘书 接口文档

> **版本：** v0.1（联调草案）
> **编制日期：** 2026-09-27
> **编制人：** 成员二（前端），供前后端联调对齐使用
> **依据：** 《校园办事小秘书实施方案》第十章「接口规划」、第八章「对话和输出设计」，以及前端各页面（`frontend/src/views/`）实际数据需求
> **状态说明：** 除标注「待确认」的条目外，其余结构与实施方案保持一致；接口变更必须写入变更记录（团队协作规则第 3 条）。

---

## 1. 通用约定

### 1.1 基础信息

| 项目 | 约定 |
|---|---|
| 协议 | HTTPS（本地开发可用 HTTP） |
| Base URL | `http://localhost:8000`（本地开发，后续以部署地址为准） |
| 数据格式 | 请求与响应均为 `application/json; charset=utf-8` |
| 字符编码 | UTF-8 |
| 时间格式 | ISO 8601，如 `2026-09-27T09:42:00+08:00` |
| 认证 | 原型阶段无登录态，全部接口匿名访问（隐私最小化原则，不采集学号、身份证号） |

### 1.2 请求头

```text
Content-Type: application/json
Accept: application/json
```

### 1.3 错误响应结构（待确认）

实施方案未统一约定错误体，前端建议采用如下结构，**需与成员三（后端）确认**：

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "message 字段不能为空"
  }
}
```

| HTTP 状态码 | 含义 | 前端处理 |
|---|---|---|
| 200 | 成功（含业务级状态，见 §2.3） | 按 `status` 分支渲染 |
| 400 | 请求参数错误 | 提示输入问题 |
| 404 | 资源不存在（如会话不存在） | 提示后重置会话 |
| 422 | 字段校验失败（FastAPI 默认） | 提示输入问题 |
| 500 | 服务内部错误 | 展示重试提示 |
| 503 | 云服务（AgentArts）异常或超时 | 展示重试提示，不白屏 |

### 1.4 超时约定

- 前端请求超时：**8 秒**（对应验收指标「典型回答时间 8 秒以内」）；
- 超时后前端展示重试提示，并保留已输入内容，不自动重试。

---

## 2. 数据模型

### 2.1 ServiceItem 支持事项

当前前端实际使用 `frontend/src/types/home.ts` 中的 `ServiceItem` 类型，字段必须直接兼容前端，不需要 `name -> title` 转换。

| 字段 | 类型 | 必返回 | 当前前端用途 |
|---|---|---:|---|
| `id` | string | 是 | 列表 key、服务识别 |
| `title` | string | 是 | 服务名称 |
| `description` | string | 是 | 服务说明 |
| `category` | string | 是 | 分类筛选 |
| `icon` | string | 是 | 服务卡片图标 |
| `tone` | `orange` / `blue` / `green` / `purple` | 是 | 服务卡片主题色 |
| `prompt` | string | 是 | 跳转咨询页时的预填问题 |

> 当前前端没有 `code`、`name`、`enabled` 字段。当前 `fetchServiceItems()` 的返回类型是 `Promise<ServiceItem[]>`，所以响应建议直接返回数组，而不是 `{ "items": [...], "total": n }`。
### 2.2 Source 来源

| 字段 | 类型 | 必返回 | 说明 |
|---|---|---:|---|
| `title` | string | 是 | 原始通知名称 |
| `department` | string | 是 | 发布部门 |
| `published_at` | string | 是 | 发布日期，`YYYY-MM-DD` |
| `url` | string | 是 | 学校官方来源地址 |

### 2.3 回答状态（`status` 枚举）

与实施方案 8.2 节一致，作为后续问答响应扩展状态；当前前端尚未实现这些分支：

| 状态 | 含义 | 前端表现 |
|---|---|---|
| `answered` | 已找到可靠依据 | 展示完整办事卡片（条件、材料、步骤、地点、时间、来源） |
| `need_clarification` | 信息不足 | 展示追问 `clarifying_question`，输入框继续追问 |
| `unsupported` | 暂不支持 | 展示支持事项列表（跳转/内嵌 `GET /api/service-items` 结果） |
| `insufficient_evidence` | 依据不足 | 展示不确定提示和咨询建议，不编造流程 |
| `conflict` | 知识存在冲突 | 不给确定结论，提示联系责任部门确认 |
| `service_error` | 云服务异常 | 展示重试提示 |

---

## 3. 接口详情

### 3.1 健康检查

```text
GET /api/health
```

**用途：** 联调时确认后端可用；前端可在应用启动时探测。

**响应示例（200）：**

```json
{"status": "ok"}
```

---

### 3.2 查询支持事项

```text
GET /api/service-items
```

**用途：** 对应前端预留的 `fetchServiceItems()`。当前 `HomeView.vue` 和 `ServicesView.vue` 仍使用 `home.mock.ts`，尚未调用该函数。

**查询参数：** 当前前端不传查询参数，暂不要求 `enabled`。

**响应（200）：** 直接返回 `ServiceItem[]`：

```json
[
  {
    "id": "student-card",
    "title": "学生证补办",
    "description": "材料、流程与办理地点",
    "category": "证件",
    "icon": "▣",
    "tone": "orange",
    "prompt": "学生证丢了怎么补办？"
  }
]
```
### 3.3 发起问答（前端已预留）

```text
POST /api/chat/messages
```

**用途：** 对应 `frontend/src/api/client.ts` 中的 `sendChatMessage()`。当前 `ChatView.vue` 仍使用 `setTimeout` 模拟回复，尚未实际调用。

**请求体（与 `ChatMessageRequest` 一致）：**

| 字段 | 类型 | 必填 |
|---|---|---:|
| `conversation_id` | string \| null | 是 |
| `message` | string | 是 |
| `context.campus` | string \| null | 否 |
| `context.student_type` | string \| null | 否 |

**响应最低兼容结构：**

```json
{
  "conversation_id": "demo-001",
  "status": "answered"
}
```

> 当前 `client.ts` 没有定义问答响应接口，也没有消费 `answer`、`sources`、`clarifying_question`。原文中的结构化办事卡片和 6 种状态只能作为后续扩展，不能视为当前页面已经实现的字段契约。
### 3.4 查询最近会话（新增，待确认）

```text
GET /api/conversations
```

**用途：** 首页「最近咨询」、最近记录页（`HistoryView.vue`）。实施方案第十章未规划此接口，但首页与历史页需要会话列表数据，**需与成员三确认**；对应数据库 `conversations` 表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | integer | 否 | 返回条数，默认 `10`，最大 `50` |

**响应示例（200）：**

```json
{
  "conversations": [
    {
      "id": "c-1001",
      "question": "学生证丢了怎么补办？",
      "last_intent": "student_card_reissue",
      "result_status": "answered",
      "started_at": "2026-09-27T09:42:00+08:00",
      "last_message_at": "2026-09-27T09:43:10+08:00"
    }
  ],
  "total": 1
}
```

> 前端展示映射：`question` → 标题；`started_at` → 时间；`last_intent` → 标签；「待继续/已完成」状态可由 `result_status` 推导（待继续 = `need_clarification`，其余为已完成，**待确认**）。

---

### 3.5 提交反馈

```text
POST /api/feedback
```

**用途：** 问答卡片下方「有帮助 / 没帮助」评价（实施方案第 5 周联调项，前端反馈组件待实现）。

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `conversation_id` | string | 是 | 关联会话 |
| `helpful` | boolean | 是 | 是否有帮助 |
| `reason_code` | string \| null | 否 | `helpful=false` 时建议提供 |
| `comment` | string \| null | 否 | 可选短评，≤200 字 |

`reason_code` 枚举（**待确认**）：`SOURCE_ERROR`（来源错误）、`INCOMPLETE_STEPS`（流程不完整）、`OUTDATED_CONTENT`（内容过期）、`OTHER`（其他）。

**请求示例：**

```json
{
  "conversation_id": "demo-001",
  "helpful": false,
  "reason_code": "OUTDATED_CONTENT",
  "comment": "办理地点似乎已经发生变化"
}
```

**响应示例（200）：**

```json
{"status": "ok"}
```

---

### 3.6 查询知识来源状态

```text
GET /api/knowledge/sources
```

**用途：** 查看回答来源的核验状态（对应知识来源页 / 答案卡片来源扩展展示）。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `status` | string | 否 | `draft` / `verified` / `expired` / `conflict`，默认全部 |
| `item_code` | string | 否 | 按事项编码过滤，如 `S01` |

**响应示例（200）：**

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

---

## 4. 页面与接口映射

| 页面 | 前端文件 | 当前数据来源（原型） | 联调接口 |
|---|---|---|---|
| 首页 | `frontend/src/views/HomeView.vue` | `home.mock.ts` | 当前无实际 API 调用；后续可接 `fetchServiceItems()` |
| 智能咨询 | `frontend/src/views/ChatView.vue` | `setTimeout` 模拟回复 | 当前无实际 API 调用；后续接 `sendChatMessage()` |
| 支持事项 | `frontend/src/views/ServicesView.vue` | `home.mock.ts` + 本地扩展项 | 当前无实际 API 调用；后续可接 `fetchServiceItems()` |
| 最近记录 | `frontend/src/views/HistoryView.vue` | `home.mock.ts`（本地计算 `status`/`detail`） | 当前无实际 API 调用；`GET /api/conversations` 仅为后续扩展 |
| 使用帮助 | `frontend/src/views/HelpView.vue` | 组件内常量 | 暂无（FAQ 保持静态，后续如需后台管理再扩展） |
| 设置 | `frontend/src/views/SettingsView.vue` | `localStorage` | 暂无（偏好仅存本地，符合隐私最小化） |

前端 API 封装位置：`frontend/src/api/client.ts`（已预留 `fetchServiceItems`、`sendChatMessage` 两个函数，对应 §3.2、§3.3；二者目前均为 TODO，且页面尚未调用。）

---

## 5. 联调注意事项

1. **会话衔接（接入 API 后）：** `ChatView` 每轮请求应携带上一轮响应的 `conversation_id`，刷新页面后视为新会话；当前页面尚未接入请求。
2. **状态处理（接入 API 后）：** 前端目前只具备原型文本回复，尚未实现 §2.3 的 6 种 `status` 分支；接入时需补充响应类型和渲染逻辑。
3. **来源展示（后续扩展）：** 当前 `ChatView.vue` 没有来源卡片或 `sources` 字段消费逻辑；实现结构化回答时再纳入该契约。
4. **追问交互：** `need_clarification` 时将 `clarifying_question` 作为助手消息展示，用户下一条消息继续携带同一 `conversation_id` 发送。
5. **敏感信息：** 前后端均不传输、不记录学号、身份证号、账号密码；提示词已禁止索取敏感信息。
6. **CORS：** 开发环境前端 `localhost:5173`（Vite），后端需允许该来源跨域（**待后端确认**）；生产环境同域部署时可关闭。
7. **接口变更：** 任何字段增删必须同步更新本文档并写入变更记录（团队协作规则第 3 条）。

---

## 6. 待确认清单

| 编号 | 事项 | 相关方 |
|---|---|---|
| Q1 | 统一错误响应结构（§1.3） | 成员三 |
| Q2 | `ServiceItem.prompt` 是否由后端返回（§2.1） | 成员三 |
| Q3 | 非 `answered` 状态下 `answer` 字段为 `null` 还是省略（§3.3） | 成员三 |
| Q4 | `GET /api/conversations` 新增接口及「待继续/已完成」状态推导规则（§3.4） | 成员三、成员一 |
| Q5 | `reason_code` 枚举值（§3.5） | 成员一、成员三 |
| Q6 | CORS 允许来源（§5 第 6 条） | 成员三 |


