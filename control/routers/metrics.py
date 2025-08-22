"""
Metrics and monitoring endpoints
"""

import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import boto3
from botocore.exceptions import ClientError

from control.core.database import get_db
from control.core.config import settings
from control.schemas import MetricsResponse
from control.models import SocialPost, Classification, Brand

router = APIRouter()

# Store startup time for uptime calculation
startup_time = time.time()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(db: Session = Depends(get_db)):
    """
    Get system metrics for monitoring and dashboards
    """
    # Database metrics
    total_posts = db.query(func.count(SocialPost.id)).scalar() or 0
    processed_posts = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_processed == True
    ).scalar() or 0
    pending_classifications = total_posts - processed_posts
    active_brands = db.query(func.count(Brand.id)).filter(
        Brand.is_active == True
    ).scalar() or 0
    
    # Storage usage (S3)
    storage_usage_gb = 0.0
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION
        )
        
        # Get bucket size (this is an approximation)
        response = s3_client.list_objects_v2(Bucket=settings.S3_BUCKET_NAME)
        if 'Contents' in response:
            total_size = sum(obj['Size'] for obj in response['Contents'])
            storage_usage_gb = total_size / (1024 ** 3)  # Convert to GB
    except ClientError:
        # If we can't access S3, just use 0
        pass
    
    # System uptime
    uptime_seconds = time.time() - startup_time
    
    return MetricsResponse(
        total_posts=total_posts,
        processed_posts=processed_posts,
        pending_classifications=pending_classifications,
        active_brands=active_brands,
        storage_usage_gb=storage_usage_gb,
        uptime_seconds=uptime_seconds
    )


@router.get("/metrics/detailed")
async def get_detailed_metrics(db: Session = Depends(get_db)):
    """
    Get detailed metrics for comprehensive monitoring
    """
    # Platform breakdown
    platform_stats = db.query(
        SocialPost.platform,
        func.count(SocialPost.id).label('count'),
        func.count(SocialPost.id).filter(SocialPost.is_processed == True).label('processed')
    ).group_by(SocialPost.platform).all()
    
    platform_metrics = {}
    for stat in platform_stats:
        platform_metrics[stat.platform] = {
            'total_posts': stat.count,
            'processed_posts': stat.processed,
            'processing_rate': stat.processed / max(stat.count, 1)
        }
    
    # Classification stage breakdown
    stage_stats = db.query(
        Classification.stage,
        func.count(Classification.id).label('count')
    ).group_by(Classification.stage).all()
    
    stage_metrics = {f'stage_{stat.stage}': stat.count for stat in stage_stats}
    
    # Sentiment distribution
    sentiment_stats = db.query(
        Classification.sentiment_label,
        func.count(Classification.id).label('count')
    ).group_by(Classification.sentiment_label).all()
    
    sentiment_metrics = {stat.sentiment_label: stat.count for stat in sentiment_stats}
    
    # Brand activity
    brand_stats = db.query(
        Brand.name,
        func.count(SocialPost.id).label('post_count')
    ).join(
        SocialPost, Brand.id == SocialPost.brand_id
    ).group_by(Brand.name).order_by(
        func.count(SocialPost.id).desc()
    ).limit(10).all()
    
    top_brands = [
        {'brand': stat.name, 'post_count': stat.post_count}
        for stat in brand_stats
    ]
    
    # Recent activity (last 24 hours)
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    recent_posts = db.query(func.count(SocialPost.id)).filter(
        SocialPost.scraped_at >= yesterday
    ).scalar() or 0
    
    recent_classifications = db.query(func.count(Classification.id)).filter(
        Classification.classified_at >= yesterday
    ).scalar() or 0
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - startup_time,
        "platform_breakdown": platform_metrics,
        "classification_stages": stage_metrics,
        "sentiment_distribution": sentiment_metrics,
        "top_brands": top_brands,
        "recent_activity": {
            "posts_last_24h": recent_posts,
            "classifications_last_24h": recent_classifications
        }
    }


@router.get("/metrics/prometheus")
async def get_prometheus_metrics(db: Session = Depends(get_db)):
    """
    Get metrics in Prometheus format
    """
    # Get basic metrics
    total_posts = db.query(func.count(SocialPost.id)).scalar() or 0
    processed_posts = db.query(func.count(SocialPost.id)).filter(
        SocialPost.is_processed == True
    ).scalar() or 0
    active_brands = db.query(func.count(Brand.id)).filter(
        Brand.is_active == True
    ).scalar() or 0
    
    # Platform breakdown
    platform_stats = db.query(
        SocialPost.platform,
        func.count(SocialPost.id).label('count')
    ).group_by(SocialPost.platform).all()
    
    # Build Prometheus format
    metrics = []
    
    # Basic counters
    metrics.append(f"ninep_total_posts {total_posts}")
    metrics.append(f"ninep_processed_posts {processed_posts}")
    metrics.append(f"ninep_pending_posts {total_posts - processed_posts}")
    metrics.append(f"ninep_active_brands {active_brands}")
    metrics.append(f"ninep_uptime_seconds {time.time() - startup_time}")
    
    # Platform breakdown
    for stat in platform_stats:
        metrics.append(f'ninep_posts_by_platform{{platform="{stat.platform}"}} {stat.count}')
    
    # Processing rate
    processing_rate = processed_posts / max(total_posts, 1)
    metrics.append(f"ninep_processing_rate {processing_rate}")
    
    return "\n".join(metrics) + "\n"
