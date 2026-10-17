# 校园办事小秘书 · Campus Service Assistant

学生问「学生证丢了怎么补办」，系统只从学校官方通知里找答案。找不到依据就说不知道，不编流程。

[中文](#中文) ｜ [English](#english)

---

## 中文

### 项目简介

校园事务的办理条件、材料、地点和截止时间，散在教务部、学工处、后勤等部门的通知里。学生要么搜不到，要么搜到的是三年前的版本。这个项目把八项高频事务整理成可核验的知识条目，用自然语言问答给出结构化答案，每条答案都能点回原始通知。

它不是通用聊天机器人。知识库外的问题（食堂几点开门、怎么选课）会明确拒答，而不是拿常识凑一个答案。

当前知识库覆盖苏州大学 8 项学生事务：

| 编码 | 事项 | 编码 | 事项 |
| --- | --- | --- | --- |
| S01 | 学生证补办 | S05 | 奖学金申请与评定 |
| S02 | 校园卡挂失、解挂与补办 | S06 | 助学金申请与困难认定 |
| S03 | 宿舍报修 | S07 | 转专业申请 |
| S04 | 请假办理 | S08 | 毕业生离校手续 |

### 功能

- 结构化回答：办理条件、所需材料、办理步骤、地点、期限、联系方式、风险提示。
- 七种回答状态。拒答、追问、超时各有各的样子，不会一律显示成一张卡片。
- 多轮对话：信息不全时主动追问（「你的请假类型是事假、病假还是公假？」），回答「病假，三天」能接上上一轮；同一会话里再问「那费用呢」，也知道指的是哪件事。
- 历史记录：一问一答成对落库，可回看、可续接，生成时会带上最近 4 轮上下文。
- 来源与反馈：回答下方列官方来源，可提交「来源错误 / 流程不完整 / 内容过期 / 其他」。
- 界面：深浅色主题、粒子背景、角色气泡、移动端横向顶栏。

### 技术栈

| 部分 | 选型 |
| --- | --- |
| 前端 | Vue 3 + TypeScript + Vite + Vue Router，组件手写，无 UI 框架 |
| 后端 | FastAPI + Pydantic + SQLAlchemy 2.0 |
| 数据库 | MySQL 8（测试用 SQLite），Alembic 迁移 0001–0006 |
| 模型 | 华为云 AgentArts 工作流，或 MaaS（OpenAI 兼容接口） |
| 部署 | Docker Compose + Nginx，frontend / backend / db 三个容器 |

### 目录结构

```text
.
├── backend/
│   ├── app/api/          七个接口的路由
│   ├── app/services/     问答编排、意图识别、知识检索、模型适配、会话
│   ├── app/core/         配置、错误响应、限流、输入清洗
│   ├── alembic/          数据库迁移
│   └── tests/            277 个用例
├── frontend/
│   ├── src/views/        首页、我的对话、支持事项、最近记录、使用帮助、设置
│   ├── src/components/   回答卡片、来源列表、反馈栏、状态提示、下拉选择
│   ├── src/composables/  主题、个人资料、角色气泡、事项数据
│   └── tests/            21 个用例
├── scripts/              建库、演示数据、真实知识导入、展示字段回填
├── docs/                 接口契约、架构文档、知识库文档、开题材料
├── docker-compose.yml
└── .env.example
```

### 快速开始

#### Docker Compose

需要 Docker Engine 与 Compose v2，80 端口空闲。

```bash
cp .env.example .env
# 至少填 MYSQL_PASSWORD、MYSQL_ROOT_PASSWORD
# 再填一组模型凭证：AGENTARTS_API_KEY + AGENTARTS_AGENT_ID + AGENTARTS_BASE_URL，
# 或 MAAS_API_KEY
docker compose up -d --build
docker compose ps
```

启动顺序是 db 健康 → backend 跑完 `alembic upgrade head` → frontend 等 backend 健康。打开 <http://localhost> 即可。

首次部署还要在宿主机导入知识。三个脚本都幂等，可以重复执行：

```bash
export DATABASE_URL="mysql+pymysql://app:<MYSQL_PASSWORD>@127.0.0.1:3306/campus"
python scripts/seed_demo_data.py
python scripts/load_real_knowledge.py
python scripts/backfill_service_display_fields.py
```

不导入知识的话，检索找不到「已核验 + 有效期内 + 有正文」的依据，问答会一律返回 `insufficient_evidence`。这是安全默认，不是故障。

#### 本地开发

后端需要 Python 3.12 和 MySQL 8：

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate                 # macOS / Linux：source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python ../scripts/create_database.py   # 首次建库
alembic upgrade head
uvicorn app.main:app --reload          # 接口文档：http://localhost:8000/docs
```

前端：

```bash
cd frontend
npm ci
npm run dev        # http://localhost:5173，/api 已代理到 8000
```

`APP_ENV=local` 且没有模型凭证时，问答走本地替身实现，卡片上会标「本地替身实现」。它只够联调，别当成真答案。

### 配置

配置从仓库根目录的 `.env` 读取，容器部署时也可用环境变量覆盖。

| 变量 | 缺省 | 说明 |
| --- | --- | --- |
| `APP_PORT` | `8000` | 后端监听端口 |
| `APP_ENV` | `local` | `local` 才允许启用替身实现，部署环境固定 `production` |
| `DATABASE_URL` | `mysql+pymysql://app:app@db:3306/campus` | 数据库连接串 |
| `AGENTARTS_API_KEY` / `AGENTARTS_BASE_URL` / `AGENTARTS_AGENT_ID` | 空 | 三项齐全才启用工作流 |
| `MAAS_API_KEY` | 空 | 直连 MaaS 模型 |
| `MAAS_BASE_URL` | `https://api.modelarts-maas.com/v2` | 以控制台「调用说明」为准 |
| `MAAS_MODEL` | `deepseek-v4-flash` | 建议显式填写，`docker-compose.yml` 里写的是 `DeepSeek-V3`，两处缺省不一致 |
| `MAAS_DISABLE_THINKING` | `true` | 关闭思考链 |
| `CHAT_RATE_LIMIT_REQUESTS` | `10` | 限流窗口内最大请求数 |
| `CHAT_RATE_LIMIT_WINDOW_SECONDS` | `60` | 限流窗口长度 |

模型接入顺序写在 `backend/app/services/llm_client.py`：AgentArts 配置齐全就走工作流，否则用 MaaS，本地再退到替身，生产环境两样都没有就返回 503。

`MAAS_DISABLE_THINKING=true` 不是随手写的。这批模型默认先输出思考链，同一个问题耗时能到 12 至 65 秒，关掉后回到 2 至 5 秒。前端超时是 8 秒，不关就过不了。

### 接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/service-items` | 支持事项列表 |
| POST | `/api/chat/messages` | 提问，返回结构化回答 |
| GET | `/api/chat/messages?conversation_id=` | 会话消息明细 |
| GET | `/api/conversations` | 最近会话 |
| POST | `/api/feedback` | 提交反馈 |
| GET | `/api/knowledge/sources` | 知识来源与核验状态 |

请求头里的 `X-Session-Token` 是匿名会话标识，前端首次访问时用 `crypto.randomUUID()` 生成并存在本机。它不承载身份信息，只用来隔离会话，换个标识读不到别人的记录。

完整字段、错误码和示例见 [`docs/api.md`](docs/api.md)，那份是前后端唯一的契约。

### 回答状态

| status | 什么情况 | 前端怎么显示 |
| --- | --- | --- |
| `answered` | 找到可靠依据 | 完整办事卡片 + 来源列表 + 反馈栏 |
| `need_clarification` | 信息不全 | 追问气泡，用户继续补充 |
| `unsupported` | 不在服务范围 | 支持事项列表 |
| `insufficient_evidence` | 依据不足 | 不确定提示，不编流程 |
| `conflict` | 来源互相矛盾 | 提示联系责任部门确认 |
| `service_error` | 模型或上游异常 | 重试入口 |
| `smalltalk` | 寒暄或引导 | 普通聊天气泡 |

### 测试

```bash
cd backend && pytest -q          # 277 passed
cd frontend && npm run test      # 21 passed
cd frontend && npm run build     # vue-tsc 类型检查 + 打包
```

后端测试用 SQLite 内存库跑迁移，不碰 MySQL，也不需要真实模型 Key，测试里会注入确定性替身。

### 设计上的几条硬约束

- 只有「已核验 + 在有效期内 + 有正文 + 链接可引用」的来源能作为生成依据。过期、草稿、冲突都不给确定结论。
- `sources` 由后端从数据库映射，模型自己写的来源一律不采信。
- 证据不足就拒答。宁可说「暂时没找到可靠依据」，也不让模型自由发挥。
- 身份证号、手机号、银行卡号、密码和提示词注入在入口直接 400。
- 会话按 `X-Session-Token` 隔离，禁止跨标识读取或续写。
- 问答限流默认 10 次 / 60 秒，按匿名标识计数。

### 已知边界

- 单机单库。限流器在进程内，多副本部署时实际阈值是「配置值 × 副本数」。
- 模型读超时 7.5 秒，约 5% 的请求会超时返回 503，前端给重试按钮。
- 知识有效期到 2027-08-31，到期前要对照调研清单复查来源。
- 没有登录体系，会话只存在本机浏览器，换设备就看不到。
- 检索按事项编码加元数据过滤，还没上向量检索。

### 文档

| 文档 | 内容 |
| --- | --- |
| [`docs/api.md`](docs/api.md) | 前后端接口契约 v1.3，字段、错误码、状态枚举 |
| [`docs/系统架构文档.md`](docs/系统架构文档.md) | 分层、问答链路、数据设计、部署架构 |
| [`docs/AgentArts知识库文档-学生事务核验版.md`](docs/AgentArts知识库文档-学生事务核验版.md) | 可直接上传 AgentArts 的知识库 Markdown |
| [`backend/docs/deploy.md`](backend/docs/deploy.md) | 后端部署、知识导入、模型选型与延迟实测 |
| [`frontend/docs/deploy.md`](frontend/docs/deploy.md) | 前端构建、Nginx 配置、上线自测清单 |
| [`plans/校园办事小秘书实施方案.md`](plans/校园办事小秘书实施方案.md) | 需求、范围、八周计划 |
| [`docs/项目进度表与成员分工表.md`](docs/项目进度表与成员分工表.md) | 逐周进度、分工矩阵、答辩安排 |

### 团队

三人小组，八周。柯常瑞负责产品与知识工程，范誉负责交互与前端并统筹进度，徐梓凯负责后端与智能体链路。

---

## English

### What this is

The rules for replacing a student ID, repairing a dorm room, or applying for financial aid live in notices scattered across different university offices. Students either can't find them or find a version from three years ago. This project turns eight common student-service procedures into verified knowledge entries and answers questions in plain language, with a card that links back to the original notice.

It is not a general-purpose chatbot. Ask about cafeteria hours or course selection and it declines, rather than filling the gap with guesswork.

The current knowledge base covers eight procedures at Soochow University:

| Code | Procedure | Code | Procedure |
| --- | --- | --- | --- |
| S01 | Student ID replacement | S05 | Scholarship application |
| S02 | Campus card loss report and replacement | S06 | Financial aid application |
| S03 | Dormitory repair request | S07 | Major transfer inquiry |
| S04 | Leave of absence | S08 | Graduation clearance |

### Features

- Structured answers: eligibility, materials, steps, location, deadline, contacts, warnings.
- Seven answer states, so a refusal looks different from a timeout.
- Multi-turn conversation. It asks for missing details ("is this personal leave, sick leave, or official leave?"), accepts "sick leave, three days" as the follow-up, and understands "what about the fee?" inside the same conversation.
- History. Each question and answer is stored as a pair, can be reopened and continued, and the last four turns are fed back as context.
- Sources and feedback. Official links sit under every answer, with a feedback bar for wrong sources, missing steps, and outdated content.
- UI. Light and dark themes, particle background, character bubbles, a mobile top bar.

### Stack

| Part | Choice |
| --- | --- |
| Frontend | Vue 3, TypeScript, Vite, Vue Router, hand-written components, no UI framework |
| Backend | FastAPI, Pydantic, SQLAlchemy 2.0 |
| Database | MySQL 8 (SQLite in tests), Alembic migrations 0001–0006 |
| Model | Huawei Cloud AgentArts workflow, or MaaS with an OpenAI-compatible API |
| Deployment | Docker Compose and Nginx, three containers |

### Layout

```text
.
├── backend/
│   ├── app/api/          seven endpoint routers
│   ├── app/services/     chat pipeline, intent, retrieval, model adapters, sessions
│   ├── app/core/         settings, errors, rate limiting, input sanitising
│   ├── alembic/          migrations
│   └── tests/            277 cases
├── frontend/
│   ├── src/views/        home, chat, services, history, help, settings
│   ├── src/components/   answer card, source list, feedback bar, state notice
│   ├── src/composables/  theme, profile, character bubbles, service data
│   └── tests/            21 cases
├── scripts/              database setup, demo data, real knowledge import
├── docs/                 API contract, architecture, knowledge base, proposal
├── docker-compose.yml
└── .env.example
```

### Getting started

#### Docker Compose

You need Docker Engine, Compose v2, and a free port 80.

```bash
cp .env.example .env
# Fill MYSQL_PASSWORD and MYSQL_ROOT_PASSWORD.
# Then add one set of model credentials: AGENTARTS_API_KEY + AGENTARTS_AGENT_ID
# + AGENTARTS_BASE_URL, or MAAS_API_KEY.
docker compose up -d --build
docker compose ps
```

Startup order is db healthy, then the backend runs `alembic upgrade head`, then the frontend waits for the backend to pass its health check. Open <http://localhost>.

On first deploy, import the knowledge base from the host. All three scripts are idempotent:

```bash
export DATABASE_URL="mysql+pymysql://app:<MYSQL_PASSWORD>@127.0.0.1:3306/campus"
python scripts/seed_demo_data.py
python scripts/load_real_knowledge.py
python scripts/backfill_service_display_fields.py
```

Without this step, retrieval finds no source that is verified, in date, and has body text, so every question returns `insufficient_evidence`. That is the safe default, not a bug.

#### Local development

The backend needs Python 3.12 and MySQL 8:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate                 # macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python ../scripts/create_database.py   # first run only
alembic upgrade head
uvicorn app.main:app --reload          # API docs at http://localhost:8000/docs
```

Frontend:

```bash
cd frontend
npm ci
npm run dev        # http://localhost:5173, /api is proxied to port 8000
```

With `APP_ENV=local` and no model credentials, the chat pipeline falls back to a local stand-in and marks its cards as such. Useful for wiring up the UI, not for real answers.

### Configuration

Settings come from `.env` at the repository root, and container environment variables override them.

| Variable | Default | Notes |
| --- | --- | --- |
| `APP_PORT` | `8000` | Backend port |
| `APP_ENV` | `local` | Only `local` may use the stand-in; deployment is pinned to `production` |
| `DATABASE_URL` | `mysql+pymysql://app:app@db:3306/campus` | Database connection string |
| `AGENTARTS_API_KEY` / `AGENTARTS_BASE_URL` / `AGENTARTS_AGENT_ID` | empty | All three are required to use the workflow |
| `MAAS_API_KEY` | empty | Direct MaaS access |
| `MAAS_BASE_URL` | `https://api.modelarts-maas.com/v2` | Check the console's call instructions |
| `MAAS_MODEL` | `deepseek-v4-flash` | Set it explicitly; `docker-compose.yml` defaults to `DeepSeek-V3` |
| `MAAS_DISABLE_THINKING` | `true` | Turn off the reasoning chain |
| `CHAT_RATE_LIMIT_REQUESTS` | `10` | Max requests per window |
| `CHAT_RATE_LIMIT_WINDOW_SECONDS` | `60` | Window length |

The adapter order lives in `backend/app/services/llm_client.py`: a fully configured AgentArts workflow wins, then MaaS, then the local stand-in, and a production instance with neither credential returns 503.

`MAAS_DISABLE_THINKING=true` earns its place. These models emit a reasoning chain by default, which pushed one question to 12–65 seconds. With it off, the same question lands in 2–5 seconds. The frontend times out at 8 seconds, so leaving it on breaks the acceptance target.

### API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Health check |
| GET | `/api/service-items` | Supported procedures |
| POST | `/api/chat/messages` | Ask a question, get a structured answer |
| GET | `/api/chat/messages?conversation_id=` | Message history for one conversation |
| GET | `/api/conversations` | Recent conversations |
| POST | `/api/feedback` | Submit feedback |
| GET | `/api/knowledge/sources` | Knowledge sources and verification status |

`X-Session-Token` is an anonymous conversation identifier. The frontend generates it with `crypto.randomUUID()` on first visit and keeps it in local storage. It carries no identity, it only isolates conversations, and another token cannot read your history.

Field-level detail, error codes, and examples are in [`docs/api.md`](docs/api.md), the single contract both sides follow.

### Answer states

| status | Meaning | What the user sees |
| --- | --- | --- |
| `answered` | A reliable source was found | Full card, source list, feedback bar |
| `need_clarification` | Missing details | A follow-up question in the chat |
| `unsupported` | Outside the supported scope | The list of supported procedures |
| `insufficient_evidence` | Not enough evidence | An uncertainty notice, no invented steps |
| `conflict` | Sources contradict each other | A prompt to confirm with the responsible office |
| `service_error` | Model or upstream failure | A retry action |
| `smalltalk` | Greeting or guidance | A plain chat bubble |

### Tests

```bash
cd backend && pytest -q          # 277 passed
cd frontend && npm run test      # 21 passed
cd frontend && npm run build     # vue-tsc type check and bundle
```

Backend tests run migrations against an in-memory SQLite database. They do not touch MySQL and do not need a real model key; a deterministic stand-in is injected.

### Design rules

- Only sources that are verified, in date, have body text, and carry a usable URL can ground an answer. Expired, draft, or conflicting sources never produce a firm conclusion.
- `sources` is mapped from the database by the backend. Whatever the model writes as a source is ignored.
- No evidence means no answer. The system would rather say it found nothing reliable than let the model improvise.
- ID numbers, phone numbers, bank cards, passwords, and prompt-injection patterns are rejected with 400 at the door.
- Conversations are isolated by `X-Session-Token`. Cross-token reads and writes are refused.
- Chat is rate limited to 10 requests per 60 seconds per anonymous token.

### Known limits

- Single host, single database. The rate limiter is in-process, so N replicas effectively allow N times the configured limit.
- The model read timeout is 7.5 seconds. Roughly 5% of requests hit it and return 503, and the UI offers a retry.
- The knowledge base expires on 2027-08-31 and needs a review before then.
- There is no login. Conversations live in the browser and do not follow the user to another device.
- Retrieval filters by procedure code and metadata. There is no vector search yet.

### Docs

| Document | Contents |
| --- | --- |
| [`docs/api.md`](docs/api.md) | API contract v1.3: fields, error codes, states |
| [`docs/系统架构文档.md`](docs/系统架构文档.md) | Layers, chat pipeline, data design, deployment |
| [`docs/AgentArts知识库文档-学生事务核验版.md`](docs/AgentArts知识库文档-学生事务核验版.md) | Knowledge base Markdown ready for AgentArts upload |
| [`backend/docs/deploy.md`](backend/docs/deploy.md) | Backend deployment, knowledge import, model latency results |
| [`frontend/docs/deploy.md`](frontend/docs/deploy.md) | Frontend build, Nginx, go-live checklist |
| [`plans/校园办事小秘书实施方案.md`](plans/校园办事小秘书实施方案.md) | Requirements, scope, eight-week plan |
| [`docs/项目进度表与成员分工表.md`](docs/项目进度表与成员分工表.md) | Weekly progress, roles, demo plan |

### Team

Three people, eight weeks. Ke Changrui owns product and knowledge engineering, Fan Yu owns interaction and frontend and coordinates the schedule, Xu Zikai owns the backend and the agent pipeline.
