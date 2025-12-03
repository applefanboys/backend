from typing import List, Optional
from pydantic import BaseModel

# [NEW] 본문 크롤링 요청용 모델
class ContentRequest(BaseModel):
    url: str

class TopicCard(BaseModel):
    id: int
    title: str
    image_url: Optional[str] = None

class NewsItem(BaseModel):
    id: int
    title: str
    summary: str
    thumbnail_url: Optional[str] = None
    news_url: Optional[str] = None
    date: str
    press: str

class StockTip(BaseModel):
    code: str
    name: str
    description: str
    price: Optional[str] = None
    change: Optional[str] = None

class FeedResponse(BaseModel):
    topics: List[TopicCard]
    news: List[NewsItem]
    trending: List[NewsItem]
    stockTips: List[StockTip]
    fortune: Optional[str] = None