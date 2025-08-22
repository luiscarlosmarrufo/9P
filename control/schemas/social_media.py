"""
Pydantic schemas for social media API endpoints
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


# Brand schemas
class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    keywords: Optional[List[str]] = None


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None


class Brand(BrandBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool


# Social Post schemas
class SocialPostBase(BaseModel):
    platform: str = Field(..., regex="^(twitter|reddit)$")
    platform_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    author: Optional[str] = None
    author_id: Optional[str] = None
    language: Optional[str] = None
    posted_at: datetime
    likes: int = 0
    shares: int = 0
    comments: int = 0
    raw_data: Optional[Dict[str, Any]] = None


class SocialPostCreate(SocialPostBase):
    brand_id: UUID


class SocialPost(SocialPostBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    brand_id: UUID
    scraped_at: datetime
    is_processed: bool
    processing_error: Optional[str] = None
    s3_key: Optional[str] = None


# Classification schemas
class ClassificationBase(BaseModel):
    # 9P scores (0.0 to 1.0)
    product: float = Field(0.0, ge=0.0, le=1.0)
    place: float = Field(0.0, ge=0.0, le=1.0)
    price: float = Field(0.0, ge=0.0, le=1.0)
    publicity: float = Field(0.0, ge=0.0, le=1.0)
    postconsumption: float = Field(0.0, ge=0.0, le=1.0)
    purpose: float = Field(0.0, ge=0.0, le=1.0)
    partnerships: float = Field(0.0, ge=0.0, le=1.0)
    people: float = Field(0.0, ge=0.0, le=1.0)
    planet: float = Field(0.0, ge=0.0, le=1.0)
    
    # Sentiment scores
    sentiment_positive: float = Field(0.0, ge=0.0, le=1.0)
    sentiment_neutral: float = Field(0.0, ge=0.0, le=1.0)
    sentiment_negative: float = Field(0.0, ge=0.0, le=1.0)
    sentiment_label: str = Field(..., regex="^(pos|neu|neg)$")


class ClassificationCreate(ClassificationBase):
    social_post_id: UUID
    brand_id: UUID
    stage: int = Field(..., ge=1, le=2)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: Optional[str] = None
    llm_response: Optional[Dict[str, Any]] = None
    llm_reasoning: Optional[str] = None


class Classification(ClassificationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    social_post_id: UUID
    brand_id: UUID
    stage: int
    confidence_score: Optional[float]
    model_version: Optional[str]
    classified_at: datetime
    llm_response: Optional[Dict[str, Any]]
    llm_reasoning: Optional[str]


# Ingestion request schemas
class TwitterIngestRequest(BaseModel):
    brand_id: UUID
    query: str = Field(..., min_length=1, max_length=500)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_results: int = Field(100, ge=1, le=1000)
    include_retweets: bool = False


class RedditIngestRequest(BaseModel):
    brand_id: UUID
    subreddits: List[str] = Field(..., min_items=1, max_items=10)
    query: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_results: int = Field(100, ge=1, le=1000)
    sort: str = Field("relevance", regex="^(relevance|hot|top|new)$")


# Classification request schemas
class ClassificationRequest(BaseModel):
    brand_id: Optional[UUID] = None
    platform: Optional[str] = Field(None, regex="^(twitter|reddit)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    force_reprocess: bool = False
    batch_size: int = Field(32, ge=1, le=100)


# Summary schemas
class MonthlySummaryRequest(BaseModel):
    brand_id: Optional[UUID] = None
    platform: Optional[str] = Field(None, regex="^(twitter|reddit)$")
    year: int = Field(..., ge=2020, le=2030)
    month: int = Field(..., ge=1, le=12)


class MonthlySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    brand_id: UUID
    platform: str
    year: int
    month: int
    total_posts: int
    processed_posts: int
    
    # 9P averages
    avg_product: float
    avg_place: float
    avg_price: float
    avg_publicity: float
    avg_postconsumption: float
    avg_purpose: float
    avg_partnerships: float
    avg_people: float
    avg_planet: float
    
    # Sentiment counts
    positive_count: int
    neutral_count: int
    negative_count: int
    avg_sentiment_score: float
    
    # Engagement totals
    total_likes: int
    total_shares: int
    total_comments: int
    
    calculated_at: datetime


# Query schemas
class ItemsQuery(BaseModel):
    brand_id: Optional[UUID] = None
    platform: Optional[str] = Field(None, regex="^(twitter|reddit)$")
    sentiment: Optional[str] = Field(None, regex="^(pos|neu|neg)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    nine_p_filter: Optional[str] = Field(
        None, 
        regex="^(product|place|price|publicity|postconsumption|purpose|partnerships|people|planet)$"
    )
    min_nine_p_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class ItemsResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


# Export schemas
class ExportRequest(BaseModel):
    brand_id: Optional[UUID] = None
    platform: Optional[str] = Field(None, regex="^(twitter|reddit)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_raw_data: bool = False
    include_classifications: bool = True
    format: str = Field("csv", regex="^(csv|json)$")


# Response schemas
class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: str
    redis: str
    s3: str


class MetricsResponse(BaseModel):
    total_posts: int
    processed_posts: int
    pending_classifications: int
    active_brands: int
    storage_usage_gb: float
    uptime_seconds: float
