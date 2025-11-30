from typing import List
from App.schemas.preference import (
    Category,
    Q1AnswerRequest,
    Q1AnswerResponse,
    Q2AnswerRequest,
    Q2AnswerResponse,
    Q3AnswerRequest,
    Q3AnswerResponse,
    OnboardingStatus
)
from App.repository.preferenceRepo import PreferenceRepository

# 고정된 Q1 카테고리 목록
Q1_CATEGORIES : List[Category] = [
    Category(id=1, key="all_economy", label="전체 경제", description="거시경제, 물가, 성장률, 정책 등 전체적인 경제 흐름을 보고 싶어요."),
    Category(id=2, key="stock", label="주식·증권", description="국내·해외 주식, ETF, 공모주, 증권사 리포트를 위주로 보고 싶어요."),
    Category(id=3, key="industry_company", label="산업·기업", description="산업 동향, 개별 기업 이슈(실적, 신규 사업, 규제 등)를 보고 싶어요."),
    Category(id=4, key="real_estate", label="부동산", description="아파트/상가/전월세, 청약, 부동산 정책 등을 보고 싶어요."),
    Category(id=5, key="finance_fx_bond", label="금융(금리·환율·채권)", description="기준금리, 환율, 채권시장, 중앙은행 관련 뉴스를 보고 싶어요."),
    Category(id=6, key="global", label="국제·글로벌 이슈", description="미국·중국 등 해외 경제, 지정학 이슈, 글로벌 리스크를 보고 싶어요."),
    Category(id=7, key="tech_it", label="기술·IT 경제", description="빅테크, 스타트업, AI, 플랫폼/콘텐츠 산업 등 IT 중심 뉴스를 보고 싶어요."),
    Category(id=8, key="commodity", label="원자재(유가·금·천연가스)", description="유가, 금, 원자재 가격과 관련 산업 이슈를 보고 싶어요."),
]

class PreferenceService:
    def __init__(self, repo: PreferenceRepository):
        self.repo = repo

    # [추가됨] 사용자의 선호 키워드를 가져와서 리스트로 반환
    def get_user_keywords(self, user_id: int) -> List[str]:
        return self.repo.get_q2_keywords(user_id)

    # Q1 카테고리 전체 반환
    def get_q1_categories(self) -> List[Category]:
        return Q1_CATEGORIES

    # Q1 답변 저장
    def save_q1_answer(self, user_id: int, payload: Q1AnswerRequest) -> Q1AnswerResponse:
        valid_ids = {c.id for c in Q1_CATEGORIES}
        filtered_ids = [cid for cid in payload.selected_category_ids if cid in valid_ids]
        filtered_ids = filtered_ids[:3] # 최대 3개

        selected = [c for c in Q1_CATEGORIES if c.id in filtered_ids]
        self.repo.save_q1_selection(user_id, selected_ids=filtered_ids)
        return Q1AnswerResponse(selected_categories=selected)

    # Q2: 선호 키워드 저장
    def save_q2_answer(self, user_id: int, payload: Q2AnswerRequest) -> Q2AnswerResponse:
        cleaned = [kw.strip() for kw in payload.keywords if kw.strip()]
        unique = []
        for kw in cleaned:
            if kw not in unique:
                unique.append(kw)
        limited = unique[:10]

        self.repo.save_q2_keywords(user_id=user_id, keywords=limited)
        return Q2AnswerResponse(keywords=limited)

    # Q3: 제외 키워드 저장
    def save_q3_answer(self, user_id: int, payload: Q3AnswerRequest) -> Q3AnswerResponse:
        cleaned = [kw.strip() for kw in payload.exclude_keywords if kw.strip()]
        unique = []
        for kw in cleaned:
            if kw not in unique:
                unique.append(kw)
        limited = unique[:10]

        self.repo.save_q3_exclude_keywords(user_id=user_id, exclude_keywords=limited)
        return Q3AnswerResponse(exclude_keywords=limited)

    # 온보딩 상태 조회
    def get_onboarding_status(self, user_id: int) -> OnboardingStatus:
        return OnboardingStatus(
            q1_completed=self.repo.has_q1(user_id),
            q2_completed=self.repo.has_q2(user_id),
            q3_completed=self.repo.has_q3(user_id),
        )