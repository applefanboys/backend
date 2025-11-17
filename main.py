import os
import requests
from fastapi import FastAPI, HTTPException
from gtts import gTTS
from fastapi.responses import FileResponse, JSONResponse
import openai

from pydantic import BaseModel
from typing import List


class SummaryRequest(BaseModel):
    text: str


class KeywordsRequest(BaseModel):
    keywords: List[str]


app = FastAPI()

# --- API 키들 ---
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

temp_user_keywords = ["경제"]


# --- [NEW!] "뉴스 요약(description)을 TTS로 바로 변환"하는 API ---
@app.get("/api/shortform/top-news")
async def get_top_news_tts(query: str = "경제"):
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="서버에 네이버 API 키가 설정되지 않았습니다.")

    # 1. 네이버 API로 뉴스 1개 가져오기
    news_json = await get_naver_news_internal(query, 1)  # 내부 함수 호출

    if not news_json.get("items"):
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")

    # 2. 첫 번째 뉴스의 'description'(요약)을 꺼냄
    try:
        top_news_description = news_json["items"][0]["description"]

        # HTML 태그 제거 (<b>, </b> 같은 거)
        top_news_description = top_news_description.replace("<b>", "").replace("</b>", "")
        print(f"TTS로 변환할 텍스트: {top_news_description}")

    except (IndexError, KeyError):
        raise HTTPException(status_code=500, detail="뉴스 요약(description)을 추출하는데 실패했습니다.")

    # 3. gTTS로 mp3 파일 생성
    try:
        tts = gTTS(text=top_news_description, lang='ko')
        file_path = "temp_news_tts.mp3"
        tts.save(file_path)

        # 4. mp3 파일 바로 반환
        return FileResponse(path=file_path, media_type='audio/mpeg', filename='news_tts.mp3')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"gTTS 변환 실패: {e}")


# --- 네이버 뉴스 API (내부 호출용 함수로 분리) ---
NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"


async def get_naver_news_internal(query: str, display: int):
    headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    params = {"query": query, "display": display, "sort": "sim"}
    try:
        response = requests.get(NAVER_NEWS_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"네이버 API 호출 실패: {e}")


@app.get("/api/news/major")
async def get_major_news(query: str = "경제"):
    # (이제는 내부 함수를 호출해서 10개 가져옴)
    return await get_naver_news_internal(query, 10)


# --- [OLD] 키워드 저장/조회 API ---
@app.post("/api/user/keywords")
async def save_user_keywords(request_body: KeywordsRequest):
    global temp_user_keywords
    temp_user_keywords = request_body.keywords
    return {"message": "키워드 저장 성공", "saved_keywords": temp_user_keywords}


@app.get("/api/user/keywords")
async def get_user_keywords():
    return {"keywords": temp_user_keywords}


# --- [OLD] OpenAI 요약 API ---
@app.post("/api/summary")
async def get_summary(request_body: SummaryRequest):
    # (코드는 이전과 동일... 생략)
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="서버에 OpenAI API 키가 설정되지 않았습니다.")
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(model="gpt-3.5-turbo", messages=[
            {"role": "system", "content": "너는 뉴스 기사를 3문장으로 요약해주는 전문 요약 봇이야."},
            {"role": "user", "content": request_body.text}])
        summary_text = completion.choices[0].message.content
        return {"summary": summary_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API 호출 실패: {e}")


# --- [OLD] TTS 기능 API ---
@app.get("/api/tts")
async def get_tts(text: str = "텍스트를 입력하세요"):
    # (코드는 이전과 동일... 생략)
    try:
        tts = gTTS(text=text, lang='ko')
        file_path = "temp_audio.mp3"
        tts.save(file_path)
        return FileResponse(path=file_path, media_type='audio/mpeg', filename='speech.mp3')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 생성 실패: {e}")


# --- [OLD] 서버 생존 확인용 ---
@app.get("/")
async def read_root():
    return {"message": "최종 PoC 서버 (뉴스+TTS+요약+키워드+숏폼) 실행 중입니다."}