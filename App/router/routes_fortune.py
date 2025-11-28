from fastapi import APIRouter, Query
from typing import List, Optional

from App.service.fortune_service import generate_today_fortune

router = APIRouter(
    prefix="/api/fortune",
    tags=["fortune"]
)

@router.get("/today")
def today_fortune(
    name: Optional[str] = None,
    birthdate: Optional[str] = None,
    sign: Optional[str] = None,
    interests: Optional[List[str]] = Query(default=None),
):
    result = generate_today_fortune(
        name=name,
        birthdate=birthdate,
        sign=sign,
        interests=interests or [],
    )
    return {
        "name": name,
        "birthdate": birthdate,
        "sign": sign,
        "fortune": result
    }