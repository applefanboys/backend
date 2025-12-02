from fastapi import APIRouter, HTTPException
from App.schemas.stock import OnboardingQ1Request, OnboardingQ2Request, OnboardingQ3Request
from App.service.stock_service import stock_service

router = APIRouter(
    prefix="/api",
    tags=["Stock"]
)

user_data = {
    "categories": ["전체 경제"],
    "keywords": [],
    "excluded": []
}

@router.post("/onboarding/q1")
async def save_q1(req: OnboardingQ1Request):
    user_data["categories"] = req.categories
    return {"message": "Q1 저장 완료", "data": req.categories}

@router.post("/onboarding/q2")
async def save_q2(req: OnboardingQ2Request):
    user_data["keywords"] = req.keywords
    return {"message": "Q2 저장 완료", "data": req.keywords}

@router.post("/onboarding/q3")
async def save_q3(req: OnboardingQ3Request):
    user_data["excluded"] = req.keywords
    return {"message": "Q3 저장 완료", "data": req.keywords}

@router.get("/stocks/recommend/personal")
async def recommend():
    try:
        return await stock_service.get_recommendation(user_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))