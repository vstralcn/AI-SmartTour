"""数据分析与大屏API。"""

from fastapi import APIRouter

from app.models.schemas import DashboardData, SentimentReport
from app.services.analytics import build_dashboard, build_sentiment_report

router = APIRouter(prefix="/admin/analytics")


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard():
    return await build_dashboard()


@router.get("/sentiment", response_model=SentimentReport)
async def get_sentiment():
    return await build_sentiment_report()
