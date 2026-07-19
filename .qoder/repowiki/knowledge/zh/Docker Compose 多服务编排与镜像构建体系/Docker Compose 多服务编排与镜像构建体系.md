---
kind: build_system
name: Docker Compose 多服务编排与镜像构建体系
category: build_system
scope:
    - '**'
source_files:
    - docker-compose.yml
    - backend/Dockerfile
    - digital_human/Dockerfile
    - frontend/admin-panel/Dockerfile
    - frontend/tourist-app/Dockerfile
    - backend/pyproject.toml
    - digital_human/requirements.txt
    - frontend/admin-panel/package.json
    - frontend/tourist-app/package.json
---

## 构建系统概览

本项目采用 **Docker + Docker Compose** 作为统一的构建、打包与编排方案，将后端 FastAPI 服务、数字人视频生成服务、游客端与管理端前端以及 PostgreSQL/Redis 基础设施统一编排，对外暴露完整智慧景区 AI 导游系统。

## 核心工具与框架

- **容器化**: 每个子项目独立 `Dockerfile`，使用多阶段构建优化镜像体积（前端 Node 构建产物由 nginx:alpine 静态托管）
- **服务编排**: 根目录 `docker-compose.yml` 定义全部服务及其依赖关系、端口映射、环境变量与健康检查
- **Python 包管理**: 后端使用 `pyproject.toml` (PEP 517/518) + setuptools，通过 `pip install .` 安装；可选依赖通过 `[project.optional-dependencies]` 分组（rag/dev）
- **前端构建**: Vue3 + Vite + TypeScript，通过 `npm ci --legacy-peer-deps` 锁定依赖，`vue-tsc --noEmit && vite build` 进行类型检查+编译

## 关键文件与职责

| 文件 | 作用 |
|------|------|
| `docker-compose.yml` | 全局服务编排：backend、tourist-app、admin-panel、postgres、redis、digital-human，含健康检查与 GPU 资源声明 |
| `backend/Dockerfile` | Python 3.11-slim 基础镜像，安装 ffmpeg（降级模拟），`pip install .` 安装后端包，uvicorn 启动 |
| `digital_human/Dockerfile` | 独立 FastAPI 服务镜像，基于 requirements.txt 安装依赖，暴露 8001 端口 |
| `frontend/admin-panel/Dockerfile` | Node 20 多阶段构建 → nginx:alpine 静态托管 |
| `frontend/tourist-app/Dockerfile` | 同上，游客端静态站点 |
| `backend/pyproject.toml` | 后端依赖声明、Ruff 代码规范、setuptools 构建配置 |
| `frontend/*/package.json` | 前端脚本与依赖，dev/build/preview 三脚本统一 |
| `digital_human/requirements.txt` | 数字人服务轻量依赖（仅 fastapi/uvicorn/multipart） |

## 架构与约定

1. **服务分层与依赖顺序**
   - backend 依赖 postgres、redis 就绪后才启动（`depends_on` + `condition: service_healthy`）
   - tourist-app 与 admin-panel 依赖 backend 健康后启动
   - digital-human 通过 `profiles: [gpu]` 按需启用，需 nvidia docker runtime 并声明 GPU 设备配额

2. **环境变量驱动配置**
   - 所有外部连接参数通过 `${VAR:-default}` 注入（数据库、LLM API Key/Base/Model、各服务端口等）
   - 提供 `.env.example` 作为模板，避免硬编码敏感信息

3. **数据持久化**
   - 通过 named volumes (`pgdata`, `redisdata`, `knowledge_data`) 持久化数据库、缓存与知识库上传/向量数据

4. **健康检查策略**
   - backend: HTTP `/health` 端点探测
   - 前端: `wget -qO- http://127.0.0.1/` 探测 nginx 是否响应
   - postgres: `pg_isready`
   - redis: `redis-cli ping`

5. **构建产物最小化**
   - 前端采用双阶段构建：Node 环境只用于编译，最终镜像仅包含 nginx + dist 静态文件
   - Python 镜像使用 `--no-cache-dir` 清理 pip 缓存，减小镜像体积

## 开发者应遵循的规则

- **新增服务**: 在对应子目录创建 `Dockerfile`，并在 `docker-compose.yml` 中注册服务、端口映射、环境变量与健康检查
- **依赖变更**: Python 依赖修改 `backend/pyproject.toml`，数字人服务修改 `digital_human/requirements.txt`，前端修改各自 `package.json`
- **GPU 功能**: 数字人服务默认不启动，需 `docker compose --profile gpu up` 显式启用
- **本地开发**: 直接 `docker compose up` 即可拉起全栈环境，无需手动安装数据库或 Redis
- **版本锁定**: 前端使用 `package-lock.json`，Python 使用精确版本号（如 `aiosqlite==0.21.0`），确保可重现构建
