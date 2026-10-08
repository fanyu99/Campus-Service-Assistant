# 前端部署说明

> 版本：v0.1 ｜ 编制日期：2026-09-30 ｜ 编制人：成员二（前端）
> 适用场景：部署到域名根目录（`base: '/'`），容器化方案（Docker Compose on ECS）

---

## 1. 构建基线

| 项目 | 值 |
|---|---|
| Node 版本 | 20（仅构建期需要） |
| 安装依赖 | `npm ci` |
| 构建命令 | `npm run build`（`vue-tsc -b && vite build`） |
| 构建产物 | `frontend/dist/` |
| 部署路径 | 域名根目录 `/`（`vite.config.ts` 已显式设置 `base: '/'`） |
| 静态资源 | `/assets/...`（`public/assets` 原样复制到 `dist/assets`，根目录部署下可直接访问） |

---

## 2. 环境变量

| 文件 | 变量 | 值 | 说明 |
|---|---|---|---|
| `.env.production` | `VITE_API_BASE_URL` | `/api` | 生产环境接口基地址 |

- **同域部署**：前端所有请求走 `/api`，由 Nginx 反代到后端，**无需配置 CORS**。
- **开发环境**：`vite.config.ts` 已将 `/api` 代理到 `http://localhost:8000`，本地开发同样无需跨域。
- `.env` 系列不入库（见 `.dockerignore`），仅 `.env.production` 参与镜像构建。

---

## 3. 容器化部署（推荐）

前端 `Dockerfile` 为多阶段构建：`node:20-alpine` 构建 → `nginx:1.27-alpine` 托管静态产物。

`docker-compose.yml` 中前端服务片段：

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

> **重要**：`nginx.conf` 中反代目标是 `http://backend:8000`，因此 compose 中**后端服务名必须为 `backend`**，否则需同步修改 `nginx.conf`。

### 3.1 只构建前端静态镜像（后端未就绪时）

后端目录尚不存在时，可以只把前端打包成镜像单独运行。**在仓库根目录执行**（构建上下文是 `frontend/`）：

```bash
# 构建
docker build -t campus-service-assistant-frontend:latest ./frontend

# 运行：浏览器访问 http://localhost:8080
docker run -d --name campus-frontend -p 8080:80 campus-service-assistant-frontend:latest

# 查看日志 / 停止并删除
docker logs -f campus-frontend
docker rm -f campus-frontend
```

镜像基于 `nginx:1.27-alpine`，静态产物位于 `/usr/share/nginx/html`。
Dockerfile 为多阶段构建，构建期用 `node:20-alpine` 执行 `npm ci` + `npm run build`，运行期不携带 Node 与源码。

> ⚠️ **单独运行时的 `/api` 行为**：`nginx.conf` 把 `/api/` 反代到 `http://backend:8000`。
> 没有 backend 容器时，访问 `/api/*` 会返回 **502**。当前六个页面都使用本地 mock 数据，
> 不影响页面浏览；等后端就绪后用 `docker compose up` 一起启动即可。

> 💡 **只想用 WSL 里已有的 nginx 托管静态文件**（不打包镜像）：本地 `npm run build` 后，
> 把 `frontend/dist/` 拷进 WSL，nginx 的 `root` 指向该目录，并保留
> `try_files $uri $uri/ /index.html;` 以支持 history 路由回退。

---

## 4. Nginx 配置要点（`frontend/nginx.conf`）

- **history 模式回退**：`try_files $uri $uri/ /index.html;`，否则 `/chat`、`/services` 等页面刷新会 404。
- **缓存策略**：`/assets/` 长缓存（1 年，immutable）；`index.html` 不缓存，保证发版即时生效。
- **接口反代**：`location /api/` → `http://backend:8000`，保留 `/api` 前缀（与 `docs/api.md` 接口路径一致）。
- gzip 压缩已开启。

---

## 5. 非容器部署（备选）

1. 本地执行 `npm run build`，将 `frontend/dist/` 上传至服务器 `/var/www/campus/`。
2. Nginx 的 `root` 指向 `/var/www/campus`，其余 location 规则同 `nginx.conf`。
3. 反代目标改为 `http://127.0.0.1:8000`（后端由 systemd 常驻）。

---

## 6. 上线自测清单

- [ ] 各页面直接刷新不 404（首页 / 我的对话 / 支持事项 / 最近记录 / 使用帮助 / 设置）
- [ ] 静态资源无 404（品牌图标、角色图、DMSans/Epilogue 字体）
- [ ] 深色 / 浅色 / 跟随系统切换正常，刷新后记忆保留
- [ ] 移动端 / 窄屏布局正常
- [ ] 背景动效流畅，移动端不卡顿
- [ ] `/api/health` 连通（同域反代生效）

---

## 7. 待完成（依赖后端就绪）

- 页面切换到真实接口：`HomeView` / `ServicesView` 接 `fetchServiceItems()`；`ChatView` 接 `sendChatMessage()`（当前仍是 mock / `setTimeout`）。
- `docs/api.md` §6 的 6 项待确认（错误结构、`prompt` 字段、`answer` 空值、`conversations` 接口、`reason_code` 枚举、CORS）。
- 可选优化：构建产物主 chunk 约 1 MB（Element Plus 全量引入），后续可按需引入或配置 `manualChunks` 拆包。