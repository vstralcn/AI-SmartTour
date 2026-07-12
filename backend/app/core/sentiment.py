"""情感分析引擎。"""

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
