"""路线推荐API"""

from fastapi import APIRouter

from app.core.recommend import recommend_route
from app.models.schemas import (
    RouteRecommendRequest,
    RouteRecommendResponse,
    ScenicSpotSchema,
)
from app.services.persistence import save_interaction

router = APIRouter()


@router.post("/recommend/route", response_model=RouteRecommendResponse)
async def get_recommended_route(req: RouteRecommendRequest):
    route, description = recommend_route(
        duration_hours=req.duration_hours,
        interests=req.interests,
        companions=req.companions,
        mobility=req.mobility,
    )
    spots = [ScenicSpotSchema(**s) for s in route]
    await save_interaction(
        session_id=req.session_id,
        user_message=f"生成 {req.duration_hours:g} 小时个性化路线",
        assistant_message=description,
        intent="route_planning",
        sentiment="neutral",
        emotion="explaining",
        confidence=1.0,
        response_ms=0,
        tools=["route"],
        route_spots=[spot.name for spot in spots],
        profile_interests=req.interests,
    )
    return RouteRecommendResponse(route=spots, description=description)
