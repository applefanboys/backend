from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from App.core.database import get_db
# from sqlalchemy.sql.functions import current_user

from App.schemas.preference import (
    Q1CategoriesResponse,
    Q1AnswerRequest,
    Q1AnswerResponse,
    Q2AnswerRequest,
    Q2AnswerResponse,
    Q3AnswerRequest,
    Q3AnswerResponse,
    OnboardingStatus,
)
from App.service.preferenceService import PreferenceService
from App.repository.preferenceRepo import PreferenceRepository
from App.user.models import User

router = APIRouter(
    prefix="/api/onboarding",
    tags=["onboarding-preferences"],
)

# 이후 요청마다 이 인스턴스를 그대로 재사용
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
    """
    온보딩 진행 상태 확인 API

    - q1_completed: 관심 분야 선택 완료 여부
    - q2_completed: 선호 키워드 입력 완료 여부
    - q3_completed: 제외 키워드 입력 완료 여부

    초기화면에서 이걸 먼저 호출해서,
    어디까지 진행했는지 보고 다음 화면을 결정하면 됨.
    """
    return service.get_onboarding_status(user_id=user_id)

# ---------- Q1: 관심 분야 선택 ----------
@router.get("/q1/categories", response_model=Q1CategoriesResponse)
def get_q1_categories(
        service: PreferenceService = Depends(get_preference_service),
):
    """
     Q1. 관심 분야 선택 - 카테고리 목록 조회
    """
    categories = service.get_q1_categories()
    return Q1CategoriesResponse(categories=categories)

@router.post("/q1/answer", response_model=Q1AnswerResponse)
def save_q1_answer(
        payload: Q1AnswerRequest,
        user_id: int,
        service: PreferenceService = Depends(get_preference_service),
):
    """
   Q1. 선택한 관심 분야 제출

   지금은 로그인/토큰이 없으니까 임시로 user_id=1로 고정.
   나중에 JWT 인증 붙이면, 거기서 user_id 꺼내서 넣어주면 됨.
   """
    return service.save_q1_answer(user_id=user_id, payload=payload)

# ---------- Q2: 선호 키워드 ----------
@router.post("/q2/answer", response_model=Q2AnswerResponse)
def save_q2_answer(
        payload: Q2AnswerRequest,
        user_id: int,
        service: PreferenceService = Depends(get_preference_service),
):
    """
       Q2. 보고 싶은 키워드 입력

       예:
       {
         "keywords": ["반도체", "2차전지", "엔비디아"]
       }
       """
    return service.save_q2_answer(user_id=user_id, payload=payload)

# ---------- Q3: 제외 키워드 ----------
@router.post("/q3/answer", response_model=Q3AnswerResponse)
def save_q3_answer(
    payload: Q3AnswerRequest,
        user_id: int,
    service: PreferenceService = Depends(get_preference_service),
):
    """
    Q3. 보고 싶지 않은 키워드 입력

    예:
    {
      "exclude_keywords": ["코인", "부동산"]
    }
    """
    return service.save_q3_answer(user_id=user_id, payload=payload)