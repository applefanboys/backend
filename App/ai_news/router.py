# App/news/router.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.user.models import User  # 기존 User 모델

from .schemas import PersonalizedNewsResponse
from .aiNews_service import build_user_keywords
from .recommendService import get_personalized_articles

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/api/ai_news/personalized", response_model=PersonalizedNewsResponse)
def get_personalized_news(
    days: int = Query(3, ge=1, le=7, description="최근 N일"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    초기 온보딩에서 입력받은 취향을 기반으로
    최근 days일 동안의 사용자 맞춤형 뉴스를 추천.
    """
    user_id = current_user.id

    user_keywords = build_user_keywords(db, user_id)
    if not user_keywords:
        raise HTTPException(
            status_code=400,
            detail="온보딩 정보가 없어서 맞춤형 뉴스를 제공할 수 없습니다.",
        )

    articles = get_personalized_articles(
        user_keywords=user_keywords,
        days=days,
        per_keyword=5,
        limit=limit,
    )

    return PersonalizedNewsResponse(
        user_id=user_id,
        days=days,
        total=len(articles),
        articles=articles,
    )
