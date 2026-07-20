"""数据分析与大屏API。"""

from fastapi import APIRouter, Depends

from app.core.auth import require_admin
from app.models.schemas import DashboardData, SentimentReport
from app.services.analytics import build_dashboard, build_sentiment_report

router = APIRouter(prefix="/admin/analytics", dependencies=[Depends(require_admin)])


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard():
    return await build_dashboard()


@router.get("/sentiment", response_model=SentimentReport)
async def get_sentiment():
    return await build_sentiment_report()
