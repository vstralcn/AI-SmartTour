"""个性化路线推荐引擎"""


SCENIC_SPOTS = [
    {
        "id": "1",
        "name": "景区入口广场",
        "description": "景区标志性建筑所在地，设有游客服务中心、导览图和历史沿革展板",
        "category": "文化景观",
        "recommended_duration": 20,
        "tags": ["历史文化", "地标", "服务"],
    },
    {
        "id": "2",
        "name": "古建筑群",
        "description": "保存完好的明清古建筑群，展现传统建筑艺术之美，包含大殿、钟楼、鼓楼等",
        "category": "历史遗迹",
        "recommended_duration": 45,
        "tags": ["历史文化", "建筑", "摄影打卡"],
    },
    {
        "id": "3",
        "name": "山水园林",
        "description": "融合江南园林精髓，亭台楼阁错落有致，有镜湖、翠竹径等景观",
        "category": "自然风光",
        "recommended_duration": 40,
        "tags": ["自然风光", "摄影打卡", "休闲"],
    },
    {
        "id": "4",
        "name": "文化体验馆",
        "description": "沉浸式体验传统文化，可参与陶艺制作、书法体验、古装换装等",
        "category": "互动体验",
        "recommended_duration": 50,
        "tags": ["民俗体验", "亲子游玩", "互动"],
    },
    {
        "id": "5",
        "name": "观景台",
        "description": "景区最高点，海拔约350米，可俯瞰全景，日出日落时分最佳",
        "category": "观景",
        "recommended_duration": 30,
        "tags": ["自然风光", "摄影打卡", "观景"],
    },
    {
        "id": "6",
        "name": "古韵茶室",
        "description": "品茗赏景，提供传统茶点，感受慢生活文化",
        "category": "休闲",
        "recommended_duration": 30,
        "tags": ["美食探索", "休闲", "文化"],
    },
    {
        "id": "7",
        "name": "小吃街",
        "description": "汇集本地特色小吃，手工豆腐、桂花糕、竹筒饭等",
        "category": "美食",
        "recommended_duration": 40,
        "tags": ["美食探索", "休闲"],
    },
    {
        "id": "8",
        "name": "非遗展示区",
        "description": "展示传统非遗技艺，可观看现场演示并参与互动体验",
        "category": "文化",
        "recommended_duration": 35,
        "tags": ["历史文化", "民俗体验", "互动"],
    },
]


def recommend_route(
    duration_hours: float = 3,
    interests: list[str] | None = None,
    companions: list[str] | None = None,
    mobility: str = "标准",
) -> tuple[list[dict], str]:
    """根据游览时长、兴趣和同行约束推荐路线。"""
    interests = interests or []
    companions = companions or []
    available_minutes = int(duration_hours * 60)

    scored = []
    for spot in SCENIC_SPOTS:
        score = 1.0
        for interest in interests:
            if interest in spot["tags"]:
                score += 4.0
        if "儿童" in companions and any(
            tag in spot["tags"] for tag in ("亲子游玩", "互动")
        ):
            score += 4.0
        if "老人" in companions and any(
            tag in spot["tags"] for tag in ("休闲", "服务")
        ):
            score += 2.0
        if mobility == "低强度":
            if spot["name"] == "观景台":
                score -= 4.0
            if any(tag in spot["tags"] for tag in ("休闲", "服务")):
                score += 2.0
        scored.append((score, spot))

    scored.sort(key=lambda x: x[0], reverse=True)

    route = []
    total_minutes = 0
    for _score, spot in scored:
        if _score <= 0:
            continue
        if total_minutes + spot["recommended_duration"] <= available_minutes:
            route.append(spot)
            total_minutes += spot["recommended_duration"]

    route.sort(key=lambda x: int(x["id"]))
    duration_text = f"{duration_hours:g}"

    if interests:
        interest_text = "、".join(interests)
        desc = (
            f"根据您对{interest_text}的兴趣偏好，为您规划了约{duration_text}小时的游览路线。"
            f"路线共{len(route)}个景点，预计游览时间{total_minutes}分钟。"
        )
    else:
        desc = (
            f"为您规划了约{duration_text}小时的综合游览路线，"
            f"涵盖{len(route)}个精华景点，预计游览时间{total_minutes}分钟。"
        )
    constraints = []
    if companions:
        constraints.append(f"同行人员：{'、'.join(companions)}")
    if mobility != "标准":
        constraints.append(f"游览强度：{mobility}")
    if constraints:
        desc += f" 已纳入{'；'.join(constraints)}约束。"

    return route, desc
