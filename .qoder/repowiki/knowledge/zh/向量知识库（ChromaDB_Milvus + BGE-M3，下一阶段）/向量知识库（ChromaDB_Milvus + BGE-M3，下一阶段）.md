---
kind: external_dependency
name: 向量知识库（ChromaDB/Milvus + BGE-M3，下一阶段）
slug: chromadb-milvus-vector-db
category: external_dependency
category_hints:
    - migration_status
scope:
    - '**'
---

### 身份与角色
- README 技术方案将 BGE-M3 嵌入模型 + ChromaDB/Milvus 向量库列为 RAG 升级路径，用于替代当前的 FAQ + bigram 子串匹配，提升中文召回率。

### 迁移状态
- 可选依赖 `[dev,rag]` 已在 pyproject.toml 中声明（langchain、chromadb、sentence-transformers、FlagEmbedding），但核心代码尚未引入；当前 RAG 仅基于内存 FAQ 与关键词排序。
- 安装 `pip install -e ".[dev,rag]"` 后可启用向量检索分支，但需要额外部署向量库服务。

### 验收关联
- README 量化指标要求 RAG Recall@5 ≥ 90%，当前 bigram 方案难以达标，向量检索是达成该指标的必经路径。