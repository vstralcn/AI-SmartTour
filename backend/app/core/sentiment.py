"""情感分析引擎 - 分析对话情绪和生成报告"""

import math

POSITIVE_WORDS = {
    "好", "棒", "赞", "喜欢", "满意", "感谢", "谢谢", "美", "漂亮", "精彩",
    "厉害", "有趣", "开心", "愉快", "太好了", "不错", "推荐", "值得", "壮观",
    "震撼", "惊艳", "难忘", "完美", "享受", "舒服", "贴心", "方便",
}

NEGATIVE_WORDS = {
    "差", "糟", "烂", "不好", "失望", "生气", "投诉", "贵", "挤", "脏",
    "累", "难吃", "无聊", "坑", "骗", "排队", "等", "太久", "不满",
    "退票", "没意思", "不值", "垃圾",
}


def analyze_emotion(text: str) -> str:
    """分析单条文本的情感倾向"""
    pos_count = sum(1 for w in POSITIVE_WORDS if w in text)
    neg_count = sum(1 for w in NEGATIVE_WORDS if w in text)

    if pos_count > neg_count:
        return "positive"
    if neg_count > pos_count:
        return "negative"
    return "neutral"


def analyze_digital_human_emotion(text: str) -> str:
    """分析用户输入，返回数字人应展示的表情"""
    emotion = analyze_emotion(text)
    if emotion == "positive":
        return "happy"
    if emotion == "negative":
        return "caring"

    if any(kw in text for kw in ["历史", "文化", "典故", "传说", "建筑"]):
        return "explaining"
    if any(kw in text for kw in ["你好", "嗨", "开始", "推荐"]):
        return "excited"
    return "neutral"


def generate_mock_dashboard():
    """生成演示用的仪表盘数据"""
    return {
        "today_visitors": 1283,
        "weekly_visitors": 8742,
        "total_sessions": 45892,
        "avg_satisfaction": 4.6,
        "hot_questions": [
            {"question": "景区开放时间是什么？", "count": 342},
            {"question": "门票价格多少？", "count": 278},
            {"question": "推荐游览路线？", "count": 256},
            {"question": "附近有什么餐厅？", "count": 198},
            {"question": "景区有哪些历史故事？", "count": 176},
        ],
        "satisfaction_trend": [
            {"date": "周一", "score": 4.5},
            {"date": "周二", "score": 4.6},
            {"date": "周三", "score": 4.4},
            {"date": "周四", "score": 4.7},
            {"date": "周五", "score": 4.8},
            {"date": "周六", "score": 4.6},
            {"date": "周日", "score": 4.5},
        ],
        "hourly_visits": [
            {"hour": h, "count": max(0, int(80 * math.sin((h - 6) / 12 * math.pi) + 10))}
            for h in range(24)
        ],
        "spot_popularity": [
            {"name": "古建筑群", "visits": 890},
            {"name": "山水园林", "visits": 756},
            {"name": "文化体验馆", "visits": 634},
            {"name": "观景台", "visits": 521},
            {"name": "入口广场", "visits": 412},
        ],
    }


def generate_mock_sentiment_report():
    """生成演示用的情感分析报告"""
    return {
        "positive_ratio": 0.72,
        "neutral_ratio": 0.21,
        "negative_ratio": 0.07,
        "trend": [
            {"date": "06-24", "positive": 70, "neutral": 22, "negative": 8},
            {"date": "06-25", "positive": 73, "neutral": 20, "negative": 7},
            {"date": "06-26", "positive": 68, "neutral": 24, "negative": 8},
            {"date": "06-27", "positive": 75, "neutral": 19, "negative": 6},
            {"date": "06-28", "positive": 71, "neutral": 21, "negative": 8},
            {"date": "06-29", "positive": 74, "neutral": 20, "negative": 6},
            {"date": "06-30", "positive": 72, "neutral": 21, "negative": 7},
        ],
        "top_concerns": [
            {"topic": "景区服务", "count": 456, "sentiment": "positive"},
            {"topic": "导览讲解质量", "count": 389, "sentiment": "positive"},
            {"topic": "排队等候", "count": 234, "sentiment": "negative"},
            {"topic": "景区设施", "count": 198, "sentiment": "neutral"},
            {"topic": "门票价格", "count": 156, "sentiment": "neutral"},
            {"topic": "餐饮服务", "count": 134, "sentiment": "positive"},
        ],
        "suggestions": [
            "建议增加高峰时段分流措施，缓解排队压力",
            "游客对历史文化类讲解满意度最高，可加强此类内容深度",
            "景区内餐饮选择受到好评，建议增加更多特色小吃",
            "部分游客反映导览路线标识不够清晰，建议优化指引",
            "推荐个性化路线功能受到积极反馈，可进一步细化兴趣分类",
        ],
    }
