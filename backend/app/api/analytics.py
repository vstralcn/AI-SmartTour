"""数据分析与大屏API"""

from fastapi import APIRouter

from app.core.sentiment import generate_mock_dashboard, generate_mock_sentiment_report
from app.models.schemas import DashboardData, SentimentReport

router = APIRouter(prefix="/admin/analytics")


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard():
    return generate_mock_dashboard()


@router.get("/sentiment", response_model=SentimentReport)
async def get_sentiment():
    return generate_mock_sentiment_report()
