"""
Twitter/X data ingestion tasks
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

import tweepy
import boto3
from celery import current_task
from sqlalchemy.orm import sessionmaker

from worker.main import celery_app
from control.core.config import settings
from control.core.database import engine
from control.models import SocialPost, Brand

# Create database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_twitter_client() -> tweepy.Client:
    """Initialize Twitter API client"""
    return tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        consumer_key=settings.TWITTER_API_KEY,
        consumer_secret=settings.TWITTER_API_SECRET,
        access_token=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )


def upload_to_s3(data: Dict[str, Any], key: str) -> str:
    """Upload raw data to S3"""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION
    )
    
    s3_client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=json.dumps(data, default=str),
        ContentType='application/json'
    )
    
    return key


@celery_app.task(bind=True)
def ingest_twitter(
    self,
    brand_id: str,
    query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 100,
    include_retweets: bool = False
) -> Dict[str, Any]:
    """
    Ingest Twitter/X posts for a brand
    """
    db = SessionLocal()
    
    try:
        # Verify brand exists
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise ValueError(f"Brand {brand_id} not found")
        
        # Initialize Twitter client
        client = get_twitter_client()
        
        # Build search query
        search_query = query
        if not include_retweets:
            search_query += " -is:retweet"
        
        # Parse dates
        start_time = datetime.fromisoformat(start_date) if start_date else None
        end_time = datetime.fromisoformat(end_date) if end_date else None
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={'message': f'Searching Twitter for: {search_query}', 'current': 0, 'total': max_results}
        )
        
        # Search tweets
        tweets = tweepy.Paginator(
            client.search_recent_tweets,
            query=search_query,
            start_time=start_time,
            end_time=end_time,
            max_results=min(max_results, 100),  # API limit per request
            tweet_fields=['created_at', 'author_id', 'public_metrics', 'lang', 'context_annotations'],
            user_fields=['username', 'name', 'verified'],
            expansions=['author_id']
        ).flatten(limit=max_results)
        
        processed_count = 0
        new_posts = 0
        errors = []
        
        for tweet in tweets:
            try:
                # Check if tweet already exists
                existing = db.query(SocialPost).filter(
                    SocialPost.platform == "twitter",
                    SocialPost.platform_id == str(tweet.id)
                ).first()
                
                if existing:
                    processed_count += 1
                    continue
                
                # Get author info
                author_info = None
                if hasattr(tweet, 'includes') and 'users' in tweet.includes:
                    author_info = tweet.includes['users'][0]
                
                # Extract metrics
                metrics = tweet.public_metrics or {}
                
                # Create S3 key for raw data
                s3_key = f"twitter/{brand_id}/{datetime.utcnow().strftime('%Y/%m/%d')}/{tweet.id}.json"
                
                # Prepare raw data
                raw_data = {
                    'tweet': tweet.data,
                    'author': author_info.data if author_info else None,
                    'metrics': metrics,
                    'ingested_at': datetime.utcnow().isoformat()
                }
                
                # Upload to S3
                upload_to_s3(raw_data, s3_key)
                
                # Create social post record
                social_post = SocialPost(
                    id=uuid.uuid4(),
                    platform="twitter",
                    platform_id=str(tweet.id),
                    brand_id=brand_id,
                    text=tweet.text,
                    author=author_info.username if author_info else None,
                    author_id=str(tweet.author_id) if tweet.author_id else None,
                    language=tweet.lang,
                    posted_at=tweet.created_at,
                    scraped_at=datetime.utcnow(),
                    likes=metrics.get('like_count', 0),
                    shares=metrics.get('retweet_count', 0),
                    comments=metrics.get('reply_count', 0),
                    raw_data=raw_data,
                    s3_key=s3_key,
                    is_processed=False
                )
                
                db.add(social_post)
                new_posts += 1
                processed_count += 1
                
                # Update progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'message': f'Processed {processed_count}/{max_results} tweets',
                        'current': processed_count,
                        'total': max_results
                    }
                )
                
                # Commit in batches
                if processed_count % 10 == 0:
                    db.commit()
                
            except Exception as e:
                errors.append(f"Error processing tweet {tweet.id}: {str(e)}")
                continue
        
        # Final commit
        db.commit()
        
        result = {
            'brand_id': brand_id,
            'brand_name': brand.name,
            'query': search_query,
            'processed_count': processed_count,
            'new_posts': new_posts,
            'errors': errors,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60, max_retries=3)
    
    finally:
        db.close()


@celery_app.task(bind=True)
def ingest_twitter_batch(
    self,
    requests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process multiple Twitter ingestion requests in batch
    """
    results = []
    
    for i, request in enumerate(requests):
        try:
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'message': f'Processing batch {i+1}/{len(requests)}',
                    'current': i,
                    'total': len(requests)
                }
            )
            
            result = ingest_twitter.apply_async(
                args=[
                    request['brand_id'],
                    request['query'],
                    request.get('start_date'),
                    request.get('end_date'),
                    request.get('max_results', 100),
                    request.get('include_retweets', False)
                ]
            ).get()
            
            results.append(result)
            
        except Exception as e:
            results.append({
                'brand_id': request.get('brand_id'),
                'error': str(e),
                'status': 'failed'
            })
    
    return {
        'batch_size': len(requests),
        'completed': len([r for r in results if 'error' not in r]),
        'failed': len([r for r in results if 'error' in r]),
        'results': results
    }
