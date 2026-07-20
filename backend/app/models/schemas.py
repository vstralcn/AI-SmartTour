"""Pydantic schemas for API request/response"""

from pydantic import BaseModel, Field

# ---- Session ----


class CreateSessionRequest(BaseModel):
    visitor_id: str | None = None
    interests: list[str] = Field(default_factory=list)
    age_group: str = "成人"
    companions: list[str] = Field(default_factory=list)
    mobility: str = "标准"
    visit_duration: float = Field(default=3.0, ge=0.5, le=12)


class CreateSessionResponse(BaseModel):
    session_id: str
    greeting: str


# ---- Chat ----

class ChatMessageIn(BaseModel):
    type: str = "text"  # "text" | "audio"
    content: str
    session_id: str


class ChatMessageOut(BaseModel):
    type: str
    content: object
    done: bool = False


# ---- Route Recommend ----

class RouteRecommendRequest(BaseModel):
    session_id: str
    duration_hours: float = 3
    interests: list[str] = Field(default_factory=list)
    companions: list[str] = Field(default_factory=list)
    mobility: str = "标准"


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
    kind: str = "document"
    source: str = ""
    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class KnowledgeDocCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(default="景区知识", max_length=80)
    content: str = Field(min_length=1)
    kind: str = "document"
    source: str = ""
    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class KnowledgeDocUpdate(KnowledgeDocCreate):
    status: str = "active"


class KnowledgeTestRequest(BaseModel):
    question: str


class KnowledgeEvidenceSchema(BaseModel):
    title: str
    category: str
    score: float
    source: str
    excerpt: str


class KnowledgeTestResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float = 0.0
    evidence: list[KnowledgeEvidenceSchema] = Field(default_factory=list)


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
    gender: str = "女"
    clothing: str = "现代导游服"
    speaking_style: str = "亲切自然"
    is_active: bool = False


# ---- TTS ----

class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    voice_id: str = "female-1"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    emotion: str = "neutral"


# ---- Analytics ----

class HotQuestion(BaseModel):
    question: str
    count: int


class ResponseTimePoint(BaseModel):
    date: str
    value: int


class HourlyVisit(BaseModel):
    hour: int
    count: int


class SpotPopularity(BaseModel):
    name: str
    visits: int


class RoutePreference(BaseModel):
    name: str
    count: int


class DashboardData(BaseModel):
    today_visitors: int
    weekly_visitors: int
    total_sessions: int
    avg_response_ms: int
    knowledge_gap_count: int
    negative_feedback_count: int
    hot_questions: list[HotQuestion]
    response_time_trend: list[ResponseTimePoint]
    hourly_visits: list[HourlyVisit]
    spot_popularity: list[SpotPopularity]
    route_preferences: list[RoutePreference]
    data_source: str
    generated_at: str


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


# ---- Admin Auth ----


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: int
