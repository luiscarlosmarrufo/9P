"""
Database models for social media data
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from control.core.database import Base


class Brand(Base):
    """Brand entity for tracking"""
    __tablename__ = "brands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    keywords = Column(JSON)  # List of keywords to track
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    social_posts = relationship("SocialPost", back_populates="brand")
    classifications = relationship("Classification", back_populates="brand")


class SocialPost(Base):
    """Raw social media posts/comments"""
    __tablename__ = "social_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform = Column(String(50), nullable=False)  # twitter, reddit
    platform_id = Column(String(255), nullable=False)  # Original post ID
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    
    # Content
    text = Column(Text, nullable=False)
    author = Column(String(255))
    author_id = Column(String(255))
    language = Column(String(10))
    
    # Metadata
    posted_at = Column(DateTime, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSON)  # Full API response
    
    # Engagement metrics
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    
    # S3 storage
    s3_key = Column(String(500))  # S3 object key for raw JSON
    
    # Relationships
    brand = relationship("Brand", back_populates="social_posts")
    classifications = relationship("Classification", back_populates="social_post")
    
    # Indexes
    __table_args__ = (
        Index("idx_social_posts_platform_id", "platform", "platform_id"),
        Index("idx_social_posts_brand_posted", "brand_id", "posted_at"),
        Index("idx_social_posts_processing", "is_processed", "scraped_at"),
    )


class Classification(Base):
    """Classification results for social posts"""
    __tablename__ = "classifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    social_post_id = Column(UUID(as_uuid=True), ForeignKey("social_posts.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    
    # 9P Classifications (multi-label)
    product = Column(Float, default=0.0)
    place = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    publicity = Column(Float, default=0.0)
    postconsumption = Column(Float, default=0.0)
    purpose = Column(Float, default=0.0)
    partnerships = Column(Float, default=0.0)
    people = Column(Float, default=0.0)
    planet = Column(Float, default=0.0)
    
    # Sentiment
    sentiment_positive = Column(Float, default=0.0)
    sentiment_neutral = Column(Float, default=0.0)
    sentiment_negative = Column(Float, default=0.0)
    sentiment_label = Column(String(20))  # pos, neu, neg
    
    # Classification metadata
    stage = Column(Integer, nullable=False)  # 1 or 2
    confidence_score = Column(Float)
    model_version = Column(String(50))
    classified_at = Column(DateTime, default=datetime.utcnow)
    
    # Stage 2 specific (vLLM)
    llm_response = Column(JSON)
    llm_reasoning = Column(Text)
    
    # Relationships
    social_post = relationship("SocialPost", back_populates="classifications")
    brand = relationship("Brand", back_populates="classifications")
    
    # Indexes
    __table_args__ = (
        Index("idx_classifications_brand_date", "brand_id", "classified_at"),
        Index("idx_classifications_sentiment", "sentiment_label", "classified_at"),
        Index("idx_classifications_stage", "stage", "confidence_score"),
    )


class MonthlyAggregate(Base):
    """Monthly aggregated statistics"""
    __tablename__ = "monthly_aggregates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    
    # Time period
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # Counts
    total_posts = Column(Integer, default=0)
    processed_posts = Column(Integer, default=0)
    
    # 9P Aggregates (average scores)
    avg_product = Column(Float, default=0.0)
    avg_place = Column(Float, default=0.0)
    avg_price = Column(Float, default=0.0)
    avg_publicity = Column(Float, default=0.0)
    avg_postconsumption = Column(Float, default=0.0)
    avg_purpose = Column(Float, default=0.0)
    avg_partnerships = Column(Float, default=0.0)
    avg_people = Column(Float, default=0.0)
    avg_planet = Column(Float, default=0.0)
    
    # Sentiment Aggregates
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    avg_sentiment_score = Column(Float, default=0.0)
    
    # Engagement Aggregates
    total_likes = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    
    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    brand = relationship("Brand")
    
    # Indexes
    __table_args__ = (
        Index("idx_monthly_agg_brand_period", "brand_id", "year", "month"),
        Index("idx_monthly_agg_platform", "platform", "year", "month"),
    )
