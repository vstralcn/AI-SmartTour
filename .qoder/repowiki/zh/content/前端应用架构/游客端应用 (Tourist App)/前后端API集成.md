# 前后端API集成

<cite>
**本文引用的文件**   
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/config.py](file://backend/app/config.py)
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/avatar.py](file://backend/app/api/avatar.py)
- [backend/app/api/digital_human_broadcast.py](file://backend/app/api/digital_human_broadcast.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/services/digital_human.py](file://backend/app/services/digital_human.py)
- [frontend/tourist-app/src/services/api.ts](file://frontend/tourist-app/src/services/api.ts)
- [frontend/admin-panel/src/services/api.ts](file://frontend/admin-panel/src/services/api.ts)
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
本文件面向前后端开发者，系统化梳理智能旅游项目的API集成方案。内容覆盖后端服务层架构、HTTP客户端配置、版本化接口设计、Mock数据支持与调试工具，并提供聊天对话、数字人控制、知识库查询、路线推荐、数据分析等关键接口的调用示例。

## 项目结构
本项目采用前后端分离的模块化架构：
- 后端（FastAPI）：按功能域划分API路由与服务层，核心能力包括对话、RAG检索增强生成、数字人控制、知识检索、推荐与分析。
- 前端（Vue + Vite）：游客端与管理后台分别封装HTTP客户端，提供统一的API调用入口。

```mermaid
graph TB
subgraph "前端"
TA["游客端<br/>tourist-app"]
AP["管理后台<br/>admin-panel"]
end
subgraph "后端"
API["API路由层<br/>chat/avatar/knowledge/recommend/analytics"]
Core["核心逻辑<br/>dialogue/rag/recommend/sentiment"]
Svc["外部服务适配<br/>digital_human/asr/tts/persistence"]
DB["数据库模型与会话"]
end
TA --> API
AP --> API
API --> Core
API --> Svc
Core --> DB
Svc --> DB
```

图表来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)
- [backend/app/api/avatar.py](file://backend/app/api/avatar.py)
- [backend/app/api/digital_human_broadcast.py](file://backend/app/api/digital_human_broadcast.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/services/digital_human.py](file://backend/app/services/digital_human.py)

章节来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/config.py](file://backend/app/config.py)

## 核心组件
- HTTP客户端封装（前端）
  - 统一实例初始化、基础URL、默认超时配置
- 后端API路由层
  - 路由组织：按领域拆分模块，集中注册到应用入口
  - 参数校验与返回模型：使用Pydantic进行输入输出约束
  - 中间件：CORS、请求日志、异常捕获与标准化错误响应
- 服务层与核心逻辑
  - RAG检索增强生成、对话状态管理、推荐算法、情感分析
  - 外部服务适配：数字人控制、ASR/TTS、持久化存储
- 配置与环境
  - 环境变量加载、跨域与安全开关、第三方服务密钥与端点

章节来源
- [frontend/tourist-app/src/services/api.ts](file://frontend/tourist-app/src/services/api.ts)
- [frontend/admin-panel/src/services/api.ts](file://frontend/admin-panel/src/services/api.ts)
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/config.py](file://backend/app/config.py)

## 架构总览
前后端通过RESTful API交互，前端在浏览器或Node环境中发起HTTP请求，后端由FastAPI提供服务，内部再调用核心逻辑与外部服务。

```mermaid
sequenceDiagram
participant FE as "前端HTTP客户端"
participant API as "后端API路由"
participant CORE as "核心逻辑(RAG/对话/推荐)"
participant SVC as "外部服务(数字人/ASR/TTS)"
participant DB as "数据库"
FE->>API : "POST /api/v1/chat/stream (WebSocket)"
API->>CORE : "创建对话上下文并生成回复"
CORE->>DB : "读取历史/检索知识库"
DB-->>CORE : "返回相关片段"
CORE->>SVC : "可选：TTS/数字人生成"
SVC-->>CORE : "返回媒体或控制结果"
CORE-->>API : "结构化响应"
API-->>FE : "JSON响应"
```

图表来源
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/services/digital_human.py](file://backend/app/services/digital_human.py)

## 详细组件分析

### 前端HTTP客户端封装（游客端）
职责
- 初始化 Axios 实例，设置基础 URL 与超时
- 封装各业务域方法：聊天、数字人、知识库、推荐、分析等
- 当前版本无请求/响应拦截器，无自动重试，无统一错误映射

```mermaid
flowchart TD
Start(["发起请求"]) --> Send["发送HTTP请求"]
Send --> Resp{"是否成功?"}
Resp --> |是| Return["返回业务数据"]
Resp --> |否| Throw["抛出 axios 错误"]
Return --> End(["结束"])
Throw --> End
```

章节来源
- [frontend/tourist-app/src/services/api.ts](file://frontend/tourist-app/src/services/api.ts)

### 前端HTTP客户端封装（管理后台）
差异点
- 可能启用不同的基础URL与超时策略
- 针对批量操作与文件上传做特殊处理

章节来源
- [frontend/admin-panel/src/services/api.ts](file://frontend/admin-panel/src/services/api.ts)

### 后端API路由层
- 路由组织
  - 聊天对话：消息发送、流式响应、会话管理
  - 数字人控制：动作指令、状态查询、媒体资源
  - 知识库：文档索引、检索、更新
  - 推荐：基于用户画像与上下文的推荐列表
  - 分析：指标统计、趋势、事件聚合
- 中间件
  - CORS、请求日志、全局异常捕获
- 版本管理
  - 路径前缀 /api/v1，便于后续演进与兼容

章节来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/avatar.py](file://backend/app/api/avatar.py)
- [backend/app/api/digital_human_broadcast.py](file://backend/app/api/digital_human_broadcast.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)

### 核心逻辑与服务层
- RAG检索增强生成
  - 将用户问题转换为向量，检索知识库片段，结合上下文生成回答
- 对话管理
  - 维护会话状态、历史摘要、意图识别
- 推荐服务
  - 基于用户行为与偏好生成个性化推荐
- 外部服务适配
  - 数字人控制：播放、暂停、表情切换、语音合成
  - ASR/TTS：语音转文本、文本转语音
  - 持久化：会话、日志、指标落库

```mermaid
classDiagram
class ChatAPI {
+发送消息()
+获取会话()
+关闭会话()
}
class KnowledgeAPI {
+检索()
+索引文档()
+更新元数据()
}
class RecommendAPI {
+个性化推荐()
+热门推荐()
}
class AnalyticsAPI {
+指标统计()
+事件聚合()
}
class DigitalHumanAPI {
+控制动作()
+查询状态()
}
class RAGCore {
+检索片段()
+生成回答()
}
class DigitalHumanSvc {
+下发指令()
+获取媒体()
}
ChatAPI --> RAGCore : "调用"
KnowledgeAPI --> RAGCore : "索引/检索"
RecommendAPI --> RAGCore : "辅助推荐"
DigitalHumanAPI --> DigitalHumanSvc : "控制"
```

图表来源
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)
- [backend/app/api/digital_human_broadcast.py](file://backend/app/api/digital_human_broadcast.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/services/digital_human.py](file://backend/app/services/digital_human.py)

章节来源
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/services/digital_human.py](file://backend/app/services/digital_human.py)

### 认证与安全说明（当前版本）
当前版本**未实现**认证授权机制，具体表现为：
- 所有 API 端点公开可访问，无 JWT/Token 验证
- CORS 设置为 `allow_origins=["*"]`，允许所有来源
- 前端 api.ts 为纯 HTTP 客户端，无拦截器或鉴权头注入

> ⚠️ 生产部署注意事项：建议在部署前补充认证中间件、CORS 白名单和速率限制。

### 请求重试与超时处理策略
当前前端 api.ts 中 Axios 实例的配置非常简单：
```typescript
const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 30000,
})
```
- **无请求/响应拦截器**：未注册任何拦截器逻辑
- **无自动重试机制**：未配置重试次数或退避策略
- **无自定义错误映射**：错误处理依赖调用方自行捕获

章节来源
- [frontend/tourist-app/src/services/api.ts](file://frontend/tourist-app/src/services/api.ts)
- [frontend/admin-panel/src/services/api.ts](file://frontend/admin-panel/src/services/api.ts)

### 统一错误处理
当前版本**未实现**统一的错误处理模型：
- 无标准错误响应体结构（无统一 code / message / trace_id 字段约定）
- 前端无拦截器进行错误码映射，由各调用方自行处理 axios 异常
- 错误处理方式为标准 axios 错误捕获（`try/catch`），无额外封装

章节来源
- [frontend/tourist-app/src/services/api.ts](file://frontend/tourist-app/src/services/api.ts)

### API版本管理
- 路径前缀
  - 所有接口以/api/v1开头，便于后续升级至v2
- 兼容性策略
  - 新增字段保持向后兼容
  - 废弃字段保留一段时间并给出迁移指引

章节来源
- [backend/app/main.py](file://backend/app/main.py)

### Mock数据支持与调试工具
- 开发环境
  - 前端可通过代理或本地Mock Server模拟后端响应
  - 使用浏览器开发者工具查看请求/响应与网络耗时
- 联调建议
  - 开启详细日志与采样率可控的埋点

章节来源
- [frontend/tourist-app/src/services/api.ts](file://frontend/tourist-app/src/services/api.ts)
- [frontend/admin-panel/src/services/api.ts](file://frontend/admin-panel/src/services/api.ts)

### 性能监控
- 前端埋点
  - 首包时间、TTI、错误率
- 后端指标
  - QPS、P95/P99延迟、错误率、缓存命中率

章节来源
- [backend/app/main.py](file://backend/app/main.py)
- [frontend/tourist-app/src/services/api.ts](file://frontend/tourist-app/src/services/api.ts)

## 依赖分析
前后端通过HTTP协议耦合，关键依赖关系如下：

```mermaid
graph LR
FE_TOURIST["游客端HTTP客户端"] --> API_CHAT["聊天API"]
FE_ADMIN["管理后台HTTP客户端"] --> API_KNOWLEDGE["知识库API"]
FE_ADMIN --> API_ANALYTICS["分析API"]
API_CHAT --> CORE_RAG["RAG核心"]
API_KNOWLEDGE --> CORE_RAG
API_RECOMMEND["推荐API"] --> CORE_RAG
API_DIGITAL["数字人API"] --> SVC_DH["数字人服务"]
```

图表来源
- [frontend/tourist-app/src/services/api.ts](file://frontend/tourist-app/src/services/api.ts)
- [frontend/admin-panel/src/services/api.ts](file://frontend/admin-panel/src/services/api.ts)
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)
- [backend/app/api/digital_human_broadcast.py](file://backend/app/api/digital_human_broadcast.py)
- [backend/app/core/rag.py](file://backend/app/core/rag.py)
- [backend/app/services/digital_human.py](file://backend/app/services/digital_human.py)

章节来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/config.py](file://backend/app/config.py)

## 性能考虑
- 前端
  - 合理设置超时，避免阻塞主线程
  - 对大列表分页加载，减少单次负载
- 后端
  - 缓存热点数据，降低数据库压力
  - 异步处理耗时任务，缩短响应时间
  - 流式返回长任务进度，提升用户体验

## 故障排查指南
- 常见问题
  - 连接失败：检查后端服务是否启动、端口是否正确
  - CORS错误：确认后端 CORS 配置是否允许前端来源
  - 5xx错误：查看后端日志定位异常堆栈
- 排查步骤
  - 前端：打开浏览器网络面板，检查请求URL与响应状态码
  - 后端：查看应用日志，定位异常堆栈
  - 配置：核对环境变量与第三方服务密钥是否正确

章节来源
- [backend/app/main.py](file://backend/app/main.py)
- [frontend/tourist-app/src/services/api.ts](file://frontend/tourist-app/src/services/api.ts)

## 结论
通过统一的前端HTTP客户端与后端API路由层，配合RAG核心与外部服务适配，本项目实现了高内聚、低耦合的API集成体系。API版本化前缀（`/api/v1`）为后续演进提供了基础。建议在上线前补充认证中间件、统一错误处理、监控与告警，持续优化性能与可靠性。

## 附录

### 典型API调用示例（路径参考）
- 聊天对话
  - 创建会话：POST /api/v1/sessions
  - WebSocket 流式对话：ws://host/api/v1/chat/stream?session_id={id}
  - Agent 能力查询：GET /api/v1/agent/capabilities
- 数字人形象管理（管理端）
  - 列表：GET /admin/avatar/list
  - 保存配置：POST /admin/avatar/config
  - 激活：PUT /admin/avatar/{id}/activate
  - 删除：DELETE /admin/avatar/{id}
- 数字人公开查询
  - 当前激活形象：GET /api/v1/avatar/active
  - 讯飞接入参数（含签名URL）：GET /api/v1/avatar/xunfei/signed-url
- 数字人高清播报
  - 提交任务：POST /api/v1/digital-human/broadcast
  - 查询状态：GET /api/v1/digital-human/broadcast/{job_id}
  - 下载视频：GET /api/v1/digital-human/broadcast/{job_id}/video
- 知识库管理（管理端）
  - 列表：GET /admin/knowledge/list
  - 创建条目：POST /admin/knowledge/entries
  - 上传文档：POST /admin/knowledge/upload
  - 更新条目：PUT /admin/knowledge/{doc_id}
  - 删除条目：DELETE /admin/knowledge/{doc_id}
  - 检索测试：POST /admin/knowledge/test
- 路线推荐
  - 生成路线：POST /api/v1/recommend/route
- 数据分析（管理端）
  - 仪表盘：GET /admin/analytics/dashboard
  - 情感报告：GET /admin/analytics/sentiment
- 语音合成
  - TTS：POST /api/v1/tts

章节来源
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/api/chat.py](file://backend/app/api/chat.py)
- [backend/app/api/avatar.py](file://backend/app/api/avatar.py)
- [backend/app/api/digital_human_broadcast.py](file://backend/app/api/digital_human_broadcast.py)
- [backend/app/api/knowledge.py](file://backend/app/api/knowledge.py)
- [backend/app/api/recommend.py](file://backend/app/api/recommend.py)
- [backend/app/api/analytics.py](file://backend/app/api/analytics.py)