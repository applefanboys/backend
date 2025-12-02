from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class NewsArticle(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    published_at: datetime
    source: Optional[str] = None

class PersonalizedNewsResponse(BaseModel):
    user_id: int
    days: int
    total: int
    articles: List[NewsArticle]
