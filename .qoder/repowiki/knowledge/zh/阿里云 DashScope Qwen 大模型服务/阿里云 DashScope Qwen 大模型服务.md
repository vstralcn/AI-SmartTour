---
kind: external_dependency
name: 阿里云 DashScope Qwen 大模型服务
slug: aliyun-dashscope-qwen
category: external_dependency
category_hints:
    - vendor_identity
    - auth_protocol
scope:
    - '**'
---

### 身份与角色
- 本项目通过 OpenAI 兼容 API 调用阿里云 DashScope 的 Qwen 系列模型（默认 qwen-plus），作为 Agent 规划与回答生成的 LLM 后端。
- 当未配置 `LLM_API_KEY` 时，系统降级为本地知识库可信检索 + grounded_answer，不调用外部模型。

### 集成方式
- 通过环境变量注入：`LLM_API_KEY`、`LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1`、`LLM_MODEL=qwen-plus`；容器编排由 docker-compose.yml 注入，本地开发由 .env 覆盖。

### 关键约束
- 鉴权协议：OpenAI 兼容的 Bearer Token（`api_key`）+ 自定义 `base_url`；密钥不得提交到仓库，需通过 `.env` 或容器环境注入。
- 超时与降级：已为 LLM 调用配置 30 秒超时（`app/services/llm.py` 中 `DEFAULT_TIMEOUT = 30.0`），超时后自动回退到 grounded_answer 本地知识库回答。
- 多实例一致性：若未来启用多 worker/多实例，需确保 LLM 调用幂等并配合会话持久化（Redis）。