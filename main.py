import time

import sqlalchemy.exc
from fastapi import FastAPI, APIRouter
from App.core.database import Base, engine
from App.user import models as user_models

# [수정] 여기에 routes_feed를 추가했습니다.
from App.router import routes_naverNews, routes_preferences, routes_fortune, routes_password_reset, routes_keyword, routes_feed
from App.user.routes import router as auth_router
from App.ai_news.router import router as news_router
from App.tts.routes import router as tts_router
from fastapi import FastAPI
from App.api.stock import router as stock_router

app = FastAPI()

# 라우터 등록
app.include_router(routes_naverNews.router)
app.include_router(routes_preferences.router)
app.include_router(routes_fortune.router)
app.include_router(routes_password_reset.router)
app.include_router(auth_router)
app.include_router(news_router)
app.include_router(routes_keyword.router)
app.include_router(tts_router)
app.include_router(stock_router)

# [수정] 메인 피드(AI 뉴스 포함) 라우터를 등록합니다.
app.include_router(routes_feed.router)

# 테이블 생성
# user_models.User.metadata.create_all(bind=engine)

@app.on_event("startup")
def on_startup():
    #MySQL이 완전히 준비될 떄까지 몇 번 재시도
    max_tries = 10
    for i in range(max_tries):
        try:
            user_models.User.metadata.create_all(bind=engine)
            print("DB 테이블 생성/확인 완료")
            break
        except sqlalchemy.exc.OperationalError as e:
            print(f"DB 연결 실패, 재시도 중... ({i+1}/{max_tries})")
            time.sleep(3)
    else:
        # 그래도 안 되면 명확한 에러로 죽이기
        raise RuntimeError("DB에 연결할 수 없습니다. main-db 상태를 확인하세요.")

app.include_router(stock_router)

@app.get("/")
async def root():
    return {"message": "백엔드 서버 정상 작동 중! (리팩토링 완료)"}