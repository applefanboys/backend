from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from App.core.database import get_db

# 서비스 import
from App.service.naverNewsService import get_today_economy_news, get_personalized_news
from App.service.preferenceService import PreferenceService
from App.repository.preferenceRepo import PreferenceRepository

router = APIRouter(prefix="/api/news", tags=["news"])

# PreferenceService 의존성 주입 함수
def get_preference_service(db: Session = Depends(get_db)) -> PreferenceService:
    repo = PreferenceRepository(db)
    return PreferenceService(repo)

# 1. 기존: 오늘의 전체 경제 뉴스
@router.get("/today")
def read_today_news():
    news = get_today_economy_news() or []
    return {"count": len(news), "data": news}

# 2. [사용자 맞춤 뉴스 추천 API]
@router.get("/recommend")
def read_recommended_news(
    user_id: int, 
    pref_service: PreferenceService = Depends(get_preference_service)
):
    """
    [앱 사용]
    user_id를 받아 DB에서 관심 키워드(Q2)를 조회하고,
    네이버 뉴스 API를 통해 관련 뉴스를 가져옵니다.
    """
    # 1. 사용자의 관심 키워드 가져오기 (DB 조회)
    user_keywords = pref_service.get_user_keywords(user_id)
    
    print(f"User {user_id} keywords: {user_keywords}") # 로그 확인용

    # 2. 해당 키워드로 뉴스 검색 (Service 계층 이용)
    # 키워드가 없으면 전체 뉴스를 반환하도록 get_personalized_news 내부에서 처리됨
    news_data = get_personalized_news(user_keywords)

    # 3. 안드로이드 NewsResponse 모델에 맞는 형식으로 반환
    # {"count": int, "data": List[NewsItem]}
    return {
        "count": len(news_data),
        "data": news_data
    }