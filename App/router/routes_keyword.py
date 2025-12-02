from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from App.core.database import get_db
from App.user.models import UserOnBoarding
from App.service.keyword_service import generate_today_keywords

router = APIRouter(prefix="/api/keywords", tags=["keywords"])

@router.get("/today_keywords")
def get_today_keywords(user_id: int, db: Session = Depends(get_db)):

    onboarding = (
        db.query(UserOnBoarding)
        .filter(UserOnBoarding.user_id == user_id)
        .first()
    )

    if onboarding is None:
        return {"keywords": []}

    keywords = generate_today_keywords(
        onboarding.q1_categories,
        onboarding.q2_keywords,
        onboarding.q3_keywords,
    )

    return {"keywords": keywords}
