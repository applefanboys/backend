from fastapi import FastAPI
from App.api.stock import router as stock_router

app = FastAPI()

# 라우터 등록
app.include_router(stock_router)

@app.get("/")
async def root():
    return {"message": "백엔드 서버 정상 작동 중! (리팩토링 완료)"}
# --- 서버 실행 코드 (이거 없으면 안 켜짐!) ---
if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0은 누구나 접속 가능, 포트는 8000번
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)