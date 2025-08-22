"""
Items query endpoints for social media posts and classifications
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from control.core.database import get_db
from control.schemas import ItemsQuery, ItemsResponse
from control.models import SocialPost, Classification, Brand

router = APIRouter()


@router.get("/items", response_model=ItemsResponse)
async def get_items(
    brand_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None, regex="^(twitter|reddit)$"),
    sentiment: Optional[str] = Query(None, regex="^(pos|neu|neg)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    nine_p_filter: Optional[str] = Query(None),
    min_nine_p_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Query social media items with classifications
    """
    # Build base query joining posts and classifications
    query = db.query(
        SocialPost,
        Classification,
        Brand.name.label('brand_name')
    ).join(
        Classification, SocialPost.id == Classification.social_post_id
    ).join(
        Brand, SocialPost.brand_id == Brand.id
    )
    
    # Apply filters
    filters = []
    
    if brand_id:
        # Verify brand exists
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        filters.append(SocialPost.brand_id == brand_id)
    
    if platform:
        filters.append(SocialPost.platform == platform)
    
    if sentiment:
        filters.append(Classification.sentiment_label == sentiment)
    
    if start_date:
        filters.append(SocialPost.posted_at >= start_date)
    
    if end_date:
        filters.append(SocialPost.posted_at <= end_date)
    
    if min_confidence:
        filters.append(Classification.confidence_score >= min_confidence)
    
    if nine_p_filter and min_nine_p_score:
        # Filter by specific 9P dimension
        nine_p_column = getattr(Classification, nine_p_filter, None)
        if nine_p_column is None:
            raise HTTPException(status_code=400, detail=f"Invalid 9P filter: {nine_p_filter}")
        filters.append(nine_p_column >= min_nine_p_score)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination and ordering
    results = query.order_by(desc(SocialPost.posted_at)).offset(offset).limit(limit).all()
    
    # Format response
    items = []
    for post, classification, brand_name in results:
        item = {
            "id": str(post.id),
            "platform": post.platform,
            "platform_id": post.platform_id,
            "brand_name": brand_name,
            "text": post.text,
            "author": post.author,
            "posted_at": post.posted_at.isoformat(),
            "scraped_at": post.scraped_at.isoformat(),
            "engagement": {
                "likes": post.likes,
                "shares": post.shares,
                "comments": post.comments
            },
            "classification": {
                "nine_p": {
                    "product": classification.product,
                    "place": classification.place,
                    "price": classification.price,
                    "publicity": classification.publicity,
                    "postconsumption": classification.postconsumption,
                    "purpose": classification.purpose,
                    "partnerships": classification.partnerships,
                    "people": classification.people,
                    "planet": classification.planet
                },
                "sentiment": {
                    "label": classification.sentiment_label,
                    "scores": {
                        "positive": classification.sentiment_positive,
                        "neutral": classification.sentiment_neutral,
                        "negative": classification.sentiment_negative
                    }
                },
                "metadata": {
                    "stage": classification.stage,
                    "confidence_score": classification.confidence_score,
                    "model_version": classification.model_version,
                    "classified_at": classification.classified_at.isoformat()
                }
            }
        }
        
        # Add LLM reasoning if available (Stage 2)
        if classification.llm_reasoning:
            item["classification"]["llm_reasoning"] = classification.llm_reasoning
        
        items.append(item)
    
    return ItemsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/items/{item_id}")
async def get_item_detail(
    item_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific item
    """
    # Query for the specific item
    result = db.query(
        SocialPost,
        Classification,
        Brand.name.label('brand_name')
    ).join(
        Classification, SocialPost.id == Classification.social_post_id
    ).join(
        Brand, SocialPost.brand_id == Brand.id
    ).filter(
        SocialPost.id == item_id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    
    post, classification, brand_name = result
    
    # Build detailed response
    detail = {
        "id": str(post.id),
        "platform": post.platform,
        "platform_id": post.platform_id,
        "brand_name": brand_name,
        "brand_id": str(post.brand_id),
        "text": post.text,
        "author": post.author,
        "author_id": post.author_id,
        "language": post.language,
        "posted_at": post.posted_at.isoformat(),
        "scraped_at": post.scraped_at.isoformat(),
        "engagement": {
            "likes": post.likes,
            "shares": post.shares,
            "comments": post.comments
        },
        "processing": {
            "is_processed": post.is_processed,
            "processing_error": post.processing_error,
            "s3_key": post.s3_key
        },
        "classification": {
            "id": str(classification.id),
            "nine_p": {
                "product": classification.product,
                "place": classification.place,
                "price": classification.price,
                "publicity": classification.publicity,
                "postconsumption": classification.postconsumption,
                "purpose": classification.purpose,
                "partnerships": classification.partnerships,
                "people": classification.people,
                "planet": classification.planet
            },
            "sentiment": {
                "label": classification.sentiment_label,
                "scores": {
                    "positive": classification.sentiment_positive,
                    "neutral": classification.sentiment_neutral,
                    "negative": classification.sentiment_negative
                }
            },
            "metadata": {
                "stage": classification.stage,
                "confidence_score": classification.confidence_score,
                "model_version": classification.model_version,
                "classified_at": classification.classified_at.isoformat(),
                "llm_response": classification.llm_response,
                "llm_reasoning": classification.llm_reasoning
            }
        }
    }
    
    # Include raw data if available
    if post.raw_data:
        detail["raw_data"] = post.raw_data
    
    return detail


@router.get("/items/stats")
async def get_items_stats(
    brand_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None, regex="^(twitter|reddit)$"),
    db: Session = Depends(get_db)
):
    """
    Get statistics about items in the database
    """
    # Base query
    query = db.query(SocialPost)
    
    if brand_id:
        # Verify brand exists
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        query = query.filter(SocialPost.brand_id == brand_id)
    
    if platform:
        query = query.filter(SocialPost.platform == platform)
    
    # Get basic counts
    total_posts = query.count()
    processed_posts = query.filter(SocialPost.is_processed == True).count()
    unprocessed_posts = total_posts - processed_posts
    
    # Get classification stats
    classification_query = db.query(Classification)
    if brand_id:
        classification_query = classification_query.filter(Classification.brand_id == brand_id)
    
    stage_1_classifications = classification_query.filter(Classification.stage == 1).count()
    stage_2_classifications = classification_query.filter(Classification.stage == 2).count()
    
    # Get sentiment distribution
    sentiment_stats = db.query(
        Classification.sentiment_label,
        func.count(Classification.id).label('count')
    ).group_by(Classification.sentiment_label)
    
    if brand_id:
        sentiment_stats = sentiment_stats.filter(Classification.brand_id == brand_id)
    
    sentiment_distribution = {row.sentiment_label: row.count for row in sentiment_stats.all()}
    
    return {
        "total_posts": total_posts,
        "processed_posts": processed_posts,
        "unprocessed_posts": unprocessed_posts,
        "processing_rate": processed_posts / max(total_posts, 1),
        "classifications": {
            "stage_1": stage_1_classifications,
            "stage_2": stage_2_classifications,
            "total": stage_1_classifications + stage_2_classifications
        },
        "sentiment_distribution": sentiment_distribution,
        "filters_applied": {
            "brand_id": brand_id,
            "platform": platform
        }
    }
