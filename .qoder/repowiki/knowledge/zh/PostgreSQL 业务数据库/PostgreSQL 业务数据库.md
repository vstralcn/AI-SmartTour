---
kind: external_dependency
name: PostgreSQL 业务数据库
slug: postgresql
category: external_dependency
category_hints:
    - client_constraint
scope:
    - '**'
---

### 身份与角色
- 项目生产数据持久化使用 PostgreSQL 16（Alpine 镜像），保存景区知识、角色配置、匿名交互事件等业务数据；本地开发可回退 SQLite。

### 集成方式
- 通过 `DATABASE_URL=postgresql+asyncpg://...` 注入连接串，使用 SQLAlchemy 2.x + asyncpg 异步驱动访问。
- Docker Compose 提供健康检查与数据卷持久化，默认数据库名 smarttour、用户 postgres。

### 关键约束
- 连接字符串格式必须包含 `postgresql+asyncpg://` 前缀，否则 SQLAlchemy 无法识别方言。
- 本地开发时默认回退到 `sqlite+aiosqlite:///./smarttour.db`，部署时需显式传入 DATABASE_URL。