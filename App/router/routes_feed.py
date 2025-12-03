import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from App.core.database import get_db

from App.schemas.feed import FeedResponse, NewsItem, TopicCard, StockTip, ContentRequest
from App.ai_news.aiNews_service import build_user_keywords
from App.ai_news.recommendService import get_personalized_articles
# [NEW] AI 요약(대본 작성) 기능을 가져옵니다.
from App.tts.service import generate_shortform_script 

router = APIRouter(prefix="/api/feed", tags=["feed"])

# --- 크롤링 함수 ---
def crawl_news_content(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code != 200: return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        
        content = []
        for p in paragraphs:
            text = p.get_text().strip()
            # 본문일 가능성이 높은 긴 문장만 수집
            if len(text) > 50: 
                content.append(text)
        
        full_text = " ".join(content)
        if len(full_text) < 100: return "" # 너무 짧으면 실패 처리
        return full_text
    except Exception:
        return ""

# [핵심] 실시간 AI 요약 API
@router.post("/content")
def get_news_content(req: ContentRequest):
    # 1. 원문 크롤링
    raw_text = crawl_news_content(req.url)
    
    if not raw_text:
        return {"content": "본문을 불러올 수 없습니다. 원문 링크를 확인해주세요."}
    
    # 2. [중요] 원문을 그대로 주지 않고, AI(GPT)에게 요약을 시킵니다.
    try:
        # 최대 300자 정도의 숏폼 대본으로 요약
        ai_summary = generate_shortform_script(raw_text, max_chars=300)
        return {"content": ai_summary}
    except Exception as e:
        print(f"AI Summary Error: {e}")
        # AI 요약 실패 시 원문 앞부분이라도 반환
        return {"content": raw_text[:300] + "..."}


@router.get("/home", response_model=FeedResponse)
def get_home_feed(user_id: int, db: Session = Depends(get_db)):
    keywords = build_user_keywords(db, user_id)
    if not keywords: keywords = ["경제", "삼성전자"]

    # [수정 1] per_keyword를 30으로 늘려서 100개(limit)를 충분히 채움
    ai_articles = get_personalized_articles(
        user_keywords=keywords, 
        days=3, 
        limit=100, 
        per_keyword=30 
    )

    news_items = []
    for idx, art in enumerate(ai_articles):
        date_str = str(art.published_at)[:10] if art.published_at else ""
        
        # [수정 2] 여기서 크롤링하지 않음! (속도 향상)
        # 네이버 요약문(snippet)을 임시로 넣어두고, 클릭 시 실시간으로 AI 요약본을 가져옵니다.
        temp_summary = art.description or "내용을 불러오려면 클릭하세요."

        news_items.append(NewsItem(
            id=idx,
            title=art.title,
            summary=temp_summary, 
            thumbnail_url="", 
            news_url=str(art.url),
            date=date_str,
            press=art.source or "네이버뉴스"
        ))

    topics = [TopicCard(id=1, title="💰 금리 인하"), TopicCard(id=2, title="🚀 반도체")]
    stock_tips = [StockTip(code="005930", name="삼성전자", description="AI 반도체")]

    return FeedResponse(
        topics=topics, news=news_items, trending=[], stockTips=stock_tips,
        fortune="오늘 당신의 투자 직감이 매우 뛰어납니다!"
    )