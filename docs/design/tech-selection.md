# 技术选型详细说明

## 一、大语言模型选型

### 主选：Qwen2.5 系列

| 使用场景 | 模型 | 部署方式 | 说明 |
|----------|------|----------|------|
| 对话生成 | Qwen2.5-72B-Instruct | API调用 (DashScope) | 质量最优 |
| 本地备选 | Qwen2.5-7B-Instruct | 本地部署 (vLLM) | 无网环境 |
| 情感分析 | Qwen2.5-7B | 本地部署 | 批量处理 |

**选型理由**：
- 中文理解和生成能力国内领先
- 支持 128K 长上下文，适合长对话
- DashScope API 免费额度充足，适合比赛
- 开源可本地部署，满足离线场景

### 备选方案

- GLM-4 (智谱AI)：中文能力强，API稳定
- DeepSeek-V2：性价比高，推理速度快

---

## 二、语音识别 (ASR)

### 主选：Paraformer (FunASR)

```
阿里开源，中文语音识别准确率业界领先
- 模型：paraformer-zh (中文)
- 特点：流式/非流式均支持，标点恢复，时间戳对齐
- 部署：本地 Python 推理 / FunASR Server
```

### 备选方案

- Whisper (OpenAI)：多语言支持好，但中文不如Paraformer
- SenseVoice (阿里)：情感识别一体化

---

## 三、语音合成 (TTS)

### 主选：CosyVoice (阿里)

```
特点：
- 支持多种说话风格（新闻播报/对话/情感）
- 零样本语音克隆（可定制景区特色音色）
- 流式合成，延迟低
- 中文自然度高
```

### 备选方案

- GPT-SoVITS：开源社区活跃，音色克隆效果好
- Edge-TTS：微软在线API，零部署成本

---

## 四、数字人驱动引擎

### 主选：MuseTalk

```
特点：
- 实时音频驱动口型（~30fps）
- 仅需一张参考图即可生成
- 资源消耗适中（单GPU可运行）
- 口型自然度高

输入：参考图片 + 音频流
输出：口型同步视频帧
```

### 备选方案

| 方案 | 优势 | 劣势 |
|------|------|------|
| SadTalker | 表情丰富，头部运动自然 | 速度稍慢，非实时 |
| Wav2Lip | 口型精准度高 | 表情单一 |
| LivePortrait | 全脸驱动效果好 | 需要更多GPU资源 |

### 推荐组合

```
MuseTalk (口型驱动) + 自定义表情层 (情感表情叠加)
```

---

## 五、知识检索 (RAG)

### Embedding模型：BGE-M3

```
特点：
- 多语言、多粒度、多功能
- 支持 Dense + Sparse + ColBERT 混合检索
- 中文语义理解能力强
- 维度：1024
```

### Reranker：BGE-Reranker-v2-m3

```
用途：对检索结果精排，提升准确率
```

### 向量数据库

| 开发阶段 | 方案 | 说明 |
|----------|------|------|
| 原型开发 | ChromaDB | 零配置，内嵌Python进程 |
| 生产部署 | Milvus Lite | 性能更好，支持混合检索 |

---

## 六、前端技术栈

```
Vue 3 + TypeScript + Vite
├── UI框架：Element Plus（管理后台） / Vant（移动端游客）
├── 状态管理：Pinia
├── 路由：Vue Router 4
├── HTTP：Axios + WebSocket原生API
├── 数据可视化：ECharts 5
├── 数字人渲染：Canvas/WebGL + 视频流播放
└── 语音录入：Web Audio API + MediaRecorder
```

---

## 七、开发工具链

| 工具 | 用途 |
|------|------|
| Ruff | Python代码格式化+Lint |
| ESLint + Prettier | 前端代码规范 |
| Pytest | 后端单元测试 |
| Vitest | 前端单元测试 |
| Docker Compose | 本地开发环境 |
| Git | 版本控制 |
