from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.service.stock_service import stock_service
from App.user.models import UserOnBoarding
from App.service.preferenceService import Q1_CATEGORIES  # Q1 카테고리 메타데이터 (id, key, label 등)

router = APIRouter(
    prefix="/api/stocks",
    tags=["Stock"],
)


def build_user_data_from_onboarding(user_id: int, db: Session) -> dict:
    """
    UserOnBoarding 테이블에 저장된 Q1/Q2/Q3 정보를 바탕으로
    stock_service에 넘길 user_data 딕셔너리를 만들어주는 함수.
    """
    onboarding: UserOnBoarding | None = (
        db.query(UserOnBoarding)
        .filter(UserOnBoarding.user_id == user_id)
        .first()
    )

    if onboarding is None:
        raise HTTPException(
            status_code=400,
            detail="온보딩 정보가 없습니다. 먼저 온보딩을 완료해주세요.",
        )

    # --- Q1: 카테고리 ID -> label 문자열로 변환 ---
    # 예: [1, 3] -> ["전체 경제", "주식·증권"]
    categories: List[str] = []
    if onboarding.q1_categories:
        id_to_label = {c.id: c.label for c in Q1_CATEGORIES}
        for cid in onboarding.q1_categories:
            label = id_to_label.get(cid)
            if label:
                categories.append(label)

    # --- Q2: 관심 키워드 ---
    # UserOnBoarding 모델 필드명은 프로젝트에 맞게 조정 (예시: q2_keywords)
    keywords: List[str] = onboarding.q2_keywords or []

    # --- Q3: 제외 키워드 ---
    # 마찬가지로 필드명은 실제 모델에 맞게 조정 (예시: q3_keywords)
    excluded: List[str] = onboarding.q3_keywords or []

    return {
        "categories": categories,
        "keywords": keywords,
        "excluded": excluded,
    }


@router.get("/recommend/personal")
async def recommend_personal(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    개인화 주식 추천 API
    - 쿼리파라미터로 user_id를 받고
    - DB에 저장된 온보딩 정보를 읽어서
    - stock_service.get_recommendation()에 넘긴다.
    """
    user_data = build_user_data_from_onboarding(user_id=user_id, db=db)

    try:
        result = await stock_service.get_recommendation(user_data)
        return result
    except Exception as e:
        # 내부 에러는 500으로 래핑
        raise HTTPException(status_code=500, detail=str(e))
