from datetime import datetime, timedelta
from typing import List, Tuple
from sqlalchemy.orm import Session

from App.user.models import UserOnBoarding

# Q1 카테고리 id -> 대표 키워드 매핑 (예시)
Q1_CATEGORY_KEYWORDS = {
    1: ["경제", "물가", "성장률", "금리", "경기"],
    2: ["주식", "코스피", "코스닥", "증권사", "개인투자자"],
    3: ["부동산", "아파트", "전세", "청약"],
    4: ["환율", "달러", "원달러", "엔화", "원화"],
    5: ["채권", "국채", "회사채"],
    6: ["암호화폐", "비트코인", "이더리움", "코인"],
    7: ["원자재", "유가", "금 가격", "구리"],
    # … 실제 카테고리 id/label에 맞춰서 추가
}


def build_user_keywords(db: Session, user_id: int) -> List[str]:
    """
    온보딩 테이블에서 사용자의 카테고리/키워드 기반으로
    최종 검색용 키워드 리스트를 만들어주는 함수.
    """
    onboarding: UserOnBoarding = (
        db.query(UserOnBoarding)
        .filter(UserOnBoarding.user_id == user_id)
        .first()
    )
    if onboarding is None:
        return []

    keywords: List[str] = []

    # Q1: 카테고리 id 리스트 (예: [2, 5, 7])
    if onboarding.q1_categories:
        for cid in onboarding.q1_categories:
            if cid in Q1_CATEGORY_KEYWORDS:
                keywords.extend(Q1_CATEGORY_KEYWORDS[cid])

    # Q2, Q3: 자유 키워드 리스트 (예: ["반도체", "2차전지"])
    if onboarding.q2_keywords:
        keywords.extend(onboarding.q2_keywords)
    if onboarding.q3_keywords:
        keywords.extend(onboarding.q3_keywords)

    # 중복 제거 + 공백 제거
    cleaned = []
    for kw in keywords:
        kw = (kw or "").strip()
        if kw and kw not in cleaned:
            cleaned.append(kw)

    return cleaned
