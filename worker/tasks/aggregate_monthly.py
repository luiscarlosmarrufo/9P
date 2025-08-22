"""
Monthly aggregation tasks for calculating summary statistics
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from calendar import monthrange

from celery import current_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, func, extract

from worker.main import celery_app
from control.core.database import engine
from control.models import SocialPost, Classification, Brand, MonthlyAggregate

# Create database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(bind=True)
def calculate_monthly_aggregates(
    self,
    brand_id: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate monthly aggregate statistics for brands and platforms
    """
    db = SessionLocal()
    
    try:
        # Determine time period
        if year and month:
            periods = [(year, month)]
        else:
            # Calculate for the previous month by default
            now = datetime.utcnow()
            if now.month == 1:
                periods = [(now.year - 1, 12)]
            else:
                periods = [(now.year, now.month - 1)]
        
        # Get brands to process
        if brand_id:
            brands = db.query(Brand).filter(Brand.id == brand_id).all()
            if not brands:
                raise ValueError(f"Brand {brand_id} not found")
        else:
            brands = db.query(Brand).filter(Brand.is_active == True).all()
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'message': f'Calculating aggregates for {len(brands)} brands',
                'current': 0,
                'total': len(brands) * len(periods)
            }
        )
        
        processed_count = 0
        results = []
        
        for brand in brands:
            for year, month in periods:
                try:
                    # Calculate aggregates for each platform
                    platforms = ['twitter', 'reddit']
                    
                    for platform in platforms:
                        aggregate_data = calculate_brand_platform_aggregate(
                            db, brand.id, platform, year, month
                        )
                        
                        if aggregate_data['total_posts'] > 0:
                            # Delete existing aggregate if it exists
                            existing = db.query(MonthlyAggregate).filter(
                                and_(
                                    MonthlyAggregate.brand_id == brand.id,
                                    MonthlyAggregate.platform == platform,
                                    MonthlyAggregate.year == year,
                                    MonthlyAggregate.month == month
                                )
                            ).first()
                            
                            if existing:
                                db.delete(existing)
                            
                            # Create new aggregate
                            monthly_aggregate = MonthlyAggregate(
                                id=uuid.uuid4(),
                                brand_id=brand.id,
                                platform=platform,
                                year=year,
                                month=month,
                                **aggregate_data,
                                calculated_at=datetime.utcnow()
                            )
                            
                            db.add(monthly_aggregate)
                            results.append({
                                'brand_name': brand.name,
                                'platform': platform,
                                'year': year,
                                'month': month,
                                'total_posts': aggregate_data['total_posts']
                            })
                    
                    processed_count += 1
                    
                    # Update progress
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'message': f'Processed {brand.name} for {year}-{month:02d}',
                            'current': processed_count,
                            'total': len(brands) * len(periods)
                        }
                    )
                    
                except Exception as e:
                    results.append({
                        'brand_name': brand.name,
                        'year': year,
                        'month': month,
                        'error': str(e)
                    })
                    continue
        
        # Commit all changes
        db.commit()
        
        return {
            'processed_brands': len(brands),
            'processed_periods': len(periods),
            'total_aggregates': len([r for r in results if 'error' not in r]),
            'errors': len([r for r in results if 'error' in r]),
            'results': results,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60, max_retries=3)
    
    finally:
        db.close()


def calculate_brand_platform_aggregate(
    db, brand_id: str, platform: str, year: int, month: int
) -> Dict[str, Any]:
    """
    Calculate aggregate statistics for a specific brand/platform/month
    """
    # Get date range for the month
    start_date = datetime(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    # Base query for posts in the time period
    posts_query = db.query(SocialPost).filter(
        and_(
            SocialPost.brand_id == brand_id,
            SocialPost.platform == platform,
            SocialPost.posted_at >= start_date,
            SocialPost.posted_at <= end_date
        )
    )
    
    # Basic counts
    total_posts = posts_query.count()
    processed_posts = posts_query.filter(SocialPost.is_processed == True).count()
    
    if total_posts == 0:
        return {
            'total_posts': 0,
            'processed_posts': 0,
            'avg_product': 0.0,
            'avg_place': 0.0,
            'avg_price': 0.0,
            'avg_publicity': 0.0,
            'avg_postconsumption': 0.0,
            'avg_purpose': 0.0,
            'avg_partnerships': 0.0,
            'avg_people': 0.0,
            'avg_planet': 0.0,
            'positive_count': 0,
            'neutral_count': 0,
            'negative_count': 0,
            'avg_sentiment_score': 0.0,
            'total_likes': 0,
            'total_shares': 0,
            'total_comments': 0
        }
    
    # Get classifications for the period
    classifications_query = db.query(Classification).join(
        SocialPost, Classification.social_post_id == SocialPost.id
    ).filter(
        and_(
            SocialPost.brand_id == brand_id,
            SocialPost.platform == platform,
            SocialPost.posted_at >= start_date,
            SocialPost.posted_at <= end_date
        )
    )
    
    # Calculate 9P averages
    nine_p_averages = classifications_query.with_entities(
        func.avg(Classification.product).label('avg_product'),
        func.avg(Classification.place).label('avg_place'),
        func.avg(Classification.price).label('avg_price'),
        func.avg(Classification.publicity).label('avg_publicity'),
        func.avg(Classification.postconsumption).label('avg_postconsumption'),
        func.avg(Classification.purpose).label('avg_purpose'),
        func.avg(Classification.partnerships).label('avg_partnerships'),
        func.avg(Classification.people).label('avg_people'),
        func.avg(Classification.planet).label('avg_planet')
    ).first()
    
    # Calculate sentiment distribution
    sentiment_counts = classifications_query.with_entities(
        Classification.sentiment_label,
        func.count(Classification.id).label('count')
    ).group_by(Classification.sentiment_label).all()
    
    sentiment_distribution = {'pos': 0, 'neu': 0, 'neg': 0}
    for sentiment, count in sentiment_counts:
        sentiment_distribution[sentiment] = count
    
    # Calculate average sentiment score
    avg_sentiment = classifications_query.with_entities(
        func.avg(
            Classification.sentiment_positive - Classification.sentiment_negative
        ).label('avg_sentiment')
    ).first()
    
    # Calculate engagement totals
    engagement_totals = posts_query.with_entities(
        func.sum(SocialPost.likes).label('total_likes'),
        func.sum(SocialPost.shares).label('total_shares'),
        func.sum(SocialPost.comments).label('total_comments')
    ).first()
    
    return {
        'total_posts': total_posts,
        'processed_posts': processed_posts,
        'avg_product': float(nine_p_averages.avg_product or 0.0),
        'avg_place': float(nine_p_averages.avg_place or 0.0),
        'avg_price': float(nine_p_averages.avg_price or 0.0),
        'avg_publicity': float(nine_p_averages.avg_publicity or 0.0),
        'avg_postconsumption': float(nine_p_averages.avg_postconsumption or 0.0),
        'avg_purpose': float(nine_p_averages.avg_purpose or 0.0),
        'avg_partnerships': float(nine_p_averages.avg_partnerships or 0.0),
        'avg_people': float(nine_p_averages.avg_people or 0.0),
        'avg_planet': float(nine_p_averages.avg_planet or 0.0),
        'positive_count': sentiment_distribution['pos'],
        'neutral_count': sentiment_distribution['neu'],
        'negative_count': sentiment_distribution['neg'],
        'avg_sentiment_score': float(avg_sentiment.avg_sentiment or 0.0),
        'total_likes': int(engagement_totals.total_likes or 0),
        'total_shares': int(engagement_totals.total_shares or 0),
        'total_comments': int(engagement_totals.total_comments or 0)
    }


@celery_app.task(bind=True)
def calculate_brand_comparison_metrics(
    self,
    brand_ids: List[str],
    year: int,
    month: int
) -> Dict[str, Any]:
    """
    Calculate comparison metrics between multiple brands
    """
    db = SessionLocal()
    
    try:
        # Verify all brands exist
        brands = db.query(Brand).filter(Brand.id.in_(brand_ids)).all()
        if len(brands) != len(brand_ids):
            raise ValueError("One or more brands not found")
        
        comparison_data = {}
        
        for brand in brands:
            brand_metrics = {}
            
            for platform in ['twitter', 'reddit']:
                platform_data = calculate_brand_platform_aggregate(
                    db, brand.id, platform, year, month
                )
                brand_metrics[platform] = platform_data
            
            comparison_data[str(brand.id)] = {
                'brand_name': brand.name,
                'metrics': brand_metrics
            }
        
        return {
            'period': f"{year}-{month:02d}",
            'brands': comparison_data,
            'calculated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise self.retry(exc=e, countdown=30, max_retries=2)
    
    finally:
        db.close()


@celery_app.task(bind=True)
def recalculate_all_aggregates(
    self,
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int
) -> Dict[str, Any]:
    """
    Recalculate all monthly aggregates for a date range
    """
    db = SessionLocal()
    
    try:
        # Generate list of (year, month) tuples
        periods = []
        current_year, current_month = start_year, start_month
        
        while (current_year, current_month) <= (end_year, end_month):
            periods.append((current_year, current_month))
            
            if current_month == 12:
                current_year += 1
                current_month = 1
            else:
                current_month += 1
        
        # Get all active brands
        brands = db.query(Brand).filter(Brand.is_active == True).all()
        
        total_tasks = len(brands) * len(periods)
        processed = 0
        
        current_task.update_state(
            state='PROGRESS',
            meta={
                'message': f'Recalculating {total_tasks} aggregates',
                'current': 0,
                'total': total_tasks
            }
        )
        
        for brand in brands:
            for year, month in periods:
                # Queue individual calculation task
                calculate_monthly_aggregates.apply_async(
                    args=[str(brand.id), year, month]
                )
                
                processed += 1
                
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'message': f'Queued {processed}/{total_tasks} calculations',
                        'current': processed,
                        'total': total_tasks
                    }
                )
        
        return {
            'queued_calculations': total_tasks,
            'brands': len(brands),
            'periods': len(periods),
            'date_range': f"{start_year}-{start_month:02d} to {end_year}-{end_month:02d}",
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise self.retry(exc=e, countdown=60, max_retries=2)
    
    finally:
        db.close()
