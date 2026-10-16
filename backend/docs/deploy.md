# 校园办事小秘书 · 后端部署与运维说明

> **适用范围**：Docker Compose 一键部署（frontend + backend + MySQL），对应实施方案第六章「技术架构」与第 7 周「部署和比赛材料」。
> **配套文件**：`docker-compose.yml`（编排）、`.env.example`（环境变量样例）、`backend/Dockerfile`（后端镜像）、`frontend/docs/deploy.md`（前端单镜像）。
> **编制日期**：2026-10-16 ｜ 版本 v1.0

---

## 1. 前置条件

| 项 | 说明 |
|---|---|
| Docker Engine + Compose v2 | Windows 用 Docker Desktop（需先手动启动） |
| 仓库根 `.env` | 不入库；从 `.env.example` 复制后填写，见第 2 节 |
| 端口 | 80（前端）、127.0.0.1:3306（数据库，仅本机回环） |

## 2. 环境变量

在仓库根目录执行 `Copy-Item .env.example .env`，然后填写：

| 变量 | 必填 | 说明 |
|---|---|---|
| `MYSQL_PASSWORD` | 是 | 应用账号口令（compose 缺省会直接报错提示） |
| `MYSQL_ROOT_PASSWORD` | 是 | root 口令 |
| `AGENTARTS_API_KEY` + `AGENTARTS_AGENT_ID` | 二选一（推荐） | 走 AgentArts 工作流；两者都填才生效 |
| `AGENTARTS_BASE_URL` | 走工作流时必填 | 以控制台该工作流「API 调用」页给出的值为准 |
| `MAAS_API_KEY` | 二选一 | 直连 MaaS 模型（未配 AgentArts 时生效） |
| `MAAS_MODEL` / `MAAS_BASE_URL` | 否 | 缺省 `DeepSeek-V3` / `https://api.modelarts-maas.com/v2`，以控制台「调用说明」为准 |

> **`APP_ENV` 不需要在 `.env` 里设置**：`docker-compose.yml` 已固定为 `production`。
> 这是硬性约定——`local` 会启用本地替身实现（返回占位卡片），绝不允许用于部署环境；
> 未配置模型凭证时，生产环境问答接口会明确返回 `503 UPSTREAM_ERROR`，而不是给出占位答案。

## 3. 启动

```powershell
cd <仓库根目录>
docker compose up -d --build
docker compose ps          # 等 backend 状态变为 healthy（首次含镜像构建与数据库初始化）
```

后端容器启动时会先执行 `alembic upgrade head`（带等待数据库就绪的重试），成功后才启动 uvicorn；
迁移失败会阻塞启动（fail fast），用 `docker compose logs backend` 查看原因。

## 4. 首次部署：导入知识库（幂等，可重复执行）

**顺序**：迁移（容器已自动完成）→ 演示事项 → 真实知识 → 展示字段。

```powershell
# 在宿主机、仓库根目录执行；数据库走 127.0.0.1（compose 只对本机开放 3306）
$env:DATABASE_URL="mysql+pymysql://app:<MYSQL_PASSWORD>@127.0.0.1:3306/campus"

cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head   # 若容器已迁移可跳过
cd ..

python scripts/seed_demo_data.py                    # 写入 S01–S08 事项（演示来源随后会被替换）
python scripts/load_real_knowledge.py                # 删除 example.edu.cn 演示来源，写入核验版来源与正文
python scripts/backfill_service_display_fields.py    # 回填 icon / tone / prompt
```

- `load_real_knowledge.py` 以「事项 + 标题」为身份覆盖写：内容更新后重跑即刷新，不会重复堆积。
- **不导入知识库的后果**：检索没有「已核验 + 有效期内 + 有正文」的依据，问答会一律返回
  `insufficient_evidence`（拒答）。这是设计上的安全默认，不是故障。

## 5. 验收自测

```powershell
curl http://localhost/api/health
# {"status":"ok"}

curl http://localhost/api/service-items
# 8 项，含 id/title/description/category/icon/tone/prompt

curl -X POST http://localhost/api/chat/messages -H "Content-Type: application/json" `
     -H "X-Session-Token: smoke-token" `
     -d '{\"conversation_id\":null,\"message\":\"学生证丢了怎么补办？\"}'
# status=answered，answer 为结构化卡片，sources 为 suda.edu.cn 官方来源

curl http://localhost/api/knowledge/sources?status=verified
# {"sources":[...],"total":8}
```

## 6. 运维要点

| 主题 | 说明 |
|---|---|
| 迁移 | 后端容器启动时自动执行；新增迁移后 `docker compose up -d --build` 即生效 |
| 限流 | 进程内滑动窗口（缺省 10 次/60 秒，按匿名标识计数）。**多副本时实际阈值为「配置值 × 副本数」**；如需严格全局限流，把 `app/core/rate_limit.py` 换成 Redis 计数实现即可，调用方无需改动 |
| 输入清洗 | 敏感数据取值（身份证 / 手机号 / 银行卡 / 凭据）与提示词注入一律 400 拒绝；来源链接仅接受 http(s) 绝对地址 |
| 数据备份 | 数据在 `db-data` 卷：`docker compose down`（保留数据）/ `docker compose down -v`（清空数据，慎用） |
| 知识时效 | 当前知识有效期至 **2027-08-31**；到期前对照 `docs/suda-affairs-research-2026-10.md` 中标注 ⚠️ 的条目复查并更新版本号 |
| 安全 | `.env` 不入库；密钥只经环境变量注入；`db` 端口仅绑定 127.0.0.1 |

## 7. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 页面能开，`/api/*` 返回 502 | backend 未启动或未通过健康检查 | `docker compose ps` / `docker compose logs backend` |
| 问答返回 503 `UPSTREAM_ERROR` | 未配置模型凭证，或 Key 未生效（新 Key 需 3–5 分钟） | 检查 `.env` 与容器环境变量；`docker compose exec backend env \| findstr AGENTARTS` |
| 问答返回 503，日志出现 `403 ModelArts.81006 The resource is frozen` | **模型服务被冻结**：欠费 / 免费额度用尽 / 需续费 | 到华为云 MaaS 控制台确认计费与额度并续费；恢复后无需改代码 |
| 问答返回 503，日志出现 `400` 或 `model not found` | `MAAS_MODEL` 与控制台开通的模型不一致 | 按控制台「调用说明」改 `MAAS_MODEL`（预置服务区域为西南-贵阳一） |
| 报 `model not found` | `MAAS_MODEL` 与控制台开通的模型不一致 | 按控制台「调用说明」改 `MAAS_MODEL`（预置服务区域为西南-贵阳一） |
| 返回 429 `RATE_LIMITED` | 触发限流 | 等待窗口滑过，或调整 `CHAT_RATE_LIMIT_REQUESTS` |
| `/api/service-items` 返回 `[]` | 未执行 `seed_demo_data.py` | 执行第 4 节导入流程 |
| 问答一律 `insufficient_evidence` | 未执行 `load_real_knowledge.py`（无正文依据） | 执行第 4 节导入流程 |
| `docker compose config` 报缺少变量 | `.env` 未填必填项 | 补 `MYSQL_PASSWORD` / `MYSQL_ROOT_PASSWORD` |
