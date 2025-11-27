# main.py  (log-clean / FastAPI 버전)

from fastapi import FastAPI
from App.db.session import init_db
from App.router.routes_login import api_router   # ★ 통합 라우터만 가져오기


def create_app() -> FastAPI:
    """FastAPI 앱 생성 + DB 초기화 + 라우터 등록"""
    app = FastAPI(title="News API Server")

    # --- 여기서 예전 Flask create_app()의 역할을 수행 ---
    init_db()  # 처음 실행 시 테이블 생성/DB 초기화

    # 라우터 등록: routes_login의 api_router 안에
    # /api/auth, /api/news, /api/onboarding 모두 포함되어 있음
    app.include_router(api_router)

    @app.get("/")
    async def root():
        return {"message": "fastAPI 서버 정상 작동중"}

    return app


# uvicorn이 참조할 전역 app 객체
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
