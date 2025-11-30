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

# 2. [추가됨] 사용자 맞춤 뉴스 추천 API
@router.get("/recommend")
def read_recommended_news(
    user_id: int, 
    pref_service: PreferenceService = Depends(get_preference_service)
):
    """
    [앱 사용]
    user_id를 쿼리 파라미터로 보내면,
    DB에서 해당 유저의 관심 키워드(Q2)를 조회하고
    관련된 뉴스를 네이버에서 찾아 요약하여 반환합니다.
    
    요청 예시: GET /api/news/recommend?user_id=1
    """
    # 1. 사용자의 관심 키워드 가져오기
    user_keywords = pref_service.get_user_keywords(user_id)
    
    # 2. 해당 키워드로 뉴스 검색 (Service 계층 이용)
    news_data = get_personalized_news(user_keywords)

    return {
        "user_id": user_id,
        "search_keywords": user_keywords,
        "count": len(news_data),
        "data": news_data
    }