from fastapi import FastAPI, APIRouter
from App.router import routes_naverNews, routes_preferences

app = FastAPI(title="News API Server")

# 라우터 등록
app.include_router(routes_naverNews.router)
app.include_router(routes_preferences.router)

@app.get("/")
async def root():
    return {"message": "fastAPI 서버 정상 작동중"}
