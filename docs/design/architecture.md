# 景区导览服务AI数字人 — 系统架构设计文档

## 一、赛题分析

### 1.1 赛题核心目标

开发一个具备**多模态交互能力**（语音、文本、表情）的AI数字人导游软件，核心能力包括：

| 维度 | 关键需求 |
|------|----------|
| 游客交互 | 语音/文本输入 → 数字人口型+表情+语音同步输出 |
| 智能问答 | 基于景区知识库的精准问答（准确率≥90%） |
| 个性化推荐 | 根据兴趣推荐路线和讲解重点 |
| 管理后台 | 知识库管理、形象配置、情感分析报告、数据大屏 |

### 1.2 评分权重分析

```
功能完整度（40%）→ 核心：确保每个功能模块稳定可用
技术创新性（30%）→ 重点：数字人表现力 + 大模型+RAG 准确性
行业实用性（20%）→ 关键：交互自然度 + 用户体验
文档质量（10%）→ 基础：设计文档 + 演示视频
```

### 1.3 技术约束

- 必须使用至少1个多模态大模型
- 必须构建本地景区知识库
- 事实性问答准确率 ≥ 90%
- 语音问答延迟 < 5秒
- 系统无崩溃或长时间无响应

---

## 二、系统总体架构

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                          前端层 (Frontend)                            │
│  ┌─────────────────────┐         ┌──────────────────────────────┐   │
│  │  游客交互端 (Vue 3)   │         │   管理后台 (Vue 3 + ECharts)   │   │
│  │  - 数字人渲染引擎      │         │   - 知识库管理                  │   │
│  │  - 语音录入组件       │         │   - 数字人形象配置              │   │
│  │  - 对话交互界面       │         │   - 数据大屏 & 报告            │   │
│  └────────┬────────────┘         └──────────────┬───────────────┘   │
└───────────┼──────────────────────────────────────┼──────────────────┘
            │ WebSocket / REST API                  │ REST API
┌───────────┼──────────────────────────────────────┼──────────────────┐
│           ▼          后端层 (Backend - FastAPI)    ▼                  │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    API Gateway / Router                          ││
│  └─────────────────────────────────────────────────────────────────┘│
│       │              │              │              │                  │
│       ▼              ▼              ▼              ▼                  │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐        │
│  │ 对话引擎  │  │ 数字人服务 │  │ 知识库服务 │  │  管理 & 分析  │        │
│  │ (LLM)   │  │ (TTS+驱动)│  │  (RAG)   │  │   服务        │        │
│  └────┬────┘  └─────┬────┘  └─────┬────┘  └──────┬───────┘        │
│       │              │              │              │                  │
└───────┼──────────────┼──────────────┼──────────────┼────────────────┘
        │              │              │              │
┌───────┼──────────────┼──────────────┼──────────────┼────────────────┐
│       ▼              ▼              ▼              ▼   数据层          │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐        │
│  │ LLM API │  │ TTS模型   │  │ 向量数据库 │  │  关系型数据库   │        │
│  │(Qwen2.5)│  │(CosyVoice)│  │ (Milvus) │  │ (PostgreSQL) │        │
│  └─────────┘  └──────────┘  └──────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术选型

| 层级 | 技术方案 | 选型理由 |
|------|----------|----------|
| **前端框架** | Vue 3 + Vite + TypeScript | 生态成熟，组件化开发效率高 |
| **数字人渲染** | MuseTalk / SadTalker (2D) | 开源方案，口型驱动效果好，资源消耗低 |
| **后端框架** | Python FastAPI | 异步高性能，适合AI推理服务 |
| **大语言模型** | Qwen2.5-72B (API) / Qwen2.5-7B (本地) | 国产开源，中文理解能力强 |
| **语音识别** | Paraformer (FunASR) | 阿里开源，中文识别准确率高 |
| **语音合成** | CosyVoice / GPT-SoVITS | 支持情感语音，音色自然 |
| **向量数据库** | Milvus Lite / ChromaDB | 轻量级向量检索，RAG核心组件 |
| **关系数据库** | PostgreSQL | 可靠的结构化数据存储 |
| **数据可视化** | ECharts | 数据大屏展示，效果丰富 |
| **实时通信** | WebSocket | 流式响应，降低感知延迟 |

---

## 三、核心模块详细设计

### 3.1 对话引擎（Dialogue Engine）

```
用户输入 ──→ 意图识别 ──→ 知识检索(RAG) ──→ LLM生成回答 ──→ 输出
   │                                              ▲
   │         ┌─────────────────────────────────────┘
   │         │
   └── 上下文管理器（对话历史 + 用户画像 + 当前位置）
```

**核心流程：**

1. **输入处理**：语音 → ASR转文本 / 直接文本输入
2. **意图分类**：景点问答 / 路线推荐 / 闲聊 / 投诉反馈
3. **知识检索（RAG）**：
   - Query改写 → Embedding → 向量检索 Top-K
   - Rerank精排 → 组装Context
4. **LLM生成**：System Prompt（角色设定 + 景区背景）+ Context + 对话历史 → 流式输出
5. **情感标注**：分析用户情绪，调整回复风格和数字人表情

**Prompt 模板设计：**

```python
SYSTEM_PROMPT = """你是{scenic_name}的AI数字人导游"{avatar_name}"，
性格{personality}，熟悉景区的历史文化和自然景观。

角色要求：
1. 回答基于【参考知识】，不编造信息
2. 语言亲切自然，像真人导游一样交流
3. 适当加入趣味性的讲解（典故、传说等）
4. 根据游客兴趣调整讲解深度和方向

游客画像：{user_profile}
当前位置：{current_location}

【参考知识】
{retrieved_context}
"""
```

### 3.2 数字人驱动引擎

```
文本回答 ──→ TTS语音合成 ──→ 音频特征提取 ──→ 口型驱动 ──→ 视频渲染
                                    │
                              情感标签 ──→ 表情控制
```

**技术方案（二选一）：**

| 方案 | 引擎 | 优势 | 劣势 |
|------|------|------|------|
| A (推荐) | MuseTalk | 实时生成，延迟低，效果自然 | 需要GPU |
| B (备选) | SadTalker | 成熟稳定，文档丰富 | 生成速度稍慢 |

**表情控制策略：**

| 情感标签 | 数字人表情 | 语音特征 |
|----------|-----------|----------|
| 热情欢迎 | 微笑、眼神注视 | 语速适中、语调上扬 |
| 讲解历史 | 沉稳、庄重 | 语速放缓、语调平稳 |
| 趣味互动 | 活泼、俏皮 | 语速稍快、语调跳跃 |
| 安慰关怀 | 温和、关切 | 语速慢、语调柔和 |

### 3.3 RAG 知识库引擎

```
┌────────────────── 知识库构建 ──────────────────┐
│                                                │
│  文档上传 → 文档解析 → 文本分块 → Embedding → 入库  │
│  (PDF/TXT/   (结构化     (Chunk      (BGE-M3)  (Milvus) │
│   DOCX)      提取)       512 tokens)            │
└────────────────────────────────────────────────┘

┌────────────────── 知识检索 ──────────────────┐
│                                              │
│  Query → Query改写 → Embedding → 向量检索     │
│                         ↓                    │
│               BM25关键词检索 (混合检索)         │
│                         ↓                    │
│                Rerank (BGE-Reranker)          │
│                         ↓                    │
│              Top-K Context (≤2000 tokens)     │
└──────────────────────────────────────────────┘
```

**关键设计点：**

- **混合检索**：向量语义检索 + BM25关键词检索，Reciprocal Rank Fusion 融合
- **分块策略**：按段落/章节分块，保留标题层级作为metadata
- **知识分类**：景点介绍 / 历史文化 / 游览路线 / 服务信息 / FAQ
- **准确性保障**：Rerank精排 + Prompt约束"仅基于参考知识回答"

### 3.4 游客个性化推荐

```python
class UserProfile:
    """游客画像模型"""
    interests: List[str]       # ["历史", "自然风光", "美食"]
    visit_duration: float      # 计划游览时长（小时）
    physical_condition: str    # "正常" / "带老人" / "带小孩"
    visited_spots: List[str]   # 已游览景点
    current_location: str      # 当前位置（可选GPS）
```

**推荐策略：**

1. **显式偏好**：通过对话收集用户兴趣标签
2. **隐式推断**：根据提问内容推断兴趣方向
3. **路线生成**：LLM基于用户画像 + 景点图谱生成个性化路线
4. **动态调整**：实时根据对话反馈调整推荐内容

### 3.5 管理后台

#### 3.5.1 知识库管理

```
功能列表：
├── 文档管理
│   ├── 上传文档（PDF/TXT/DOCX/图片OCR）
│   ├── 在线编辑知识条目
│   ├── 文档版本管理
│   └── 知识标签分类
├── FAQ管理
│   ├── 问答对 CRUD
│   └── 批量导入/导出
└── 知识测试
    ├── 在线测试问答效果
    └── 准确率统计
```

#### 3.5.2 数字人形象管理

```
配置项：
├── 形象选择（预置多款 / 自定义上传）
├── 服装配置（汉服、现代、民族特色）
├── 声音选择（男声/女声/方言）
├── 性格设定（热情/稳重/活泼）
└── 背景场景（景区实景/虚拟场景）
```

#### 3.5.3 游客感受度分析

```
分析维度：
├── 情感趋势：正面/中性/负面比例变化
├── 关注热点：高频提问景点和话题
├── 满意度评分：基于对话情感和显式评价
└── 服务建议：基于LLM分析交互记录生成改进建议
```

#### 3.5.4 数据大屏

```
核心指标：
├── 当日/本周/本月服务人次
├── 实时在线用户数
├── 热门问答 Top10
├── 游客满意度趋势
├── 景点热度排行
└── 平均会话时长 & 问答延迟
```

---

## 四、数据模型设计

### 4.1 关系型数据（PostgreSQL）

```sql
-- 游客会话
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    visitor_id VARCHAR(64),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_turns INT,
    avg_response_time FLOAT,
    satisfaction_score FLOAT,
    user_profile JSONB
);

-- 对话记录
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    role VARCHAR(16),  -- 'user' / 'assistant'
    content TEXT,
    emotion VARCHAR(32),
    timestamp TIMESTAMP,
    response_latency_ms INT
);

-- 知识文档
CREATE TABLE knowledge_docs (
    id UUID PRIMARY KEY,
    title VARCHAR(256),
    category VARCHAR(64),
    content TEXT,
    file_path VARCHAR(512),
    upload_time TIMESTAMP,
    updated_at TIMESTAMP,
    status VARCHAR(16)  -- 'active' / 'archived'
);

-- 数字人配置
CREATE TABLE avatar_configs (
    id UUID PRIMARY KEY,
    name VARCHAR(64),
    appearance JSONB,   -- 形象配置
    voice_config JSONB, -- 声音配置
    personality TEXT,    -- 性格设定
    is_active BOOLEAN DEFAULT FALSE
);

-- 景点信息
CREATE TABLE scenic_spots (
    id UUID PRIMARY KEY,
    name VARCHAR(128),
    description TEXT,
    category VARCHAR(64),
    location JSONB,      -- {lat, lng}
    recommended_duration INT,  -- 建议游览时间(分钟)
    tags TEXT[]
);
```

### 4.2 向量数据（Milvus/ChromaDB）

```python
# 知识向量集合
collection_schema = {
    "name": "scenic_knowledge",
    "fields": [
        {"name": "id", "type": "VARCHAR", "max_length": 64},
        {"name": "doc_id", "type": "VARCHAR", "max_length": 64},
        {"name": "chunk_text", "type": "VARCHAR", "max_length": 4096},
        {"name": "category", "type": "VARCHAR", "max_length": 32},
        {"name": "spot_name", "type": "VARCHAR", "max_length": 128},
        {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 1024},
    ],
    "index": {"field": "embedding", "type": "HNSW", "metric": "COSINE"}
}
```

---

## 五、接口设计（核心API）

### 5.1 游客交互接口

```yaml
# WebSocket: 实时对话
WS /api/v1/chat/stream
  → Client: { "type": "text"|"audio", "content": "..." , "session_id": "..." }
  ← Server: { "type": "text_chunk"|"audio_chunk"|"video_frame"|"emotion",
              "content": "...", "done": bool }

# REST: 创建会话
POST /api/v1/sessions
  Body: { "visitor_id": "optional", "interests": ["历史", "自然"] }
  Response: { "session_id": "uuid", "greeting": "..." }

# REST: 获取推荐路线
POST /api/v1/recommend/route
  Body: { "session_id": "...", "duration_hours": 3, "interests": [...] }
  Response: { "route": [...], "description": "..." }
```

### 5.2 管理后台接口

```yaml
# 知识库管理
POST   /api/v1/admin/knowledge/upload     # 上传文档
GET    /api/v1/admin/knowledge/list        # 文档列表
PUT    /api/v1/admin/knowledge/{id}        # 更新
DELETE /api/v1/admin/knowledge/{id}        # 删除
POST   /api/v1/admin/knowledge/test        # 测试问答效果

# 数字人管理
GET    /api/v1/admin/avatar/list           # 形象列表
POST   /api/v1/admin/avatar/config         # 创建/更新配置
PUT    /api/v1/admin/avatar/{id}/activate  # 激活形象

# 数据分析
GET    /api/v1/admin/analytics/dashboard   # 大屏数据
GET    /api/v1/admin/analytics/sentiment   # 情感趋势
GET    /api/v1/admin/analytics/hotspots    # 热门问答
POST   /api/v1/admin/analytics/report      # 生成报告
```

---

## 六、性能优化策略

### 6.1 延迟控制（目标 < 5秒）

```
用户语音输入 → ASR(~0.5s) → RAG检索(~0.3s) → LLM首token(~0.8s) → 流式输出
                                                         ↓
                                              TTS首帧(~0.3s) → 口型驱动(~0.2s)
                                                         ↓
                                              总首响应: ~2.1s ✓
```

**优化手段：**

| 策略 | 实现方式 | 预期收益 |
|------|----------|----------|
| 流式响应 | LLM token → 句子级TTS → 实时口型驱动 | 感知延迟降低60% |
| 并行处理 | ASR与意图识别并行，TTS与口型渲染并行 | 总延迟降低30% |
| 缓存机制 | 高频FAQ缓存、Embedding缓存 | 命中率高时延迟<1s |
| 模型量化 | LLM使用INT4量化 / API调用 | 推理速度提升2x |
| 预加载 | 数字人模型预加载，连接池预建立 | 首次交互延迟降低 |

### 6.2 准确率保障（目标 ≥ 90%）

- **RAG增强**：混合检索 + Rerank，召回率提升至95%+
- **Prompt工程**：严格约束"仅基于参考知识回答，不确定时明确告知"
- **知识分层**：FAQ精准匹配 → RAG语义检索 → LLM通用回答
- **质量评估**：构建标准测试集，定期评估并优化

---

## 七、项目目录结构

```
AI-SmartTour/
├── frontend/                      # 前端工程
│   ├── tourist-app/               # 游客交互端
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── DigitalHuman/  # 数字人渲染组件
│   │   │   │   ├── ChatPanel/     # 对话面板
│   │   │   │   └── VoiceInput/    # 语音输入
│   │   │   ├── views/
│   │   │   ├── stores/            # Pinia状态管理
│   │   │   └── services/          # API调用封装
│   │   └── package.json
│   └── admin-panel/               # 管理后台
│       ├── src/
│       │   ├── views/
│       │   │   ├── KnowledgeBase/ # 知识库管理
│       │   │   ├── AvatarConfig/  # 形象管理
│       │   │   ├── Analytics/     # 数据分析
│       │   │   └── Dashboard/     # 数据大屏
│       │   └── components/
│       └── package.json
├── backend/                       # 后端服务
│   ├── app/
│   │   ├── api/                   # API路由
│   │   │   ├── chat.py            # 对话接口
│   │   │   ├── knowledge.py       # 知识库接口
│   │   │   ├── avatar.py          # 数字人管理
│   │   │   └── analytics.py       # 数据分析
│   │   ├── core/                  # 核心逻辑
│   │   │   ├── dialogue.py        # 对话引擎
│   │   │   ├── rag.py             # RAG检索
│   │   │   ├── recommend.py       # 推荐引擎
│   │   │   └── sentiment.py       # 情感分析
│   │   ├── services/              # 外部服务封装
│   │   │   ├── llm.py             # LLM调用
│   │   │   ├── asr.py             # 语音识别
│   │   │   ├── tts.py             # 语音合成
│   │   │   └── digital_human.py   # 数字人驱动
│   │   ├── models/                # 数据模型
│   │   ├── db/                    # 数据库配置
│   │   └── config.py              # 配置管理
│   ├── knowledge_base/            # 知识库数据
│   │   ├── raw/                   # 原始文档
│   │   ├── processed/             # 处理后文档
│   │   └── vectors/               # 向量索引
│   ├── pyproject.toml
│   └── Dockerfile
├── digital_human/                 # 数字人引擎（独立模块）
│   ├── models/                    # 预训练模型
│   ├── inference/                 # 推理脚本
│   └── assets/                    # 数字人素材（形象图片等）
├── docs/                          # 项目文档
│   ├── design/                    # 设计文档
│   ├── api/                       # API文档
│   └── deployment/                # 部署文档
├── tests/                         # 测试
│   ├── test_qa_accuracy.py        # 问答准确率测试
│   └── test_api.py                # 接口测试
├── scripts/                       # 工具脚本
│   ├── build_knowledge_base.py    # 构建知识库
│   └── evaluate_accuracy.py       # 准确率评估
├── docker-compose.yml             # 容器编排
└── README.md                      # 项目说明
```

---

## 八、开发计划（建议分期）

### Phase 1: 核心对话能力（Week 1-2）

- [x] 项目框架搭建（前后端基础工程）
- [ ] RAG知识库引擎（文档解析 + 向量检索 + 混合检索）
- [ ] LLM对话引擎（Prompt设计 + 流式输出 + 上下文管理）
- [ ] 基础文本对话界面

### Phase 2: 数字人集成（Week 3-4）

- [ ] ASR语音识别接入
- [ ] TTS语音合成接入
- [ ] 数字人口型驱动集成（MuseTalk）
- [ ] 前端数字人渲染组件

### Phase 3: 管理后台（Week 5-6）

- [ ] 知识库管理界面
- [ ] 数字人形象配置
- [ ] 情感分析模块
- [ ] 数据大屏 & 报告生成

### Phase 4: 优化与测试（Week 7-8）

- [ ] 性能优化（延迟降低、缓存策略）
- [ ] 准确率调优（测试集评估 + Prompt迭代）
- [ ] 个性化推荐完善
- [ ] 整体测试 & 演示视频制作

---

## 九、创新点设计

### 9.1 差异化亮点

1. **情感驱动数字人**：不仅口型同步，还根据对话情感动态调整表情和语音风格
2. **多轮画像推理**：通过多轮对话逐步构建游客画像，实现越聊越懂你
3. **混合检索+Rerank**：确保问答准确率，超越纯向量检索方案
4. **流式管线**：LLM → 句子级TTS → 实时口型，大幅降低感知延迟
5. **管理闭环**：游客反馈 → 情感分析 → 优化建议 → 知识库更新

### 9.2 可选加分项

- **GPS定位联动**：结合位置自动触发附近景点讲解
- **离线降级方案**：无网/弱网时提供预缓存的基础问答
- **多语言支持**：英文/日文游客自动切换语言
- **AR导航叠加**：摄像头画面叠加AR箭头指引

---

## 十、部署架构

```
┌─── Docker Compose 容器编排 ─────────────────────┐
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Frontend │  │ Backend  │  │ Digital Human│  │
│  │ (Nginx)  │  │ (FastAPI)│  │  (GPU)       │  │
│  │ :80      │  │ :8000    │  │  :8001       │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │PostgreSQL│  │  Milvus  │  │    Redis     │  │
│  │ :5432    │  │  :19530  │  │    :6379     │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└──────────────────────────────────────────────────┘
```

---

## 十一、风险评估与应对

| 风险 | 影响 | 应对策略 |
|------|------|----------|
| GPU资源不足 | 数字人渲染延迟 | 使用2D方案 + API调用模式 |
| LLM幻觉 | 回答不准确 | 严格RAG约束 + 置信度判断 |
| 知识库覆盖不全 | 无法回答 | 兜底回答 + 引导至人工服务 |
| 首次延迟过高 | 用户体验差 | 预加载 + 欢迎语填充 |
| 并发压力 | 系统卡顿 | 请求队列 + 水平扩容 |

---

## 十二、总结

本方案以 **"精准知识 + 自然交互 + 情感共鸣"** 为设计理念，通过：

1. **RAG + 混合检索** 确保 ≥90% 问答准确率
2. **流式管线** 控制端到端延迟 < 5秒
3. **情感驱动数字人** 实现自然逼真的交互体验
4. **闭环管理系统** 覆盖运营全场景

全面满足赛题功能、非功能、创新性要求，打造一个可落地的景区智能导览解决方案。
