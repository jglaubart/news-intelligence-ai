from pydantic import BaseModel
from typing import Optional, List

class TopicRequest(BaseModel):
    topic: str
    days_back: int = 30
    queries_used: Optional[List[str]] = None