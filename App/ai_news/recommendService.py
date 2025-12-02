# App/news/recommendation.py
from datetime import datetime, timezone
from typing import List, Dict, Any
from dateutil import parser as date_parser  # pip install python-dateutil

from App.api.naverNewsAPI import fetch_naver_news_recent
from .schemas import NewsArticle


def score_article(article: Dict[str, Any], user_keywords: List[str], days: int) -> float:
    """
    - 최신일수(0~days)와
    - 제목/설명에 포함된 키워드 수
    로 간단한 점수를 계산
    """
    title = (article.get("title") or "").lower()
    # 네이버 결과에는 "summary"가 있으므로, description이 없으면 summary를 사용
    description = (
        article.get("description")
        or article.get("summary")
        or ""
    ).lower()

    # 키워드 매칭 수
    kw_score = 0
    for kw in user_keywords:
        k = kw.lower()
        if k in title or k in description:
            kw_score += 1

    # 발행일 기준 최신 점수
    # 네이버 래퍼가 "published_at"에 pubDate 문자열을 넣어줌
    published_str = (
        article.get("publishedAt")
        or article.get("published_at")
        or article.get("published_at".lower())
    )
    try:
        published_dt = date_parser.parse(published_str)
        if published_dt.tzinfo is None:
            published_dt = published_dt.replace(tzinfo=timezone.utc)
    except Exception:
        published_dt = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    age_days = (now - published_dt).days
    recency_score = max(0, days - age_days)  # 3일 이내면 3,2,1 정도

    # 최종 점수 (가중치는 상황에 맞게 조절)
    return kw_score * 2 + recency_score


def get_personalized_articles(
    user_keywords: List[str],
    days: int = 3,
    per_keyword: int = 5,
    limit: int = 20,
) -> List[NewsArticle]:
    if not user_keywords:
        return []

    raw_articles: List[Dict[str, Any]] = []

    # 1) 키워드별로 뉴스 긁어오기 (네이버 API 재사용)
    for kw in user_keywords:
        articles = fetch_naver_news_recent(
            query=kw,
            days=days,
            max_pages=1,          # 키워드당 1페이지 정도만
            display=per_keyword,  # 키워드당 per_keyword개
        )
        raw_articles.extend(articles)

    # 2) URL 기준으로 중복 제거
    unique_by_url: Dict[str, Dict[str, Any]] = {}
    for art in raw_articles:
        url = art.get("origin_url") or art.get("url")
        if not url:
            continue
        if url not in unique_by_url:
            unique_by_url[url] = art

    deduped_articles = list(unique_by_url.values())

    # 3) 스코어 계산
    scored: List[tuple[float, Dict[str, Any]]] = []
    for art in deduped_articles:
        score = score_article(art, user_keywords, days)
        scored.append((score, art))

    # 4) 점수 순으로 정렬 후 상위 limit개 선택
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [a for _, a in scored[:limit]]

    result: List[NewsArticle] = []
    for art in top:
        published_str = (
            art.get("publishedAt")
            or art.get("published_at")
        )
        try:
            published_dt = date_parser.parse(published_str)
        except Exception:
            published_dt = datetime.utcnow()

        # 네이버 응답의 "summary"를 NewsArticle.description에 매핑
        description = art.get("description") or art.get("summary")

        # 네이버 응답의 "source"는 문자열이므로 그대로 사용
        src = art.get("source")
        if isinstance(src, dict):
            src_name = src.get("name")
        else:
            src_name = src

        result.append(
            NewsArticle(
                title=art.get("title", ""),
                description=description,
                url=art.get("origin_url") or art.get("url", ""),
                published_at=published_dt,
                source=src_name,
            )
        )

    return result
