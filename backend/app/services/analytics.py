"""基于真实会话事件的运营指标聚合。"""

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.db import session_scope
from app.db.models import ConversationSessionRecord, InteractionRecord


def _last_seven_days(today: date) -> list[date]:
    return [today - timedelta(days=offset) for offset in range(6, -1, -1)]


def _concern_topic(message: str) -> str:
    topic_keywords = {
        "开放时间": ("开放", "几点", "关门", "开门"),
        "门票价格": ("门票", "票价", "价格", "收费"),
        "路线规划": ("路线", "行程", "怎么游"),
        "餐饮服务": ("餐厅", "吃", "美食", "小吃"),
        "景区设施": ("厕所", "卫生间", "停车", "母婴"),
        "历史文化": ("历史", "文化", "建筑", "故事"),
    }
    for topic, keywords in topic_keywords.items():
        if any(keyword in message for keyword in keywords):
            return topic
    return "其他咨询"


async def build_dashboard() -> dict:
    async with session_scope() as session:
        sessions = list(
            (await session.scalars(select(ConversationSessionRecord))).all()
        )
        events = list((await session.scalars(select(InteractionRecord))).all())

    now = datetime.now()
    today = now.date()
    week_start = today - timedelta(days=6)
    today_sessions = [item for item in sessions if item.created_at.date() == today]
    weekly_sessions = [
        item for item in sessions if item.created_at.date() >= week_start
    ]
    response_values = [event.response_ms for event in events]
    questions = Counter(
        event.user_message.strip()
        for event in events
        if event.intent == "knowledge_query" and event.user_message.strip()
    )
    spots: Counter[str] = Counter()
    route_preferences: Counter[str] = Counter()
    for event in events:
        spots.update(event.route_spots)
        if event.intent == "route_planning":
            route_preferences.update(event.profile_interests or ["综合游览"])

    daily_response: defaultdict[date, list[int]] = defaultdict(list)
    for event in events:
        daily_response[event.created_at.date()].append(event.response_ms)

    hourly_counts = Counter(
        event.created_at.hour
        for event in events
        if event.created_at.date() == today
    )
    return {
        "today_visitors": len(today_sessions),
        "weekly_visitors": len(weekly_sessions),
        "total_sessions": len(sessions),
        "avg_response_ms": round(
            sum(response_values) / len(response_values)
            if response_values
            else 0
        ),
        "knowledge_gap_count": sum(
            1
            for event in events
            if event.intent == "knowledge_query" and event.confidence == 0
        ),
        "negative_feedback_count": sum(
            1 for event in events if event.sentiment == "negative"
        ),
        "hot_questions": [
            {"question": question, "count": count}
            for question, count in questions.most_common(5)
        ],
        "response_time_trend": [
            {
                "date": day.strftime("%m-%d"),
                "value": round(
                    sum(daily_response[day]) / len(daily_response[day])
                    if daily_response[day]
                    else 0
                ),
            }
            for day in _last_seven_days(today)
        ],
        "hourly_visits": [
            {"hour": hour, "count": hourly_counts[hour]} for hour in range(24)
        ],
        "spot_popularity": [
            {"name": name, "visits": visits}
            for name, visits in spots.most_common(5)
        ],
        "route_preferences": [
            {"name": name, "count": count}
            for name, count in route_preferences.most_common(6)
        ],
        "data_source": "live",
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
    }


async def build_sentiment_report() -> dict:
    async with session_scope() as session:
        events = list((await session.scalars(select(InteractionRecord))).all())

    today = datetime.now().date()
    sentiment_counts = Counter(event.sentiment for event in events)
    total = len(events)
    daily_counts: defaultdict[date, Counter[str]] = defaultdict(Counter)
    concern_counts: Counter[tuple[str, str]] = Counter()
    for event in events:
        daily_counts[event.created_at.date()][event.sentiment] += 1
        concern_counts[(_concern_topic(event.user_message), event.sentiment)] += 1

    trend = []
    for day in _last_seven_days(today):
        counts = daily_counts[day]
        day_total = sum(counts.values())
        trend.append(
            {
                "date": day.strftime("%m-%d"),
                "positive": round(counts["positive"] / day_total * 100)
                if day_total
                else 0,
                "neutral": round(counts["neutral"] / day_total * 100)
                if day_total
                else 0,
                "negative": round(counts["negative"] / day_total * 100)
                if day_total
                else 0,
            }
        )

    top_concerns = [
        {"topic": topic, "count": count, "sentiment": sentiment}
        for (topic, sentiment), count in concern_counts.most_common(6)
    ]
    suggestions = []
    if sentiment_counts["negative"]:
        suggestions.append("优先复盘负面咨询原文并补充现场服务与知识库内容")
    if any(item["topic"] == "路线规划" for item in top_concerns):
        suggestions.append("按高频同行人和兴趣标签完善差异化路线模板")
    if any(item["topic"] == "景区设施" for item in top_concerns):
        suggestions.append("补充卫生间、停车场和无障碍设施的实时位置说明")
    if not suggestions:
        suggestions.append("当前数据量较少，建议持续收集真实游客咨询后再形成运营结论")

    return {
        "positive_ratio": sentiment_counts["positive"] / total if total else 0.0,
        "neutral_ratio": sentiment_counts["neutral"] / total if total else 0.0,
        "negative_ratio": sentiment_counts["negative"] / total if total else 0.0,
        "trend": trend,
        "top_concerns": top_concerns,
        "suggestions": suggestions,
    }
