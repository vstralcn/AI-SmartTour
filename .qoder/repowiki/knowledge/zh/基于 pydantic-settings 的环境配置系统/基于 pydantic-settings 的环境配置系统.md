---
kind: configuration_system
name: 基于 pydantic-settings 的环境配置系统
category: configuration_system
scope:
    - '**'
source_files:
    - backend/app/config.py
    - .env.example
    - docker-compose.yml
    - backend/pyproject.toml
---

## 1. 使用的系统与工具
- **pydantic-settings** (`BaseSettings`)：作为后端唯一运行时配置加载器，提供类型校验、默认值与环境变量注入。
- **.env 文件 + docker-compose environment**：开发时通过 `.env` 覆盖默认值；容器编排通过 `docker-compose.yml` 的 `environment` 字段注入环境变量。
- **OpenAI SDK 兼容模式**：LLM 相关配置（`llm_api_key` / `llm_api_base` / `llm_model`）通过 OpenAI 客户端间接消费，统一走阿里云 DashScope 兼容端点。

## 2. 核心文件与包
- `backend/app/config.py`：定义 `Settings(BaseSettings)` 模型，集中声明所有配置项及默认值，并暴露全局 `settings` 实例。
- `.env.example`：提供本地开发所需的环境变量模板（端口、Postgres 密码、LLM 密钥等）。
- `docker-compose.yml`：为各服务注入运行期环境变量，将 compose 变量（如 `${BACKEND_PORT:-8000}`）映射到容器内环境变量。
- `backend/pyproject.toml`：声明 `pydantic-settings>=2.3` 依赖，确保配置加载能力可用。

## 3. 架构与约定
- **单一 Settings 模型**：所有后端配置集中在 `app.config.Settings` 中，按领域分组（应用、数据库、LLM、向量库、数字人、ASR/TTS），每个字段都有 Python 类型与合理默认值，便于本地 SQLite 直连启动。
- **配置来源优先级**：`model_config = SettingsConfigDict(env_file=".env")` 使 `.env` 中的变量覆盖默认值；容器环境下的环境变量又覆盖 `.env`，形成“默认 → .env → 容器 env”三层覆盖。
- **compose 变量桥接**：`.env.example` 定义的 `BACKEND_PORT`、`POSTGRES_PASSWORD` 等通过 compose 的 `${VAR:-default}` 语法注入到容器环境变量名（如 `DATABASE_URL`、`REDIS_URL`、`LLM_API_KEY`），由 `Settings` 直接读取。
- **无独立配置文件**：项目未使用 YAML/JSON/TOML 等外部配置文件，全部以环境变量驱动，符合云原生 12-Factor 实践。
- **前端侧无运行时配置**：前后端分离，前端通过 Nginx/Vite 构建产物访问后端 API，不引入运行时配置机制。

## 4. 开发者应遵循的规则
- **新增配置项**：在 `app.config.Settings` 中添加字段，给出明确类型与默认值；若该配置仅用于容器部署，保持默认值为空或占位符，并通过 `docker-compose.yml` 注入。
- **敏感信息**：API Key、密码等必须通过环境变量传入，禁止硬编码到源码或提交到版本库；参考 `.env.example` 的命名风格（全大写、下划线分隔）。
- **不要绕过 `settings` 单例**：业务代码统一通过 `from app.config import settings` 获取配置，避免重复解析环境变量。
- **容器化部署**：修改 `docker-compose.yml` 的 `environment` 段来覆盖配置，而非修改 `.env`；生产环境建议通过 K8s ConfigMap/Secret 注入同名环境变量。