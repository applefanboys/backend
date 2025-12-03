from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from App.core.database import get_db

from App.schemas.preference import (
    Q1CategoriesResponse,
    Q1AnswerRequest,
    Q1AnswerResponse,
    Q2AnswerRequest,
    Q2AnswerResponse,
    Q3AnswerRequest,
    Q3AnswerResponse,
    OnboardingStatus,
    OnboardingCompleteRequest  # [중요] 새로 추가한 스키마 import
)
from App.service.preferenceService import PreferenceService
from App.repository.preferenceRepo import PreferenceRepository

router = APIRouter(
    prefix="/api/onboarding",
    tags=["onboarding-preferences"],
)

# 의존성 주입 함수
def get_preference_service(
        db: Session = Depends(get_db)
) -> PreferenceService:
    repo = PreferenceRepository(db)
    return PreferenceService(repo)

# ---------- 온보딩 상태 ----------
@router.get("/status", response_model=OnboardingStatus)
def get_onboarding_status(
        user_id: int,
        service: PreferenceService = Depends(get_preference_service),
):
    return service.get_onboarding_status(user_id=user_id)

# ---------- Q1: 관심 분야 선택 ----------
@router.get("/q1/categories", response_model=Q1CategoriesResponse)
def get_q1_categories(
        service: PreferenceService = Depends(get_preference_service),
):
    categories = service.get_q1_categories()
    return Q1CategoriesResponse(categories=categories)

@router.post("/q1/answer", response_model=Q1AnswerResponse)
def save_q1_answer(
        payload: Q1AnswerRequest,
        user_id: int,
        service: PreferenceService = Depends(get_preference_service),
):
    return service.save_q1_answer(user_id=user_id, payload=payload)

# ---------- Q2: 선호 키워드 ----------
@router.post("/q2/answer", response_model=Q2AnswerResponse)
def save_q2_answer(
        payload: Q2AnswerRequest,
        user_id: int,
        service: PreferenceService = Depends(get_preference_service),
):
    return service.save_q2_answer(user_id=user_id, payload=payload)

# ---------- Q3: 제외 키워드 ----------
@router.post("/q3/answer", response_model=Q3AnswerResponse)
def save_q3_answer(
    payload: Q3AnswerRequest,
    user_id: int,
    service: PreferenceService = Depends(get_preference_service),
):
    return service.save_q3_answer(user_id=user_id, payload=payload)

# ---------- [NEW] 안드로이드 앱 전용 통합 저장 (완료 버튼) ----------
@router.post("/complete")
def complete_onboarding(
    payload: OnboardingCompleteRequest,
    user_id: int,
    service: PreferenceService = Depends(get_preference_service)
):
    """
    안드로이드 앱의 '완료' 버튼을 눌렀을 때 호출됩니다.
    Q1(텍스트), Q2(키워드), Q3(제외 키워드)를 한 번에 받습니다.
    """
    # 1. 로그 출력 (데이터 확인용)
    print(f"=== User {user_id} Onboarding Complete ===")
    print(f"Q1 (Text): {payload.q1_text}")
    print(f"Include: {payload.include_keywords}")
    print(f"Exclude: {payload.exclude_keywords}")

    # 2. 실제 서비스 저장 로직 호출
    # (Q1 텍스트는 현재 DB 스키마가 ID 기반이라 로그만 찍고, 키워드들은 저장합니다)
    
    # Q2 저장
    service.save_q2_answer(user_id, Q2AnswerRequest(keywords=payload.include_keywords))
    
    # Q3 저장
    service.save_q3_answer(user_id, Q3AnswerRequest(exclude_keywords=payload.exclude_keywords))

    return {"message": "온보딩 정보가 성공적으로 저장되었습니다."}