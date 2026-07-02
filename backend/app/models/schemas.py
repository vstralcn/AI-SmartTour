"""Pydantic schemas for API request/response"""

from pydantic import BaseModel, Field


# ---- Session ----

class CreateSessionRequest(BaseModel):
    visitor_id: str | None = None
    interests: list[str] = Field(default_factory=list)


class CreateSessionResponse(BaseModel):
    session_id: str
    greeting: str


# ---- Chat ----

class ChatMessageIn(BaseModel):
    type: str = "text"  # "text" | "audio"
    content: str
    session_id: str


class ChatMessageOut(BaseModel):
    type: str  # "text_chunk" | "audio_chunk" | "emotion"
    content: str
    done: bool = False


# ---- Route Recommend ----

class RouteRecommendRequest(BaseModel):
    session_id: str
    duration_hours: float = 3
    interests: list[str] = Field(default_factory=list)


class ScenicSpotSchema(BaseModel):
    id: str
    name: str
    description: str
    category: str
    recommended_duration: int
    tags: list[str]


class RouteRecommendResponse(BaseModel):
    route: list[ScenicSpotSchema]
    description: str


# ---- Knowledge ----

class KnowledgeDocSchema(BaseModel):
    id: str
    title: str
    category: str
    content: str
    file_path: str
    upload_time: str
    status: str = "active"


class KnowledgeTestRequest(BaseModel):
    question: str


class KnowledgeTestResponse(BaseModel):
    answer: str
    sources: list[str]


# ---- Avatar ----

class AppearanceConfig(BaseModel):
    image_url: str = ""
    style: str = "现代"


class VoiceConfig(BaseModel):
    voice_id: str = "female-1"
    speed: float = 1.0
    pitch: float = 1.0


class AvatarConfigSchema(BaseModel):
    id: str = ""
    name: str = ""
    appearance: AppearanceConfig = Field(default_factory=AppearanceConfig)
    voice_config: VoiceConfig = Field(default_factory=VoiceConfig)
    personality: str = ""
    is_active: bool = False


# ---- Analytics ----

class HotQuestion(BaseModel):
    question: str
    count: int


class SatisfactionPoint(BaseModel):
    date: str
    score: float


class HourlyVisit(BaseModel):
    hour: int
    count: int


class SpotPopularity(BaseModel):
    name: str
    visits: int


class DashboardData(BaseModel):
    today_visitors: int
    weekly_visitors: int
    total_sessions: int
    avg_satisfaction: float
    hot_questions: list[HotQuestion]
    satisfaction_trend: list[SatisfactionPoint]
    hourly_visits: list[HourlyVisit]
    spot_popularity: list[SpotPopularity]


class SentimentTrendPoint(BaseModel):
    date: str
    positive: int
    neutral: int
    negative: int


class TopConcern(BaseModel):
    topic: str
    count: int
    sentiment: str


class SentimentReport(BaseModel):
    positive_ratio: float
    neutral_ratio: float
    negative_ratio: float
    trend: list[SentimentTrendPoint]
    top_concerns: list[TopConcern]
    suggestions: list[str]
