from typing import List
from pydantic import BaseModel

class Category(BaseModel):
    id: int
    key: str
    label: str
    description: str

# ---------- Q1: 관심 분야 선택 ----------

# Q1 카테고리 전체 응답 (GET)
class Q1CategoriesResponse(BaseModel):
    categories: List[Category]

# Q1 답변 요청 (POST)
class Q1AnswerRequest(BaseModel):
    selected_category_ids: List[int]

# Q1 답변 응답 (POST)
class Q1AnswerResponse(BaseModel):
    selected_categories: List[Category]

# ---------- Q2: 선호 키워드 (보고 싶은 것) ----------

class Q2AnswerRequest(BaseModel):
    keywords: List[str]

class Q2AnswerResponse(BaseModel):
    keywords: List[str]

# ---------- Q3: 제외 키워드 (보고 싶지 않은 것) ----------
class Q3AnswerRequest(BaseModel):
    exclude_keywords: List[str]

class Q3AnswerResponse(BaseModel):
    exclude_keywords: List[str]

# ---------- 온보딩 전체 상태 체크용 ----------

class OnboardingStatus(BaseModel):
    q1_completed: bool
    q2_completed: bool
    q3_completed: bool

# ---------- [NEW] 안드로이드 완료 버튼용 통합 요청 모델 ----------
class OnboardingCompleteRequest(BaseModel):
    q1_text: str               # 안드로이드에서 보낸 관심 뉴스 유형 (텍스트)
    include_keywords: List[str] # 포함할 키워드 리스트
    exclude_keywords: List[str] # 제외할 키워드 리스트