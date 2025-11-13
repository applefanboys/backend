from fastapi import FastAPI
from App.Router.routes_naverNews import router as news_router

app = FastAPI(title="News API Server")

# 라우터 등록
app.include_router(news_router)

@app.get("/")
async def root():
    return {"message": "fastAPI 서버 정상 작동중"}
