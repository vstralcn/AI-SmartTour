---
kind: external_dependency
name: Redis 缓存与会话存储（已就绪但未接入）
slug: redis
category: external_dependency
category_hints:
    - migration_status
scope:
    - '**'
---

### 身份与角色
- Docker Compose 已启动 Redis 7（带 AOF 持久化），并通过 `REDIS_URL` 注入后端，但当前会话状态、游客画像、反馈记录仍全部保存在进程内存 dict 中，Redis 处于"空转"状态。

### 迁移状态
- README 明确将"账号级长期画像"列为待实现能力，且架构图中 Session → Redis 是目标路径；当前代码尚未接入 redis-py 客户端，属于"基础设施就绪、应用层待迁移"的状态。
- 若直接 `uvicorn --workers>1` 或多实例部署，会话与画像会丢失或不一致。

### 后续方向
- 将 `DialogueEngine.sessions`、`GuideAgent.user_profiles`、`feedback_records` 迁至 Redis，同时把 feedback 落库，以兑现并发与长期画像承诺。