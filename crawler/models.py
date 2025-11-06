from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Book(BaseModel):
    source_url: str
    name: str
    description: Optional[str]
    category: Optional[str]
    price_including_tax: Optional[float]
    price_excluding_tax: Optional[float]
    availability: Optional[str]
    num_reviews: Optional[int]
    image_url: Optional[str]
    rating: Optional[int]
    crawl_timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_html: Optional[str]
