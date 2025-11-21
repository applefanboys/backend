from pydantic import BaseModel, HttpUrl
from typing import Optional

class NewsItem(BaseModel):
    title: str
    summary: str
    published_at: str
    source: Optional[str] = None
    url: Optional[HttpUrl] = None
    origin_url: Optional[str] = None