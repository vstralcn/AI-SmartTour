# API接口层

<cite>
**本文引用的文件**   
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)
- [backend/app/api/avatar.py](file://backend/app/api/avatar.py)
- [backend/app/models/schemas.py](file://backend/app/models/schemas.py)
- [backend/app/services/llm.py](file://backend/app/services/llm.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/db/session.py](file://backend/app/db/session.py)
- [backend/app/config.py](file://backend/app/config.py)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构总览](#架构总览)
5. [详细组件分析](#详细组件分析)
6. [依赖分析](#依赖分析)
7. [性能考虑](#性能考虑)
8. [故障排查指南](#故障排查指南)
9. [结论](#结论)
10. [附录](#附录)

## 简介
本文件聚焦SmartTour后端API接口层，基于FastAPI构建RESTful服务。文档覆盖路由组织、请求参数验证、响应格式标准化与错误处理机制；并对各业务模块（聊天对话、知识库管理、推荐系统、数据分析、头像配置）的职责划分进行说明。同时给出中间件使用、CORS配置、速率限制与安全防护建议，以及API版本管理与向后兼容策略，为前端集成提供清晰指引与最佳实践。

## 项目结构
后端采用按“功能域”划分的模块化组织方式：
- 应用入口与全局配置：main.py、config.py
- API路由层：api/ 下按领域拆分 chat.py、knowledge.py、recommend.py、analytics.py、avatar.py
- 数据模型与Schema：models/schemas.py
- 服务层：services/ 封装LLM、持久化等外部能力
- 核心逻辑：core/ 包含RAG、对话管理等
- 数据库会话：db/session.py

```mermaid
graph TB
A["应用入口<br/>main.py"] --> B["全局配置<br/>config.py"]
A --> C["聊天API<br/>api/chat.py"]
A --> D["知识库API<br/>api/knowledge.py"]
A --> E["推荐API<br/>api/recommend.py"]
A --> F["数据分析API<br/>api/analytics.py"]
A --> G["头像配置API<br/>api/avatar.py"]
C --> H["服务: LLM<br/>services/llm.py"]
C --> I["服务: 持久化<br/>services/persistence.py"]
D --> J["核心: RAG<br/>core/rag.py"]
D --> I
E --> H
F --> I
G --> I
I --> K["数据库会话<br/>db/session.py"]
```

图表来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/config.py](file://backend/app/config.py)
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)
- [backend/app/api/avatar.py](file://backend/app/api/avatar.py)
- [backend/app/services/llm.py](file://backend/app/services/llm.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/db/session.py](file://backend/app/db/session.py)

章节来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/config.py](file://backend/app/config.py)

## 核心组件
- 应用入口与挂载
  - 创建FastAPI实例并注册各子路由，统一前缀与版本控制
  - 挂载全局中间件（CORS、请求日志、异常转换等）
  - 定义根路径与健康检查端点
- 全局配置
  - 读取环境变量，集中管理跨域白名单、密钥、限流阈值、数据库连接等
- 数据模型与校验
  - 使用Pydantic Schema对请求体与响应体进行强类型校验与序列化
- 服务层
  - LLM调用封装、持久化存储封装，屏蔽外部依赖细节
- 核心逻辑
  - RAG检索增强生成流程编排
- 数据库会话
  - 提供统一的DB会话生命周期管理

章节来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/config.py](file://backend/app/config.py)
- [backend/app/models/schemas.py](file://backend/app/models/schemas.py)
- [backend/app/services/llm.py](file://backend/app/services/llm.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/db/session.py](file://backend/app/db/session.py)

## 架构总览
整体遵循分层架构：API路由层负责协议与校验，服务层封装业务与外部依赖，核心层实现领域算法，数据访问层通过会话对象与数据库交互。

```mermaid
sequenceDiagram
participant FE as "前端"
participant API as "FastAPI应用"
participant Router as "路由处理器"
participant Service as "服务层"
participant Core as "核心逻辑(RAG/对话)"
participant DB as "数据库会话"
FE->>API : HTTP请求(带鉴权头)
API->>Router : 匹配路由/校验参数
Router->>Service : 调用业务方法
Service->>Core : 执行领域逻辑
Core->>DB : 读写数据
DB-->>Core : 返回结果
Core-->>Service : 结构化结果
Service-->>Router : 标准化响应
Router-->>FE : JSON响应(含状态码)
```

图表来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)
- [backend/app/api/avatar.py](file://backend/app/api/avatar.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/db/session.py](file://backend/app/db/session.py)

## 详细组件分析

### 聊天对话API（Chat）
职责
- 提供实时流式对话，通过WebSocket推送多轮交互
- 会话管理（创建、状态维护）
- 智能体能力查询与路径推荐

主要接口
- WebSocket /api/v1/chat/stream
  - 查询参数：session_id（会话标识）
  - 消息格式（JSON）：`{"content": "...", "type": "text"}`
  - 流式事件：`emotion`（情绪状态）、`agent_step`（智能体步骤）、`sources`（引用来源）、`text_chunk`（文本片段）、`error`（错误信息）
  - 无需认证
- GET /api/v1/agent/capabilities
  - 返回：可用工具列表（智能体能力描述）
  - 无需认证
- POST /api/v1/sessions
  - 请求体：`{visitor_id?, interests?, age_group?, companions?, mobility?, visit_duration?}`
  - 响应：`{session_id, greeting}`
  - 无需认证

流程图（消息发送与生成）
```mermaid
flowchart TD
Start(["进入聊天接口"]) --> Validate["校验请求参数与会话存在性"]
Validate --> Valid{"参数有效?"}
Valid -- "否" --> Err400["返回400参数错误"]
Valid -- "是" --> Persist["持久化用户消息"]
Persist --> CallLLM["调用LLM服务生成回复"]
CallLLM --> SaveReply["保存回复到会话"]
SaveReply --> Return200["返回200响应"]
Err400 --> End(["结束"])
Return200 --> End
```

图表来源
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/services/llm.py](file://backend/app/services/llm.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/models/schemas.py](file://backend/app/models/schemas.py)

章节来源
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/services/llm.py](file://backend/app/services/llm.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/models/schemas.py](file://backend/app/models/schemas.py)

### 知识库管理API（Knowledge）
职责
- 知识文档的增删改查管理
- 文档上传、解析与检索测试

主要接口
- GET /admin/knowledge/list
  - 返回：知识文档列表
  - 无需认证
- POST /admin/knowledge/entries
  - 请求体：`{title, category, content, kind, source?, keywords?, tags?}`
  - 响应：创建确认
  - 无需认证
- PUT /admin/knowledge/{doc_id}
  - 请求体：`{title?, category?, content?, kind?, source?, keywords?, tags?}`
  - 响应：更新确认
  - 无需认证
- POST /admin/knowledge/upload
  - 请求体：multipart/form-data（file + category）
  - 响应：上传确认
  - 无需认证
- DELETE /admin/knowledge/{doc_id}
  - 响应：删除确认
  - 无需认证
- POST /admin/knowledge/test
  - 请求体：`{question}`
  - 响应：`{answer, evidence[]}`（答案与引用来源）
  - 无需认证

RAG检索流程
```mermaid
flowchart TD
QStart(["接收查询"]) --> Parse["解析问题与参数"]
Parse --> Index["检索向量/倒排索引"]
Index --> Rank["排序与去重"]
Rank --> Context["组装上下文"]
Context --> LLM["调用LLM生成回答"]
LLM --> Format["格式化响应(含引用)"]
Format --> QEnd(["返回结果"])
```

图表来源
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/models/schemas.py](file://backend/app/models/schemas.py)

章节来源
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/models/schemas.py](file://backend/app/models/schemas.py)

### 推荐系统API（Recommend）
职责
- 基于用户画像、兴趣与上下文生成个性化游览路线推荐

主要接口
- POST /api/v1/recommend/route
  - 请求体：`{session_id, duration_hours, interests, companions, mobility}`
  - 响应：`{route: ScenicSpot[], description}`
  - 无需认证

章节来源
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/services/llm.py](file://backend/app/services/llm.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/models/schemas.py](file://backend/app/models/schemas.py)

### 数据分析API（Analytics）
职责
- 聚合统计数据、趋势分析与运行指标监控

主要接口
- GET /admin/analytics/dashboard
  - 返回：DashboardData（聚合指标总览）
  - 无需认证
- GET /admin/analytics/sentiment
  - 返回：SentimentReport（情感分析报告）
  - 无需认证

章节来源
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/models/schemas.py](file://backend/app/models/schemas.py)

### 数字人形象API（Avatar）
职责
- 数字人（Digital Human）形象的增删改查管理
- 提供前端实时数字人驱动的配置与签名接口

主要接口（管理端）
- GET /admin/avatar/list
  - 返回：所有数字人形象列表
  - 无需认证
- POST /admin/avatar/config
  - 请求体：`{id?, name, appearance:{image_url, style}, voice_config:{voice_id, speed, pitch}, personality, gender, clothing, speaking_style}`
  - 响应：保存确认
  - 无需认证
- PUT /admin/avatar/{avatar_id}/activate
  - 响应：激活确认
  - 无需认证
- DELETE /admin/avatar/{avatar_id}
  - 响应：删除确认
  - 无需认证

主要接口（公开）
- GET /api/v1/avatar/active
  - 返回：当前激活的数字人形象配置
  - 无需认证
- GET /api/v1/avatar/xunfei/signed-url
  - 返回：`{enabled, appId, sceneId, avatarId, vcn, signedUrl}`
  - 说明：获取讯飞（Xunfei）签名WebSocket URL，用于前端实时驱动数字人播报，是数字人功能的关键依赖
  - 无需认证

章节来源
- [backend/app/api/avatar.py](file://backend/app/api/avatar.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/models/schemas.py](file://backend/app/models/schemas.py)

## 依赖分析
API层与服务层、核心层、数据层的依赖关系如下：

```mermaid
graph LR
Chat["chat.py"] --> SvcLLM["services/llm.py"]
Chat --> SvcPersist["services/persistence.py"]
Knowledge["knowledge.py"] --> CoreRAG["core/rag.py"]
Knowledge --> SvcPersist
Recommend["recommend.py"] --> SvcLLM
Recommend --> SvcPersist
Analytics["analytics.py"] --> SvcPersist
Avatar["avatar.py"] --> SvcPersist
SvcPersist --> DBSession["db/session.py"]
```

图表来源
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)
- [backend/app/api/avatar.py](file://backend/app/api/avatar.py)
- [backend/app/services/llm.py](file://backend/app/services/llm.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/db/session.py](file://backend/app/db/session.py)

章节来源
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)
- [backend/app/api/avatar.py](file://backend/app/api/avatar.py)
- [backend/app/services/llm.py](file://backend/app/services/llm.py)
- [backend/app/services/persistence.py](file://backend/app/services/persistence.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/db/session.py](file://backend/app/db/session.py)

## 性能考虑
- 异步I/O：优先使用异步路由与服务调用，减少阻塞
- 批量操作：对知识库导入与分析聚合提供批量接口，降低往返开销
- 缓存策略：热点问答与推荐结果可引入短期缓存（需结合一致性要求）
- 分页与过滤：所有列表接口默认分页，避免大结果集传输
- 资源限制：对上传文件大小、并发请求数进行限制，防止资源耗尽
- 数据库优化：合理索引与查询计划，避免N+1查询

[本节为通用指导，不直接分析具体文件]

## 故障排查指南
- 常见状态码
  - 400：请求参数校验失败，检查Schema约束与必填字段
  - 401：未携带或无效鉴权头，确认令牌签发与传递
  - 403：权限不足，检查角色与资源访问策略
  - 404：资源不存在，核对ID与路径
  - 413：上传文件过大，调整服务端限制或客户端压缩
  - 429：触发速率限制，实施退避重试
  - 500：内部异常，查看服务日志与堆栈
- 日志与追踪
  - 在中间件中记录请求ID、耗时与关键步骤
  - 将异常转换为标准错误响应体，便于前端统一处理
- 健康检查
  - 提供健康检查端点用于探针与自恢复

章节来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/models/schemas.py](file://backend/app/models/schemas.py)

## 结论
本接口层以FastAPI为核心，围绕聊天、知识库、推荐、分析与头像五大模块构建了清晰的RESTful边界。通过统一的Schema校验、标准化的响应结构与完善的错误处理，提升了前后端协作效率与系统稳定性。建议在后续迭代中持续完善鉴权、限流与监控能力，确保可扩展性与安全性。

[本节为总结性内容，不直接分析具体文件]

## 附录

### 设计原则与规范
- REST风格
  - 资源名词化、HTTP语义明确、幂等性遵循
- 版本管理
  - URL前缀包含版本号（如/api/v1），重大变更升级至v2，保持向后兼容
- 请求/响应
  - 统一JSON结构，包含code、message、data字段
  - 使用Pydantic Schema进行强类型校验与序列化
- 安全与合规
  - 输入校验严格、输出脱敏
  - 上传文件类型与大小限制、防注入与XSS防护

> **注意：** 当前版本**未实现认证层**，所有API端点均为公开访问（CORS `allow_origins=["*"]`），无Bearer Token校验、无RBAC角色控制。此状态为已知限制，生产部署前需补充完整鉴权与授权机制。

### 中间件与全局配置
- CORS
  - `allow_origins=["*"]`（开放所有来源）
- 速率限制
  - 暂未实现
- 认证中间件
  - 暂未实现
- 请求日志
  - 记录请求ID、方法、路径、耗时、状态码
- 异常转换
  - 将业务异常与系统异常映射为标准错误响应
- 健康检查
  - `/health` 端点用于探针与自恢复

章节来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/config.py](file://backend/app/config.py)

### 前端集成指南与最佳实践
- 基础设置
  - 统一BaseURL包含版本前缀
  - 自动附加鉴权头（Authorization: Bearer <token>）
- 错误处理
  - 根据状态码分支处理，提示用户友好信息
  - 对429实施指数退避重试
- 文件上传
  - 使用multipart/form-data，限制最大体积与类型
  - 显示上传进度与失败重试
- 分页与搜索
  - 默认加载第一页，提供加载更多与搜索过滤
- 缓存与离线
  - 对静态资源与只读数据进行本地缓存
  - 网络不可用时降级展示

[本节为通用指导，不直接分析具体文件]