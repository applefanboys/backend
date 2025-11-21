from fastapi import APIRouter
from App.service.naverNewsService import get_today_economy_news

router = APIRouter(prefix="/api/news", tags=["news"])

@router.get("/today")
def read_today_news():
    news = get_today_economy_news() or []
    return {"count": len(news), "data": news}