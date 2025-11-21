from typing import List
from pydantic import BaseModel

class Category(BaseModel):
    id: int     # 1 ~ 8
    key: str    # 내부용 키
    label: str  # 표시 이름
    description: str    # 설명

# ---------- Q1: 관심 분야 선택 ----------

# Q1 카테고리 전체 응답 (GET)
class Q1CategoriesResponse(BaseModel):
    categories: List[Category]

# Q1 답변 요청 (POST)
class Q1AnswerRequest(BaseModel):
    # 나중에 로그인 붙으면 user_id는 토큰에서 꺼낼 거라서,
    # 지금은 프론트에서 user_id 안 보내도 되게 해둠.
    selected_category_ids: List[int] # 1~3개 선택

# Q1 답변 응답 (POST)
class Q1AnswerResponse(BaseModel):
    selected_categories: List[Category]

# ---------- Q2: 선호 키워드 (보고 싶은 것) ----------

class Q2AnswerRequest(BaseModel):
    # 예 : ["반도체", "2차전지", "엔비디아"]
    keywords: List[str]

class Q2AnswerResponse(BaseModel):
    keywords: List[str]

# ---------- Q3: 제외 키워드 (보고 싶지 않은 것) ----------
class Q3AnswerRequest(BaseModel):
    # 예 : ["코인", "부동산"]
    exclude_keywords: List[str]

class Q3AnswerResponse(BaseModel):
    exclude_keywords: List[str]

# ---------- 온보딩 전체 상태 체크용 ----------

class OnboardingStatus(BaseModel):
    q1_completed: bool
    q2_completed: bool
    q3_completed: bool