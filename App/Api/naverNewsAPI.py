import os, time, re, html
from asyncio import timeout
from typing import List, Dict
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv

import requests

# search_keyword = STOCK_QUERY

# 네이버 검색 API
load_dotenv()
client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")

if not client_id or not client_secret:
    raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 설정되지 않았습니다.")

BASE_URL = "https://openapi.naver.com/v1/search/news.json"

# API 기본 설정
# 네이버 뉴스 검색 API의 엔드포인트를 설정
# 헤더에 Client ID/Secret을 넣어야 요청이 허용됨
HEADERS = {
    "X-Naver-Client-Id" : client_id,
    "X-Naver-Client-Secret" : client_secret,
    "User-Agent" : "news-fetcher/1.0"
}

# 텍스트 정제 함수
# 네이버 API결과에는 <b>삼성전자</b>와 같은 강조 태그 존재
# 그걸 제거하고 깔끔한 문자열로 변경
def clean_text(s: str) -> str:
    if not s:
        return s
    s = re.sub(r"<\/?b", "", s) #<b>...<b> 제거
    s = re.sub(r"<[^>]+>", "", s).strip() # 잔여 태그 제거
    s = html.unescape(s) # &quto; 등 엔티티 해제
    s = re.sub(r"\s+", " ", s).strip()
    return s

# 날짜 필터 함수
# 뉴스의 pubDate 값이 "Mon, ~" 으로 오기 때문에, parsedate_to_datetime()으로 datetime으로 변경
# 그 날짜가 오늘(datetime.now())과 같으면 True 반환
def is_today_kst(pub_date: str) -> bool:
    """
    pubDate 예: "Mon, 10 Nov 2025 10:25:00 +0900'
    """
    try:
        dt = parsedate_to_datetime(pub_date)
        # 네이버는 타임존 포함 -> 그대로 한국시간 날짜 비교 가능
        kst_date = dt.date() # tz-aware
        today_kst = datetime.now(dt.tzinfo).date()
        return kst_date == today_kst
    except Exception:
        return False

def is_within_days_kst(pub_date: str, days: int = 3) -> bool:
    """
    pubDate 예: "Mon, 13 Nov 2025 10:25:00 +0900"
    최근 `days`일 안(오늘 프함)이면 True.
    days=3이면: 오늘, 어제, 그제까지 허용.
    """
    try:
        dt = parsedate_to_datetime(pub_date) # tz-aware datetime
        news_date = dt.date() # 뉴스 날짜
        today = datetime.now(dt.tzinfo).date() # 같은 타임존 기준 오늘 날짜

        diff_days = (today - news_date).days
        # 0: 오늘, 1: 어제, 2: 그제
        return 0 <= diff_days < days
    except Exception:
        return False

# 실제 뉴스 수집 부분
# 한 번 호출에 최대 100건(display = 100)
# sort=date 최신순 정렬
# max_pages 300개까지 가능
def fetch_news_today(query: str, max_pages: int = 3, display: int = 100) -> List[Dict]:
    results: List[Dict] = []
    start = 1
    pages = 0

    while pages < max_pages:
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort" : "date" # 최신순
        }
        try:
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout = 8)
        except requests.RequestException as e:
            print(f"[ERR] request failed: {e}")
            return []

        if resp.status_code == 429:
            # 레이트리밋 대응 (간단 백오프(?))
            time.sleep(1.0)
            continue
        if not resp.ok:
            print(f"[ERR] status={resp.status_code}, body={resp.text[:200]}")
            return []

        data = resp.json()
        items = data.get("items", [])
        if not items:
            break

        # 오늘 뉴스만 저장
        # is_today_kst() 결과가 True인 뉴스만 추가
        for it in items:
            pub = it.get("pubDate","")
            if not is_within_days_kst(pub, days=3):
                continue

            results.append({
                "title": clean_text(it.get("title")),
                "summary": clean_text(it.get("description")),
                "published_at": it.get("pubDate"),
                "source": clean_text(it.get("originallink") or ""),
                "url": it.get("link"),
                "origin_url": it.get("originallink"),
            })

        total = data.get("total", 0)
        # 다음 페이지로
        pages += 1
        start += display
        if start > total:
            break

        time.sleep(0.2)

    # 중복 제거 (origin_url 우선, 없으면 url로)
    seen = set()
    deduped = []
    for row in results:
        key = row["origin_url"] or row["url"]
        if key and key not in seen:
            seen.add(key)
            deduped.append(row)

    return deduped

    if __name__ == "__main__":
        rows = fetch_news_today("오늘의 주요 경제뉴스")
        print(f"Fetched {len(rows)} items (today).")
        # 예 : pandas로 저장
        try:
            import pandas as pd
            df = pd.DataFrame(rows, columns=["title", "summary", "published_at", "source", "url", "origin_url"])
            df.to_csv("today_economy.csv", index=False, encoding="utf-8-sig")
            print("Saved: today_economy_news.csv")
        except Exception as e:
            print(f"[WARN] pandas not installed or save failed: {e}")