# 前端接口说明（已迁移）

> **本文件不再是接口契约的来源。** 权威接口文档已统一到仓库根的
> **[`docs/api.md`](../../docs/api.md)**（v1.0 定稿）。
>
> 原先这里是「联调草案」，与 `src/api/client.ts` 的实现各自漂移
> （例如草案称「client.ts 没有定义问答响应接口」，而实际早已定义）。
> 为避免两份来源继续分叉，接口定义、参数、返回值、错误处理一律以 `docs/api.md` 为准。
>
> 2026-10-07 修正说明见 `docs/api.md` §8 变更记录。

---

## 前端侧要点（只保留「本仓库前端如何用」的部分）

### 1. 调用封装

全部接口封装在 `frontend/src/api/client.ts`：

| 函数 | 对应接口 | 说明 |
|---|---|---|
| `checkHealth()` | `GET /api/health` | 联调 / 部署探测 |
| `fetchServiceItems()` | `GET /api/service-items` | 返回 `ServiceItem[]`（直接数组） |
| `sendChatMessage(payload)` | `POST /api/chat/messages` | 返回结构化 `ChatResponse` |
| `submitFeedback(payload)` | `POST /api/feedback` | 返回 `{ status }` |
| `fetchConversations(limit)` | `GET /api/conversations` | 返回 `ConversationListResponse` |
| `isSafeSourceUrl(url)` | — | 渲染来源链接前的协议校验（仅 http/https） |

### 2. 类型定义

`ChatResponse` / `AnswerCard` / `Source` / `AnswerStatus` / `FeedbackRequest` /
`ConversationSummary` 等类型全部定义在 `client.ts`，与 `docs/api.md` §3 一一对应。
**新增字段时先改 `docs/api.md`，再改 `client.ts`。**

### 3. 错误处理

`client.ts` 把一切失败收敛成 `ApiError`：

- 后端错误体：读 `payload.error.message` / `payload.error.code`；
- 本地错误码：`TIMEOUT`（超 8 秒）、`NETWORK_ERROR`、`INVALID_RESPONSE`；
- 页面据此展示重试提示，不展示内部错误细节。

### 4. 当前接线状态

六个页面仍在使用 `src/data/home.mock.ts` 与 `setTimeout` 模拟数据，
**尚未调用上述任何函数**；接入顺序与注意事项见 `docs/api.md` §5、§6。

### 5. 环境变量

| 文件 | 变量 | 值 |
|---|---|---|
| `.env.production` | `VITE_API_BASE_URL` | `/api`（同域反代，无需 CORS） |

开发环境由 `vite.config.ts` 把 `/api` 代理到 `http://localhost:8000`。
