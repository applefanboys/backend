# App/tts/service.py

import os
import random
import json
from typing import Generator, List, Tuple

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from openai import OpenAI
import requests

from App.repository.preferenceRepo import PreferenceRepository
from App.service.preferenceService import Q1_CATEGORIES  # ✅ 여기 중요

from App.user.models import UserOnBoarding  # 타입 힌트용 (선택)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


# ---------------- 공통: 숏폼 스크립트 생성 + TTS 스트림 ---------------- #

def generate_shortform_script(original_text: str, max_chars: int = 180) -> str:
    if not original_text.strip():
        raise ValueError("뉴스 텍스트가 비어 있습니다.")

    system_prompt = (
        "너는 한국어 경제 뉴스 숏폼 스크립트를 쓰는 전문 아나운서야. "
        "스크립트는 차분하고 또렷하게 읽기 좋은 문장으로 작성해. "
        "너무 빠르지 않은 말투를 가정하고, 문장을 적당히 끊어줘. "
        "투자 권유, 매수/매도 조언은 절대 하지 말고, "
        "사실 위주의 간단한 요약과 오늘 시장 분위기 정도만 말해."
    )

    user_prompt = f"""
다음 경제 뉴스를 음성으로 읽기 좋은 한국어 스크립트로 만들어줘.

조건:
- 2~3문장, 최대 {max_chars}자 이내
- 한 문장은 너무 길지 않게 끊어주기
- '~입니다', '~했어요' 같은 존댓말 사용
- 숫자/단위는 듣기 편하게 자연스럽게 읽기 좋게 풀어서 말하기
- 투자 판단이나 종목 추천은 하지 말기

[뉴스 텍스트]
{original_text}
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",  "content": user_prompt},
        ],
        temperature=0.4,
    )

    script = completion.choices[0].message.content.strip()
    if len(script) > max_chars:
        script = script[:max_chars]
    return script


def tts_stream(script: str) -> Generator[bytes, None, None]:
    # TTS에는 진짜 읽을 텍스트만 들어가야 한다
    full_input = script

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        response_format="mp3",
        input=full_input,
    ) as response:
        for chunk in response.iter_bytes(chunk_size=1024):
            if chunk:
                yield chunk


# ---------------- 온보딩 기반 사용자 선호 분석 로직 ---------------- #

def _get_user_onboarding(db: Session, user_id: int) -> UserOnBoarding | None:
    pref_repo = PreferenceRepository(db)
    return pref_repo.get_onboarding(user_id)


def _build_query_keywords_from_onboarding(onboarding: UserOnBoarding) -> Tuple[List[str], List[str]]:
    """
    - Q2: 포함 키워드 (user_onboarding.q2_keywords)
    - Q3: 제외 키워드 (user_onboarding.q3_keywords)
    - Q1: 포함 키워드가 비어있을 때 카테고리 id -> key 기반으로 기본 키워드 세팅
    """
    include_keywords: List[str] = []
    exclude_keywords: List[str] = []

    # ----- Q2: 관심 키워드 (포함) ----- #
    if getattr(onboarding, "q2_keywords", None):
        if isinstance(onboarding.q2_keywords, list):
            include_keywords = [kw for kw in onboarding.q2_keywords if kw]
        else:
            include_keywords = [
                kw.strip()
                for kw in str(onboarding.q2_keywords).split(",")
                if kw.strip()
            ]

    # ----- Q3: 제외 키워드 ----- #
    if getattr(onboarding, "q3_keywords", None):
        if isinstance(onboarding.q3_keywords, list):
            exclude_keywords = [kw for kw in onboarding.q3_keywords if kw]
        else:
            exclude_keywords = [
                kw.strip()
                for kw in str(onboarding.q3_keywords).split(",")
                if kw.strip()
            ]

    # ----- Q1: 카테고리 기반 기본 키워드 보강 ----- #
    # q1_categories = [1, 2, 5] 형태 (id 리스트) 라고 PreferenceRepository에서 저장 중
    if not include_keywords and getattr(onboarding, "q1_categories", None):
        category_ids = onboarding.q1_categories

        if isinstance(category_ids, str):
            try:
                category_ids = json.loads(category_ids)
            except Exception:
                category_ids = [int(category_ids)]

        category_keys: List[str] = []
        for cid in category_ids:
            cat = next((c for c in Q1_CATEGORIES if c.id == cid), None)
            if cat:
                category_keys.append(cat.key)

        for key in category_keys:
            if key == "stock":
                include_keywords += ["주식", "증권", "코스피", "코스닥"]
            elif key == "all_economy":
                include_keywords += ["경제", "물가", "성장률", "금리"]
            elif key == "global_economy":
                include_keywords += ["미국 증시", "연준", "달러", "환율"]

    include_keywords = list(dict.fromkeys(include_keywords))
    exclude_keywords = list(dict.fromkeys(exclude_keywords))

    return include_keywords, exclude_keywords


# ---------------- 네이버 뉴스 API 호출 로직 ---------------- #

def _search_naver_news(query: str, display: int = 10, sort: str = "sim") -> List[dict]:
    """
    네이버 뉴스 검색 API 호출
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        # 테스트용으로는 여기서 예외 던지기보다 더미 기사를 리턴해도 됨
        raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 설정되어 있지 않습니다.")

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": display,
        "sort": sort,
    }

    resp = requests.get(url, headers=headers, params=params, timeout=5)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])
    return items


# ---------------- 최종: user_id → 맞춤형 뉴스 텍스트 ---------------- #

def build_personalized_news_text(db: Session, user_id: int) -> str:
    onboarding = _get_user_onboarding(db, user_id)
    if onboarding is None:
        raise ValueError("해당 사용자에 대한 온보딩 정보가 없습니다.")

    include_keywords, exclude_keywords = _build_query_keywords_from_onboarding(onboarding)

    if not include_keywords:
        include_keywords = ["경제", "증시"]

    query_parts = []
    query_parts.extend(include_keywords)
    query_parts.extend([f"-{kw}" for kw in exclude_keywords])
    query = " ".join(query_parts)

    articles = _search_naver_news(query=query, display=10, sort="sim")

    if not articles:
        raise ValueError("사용자 선호에 맞는 뉴스를 찾지 못했습니다.")

    # 기사 하나 선택
    selected = random.choice(articles)

    title = selected.get("title", "")
    desc = selected.get("description", "")
    origin_link = selected.get("originallink") or selected.get("link")

    for ch in ["<b>", "</b>", "&quot;", "&apos;"]:
        title = title.replace(ch, "")
        desc = desc.replace(ch, "")

    # OG 이미지 URL 추출
    image_url = None
    if origin_link:
        image_url = extract_og_image(origin_link)

    base_text = f"""
제목: {title}
내용: {desc}

(출처: 네이버 뉴스, 원문 링크: {origin_link})
""".strip()

    return {
        "base_text": base_text,  # TTS 스크립트 생성에 쓸 원본 텍스트
        "title": title,
        "description": desc,
        "origin_link": origin_link,
        "image_url": image_url,  # 프론트에서 썸네일로 쓰면 됨
    }

# OG 이미지 추출 함수 만들기
def extract_og_image(url: str) -> str | None:
    try:
        resp = requests.get(url, timeout=2)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.content, "html.parser")
        tag = soup.find("meta", property="og:image")
        if tag and tag.get("content"):
            return tag["content"]

    except Exception:
        return None

    return None
