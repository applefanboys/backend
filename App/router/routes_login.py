# App/router/routes_login.py

from fastapi import APIRouter

from App.api.v1.endpoints import auth          # auth.py 안에 router = APIRouter(...)
from App.router import routes_naverNews, routes_preferences

# 모든 하위 라우터를 모으는 루트 라우터
api_router = APIRouter()

# /api/auth/*
api_router.include_router(auth.router)

# /api/news/* 이런 식으로 이미 prefix가 안에 정의돼 있다고 가정
api_router.include_router(routes_naverNews.router)
api_router.include_router(routes_preferences.router)
