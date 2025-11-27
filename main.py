import os
import json
from fastapi import FastAPI, HTTPException
import google.generativeai as genai
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import random

from pydantic import BaseModel
from typing import List


# --- 데이터 모델 ---
class OnboardingQ1Request(BaseModel):
    categories: List[str]


class OnboardingQ2Request(BaseModel):
    keywords: List[str]


class OnboardingQ3Request(BaseModel):
    keywords: List[str]


app = FastAPI()

# --- API 키 설정 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# [핵심] 스마트 모델 선택기
# 사용 가능한 모델을 찾아서 전역 변수에 저장해둡니다.
CURRENT_MODEL_NAME = "gemini-1.5-flash"  # 기본값 (실패 시 대비)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        # 사용 가능한 모델 목록 조회 (generateContent 지원하는 모델만)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"📋 사용 가능 모델 목록: {available_models}")

        # 우선순위: 1.5-flash -> pro -> 아무거나
        # 모델명은 보통 'models/gemini-1.5-flash' 형태이므로 'gemini-1.5-flash'만 추출하거나 그대로 사용
        if any('gemini-1.5-flash' in m for m in available_models):
            # 리스트에서 정확한 이름 찾기
            CURRENT_MODEL_NAME = next(m for m in available_models if 'gemini-1.5-flash' in m)
        elif any('gemini-pro' in m for m in available_models):
            CURRENT_MODEL_NAME = next(m for m in available_models if 'gemini-pro' in m)
        elif available_models:
            CURRENT_MODEL_NAME = available_models[0]

        # 'models/' 접두사가 있으면 제거 (라이브러리 버전에 따라 필요할 수도 있음)
        # 하지만 보통 full name을 써도 됨. 여기선 안전하게 감지된 이름 그대로 사용.
        print(f"🚀 최종 선택된 모델: {CURRENT_MODEL_NAME}")

    except Exception as e:
        print(f"⚠️ 모델 목록 조회 실패 (기본값 {CURRENT_MODEL_NAME} 사용): {e}")

# --- [메모리 저장소] ---
user_data = {
    "categories": ["전체 경제"],
    "keywords": [],
    "excluded": []
}


# ==========================================
# 1. 온보딩 API
# ==========================================
@app.post("/api/onboarding/q1")
async def save_q1_categories(req: OnboardingQ1Request):
    user_data["categories"] = req.categories
    return {"message": "Q1 저장 완료", "data": user_data["categories"]}


@app.post("/api/onboarding/q2")
async def save_q2_keywords(req: OnboardingQ2Request):
    user_data["keywords"] = req.keywords
    return {"message": "Q2 저장 완료", "data": user_data["keywords"]}


@app.post("/api/onboarding/q3")
async def save_q3_excluded(req: OnboardingQ3Request):
    user_data["excluded"] = req.keywords
    return {"message": "Q3 저장 완료", "data": user_data["excluded"]}


# ==========================================
# 2. 개인화 AI 주식 추천 API
# ==========================================
@app.get("/api/stocks/recommend/personal")
async def recommend_personal_stock():
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API KEY 없음")

    try:
        # 1. 추천 주제 선정
        target_topic = "경제"
        if user_data["keywords"]:
            target_topic = random.choice(user_data["keywords"])
        elif user_data["categories"]:
            target_topic = random.choice(user_data["categories"])

        excluded_str = ", ".join(user_data["excluded"]) if user_data["excluded"] else "없음"

        # 2. AI에게 종목 물어보기 (자동 선택된 모델 사용)
        # [수정: 전역 변수 CURRENT_MODEL_NAME 사용]
        model = genai.GenerativeModel(CURRENT_MODEL_NAME)

        search_prompt = f"""
        사용자는 '{target_topic}' 분야에 관심이 있어.
        단, '{excluded_str}'와 관련된 종목은 절대 추천하지 마.
        한국 주식 시장(KRX)에서 '{target_topic}'와 가장 관련성이 높은 대장주 3개만 찾아줘.

        반드시 아래 JSON 형식으로만 대답해. (마크다운 없이 순수 JSON만)
        [
            {{"name": "종목명", "code": "종목코드(6자리숫자)"}},
            {{"name": "종목명", "code": "종목코드(6자리숫자)"}},
            {{"name": "종목명", "code": "종목코드(6자리숫자)"}}
        ]
        """

        search_resp = model.generate_content(search_prompt)
        cleaned_search = search_resp.text.replace("```json", "").replace("```", "").strip()

        try:
            candidates = json.loads(cleaned_search)
        except:
            candidates = [{"name": "KODEX 200", "code": "069500"}]  # 실패시 기본값

        print(f"AI 후보: {candidates}")

        # 3. 데이터 수집
        candidates_data_str = ""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)
        valid_candidates = []

        for stock in candidates:
            try:
                # 코드 문자열 처리 강화
                code = str(stock.get("code", "")).zfill(6)
                name = stock.get("name", "Unknown")

                df = fdr.DataReader(code, start_date, end_date)
                if not df.empty:
                    start = int(df.iloc[0]['Close'])
                    end = int(df.iloc[-1]['Close'])
                    change = ((end - start) / start) * 100
                    candidates_data_str += f"- {name}({code}): {change:.2f}% 변동\n"
                    valid_candidates.append(name)
            except:
                continue

        if not valid_candidates:
            return {"message": "데이터 조회 실패", "ai_result": "분석할 종목을 찾지 못했습니다."}

        # 4. 최종 분석
        analyze_prompt = f"""
        너는 주식 전문가야. 주제: '{target_topic}'
        후보 데이터:
        {candidates_data_str}

        이 중 가장 투자 매력도가 높은 종목 1개를 추천해줘.

        반드시 아래 JSON 형식으로만 대답해. (마크다운 없이 순수 JSON만)
        {{
            "recommended_stock": "종목명",
            "stock_code": "종목코드",
            "reason": "추천 이유..."
        }}
        """

        final_resp = model.generate_content(analyze_prompt)
        cleaned_final = final_resp.text.replace("```json", "").replace("```", "").strip()

        return {
            "user_interest": target_topic,
            "candidates_found": valid_candidates,
            "ai_result": cleaned_final
        }

    except Exception as e:
        print(f"에러 발생: {e}")
        # 에러 내용을 자세히 보여줌
        raise HTTPException(status_code=500, detail=f"서버 에러: {str(e)}")


@app.get("/")
async def read_root():
    return {"message": f"서버 실행 중 (모델: {CURRENT_MODEL_NAME})"}