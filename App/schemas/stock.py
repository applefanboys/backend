from pydantic import BaseModel
from typing import List

# --- 데이터 모델 (DTO) ---
class OnboardingQ1Request(BaseModel):
    categories: List[str]

class OnboardingQ2Request(BaseModel):
    keywords: List[str]

class OnboardingQ3Request(BaseModel):
    keywords: List[str]