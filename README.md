# AI-SmartTour — 景区导览服务AI数字人

> 第十五届中国软件杯大赛 A组赛题 | 出题企业：锐捷网络（苏州）有限公司

## 项目简介

基于多模态大模型的景区智能导览系统，通过AI数字人为游客提供实时智能问答、个性化路线讲解和情感互动服务，同时为景区管理方提供数据分析和运营支持。

## 核心能力

| 模块 | 功能 |
|------|------|
| 🎭 AI数字人 | 口型同步 + 表情驱动 + 语音合成，自然逼真的交互体验 |
| 🧠 智能问答 | RAG知识库引擎，景区问答准确率 ≥ 90% |
| 🗣️ 多模态交互 | 语音/文本输入，数字人语音+表情输出 |
| 🗺️ 个性化推荐 | 基于用户画像的路线和讲解推荐 |
| 📊 管理后台 | 知识库管理 + 形象配置 + 数据大屏 + 情感分析 |

## 技术栈

- **前端**：Vue 3 + TypeScript + Vite + ECharts
- **后端**：Python + FastAPI + WebSocket
- **大模型**：Qwen2.5（对话 + 分析）
- **语音**：Paraformer (ASR) + CosyVoice (TTS)
- **数字人**：MuseTalk (2D口型驱动)
- **知识库**：Milvus/ChromaDB (向量检索) + BGE-M3 (Embedding)
- **数据库**：PostgreSQL + Redis
- **部署**：Docker Compose

## 系统架构

```
游客端 (Vue3) ←→ WebSocket ←→ FastAPI 后端
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              对话引擎(LLM)   RAG知识库    数字人引擎(TTS+口型)
                    │              │              │
                    ▼              ▼              ▼
              Qwen2.5 API     Milvus        MuseTalk

管理后台 (Vue3) ←→ REST API ←→ PostgreSQL + 分析服务
```

## 快速开始

```bash
# 克隆项目
git clone https://github.com/vstralcn/AI-SmartTour.git
cd AI-SmartTour

# 启动后端
cd backend
pip install -e .
uvicorn app.main:app --reload --port 8000

# 启动前端（游客端）
cd frontend/tourist-app
npm install && npm run dev

# 启动前端（管理后台）
cd frontend/admin-panel
npm install && npm run dev

# Docker一键启动（推荐）
docker-compose up -d
```

## 项目结构

```
AI-SmartTour/
├── frontend/
│   ├── tourist-app/         # 游客交互端
│   └── admin-panel/         # 管理后台
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/             # API路由
│   │   ├── core/            # 核心引擎（对话/RAG/推荐）
│   │   ├── services/        # 外部服务（LLM/ASR/TTS）
│   │   └── models/          # 数据模型
│   └── knowledge_base/      # 知识库数据
├── digital_human/           # 数字人引擎
├── docs/                    # 设计文档
├── tests/                   # 测试
├── scripts/                 # 工具脚本
└── docker-compose.yml
```

## 设计文档

详细系统设计见 [docs/design/architecture.md](docs/design/architecture.md)

## 赛题要求概览

- ✅ 多模态交互（语音+文本输入，数字人语音+口型+表情输出）
- ✅ 智能问答与讲解（基于RAG，准确率≥90%）
- ✅ 个性化推荐（兴趣驱动路线规划）
- ✅ 知识库管理（上传/更新/维护）
- ✅ 数字人形象管理（外观/服装/声音配置）
- ✅ 游客感受度报告（情感分析+满意度）
- ✅ 数据大屏（服务人次/热门问答/趋势）
- ✅ 响应延迟 < 5秒
- ✅ 使用多模态大模型

## 开发团队

vstralcn

## License

MIT
