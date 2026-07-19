---
kind: logging_system
name: Python 标准库 logging 分散式日志输出
category: logging_system
scope:
    - '**'
source_files:
    - backend/app/api/chat.py
    - backend/app/api/digital_human_broadcast.py
    - backend/app/api/knowledge.py
    - digital_human/server.py
    - backend/app/main.py
---

本仓库未引入第三方日志框架（如 loguru、structlog），全部使用 Python 标准库 `logging`，且各模块自行创建 logger 实例，未在应用启动处集中配置。

## 1. 使用的系统与工具
- 后端服务 (`backend/app`)：`import logging` + `logging.getLogger(__name__)` 或自定义名称（如 `"broadcast"`）。
- 数字人推理服务 (`digital_human/server.py`)：`logging.getLogger("digital-human")`。
- 未使用任何结构化日志库、日志级别环境变量、文件/流处理器集中注册。

## 2. 关键文件与位置
- `backend/app/api/chat.py` — 对话路由，`logger = logging.getLogger(__name__)`，在持久化异常时调用 `logger.exception(...)`。
- `backend/app/api/digital_human_broadcast.py` — 播报代理路由，`logger = logging.getLogger("broadcast")`，记录降级、轮询失败等 warning。
- `backend/app/api/knowledge.py` — 知识库路由，`logger = logging.getLogger(__name__)`，记录文件删除警告。
- `digital_human/server.py` — 独立 FastAPI 服务，`logger = logging.getLogger("digital-human")`，记录引擎选择、生成完成/失败等信息。
- `backend/app/main.py` — 应用入口，**未进行任何 logging 初始化**（无 `basicConfig`、无 Handler、无 level 设置）。

## 3. 架构与约定
- **每个模块自管 logger**：通过 `logging.getLogger(__name__)` 获取按模块名命名的 logger，或使用固定字符串命名（如 `"broadcast"`、`"digital-human"`）。
- **仅 stdout 输出**：未发现任何 `StreamHandler` / `FileHandler` / `RotatingFileHandler` 的注册，日志默认输出到进程标准输出，由容器运行时（Docker）收集。
- **无全局级别控制**：没有 `LOG_LEVEL` 环境变量、没有在 `main.py` 中统一 `setLevel`，日志级别依赖调用方传入的 level 和 Python 默认 WARNING。
- **无结构化字段**：所有日志均为纯文本格式化字符串，未使用 JSON 序列化或统一字段（如 `service_name`、`trace_id`、`request_id`）。
- **跨服务命名不一致**：主后端用 `__name__` 派生 logger 名，广播路由用 `"broadcast"`，数字人服务用 `"digital-human"`，缺乏统一的 logger 前缀规范。

## 4. 开发者应遵循的规则
- 如需新增日志，请沿用 `logger = logging.getLogger(__name__)` 模式，并通过 `logger.info/warning/error/exception` 输出。
- 当前仓库未提供集中配置，若需调整日志级别或添加文件输出，应在 `backend/app/main.py` 的 `lifespan` 中统一执行 `logging.basicConfig(...)`。
- 建议后续引入结构化日志（如 `python-json-logger` 或 `loguru`），并增加 `request_id`、`service` 等公共字段以便链路追踪。