"""
Summary and analytics endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, extract

from control.core.database import get_db
from control.schemas import MonthlySummaryRequest, MonthlySummary
from control.models import MonthlyAggregate, Brand

router = APIRouter()


@router.get("/summary/monthly", response_model=List[MonthlySummary])
async def get_monthly_summary(
    brand_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None, regex="^(twitter|reddit)$"),
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db)
):
    """
    Get monthly summary statistics
    """
    query = db.query(MonthlyAggregate).filter(
        and_(
            MonthlyAggregate.year == year,
            MonthlyAggregate.month == month
        )
    )
    
    if brand_id:
        # Verify brand exists
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        query = query.filter(MonthlyAggregate.brand_id == brand_id)
    
    if platform:
        query = query.filter(MonthlyAggregate.platform == platform)
    
    summaries = query.all()
    
    if not summaries:
        raise HTTPException(
            status_code=404, 
            detail=f"No summary data found for {year}-{month:02d}"
        )
    
    return summaries


@router.get("/summary/trends")
async def get_trends(
    brand_id: str,
    platform: Optional[str] = Query(None, regex="^(twitter|reddit)$"),
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """
    Get trend data for the last N months
    """
    # Verify brand exists
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    query = db.query(MonthlyAggregate).filter(
        MonthlyAggregate.brand_id == brand_id
    ).order_by(
        MonthlyAggregate.year.desc(),
        MonthlyAggregate.month.desc()
    ).limit(months)
    
    if platform:
        query = query.filter(MonthlyAggregate.platform == platform)
    
    trends = query.all()
    
    # Calculate trend metrics
    trend_data = []
    for aggregate in reversed(trends):  # Reverse to get chronological order
        trend_data.append({
            "period": f"{aggregate.year}-{aggregate.month:02d}",
            "total_posts": aggregate.total_posts,
            "processed_posts": aggregate.processed_posts,
            "sentiment_distribution": {
                "positive": aggregate.positive_count,
                "neutral": aggregate.neutral_count,
                "negative": aggregate.negative_count
            },
            "nine_p_scores": {
                "product": aggregate.avg_product,
                "place": aggregate.avg_place,
                "price": aggregate.avg_price,
                "publicity": aggregate.avg_publicity,
                "postconsumption": aggregate.avg_postconsumption,
                "purpose": aggregate.avg_purpose,
                "partnerships": aggregate.avg_partnerships,
                "people": aggregate.avg_people,
                "planet": aggregate.avg_planet
            },
            "engagement": {
                "total_likes": aggregate.total_likes,
                "total_shares": aggregate.total_shares,
                "total_comments": aggregate.total_comments,
                "avg_engagement": (
                    aggregate.total_likes + aggregate.total_shares + aggregate.total_comments
                ) / max(aggregate.total_posts, 1)
            }
        })
    
    return {
        "brand_name": brand.name,
        "platform": platform or "all",
        "period_count": len(trend_data),
        "trends": trend_data
    }


@router.get("/summary/comparison")
async def compare_brands(
    brand_ids: List[str] = Query(...),
    platform: Optional[str] = Query(None, regex="^(twitter|reddit)$"),
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db)
):
    """
    Compare multiple brands for a given period
    """
    if len(brand_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 brands can be compared")
    
    # Verify all brands exist
    brands = db.query(Brand).filter(Brand.id.in_(brand_ids)).all()
    if len(brands) != len(brand_ids):
        raise HTTPException(status_code=404, detail="One or more brands not found")
    
    # Get aggregates for all brands
    query = db.query(MonthlyAggregate).filter(
        and_(
            MonthlyAggregate.brand_id.in_(brand_ids),
            MonthlyAggregate.year == year,
            MonthlyAggregate.month == month
        )
    )
    
    if platform:
        query = query.filter(MonthlyAggregate.platform == platform)
    
    aggregates = query.all()
    
    # Group by brand
    brand_data = {}
    brand_lookup = {str(b.id): b.name for b in brands}
    
    for aggregate in aggregates:
        brand_id = str(aggregate.brand_id)
        if brand_id not in brand_data:
            brand_data[brand_id] = {
                "brand_name": brand_lookup[brand_id],
                "platforms": {}
            }
        
        brand_data[brand_id]["platforms"][aggregate.platform] = {
            "total_posts": aggregate.total_posts,
            "processed_posts": aggregate.processed_posts,
            "sentiment_distribution": {
                "positive": aggregate.positive_count,
                "neutral": aggregate.neutral_count,
                "negative": aggregate.negative_count
            },
            "nine_p_scores": {
                "product": aggregate.avg_product,
                "place": aggregate.avg_place,
                "price": aggregate.avg_price,
                "publicity": aggregate.avg_publicity,
                "postconsumption": aggregate.avg_postconsumption,
                "purpose": aggregate.avg_purpose,
                "partnerships": aggregate.avg_partnerships,
                "people": aggregate.avg_people,
                "planet": aggregate.avg_planet
            },
            "engagement": {
                "total_likes": aggregate.total_likes,
                "total_shares": aggregate.total_shares,
                "total_comments": aggregate.total_comments
            }
        }
    
    return {
        "period": f"{year}-{month:02d}",
        "platform": platform or "all",
        "brands": brand_data
    }
