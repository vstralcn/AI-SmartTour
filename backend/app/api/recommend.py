"""路线推荐API"""

from fastapi import APIRouter

from app.core.recommend import recommend_route
from app.models.schemas import (
    RouteRecommendRequest,
    RouteRecommendResponse,
    ScenicSpotSchema,
)

router = APIRouter()


@router.post("/recommend/route", response_model=RouteRecommendResponse)
async def get_recommended_route(req: RouteRecommendRequest):
    route, description = recommend_route(
        duration_hours=req.duration_hours,
        interests=req.interests,
    )
    spots = [ScenicSpotSchema(**s) for s in route]
    return RouteRecommendResponse(route=spots, description=description)
