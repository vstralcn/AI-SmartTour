"""RAG知识库引擎 - 文档解析 + 向量检索 + 混合检索"""

import json
import re
from pathlib import Path


class RAGEngine:
    """景区知识库检索引擎

    支持两种检索模式：
    1. 精确FAQ匹配（关键词命中）
    2. 语义向量检索（ChromaDB，需初始化）
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

    def retrieve(self, query: str, top_k: int = 3) -> str:
        faq_result = self._faq_match(query)
        if faq_result:
            return faq_result

        results = self._keyword_search(query, top_k)
        if results:
            return "\n\n".join(results)
        return ""

    def _faq_match(self, query: str) -> str:
        for item in self.faq:
            keywords = item.get("keywords", [])
            if any(kw in query for kw in keywords):
                return item["answer"]
        return ""

    def _keyword_search(self, query: str, top_k: int = 3) -> list[str]:
        scored: list[tuple[float, str]] = []
        query_terms = set(re.findall(r"[\u4e00-\u9fff]+", query))

        for doc in self.knowledge_base:
            content = doc.get("content", "")
            title = doc.get("title", "")
            tags = set(doc.get("tags", []))

            score = 0.0
            for term in query_terms:
                if term in title:
                    score += 3.0
                if term in content:
                    score += 1.0
                if term in tags:
                    score += 2.0
            if score > 0:
                scored.append((score, content))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:top_k]]

    def add_document(self, title: str, content: str, category: str, tags: list[str]):
        self.knowledge_base.append(
            {
                "title": title,
                "content": content,
                "category": category,
                "tags": tags,
            }
        )

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
