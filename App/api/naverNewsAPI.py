# App/news/naver_news_client.py

import os
import time
import re
import html
from typing import List, Dict, Optional
from datetime import datetime
from email.utils import parsedate_to_datetime

from dotenv import load_dotenv
import requests

# ---------------------------
# 환경변수 / 기본 설정
# ---------------------------

load_dotenv()
client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")

if not client_id or not client_secret:
    raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 설정되지 않았습니다.")

BASE_URL = "https://openapi.naver.com/v1/search/news.json"

HEADERS = {
    "X-Naver-Client-Id": client_id,
    "X-Naver-Client-Secret": client_secret,
    "User-Agent": "news-fetcher/1.0",
}

# ---------------------------
# 유틸 함수들
# ---------------------------

def clean_text(s: Optional[str]) -> str:
    """
    네이버 뉴스 응답의 <b>태그, 기타 HTML 태그, 엔티티 등을 제거해서
    사람이 보기 좋은 텍스트로 정제.
    """
    if not s:
        return ""
    # <b>...</b> 제거
    s = re.sub(r"</?b>", "", s)
    # 나머지 HTML 태그 제거
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)  # &quot; 등 HTML 엔티티 해제
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_within_days_kst(pub_date: str, days: int = 3) -> bool:
    """
    pubDate 예: "Mon, 13 Nov 2025 10:25:00 +0900"
    최근 `days`일 안(오늘 포함)이면 True.
    days=3이면: 오늘(0), 어제(1), 그제(2)까지 허용.
    """
    try:
        dt = parsedate_to_datetime(pub_date)  # tz-aware datetime
        news_date = dt.date()
        today = datetime.now(dt.tzinfo).date()  # 같은 타임존 기준 오늘 날짜

        diff_days = (today - news_date).days
        return 0 <= diff_days < days
    except Exception:
        return False


# ---------------------------
# 핵심: 재사용 가능한 네이버 뉴스 fetch 함수
# ---------------------------

def fetch_naver_news_recent(
    query: str,
    days: int = 3,
    max_pages: int = 3,
    display: int = 100,
) -> List[Dict]:
    """
    - 네이버 뉴스 검색 API에서 `query`로 검색
    - sort=date (최신순)
    - pubDate 기준으로 최근 `days`일 안에 있는 기사만 필터링
    - 결과는 중복(origin_url 또는 url 기준) 제거 후 Dict 리스트로 반환

    반환 형식 예:
    {
        "title": "...",
        "summary": "...",
        "published_at": "Mon, 13 Nov 2025 10:25:00 +0900",
        "source": "...",
        "url": "...",
        "origin_url": "..."
    }
    """
    results: List[Dict] = []
    start = 1
    pages = 0

    while pages < max_pages:
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": "date",  # 최신순
        }
        try:
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=8)
        except requests.RequestException as e:
            print(f"[ERR] Naver request failed: {e}")
            break

        if resp.status_code == 429:
            # 레이트리밋: 간단한 백오프
            time.sleep(1.0)
            continue

        if not resp.ok:
            print(f"[ERR] status={resp.status_code}, body={resp.text[:200]}")
            break

        data = resp.json()
        items = data.get("items", [])
        if not items:
            break

        for it in items:
            pub = it.get("pubDate", "")
            if not is_within_days_kst(pub, days=days):
                continue  # 최근 days일 밖이면 버림

            results.append(
                {
                    "title": clean_text(it.get("title")),
                    "summary": clean_text(it.get("description")),
                    "published_at": it.get("pubDate"),
                    # 네이버는 별도의 source name 필드는 없어서
                    # originallink(언론사 페이지)를 그대로 source로 쓰는 정도
                    "source": clean_text(it.get("originallink") or ""),
                    "url": it.get("link"),  # 네이버 뉴스 링크
                    "origin_url": it.get("originallink"),  # 원문 언론사 링크
                }
            )

        total = data.get("total", 0)

        pages += 1
        start += display
        if start > total:
            break

        time.sleep(0.2)

    # 중복 제거 (origin_url 우선, 없으면 url로)
    seen = set()
    deduped: List[Dict] = []
    for row in results:
        key = row["origin_url"] or row["url"]
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    return deduped


# 간단 테스트용 (로컬 실행 시에만)
if __name__ == "__main__":
    rows = fetch_naver_news_recent("오늘의 주요 경제뉴스", days=3)
    print(f"Fetched {len(rows)} items (within 3 days).")
    for r in rows[:5]:
        print("-", r["published_at"], r["title"])
