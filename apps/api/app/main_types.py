from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventCategory(str, Enum):
    earthquake = "earthquake"
    wildfire = "wildfire"
    flood = "flood"
    storm = "storm"
    volcano = "volcano"


class EventSeverity(str, Enum):
    critical = "critical"
    warning = "warning"
    advisory = "advisory"
    normal = "normal"


class Event(BaseModel):
    id: str
    category: EventCategory
    severity: EventSeverity
    title: str
    location: str
    lat: float
    lon: float
    magnitude: Optional[float] = None
    timestamp: datetime
    source: str
    source_url: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    events: list[Event] = Field(default_factory=list, max_length=100)


class AskResponse(BaseModel):
    answer: str
    mode: str
    sources: list[str]
