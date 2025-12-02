from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from App.core.database import get_db
from App.user.models import UserOnBoarding

class PreferenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_onboarding(self, user_id: int) -> Optional[UserOnBoarding]:
        """
        해당 유저의 온보딩 레코드를 하나 가져온다.
        없으면 None 리턴.
        """
        return (
            self.db.query(UserOnBoarding)
            .filter(UserOnBoarding.user_id == user_id)
            .first()
        )

    # ---------- Q1 ----------
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

    # ---------- Q2 ----------
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

    # ---------- Q3 ----------
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

    # ---------- 온보딩 상태 ----------

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