"""RAG知识库引擎 - 文档解析 + 向量检索 + 混合检索"""

import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path


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

    当前支持 FAQ 精确匹配和轻量关键词排序，并输出结构化证据。
    BGE-M3、Reranker 与向量数据库通过 rag 可选依赖预留升级路径。
    """

    def __init__(self):
        self.knowledge_base: list[dict] = []
        self.faq: list[dict] = []
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
        for item in self.faq:
            keywords = item.get("keywords", [])
            if any(kw in query for kw in keywords):
                return KnowledgeEvidence(
                    title=item.get("title", "常见问题 FAQ"),
                    content=item["content"],
                    category=item.get("category", "FAQ"),
                    score=1.0,
                    source=item.get("source", "景区常见问题"),
                )
        return None

    def _keyword_search(self, query: str, top_k: int = 3) -> list[KnowledgeEvidence]:
        scored: list[KnowledgeEvidence] = []
        normalized_query = self._normalize(query)
        query_bigrams = self._bigrams(normalized_query)

        for doc in self.knowledge_base:
            content = doc.get("content", "")
            title = doc.get("title", "")
            category = doc.get("category", "景区知识")
            tags = doc.get("tags", [])
            normalized_doc = self._normalize(" ".join([title, content, category, *tags]))
            doc_bigrams = self._bigrams(normalized_doc)

            normalized_title = self._normalize(title)
            normalized_category = self._normalize(category)
            title_hit = 0.45 if normalized_title and normalized_title in normalized_query else 0.0
            category_hit = (
                0.15
                if normalized_category and normalized_category in normalized_query
                else 0.0
            )
            tag_hits = sum(1 for tag in tags if self._normalize(tag) in normalized_query)
            tag_score = min(tag_hits * 0.2, 0.4)
            overlap = len(query_bigrams & doc_bigrams) / max(len(query_bigrams), 1)
            score = min(title_hit + category_hit + tag_score + overlap * 0.6, 1.0)

            if score >= 0.12:
                scored.append(
                    KnowledgeEvidence(
                        title=title,
                        content=content,
                        category=category,
                        score=round(score, 3),
                        source=doc.get("source", title),
                    )
                )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    @staticmethod
    def _normalize(text: str) -> str:
        return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", text)).lower()

    @staticmethod
    def _bigrams(text: str) -> set[str]:
        if len(text) < 2:
            return {text} if text else set()
        return {text[index : index + 2] for index in range(len(text) - 1)}

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
            self._normalize_entry(entry, str(entry.get("kind", "document")), index)
            for index, entry in enumerate(entries)
            if entry.get("status", "active") == "active"
        ]
        self.knowledge_base = [
            entry for entry in active_entries if entry["kind"] != "faq"
        ]
        self.faq = [entry for entry in active_entries if entry["kind"] == "faq"]

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

    def delete_entry(self, entry_id: str) -> None:
        self.knowledge_base = [
            item for item in self.knowledge_base if item["id"] != entry_id
        ]
        self.faq = [item for item in self.faq if item["id"] != entry_id]
        self.faq = [item for item in self.faq if item["id"] != entry_id]

    def export_entries(self) -> list[dict]:
        return [dict(entry) for entry in [*self.knowledge_base, *self.faq]]

    @staticmethod
    def _normalize_entry(item: dict, kind: str, index: int) -> dict:
        content = str(item.get("content") or item.get("answer") or "")
        title = str(item.get("title") or ("常见问题 FAQ" if kind == "faq" else "景区知识"))
        category = str(item.get("category") or ("FAQ" if kind == "faq" else "景区知识"))
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
