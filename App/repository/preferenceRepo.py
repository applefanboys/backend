from typing import List
from sqlalchemy.orm import Session
from App.user.models import UserOnBoarding

class PreferenceRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------- Q1: 관심 분야 저장 ----------
    def save_q1_selection(self, user_id: int, selected_ids: List[int]) -> None:
        onboarding = (
            self.db.query(UserOnBoarding)
            .filter(UserOnBoarding.user_id == user_id)
            .first()
        )

        if onboarding is None:
            onboarding = UserOnBoarding(
                user_id=user_id,
                q1_categories=selected_ids,
            )
            self.db.add(onboarding)
        else:
            onboarding.q1_categories = selected_ids

        self.db.commit()
        self.db.refresh(onboarding)

    # ---------- Q2: 선호 키워드 저장 ----------
    def save_q2_keywords(self, user_id: int, keywords: List[str]) -> None:
        onboarding = (
            self.db.query(UserOnBoarding)
            .filter(UserOnBoarding.user_id == user_id)
            .first()
        )

        if onboarding is None:
            onboarding = UserOnBoarding(
                user_id=user_id,
                q2_keywords=keywords,
            )
            self.db.add(onboarding)
        else:
            onboarding.q2_keywords = keywords

        self.db.commit()
        self.db.refresh(onboarding)

    # ---------- [NEW] Q2: 선호 키워드 조회 (추가됨) ----------
    def get_q2_keywords(self, user_id: int) -> List[str]:
        """
        사용자의 선호 키워드 리스트를 DB에서 가져옵니다.
        """
        onboarding = (
            self.db.query(UserOnBoarding)
            .filter(UserOnBoarding.user_id == user_id)
            .first()
        )

        # 데이터가 있고, 키워드가 존재하면 반환
        if onboarding and onboarding.q2_keywords:
            return onboarding.q2_keywords
        
        # 없으면 빈 리스트 반환
        return []

    # ---------- Q3: 제외 키워드 저장 ----------
    def save_q3_exclude_keywords(self, user_id: int, exclude_keywords: List[str]) -> None:
        onboarding = (
            self.db.query(UserOnBoarding)
            .filter(UserOnBoarding.user_id == user_id)
            .first()
        )

        if onboarding is None:
            onboarding = UserOnBoarding(
                user_id=user_id,
                q3_keywords=exclude_keywords,
            )
            self.db.add(onboarding)
        else:
            onboarding.q3_keywords = exclude_keywords

        self.db.commit()
        self.db.refresh(onboarding)

    # ---------- 온보딩 상태 확인 ----------

    def has_q1(self, user_id: int) -> bool:
        onboarding = (
            self.db.query(UserOnBoarding)
            .filter(UserOnBoarding.user_id == user_id)
            .first()
        )
        return onboarding is not None and onboarding.q1_categories is not None

    def has_q2(self, user_id: int) -> bool:
        onboarding = (
            self.db.query(UserOnBoarding)
            .filter(UserOnBoarding.user_id == user_id)
            .first()
        )
        return onboarding is not None and onboarding.q2_keywords is not None

    def has_q3(self, user_id: int) -> bool:
        onboarding = (
            self.db.query(UserOnBoarding)
            .filter(UserOnBoarding.user_id == user_id)
            .first()
        )
        return onboarding is not None and onboarding.q3_keywords is not None