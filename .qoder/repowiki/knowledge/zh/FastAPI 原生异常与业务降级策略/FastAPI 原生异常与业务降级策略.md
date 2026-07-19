---
kind: error_handling
name: FastAPI 原生异常与业务降级策略
category: error_handling
scope:
    - '**'
source_files:
    - backend/app/main.py
    - backend/app/api/chat.py
    - backend/app/api/digital_human_broadcast.py
    - backend/app/api/avatar.py
    - backend/app/services/persistence.py
    - backend/app/services/llm.py
---

本仓库未建立统一的错误类型体系或全局异常处理器，而是采用 FastAPI 原生的 HTTPException 在 API 层直接抛出 HTTP 状态码，并在 WebSocket、异步任务等场景中使用 try/except + 日志记录的方式处理异常。整体风格偏就地处理，没有集中式 error code 枚举或中间件统一包装。

1. REST 接口：在各路由模块中直接 raise HTTPException(status_code, detail)，如 avatar 路由的 404/409、digital_human_broadcast 路由的 404/422/425 等，detail 使用中文描述。
2. WebSocket 流：chat.py 的 /chat/stream 用 try/except Exception 捕获，通过发送 {type: error, content: str(e), done: True} 消息返回给前端；对持久化写入失败单独 try/except 并 logger.exception，不中断主流程。
3. 外部依赖降级：digital_human_broadcast.py 在调用下游 digital-human 服务时捕获 httpx.RequestError，自动回退到本地 ffmpeg 模拟生成；若 ffmpeg 也不可用则标记 job 为 failed，前端再进一步降级为 TTS 播报。
4. 数据库层：persistence.py 中的 database_is_ready() 用 try/except Exception 返回布尔值，供 health 端点判断；其余 DB 操作均通过 session_scope() 上下文管理器隐式管理会话生命周期，未显式捕获异常。
5. LLM/ASR/TTS 等服务封装（如 services/llm.py）未做异常包装，OpenAI SDK 抛出的异常会向上传播至调用方。
6. 无全局异常中间件、无自定义 Error 类、无 panic/recover 模式（Python 本身无 panic），也未定义统一的错误码表。

开发者约定建议：
- 新增 API 的错误分支应沿用 raise HTTPException(status_code, detail=...) 风格，detail 保持简洁可读。
- 对外部不可靠依赖（下游服务、ffmpeg、LLM）的调用需包裹 try/except，优先走降级路径而非直接向上抛错。
- WebSocket 场景下任何异常都应确保能发送一条 {type: error, ...} 消息后再关闭连接。
- 如需引入统一错误码或全局异常处理器，可在 main.py 中注册 @app.exception_handler 或在 app/core 下新建 errors.py 集中定义。