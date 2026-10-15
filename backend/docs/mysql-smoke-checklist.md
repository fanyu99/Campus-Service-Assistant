# MySQL 冒烟检查清单

> 用途：SQLite 内存库无法覆盖的 MySQL 专属行为（utf8mb4 落库、原生 ENUM DDL、`caching_sha2_password` 认证、连接字符集），在真实 MySQL 8.x 可用时按本清单逐项手动核验。
> 前置：`backend/requirements.txt` 已安装完毕；仓库根 `.env` 已配置 `DATABASE_URL`（含真实口令，不入库）。
> 编制日期：2026-10-10

---

## 1. 建库

```powershell
python scripts/create_database.py
```

- 期待输出：`数据库 campus 已就绪（新建或已存在）`
- 首次执行：新建库；重复执行：静默跳过不报错、不破坏数据
- 失败排查：输出「数据库服务器不可达」时，检查 MySQL 实例状态与 `DATABASE_URL` 配置（主机 / 端口 / 口令）

## 2. 迁移

```powershell
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
```

- 期待输出：`Running upgrade  -> 0001, initial schema`
- 重复执行：`upgrade head` 对已处于最新版本的库为 no-op（无副作用）
- 回滚验证（可选）：

```powershell
.venv\Scripts\python.exe -m alembic downgrade base
.venv\Scripts\python.exe -m alembic upgrade head
```

- 期待：回滚后四张表移除、再次升级结构恢复一致

## 3. 演示数据

```powershell
cd 仓库根
.venv\Scripts\python.exe scripts\seed_demo_data.py
```

- 期待输出：`演示数据写入完成：service_items 8 条，source_documents 8 条，conversations 5 条，feedback 5 条`
- 重复执行：输出计数不变（幂等）

## 4. 零漂移核验

```powershell
cd backend
.venv\Scripts\python.exe -m alembic check
```

- 期待输出：`No new upgrade operations detected.`
- 含义：数据库实际表结构与模型元数据零漂移（迁移为表结构唯一定义点的红线核验）

## 5. 字符集核验（utf8mb4）

连接 MySQL 后执行：

```sql
SHOW VARIABLES LIKE 'character%';
SHOW CREATE TABLE campus.service_items;
```

- 期待：`character_set_server` / `character_set_database` 为 `utf8mb4`；`SHOW CREATE TABLE` 的建表语句含 `ENGINE=InnoDB` 与 `DEFAULT CHARSET=utf8mb4`
- 中文抽样：`INSERT` 一条含中文的记录后 `SELECT` 回读，确认无乱码

## 6. 认证与连接核验（caching_sha2_password）

```powershell
cd backend
.venv\Scripts\python.exe -c "from app.db.session import create_db_engine; from sqlalchemy import text; e = create_db_engine(); print(e.connect().execute(text('SELECT 1')).scalar())"
```

- 期待输出：`1`
- 含义：PyMySQL 经 `cryptography` 支持 MySQL 8 默认认证插件 `caching_sha2_password`，连接成功
- 失败排查：报认证插件相关错误时，确认 `cryptography` 已安装（`pip show cryptography`）

## 7. 时间字段抽样核验（ISO 8601 带时区）

连接 MySQL 后执行：

```sql
SELECT started_at, last_message_at FROM campus.conversations LIMIT 1;
```

- 期待：时间为 UTC（比北京时间早 8 小时）；应用层读取后可还原为 ISO 8601 带时区格式（如 `2026-10-10T12:00:00+00:00`）
- 说明：MySQL `DATETIME` 不保留时区，本组件统一存 UTC，序列化层输出时固定 `+00:00` 偏移

---

## 核验记录

| 日期 | 执行人 | 结果 | 备注 |
|---|---|---|---|
| | | | |