"""
Reddit data ingestion tasks
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

import praw
import boto3
from celery import current_task
from sqlalchemy.orm import sessionmaker

from worker.main import celery_app
from control.core.config import settings
from control.core.database import engine
from control.models import SocialPost, Brand

# Create database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_reddit_client() -> praw.Reddit:
    """Initialize Reddit API client"""
    return praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT,
        ratelimit_seconds=600  # 10 minutes
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
def ingest_reddit(
    self,
    brand_id: str,
    subreddits: List[str],
    query: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 100,
    sort: str = "relevance"
) -> Dict[str, Any]:
    """
    Ingest Reddit posts and comments for a brand
    """
    db = SessionLocal()
    
    try:
        # Verify brand exists
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise ValueError(f"Brand {brand_id} not found")
        
        # Initialize Reddit client
        reddit = get_reddit_client()
        
        # Parse dates
        start_time = datetime.fromisoformat(start_date) if start_date else None
        end_time = datetime.fromisoformat(end_date) if end_date else None
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={
                'message': f'Searching Reddit in {len(subreddits)} subreddits',
                'current': 0,
                'total': max_results
            }
        )
        
        processed_count = 0
        new_posts = 0
        errors = []
        
        results_per_subreddit = max_results // len(subreddits)
        
        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                
                # Search posts in subreddit
                if query:
                    if sort == "relevance":
                        posts = subreddit.search(query, limit=results_per_subreddit)
                    elif sort == "hot":
                        posts = subreddit.hot(limit=results_per_subreddit)
                    elif sort == "top":
                        posts = subreddit.top(limit=results_per_subreddit)
                    elif sort == "new":
                        posts = subreddit.new(limit=results_per_subreddit)
                    else:
                        posts = subreddit.search(query, limit=results_per_subreddit)
                else:
                    # Get posts without search query
                    if sort == "hot":
                        posts = subreddit.hot(limit=results_per_subreddit)
                    elif sort == "top":
                        posts = subreddit.top(limit=results_per_subreddit)
                    elif sort == "new":
                        posts = subreddit.new(limit=results_per_subreddit)
                    else:
                        posts = subreddit.hot(limit=results_per_subreddit)
                
                for post in posts:
                    try:
                        # Check date filters
                        post_date = datetime.fromtimestamp(post.created_utc)
                        if start_time and post_date < start_time:
                            continue
                        if end_time and post_date > end_time:
                            continue
                        
                        # Check if post already exists
                        existing = db.query(SocialPost).filter(
                            SocialPost.platform == "reddit",
                            SocialPost.platform_id == str(post.id)
                        ).first()
                        
                        if existing:
                            processed_count += 1
                            continue
                        
                        # Create S3 key for raw data
                        s3_key = f"reddit/{brand_id}/{datetime.utcnow().strftime('%Y/%m/%d')}/{post.id}.json"
                        
                        # Prepare raw data
                        raw_data = {
                            'post': {
                                'id': post.id,
                                'title': post.title,
                                'selftext': post.selftext,
                                'url': post.url,
                                'subreddit': post.subreddit.display_name,
                                'author': str(post.author) if post.author else '[deleted]',
                                'created_utc': post.created_utc,
                                'score': post.score,
                                'upvote_ratio': post.upvote_ratio,
                                'num_comments': post.num_comments,
                                'permalink': post.permalink,
                                'is_self': post.is_self,
                                'over_18': post.over_18,
                                'spoiler': post.spoiler,
                                'stickied': post.stickied,
                                'locked': post.locked
                            },
                            'ingested_at': datetime.utcnow().isoformat()
                        }
                        
                        # Upload to S3
                        upload_to_s3(raw_data, s3_key)
                        
                        # Combine title and selftext for analysis
                        text_content = post.title
                        if post.selftext and post.selftext.strip():
                            text_content += "\n\n" + post.selftext
                        
                        # Create social post record
                        social_post = SocialPost(
                            id=uuid.uuid4(),
                            platform="reddit",
                            platform_id=str(post.id),
                            brand_id=brand_id,
                            text=text_content,
                            author=str(post.author) if post.author else '[deleted]',
                            author_id=str(post.author) if post.author else None,
                            language=None,  # Reddit doesn't provide language detection
                            posted_at=post_date,
                            scraped_at=datetime.utcnow(),
                            likes=post.score,
                            shares=0,  # Reddit doesn't have shares
                            comments=post.num_comments,
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
                                'message': f'Processed {processed_count} posts from r/{subreddit_name}',
                                'current': processed_count,
                                'total': max_results
                            }
                        )
                        
                        # Commit in batches
                        if processed_count % 10 == 0:
                            db.commit()
                        
                        # Break if we've reached max results
                        if processed_count >= max_results:
                            break
                    
                    except Exception as e:
                        errors.append(f"Error processing post {post.id}: {str(e)}")
                        continue
                
                # Break if we've reached max results
                if processed_count >= max_results:
                    break
                    
            except Exception as e:
                errors.append(f"Error accessing subreddit r/{subreddit_name}: {str(e)}")
                continue
        
        # Final commit
        db.commit()
        
        result = {
            'brand_id': brand_id,
            'brand_name': brand.name,
            'subreddits': subreddits,
            'query': query,
            'sort': sort,
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
def ingest_reddit_comments(
    self,
    brand_id: str,
    post_ids: List[str],
    max_comments_per_post: int = 50
) -> Dict[str, Any]:
    """
    Ingest comments for specific Reddit posts
    """
    db = SessionLocal()
    
    try:
        # Verify brand exists
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise ValueError(f"Brand {brand_id} not found")
        
        # Initialize Reddit client
        reddit = get_reddit_client()
        
        processed_count = 0
        new_comments = 0
        errors = []
        
        for post_id in post_ids:
            try:
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'message': f'Processing comments for post {post_id}',
                        'current': processed_count,
                        'total': len(post_ids)
                    }
                )
                
                submission = reddit.submission(id=post_id)
                submission.comments.replace_more(limit=0)  # Remove "more comments" objects
                
                comment_count = 0
                for comment in submission.comments.list():
                    if comment_count >= max_comments_per_post:
                        break
                    
                    try:
                        # Check if comment already exists
                        existing = db.query(SocialPost).filter(
                            SocialPost.platform == "reddit",
                            SocialPost.platform_id == str(comment.id)
                        ).first()
                        
                        if existing:
                            continue
                        
                        # Skip deleted/removed comments
                        if comment.body in ['[deleted]', '[removed]']:
                            continue
                        
                        # Create S3 key for raw data
                        s3_key = f"reddit/{brand_id}/comments/{datetime.utcnow().strftime('%Y/%m/%d')}/{comment.id}.json"
                        
                        # Prepare raw data
                        raw_data = {
                            'comment': {
                                'id': comment.id,
                                'body': comment.body,
                                'author': str(comment.author) if comment.author else '[deleted]',
                                'created_utc': comment.created_utc,
                                'score': comment.score,
                                'parent_id': comment.parent_id,
                                'link_id': comment.link_id,
                                'permalink': comment.permalink,
                                'is_submitter': comment.is_submitter,
                                'stickied': comment.stickied
                            },
                            'parent_post_id': post_id,
                            'ingested_at': datetime.utcnow().isoformat()
                        }
                        
                        # Upload to S3
                        upload_to_s3(raw_data, s3_key)
                        
                        # Create social post record for comment
                        social_post = SocialPost(
                            id=uuid.uuid4(),
                            platform="reddit",
                            platform_id=str(comment.id),
                            brand_id=brand_id,
                            text=comment.body,
                            author=str(comment.author) if comment.author else '[deleted]',
                            author_id=str(comment.author) if comment.author else None,
                            language=None,
                            posted_at=datetime.fromtimestamp(comment.created_utc),
                            scraped_at=datetime.utcnow(),
                            likes=comment.score,
                            shares=0,
                            comments=0,
                            raw_data=raw_data,
                            s3_key=s3_key,
                            is_processed=False
                        )
                        
                        db.add(social_post)
                        new_comments += 1
                        comment_count += 1
                        
                    except Exception as e:
                        errors.append(f"Error processing comment {comment.id}: {str(e)}")
                        continue
                
                processed_count += 1
                
                # Commit in batches
                if processed_count % 5 == 0:
                    db.commit()
                    
            except Exception as e:
                errors.append(f"Error processing post {post_id}: {str(e)}")
                continue
        
        # Final commit
        db.commit()
        
        result = {
            'brand_id': brand_id,
            'brand_name': brand.name,
            'processed_posts': processed_count,
            'new_comments': new_comments,
            'errors': errors,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60, max_retries=3)
    
    finally:
        db.close()
