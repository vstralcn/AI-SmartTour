"""RAG知识库引擎 - 文档解析 + 关键词检索(jieba 分词 + BM25) + 混合检索"""

import json
import logging
import math
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

try:  # jieba 为纯 Python 中文分词，自带词典、无需模型/联网；缺失时降级到 bigram
    import jieba

    jieba.setLogLevel(logging.WARNING)
    _JIEBA = jieba
except Exception:  # pragma: no cover - 仅在未安装 jieba 时触发
    _JIEBA = None


@dataclass(frozen=True)
class KnowledgeEvidence:
    title: str
    content: str
    category: str
    score: float
    source: str


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    evidence: list[KnowledgeEvidence]
    confidence: float
    answer: str
    matched_by: str

    @property
    def found(self) -> bool:
        return bool(self.evidence)


class RAGEngine:
    """景区知识库检索引擎

    当前支持 FAQ 精确匹配与 jieba 分词 + BM25 关键词检索，并输出结构化证据。
    BGE-M3、Reranker 与向量数据库通过 rag 可选依赖预留升级路径。
    """

    # 泛词：单独命中不足以判定 FAQ，需配合更具体的关键词，避免
    # 例如“我没时间了”误命中“开放时间”FAQ
    _GENERIC_KEYWORDS = {"时间", "路线", "价格", "怎么", "多少"}
    # FAQ 命中置信度阈值：低于该值则回退到关键词检索或拒答
    _FAQ_THRESHOLD = 0.5
    # BM25 超参：k1 控制词频饱和，b 控制文档长度归一化
    _BM25_K1 = 1.5
    _BM25_B = 0.75
    # 关键词检索最低查询覆盖率：低于该值视为答非所问而拒答，避免
    # 仅命中“介绍”等高频泛词就回答领域外问题
    _KEYWORD_MIN_COVERAGE = 0.3
    # 高频虚词：分词后剔除，避免稀释召回与置信度
    _STOPWORDS = {
        "的", "了", "是", "我", "你", "他", "她", "它", "们", "要", "吗", "呢",
        "啊", "和", "与", "在", "有", "个", "请", "问", "这", "那", "就", "也",
        "都", "很", "想", "会", "能", "什么", "怎么", "如何",
    }

    def __init__(self):
        self.knowledge_base: list[dict] = []
        self.faq: list[dict] = []
        # BM25 统计索引，随知识库变更重建
        self._doc_freqs: list[dict[str, int]] = []
        self._doc_len: list[int] = []
        self._df: dict[str, int] = {}
        self._doc_count = 0
        self._avgdl = 0.0
        self._load_knowledge()

    def _load_knowledge(self):
        kb_path = Path(__file__).parent.parent.parent / "knowledge_base"
        faq_path = kb_path / "faq.json"
        docs_path = kb_path / "docs.json"

        if faq_path.exists():
            with open(faq_path, encoding="utf-8") as f:
                self.faq = json.load(f)

        if docs_path.exists():
            with open(docs_path, encoding="utf-8") as f:
                self.knowledge_base = json.load(f)

        if not self.knowledge_base:
            self.knowledge_base = self._default_knowledge()
        if not self.faq:
            self.faq = self._default_faq()
        self.knowledge_base = [
            self._normalize_entry(item, "document", index)
            for index, item in enumerate(self.knowledge_base)
        ]
        self.faq = [
            self._normalize_entry(item, "faq", index)
            for index, item in enumerate(self.faq)
        ]
        self._build_index()

    def retrieve(self, query: str, top_k: int = 3) -> str:
        result = self.retrieve_with_sources(query, top_k)
        return "\n\n".join(item.content for item in result.evidence)

    def retrieve_with_sources(self, query: str, top_k: int = 3) -> RetrievalResult:
        clean_query = query.strip()
        if not clean_query:
            return RetrievalResult(
                query=query,
                evidence=[],
                confidence=0.0,
                answer="",
                matched_by="none",
            )

        faq_result = self._faq_match(clean_query)
        if faq_result:
            return RetrievalResult(
                query=clean_query,
                evidence=[faq_result],
                confidence=faq_result.score,
                answer=faq_result.content,
                matched_by="faq",
            )

        evidence = self._keyword_search(clean_query, top_k)
        if not evidence:
            return RetrievalResult(
                query=clean_query,
                evidence=[],
                confidence=0.0,
                answer="",
                matched_by="none",
            )

        confidence = evidence[0].score
        answer = evidence[0].content
        return RetrievalResult(
            query=clean_query,
            evidence=evidence,
            confidence=confidence,
            answer=answer,
            matched_by="keyword",
        )

    def _faq_match(self, query: str) -> KnowledgeEvidence | None:
        best_item: dict | None = None
        best_score = 0.0
        for item in self.faq:
            keywords = [kw for kw in item.get("keywords", []) if kw]
            matched = [kw for kw in keywords if kw in query]
            if not matched:
                continue
            specific = [
                kw for kw in matched if kw not in self._GENERIC_KEYWORDS]
            if not specific:
                # 仅命中泛词：给低分，交由阈值决定是否回退
                score = 0.35
            else:
                longest = max(len(kw) for kw in specific)
                score = 0.6 + 0.12 * len(specific) + 0.06 * max(longest - 2, 0)
            score = min(score, 1.0)
            if score > best_score:
                best_score = score
                best_item = item

        if best_item is None or best_score < self._FAQ_THRESHOLD:
            return None
        return KnowledgeEvidence(
            title=best_item.get("title", "常见问题 FAQ"),
            content=best_item["content"],
            category=best_item.get("category", "FAQ"),
            score=round(best_score, 3),
            source=best_item.get("source", "景区常见问题"),
        )

    def _keyword_search(self, query: str, top_k: int = 3) -> list[KnowledgeEvidence]:
        if not self.knowledge_base:
            return []
        query_terms = set(self._tokenize(query))
        if not query_terms:
            return []

        normalized_query = self._normalize(query)
        total_idf = sum(self._idf(term) for term in query_terms) or 1.0
        avgdl = self._avgdl or 1.0

        raw: list[tuple[int, float, float, float]] = []
        for idx, doc in enumerate(self.knowledge_base):
            freqs = self._doc_freqs[idx]
            doc_len = self._doc_len[idx]
            bm25 = 0.0
            matched_idf = 0.0
            for term in query_terms:
                freq = freqs.get(term, 0)
                if freq == 0:
                    continue
                idf = self._idf(term)
                denom = freq + self._BM25_K1 * (
                    1 - self._BM25_B + self._BM25_B * doc_len / avgdl
                )
                bm25 += idf * (freq * (self._BM25_K1 + 1)) / denom
                matched_idf += idf
            coverage = matched_idf / total_idf

            # 字段加权：标题命中、标签命中比纯正文命中更可信
            boost = 0.0
            norm_title = self._normalize(doc.get("title", ""))
            if norm_title and norm_title in normalized_query:
                boost += 0.15
            if any(
                self._normalize(tag) and self._normalize(
                    tag) in normalized_query
                for tag in doc.get("tags", [])
            ):
                boost += 0.1
            raw.append((idx, bm25, coverage, boost))

        max_bm25 = max((item[1] for item in raw), default=0.0)
        scored: list[KnowledgeEvidence] = []
        for idx, bm25, coverage, boost in raw:
            # 查询覆盖率不足：主要命中的是泛词，视为不相关，拒答
            if coverage < self._KEYWORD_MIN_COVERAGE:
                continue
            if bm25 <= 0.0 and boost <= 0.0:
                continue
            bm25_norm = bm25 / max_bm25 if max_bm25 > 0 else 0.0
            # 覆盖率为主、BM25 为辅校准置信度到 [0,1]，BM25 同时决定排序
            score = min(0.6 * coverage + 0.4 * bm25_norm + boost, 1.0)
            if score < 0.12:
                continue
            doc = self.knowledge_base[idx]
            scored.append(
                KnowledgeEvidence(
                    title=doc.get("title", ""),
                    content=doc.get("content", ""),
                    category=doc.get("category", "景区知识"),
                    score=round(score, 3),
                    source=doc.get("source", doc.get("title", "")),
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def _build_index(self) -> None:
        """构建 BM25 统计索引：文档词频、文档频率(df)、平均长度。

        知识库内容变更后需重新调用，保持检索与最新数据一致。
        """
        self._doc_freqs = []
        self._doc_len = []
        df: dict[str, int] = {}
        total_len = 0
        for doc in self.knowledge_base:
            tokens = self._tokenize(self._doc_text(doc))
            freqs: dict[str, int] = {}
            for token in tokens:
                freqs[token] = freqs.get(token, 0) + 1
            self._doc_freqs.append(freqs)
            self._doc_len.append(len(tokens))
            total_len += len(tokens)
            for token in freqs:
                df[token] = df.get(token, 0) + 1
        self._df = df
        self._doc_count = len(self.knowledge_base)
        self._avgdl = total_len / self._doc_count if self._doc_count else 0.0

    def _idf(self, term: str) -> float:
        if self._doc_count <= 0:
            return 0.0
        df = self._df.get(term, 0)
        # df=0（未登录词）仍给出高 idf：作为“未被覆盖”信号计入置信度分母，
        # 使以生僻/领域外词为主的查询自然降为低覆盖率而被拒答
        return math.log(1 + (self._doc_count - df + 0.5) / (df + 0.5))

    def _tokenize(self, text: str) -> list[str]:
        """中文分词：优先 jieba 搜索引擎模式，缺失时降级到字符 bigram。"""
        cleaned = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+",
                         " ", text).lower().strip()
        if not cleaned:
            return []
        if _JIEBA is not None:
            tokens = [tok.strip() for tok in _JIEBA.cut_for_search(cleaned)]
        else:
            tokens = list(self._bigrams(self._normalize(text)))
        return [tok for tok in tokens if tok and tok not in self._STOPWORDS]

    @staticmethod
    def _doc_text(doc: dict) -> str:
        return " ".join(
            [
                doc.get("title", ""),
                doc.get("content", ""),
                doc.get("category", ""),
                *doc.get("tags", []),
            ]
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", text)).lower()

    @staticmethod
    def _bigrams(text: str) -> set[str]:
        if len(text) < 2:
            return {text} if text else set()
        return {text[index: index + 2] for index in range(len(text) - 1)}

    def add_document(self, title: str, content: str, category: str, tags: list[str]):
        entry_id = str(uuid.uuid4())
        self.upsert_entry(
            {
                "id": entry_id,
                "title": title,
                "content": content,
                "category": category,
                "tags": tags,
                "keywords": [],
                "kind": "document",
                "source": title,
                "status": "active",
            }
        )
        return entry_id

    def replace_entries(self, entries: list[dict]) -> None:
        active_entries = [
            self._normalize_entry(entry, str(
                entry.get("kind", "document")), index)
            for index, entry in enumerate(entries)
            if entry.get("status", "active") == "active"
        ]
        self.knowledge_base = [
            entry for entry in active_entries if entry["kind"] != "faq"
        ]
        self.faq = [entry for entry in active_entries if entry["kind"] == "faq"]
        self._build_index()

    def upsert_entry(self, entry: dict) -> None:
        normalized = self._normalize_entry(
            entry,
            str(entry.get("kind", "document")),
            0,
        )
        target = self.faq if normalized["kind"] == "faq" else self.knowledge_base
        target[:] = [item for item in target if item["id"] != normalized["id"]]
        if normalized["status"] == "active":
            target.append(normalized)
        self._build_index()

    def delete_entry(self, entry_id: str) -> None:
        self.knowledge_base = [
            item for item in self.knowledge_base if item["id"] != entry_id
        ]
        self.faq = [item for item in self.faq if item["id"] != entry_id]
        self._build_index()

    def export_entries(self) -> list[dict]:
        return [dict(entry) for entry in [*self.knowledge_base, *self.faq]]

    @staticmethod
    def _normalize_entry(item: dict, kind: str, index: int) -> dict:
        content = str(item.get("content") or item.get("answer") or "")
        title = str(item.get("title") or (
            "常见问题 FAQ" if kind == "faq" else "景区知识"))
        category = str(item.get("category") or (
            "FAQ" if kind == "faq" else "景区知识"))
        return {
            "id": str(item.get("id") or f"default-{kind}-{index + 1}"),
            "title": title,
            "content": content,
            "category": category,
            "tags": list(item.get("tags", [])),
            "keywords": list(item.get("keywords", [])),
            "kind": kind,
            "source": str(
                item.get("source")
                or ("景区常见问题" if kind == "faq" else title)
            ),
            "status": str(item.get("status", "active")),
        }

    def _default_knowledge(self) -> list[dict]:
        return [
            {
                "title": "景区概况",
                "content": "本景区始建于明代，距今已有600多年历史。景区占地面积约500亩，"
                "是国家AAAAA级旅游景区。景区融合了自然风光与历史文化，"
                "包含古建筑群、山水园林、文化体验馆等多个景点。年接待游客超过200万人次。",
                "category": "景区信息",
                "tags": ["概况", "历史", "面积", "等级"],
            },
            {
                "title": "古建筑群",
                "content": "古建筑群是景区的核心景点，占地约50亩，包含大殿、钟楼、鼓楼等"
                "10余座古建筑。建筑群始建于明永乐年间（1403年），"
                "历经明清两代多次修缮，保存完好。建筑风格融合了南北特色，"
                "飞檐翘角、雕梁画栋，是研究明清建筑艺术的珍贵实物资料。",
                "category": "景点介绍",
                "tags": ["古建筑", "大殿", "钟楼", "明代", "历史"],
            },
            {
                "title": "山水园林",
                "content": "山水园林区占地约80亩，融合江南园林精髓。园中有假山叠石、"
                "曲水流觞、亭台楼阁错落有致。主要景观包括镜湖、翠竹径、"
                "望月亭、听雨轩等。春季赏花、夏季纳凉、秋季观叶、冬季赏雪，"
                "四季皆有不同景致。",
                "category": "景点介绍",
                "tags": ["园林", "自然", "风光", "湖", "亭"],
            },
            {
                "title": "文化体验馆",
                "content": "文化体验馆是景区的互动体验中心，馆内设有传统手工艺体验区、"
                "非遗展示区、VR历史重现区等。游客可以亲手制作传统工艺品，"
                "观赏非遗技艺表演，通过VR技术穿越回古代体验历史场景。"
                "体验项目包括：陶艺制作、书法体验、古装换装等。",
                "category": "景点介绍",
                "tags": ["体验", "文化", "手工艺", "VR", "互动"],
            },
            {
                "title": "观景台",
                "content": "观景台位于景区最高处，海拔约350米，是景区的最佳观景点。"
                "登上观景台，可以俯瞰景区全貌和远处山峦叠嶂的壮丽景色。"
                "日出和日落时分是最佳观赏时间。观景台设有望远镜和休息区，"
                "也是摄影爱好者的最佳取景地。",
                "category": "景点介绍",
                "tags": ["观景", "摄影", "日出", "全景"],
            },
            {
                "title": "游览路线推荐",
                "content": "经典路线（3小时）：入口广场 → 古建筑群 → 山水园林 → 观景台\n"
                "深度路线（5小时）：入口广场 → 古建筑群 → 文化体验馆 → 山水园林 → 观景台\n"
                "休闲路线（2小时）：入口广场 → 山水园林 → 茶室休憩\n"
                "亲子路线（3小时）：入口广场 → 文化体验馆 → 山水园林 → 观景台",
                "category": "游览信息",
                "tags": ["路线", "推荐", "游览", "行程"],
            },
            {
                "title": "景区餐饮",
                "content": "景区内有多处餐饮点：\n"
                "1. 云水间餐厅 - 提供本地特色菜肴，人均60-80元\n"
                "2. 古韵茶室 - 品茗赏景，提供传统茶点\n"
                "3. 小吃街 - 汇集本地特色小吃，10-30元/份\n"
                "推荐特色美食：手工豆腐、桂花糕、竹筒饭、山珍菌菇汤。",
                "category": "服务信息",
                "tags": ["餐饮", "美食", "餐厅", "小吃"],
            },
        ]

    def _default_faq(self) -> list[dict]:
        return [
            {
                "keywords": ["开放时间", "营业时间", "几点开门", "几点关门", "时间"],
                "answer": "景区开放时间为每日8:00-18:00（最晚入园时间17:00）。"
                "旺季（5月-10月）可能延长至18:30。"
                "建议上午入园，可以充分游览各个景点。",
            },
            {
                "keywords": ["门票", "票价", "多少钱", "价格", "收费"],
                "answer": "景区门票价格：成人票80元/人，学生票40元/人（凭有效学生证），"
                "60岁以上老人凭身份证享半价优惠，1.2米以下儿童免票。"
                "建议通过官方小程序或OTA平台提前购票，可享9折优惠。",
            },
            {
                "keywords": ["停车", "车位", "自驾"],
                "answer": "景区设有两个停车场：南门停车场（300个车位）和北门停车场（200个车位）。"
                "小型车收费10元/次，大型车20元/次。旺季建议提前预约停车位。",
            },
            {
                "keywords": ["交通", "怎么去", "公交", "地铁", "路线"],
                "answer": "公共交通：可乘坐公交12路、56路、89路至「景区站」下车，步行约5分钟。"
                "地铁：乘坐3号线至「景区南门站」，B出口步行3分钟到达。"
                "自驾：导航搜索「景区南门停车场」。",
            },
            {
                "keywords": ["厕所", "卫生间", "洗手间"],
                "answer": "景区内设有6处公共卫生间，分别位于：入口广场、古建筑群附近、"
                "山水园林东侧、文化体验馆内、观景台下方、小吃街旁。"
                "所有卫生间均有无障碍设施和母婴室。",
            },
            {
                "keywords": ["天气", "下雨", "穿什么"],
                "answer": "建议出行前查看天气预报。景区为室内外结合景点，"
                "建议穿着舒适的步行鞋。夏季注意防晒和补水，"
                "冬季注意保暖。雨天部分室外景点可能临时关闭。",
            },
        ]


rag_engine = RAGEngine()
