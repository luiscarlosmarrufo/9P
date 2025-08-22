"""
Classification tasks for 9P and sentiment analysis
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from celery import current_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_

from worker.main import celery_app
from control.core.config import settings
from control.core.database import engine
from control.models import SocialPost, Classification, Brand
from ml.classification.nine_p_classifier import NinePClassifier
from ml.sentiment.sentiment_analyzer import SentimentAnalyzer
from inference.vllm_client import VLLMClient

# Create database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(bind=True)
def classify_posts(
    self,
    brand_id: Optional[str] = None,
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    force_reprocess: bool = False,
    batch_size: int = 32
) -> Dict[str, Any]:
    """
    Classify social media posts using two-stage inference
    """
    db = SessionLocal()
    
    try:
        # Build query for unprocessed posts
        query = db.query(SocialPost)
        
        filters = []
        
        if not force_reprocess:
            # Only process posts that haven't been classified
            filters.append(SocialPost.is_processed == False)
        
        if brand_id:
            # Verify brand exists
            brand = db.query(Brand).filter(Brand.id == brand_id).first()
            if not brand:
                raise ValueError(f"Brand {brand_id} not found")
            filters.append(SocialPost.brand_id == brand_id)
        
        if platform:
            filters.append(SocialPost.platform == platform)
        
        if start_date:
            filters.append(SocialPost.posted_at >= datetime.fromisoformat(start_date))
        
        if end_date:
            filters.append(SocialPost.posted_at <= datetime.fromisoformat(end_date))
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get posts to process
        posts = query.order_by(SocialPost.scraped_at).all()
        
        if not posts:
            return {
                'message': 'No posts found to classify',
                'processed_count': 0,
                'stage_1_processed': 0,
                'stage_2_processed': 0
            }
        
        # Initialize classifiers
        nine_p_classifier = NinePClassifier()
        sentiment_analyzer = SentimentAnalyzer()
        vllm_client = VLLMClient()
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={
                'message': f'Starting classification of {len(posts)} posts',
                'current': 0,
                'total': len(posts),
                'stage_1_processed': 0,
                'stage_2_processed': 0
            }
        )
        
        processed_count = 0
        stage_1_processed = 0
        stage_2_processed = 0
        errors = []
        
        # Process posts in batches
        for i in range(0, len(posts), batch_size):
            batch = posts[i:i + batch_size]
            
            try:
                # Stage 1: Embeddings + LogisticRegression
                stage_1_results = classify_batch_stage_1(
                    batch, nine_p_classifier, sentiment_analyzer
                )
                
                # Stage 2: vLLM fallback for low confidence predictions
                stage_2_results = classify_batch_stage_2(
                    stage_1_results, vllm_client
                )
                
                # Save results to database
                for post, classification_data in stage_2_results:
                    try:
                        # Delete existing classification if force_reprocess
                        if force_reprocess:
                            existing = db.query(Classification).filter(
                                Classification.social_post_id == post.id
                            ).first()
                            if existing:
                                db.delete(existing)
                        
                        # Create new classification
                        classification = Classification(
                            id=uuid.uuid4(),
                            social_post_id=post.id,
                            brand_id=post.brand_id,
                            **classification_data
                        )
                        
                        db.add(classification)
                        
                        # Mark post as processed
                        post.is_processed = True
                        post.processing_error = None
                        
                        processed_count += 1
                        
                        if classification_data['stage'] == 1:
                            stage_1_processed += 1
                        else:
                            stage_2_processed += 1
                        
                    except Exception as e:
                        post.processing_error = str(e)
                        errors.append(f"Error saving classification for post {post.id}: {str(e)}")
                
                # Commit batch
                db.commit()
                
                # Update progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'message': f'Processed {processed_count}/{len(posts)} posts',
                        'current': processed_count,
                        'total': len(posts),
                        'stage_1_processed': stage_1_processed,
                        'stage_2_processed': stage_2_processed
                    }
                )
                
            except Exception as e:
                db.rollback()
                errors.append(f"Error processing batch {i//batch_size + 1}: {str(e)}")
                continue
        
        result = {
            'processed_count': processed_count,
            'stage_1_processed': stage_1_processed,
            'stage_2_processed': stage_2_processed,
            'errors': errors,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60, max_retries=3)
    
    finally:
        db.close()


def classify_batch_stage_1(
    posts: List[SocialPost],
    nine_p_classifier: NinePClassifier,
    sentiment_analyzer: SentimentAnalyzer
) -> List[Tuple[SocialPost, Dict[str, Any]]]:
    """
    Stage 1 classification using embeddings and LogisticRegression
    """
    results = []
    
    # Extract texts
    texts = [post.text for post in posts]
    
    # Get 9P classifications
    nine_p_predictions = nine_p_classifier.predict_batch(texts)
    
    # Get sentiment predictions
    sentiment_predictions = sentiment_analyzer.predict_batch(texts)
    
    for i, post in enumerate(posts):
        nine_p_scores = nine_p_predictions[i]
        sentiment_scores = sentiment_predictions[i]
        
        # Calculate overall confidence
        nine_p_confidence = nine_p_classifier.calculate_confidence(nine_p_scores)
        sentiment_confidence = sentiment_analyzer.calculate_confidence(sentiment_scores)
        overall_confidence = (nine_p_confidence + sentiment_confidence) / 2
        
        classification_data = {
            'product': nine_p_scores['product'],
            'place': nine_p_scores['place'],
            'price': nine_p_scores['price'],
            'publicity': nine_p_scores['publicity'],
            'postconsumption': nine_p_scores['postconsumption'],
            'purpose': nine_p_scores['purpose'],
            'partnerships': nine_p_scores['partnerships'],
            'people': nine_p_scores['people'],
            'planet': nine_p_scores['planet'],
            'sentiment_positive': sentiment_scores['positive'],
            'sentiment_neutral': sentiment_scores['neutral'],
            'sentiment_negative': sentiment_scores['negative'],
            'sentiment_label': sentiment_scores['label'],
            'stage': 1,
            'confidence_score': overall_confidence,
            'model_version': f"stage1_v{settings.APP_VERSION}",
            'classified_at': datetime.utcnow()
        }
        
        results.append((post, classification_data))
    
    return results


def classify_batch_stage_2(
    stage_1_results: List[Tuple[SocialPost, Dict[str, Any]]],
    vllm_client: VLLMClient
) -> List[Tuple[SocialPost, Dict[str, Any]]]:
    """
    Stage 2 classification using vLLM for low confidence predictions
    """
    results = []
    low_confidence_items = []
    
    # Separate high and low confidence predictions
    for post, classification_data in stage_1_results:
        if classification_data['confidence_score'] < settings.CLASSIFICATION_CONFIDENCE_THRESHOLD:
            low_confidence_items.append((post, classification_data))
        else:
            results.append((post, classification_data))
    
    # Process low confidence items with vLLM
    if low_confidence_items and vllm_client.is_available():
        for post, stage_1_data in low_confidence_items:
            try:
                # Get vLLM prediction
                vllm_response = vllm_client.classify_post(
                    text=post.text,
                    platform=post.platform,
                    brand_context=None  # Could add brand context here
                )
                
                if vllm_response and vllm_response.get('success'):
                    # Use vLLM results
                    vllm_data = vllm_response['classification']
                    
                    classification_data = {
                        'product': vllm_data.get('product', stage_1_data['product']),
                        'place': vllm_data.get('place', stage_1_data['place']),
                        'price': vllm_data.get('price', stage_1_data['price']),
                        'publicity': vllm_data.get('publicity', stage_1_data['publicity']),
                        'postconsumption': vllm_data.get('postconsumption', stage_1_data['postconsumption']),
                        'purpose': vllm_data.get('purpose', stage_1_data['purpose']),
                        'partnerships': vllm_data.get('partnerships', stage_1_data['partnerships']),
                        'people': vllm_data.get('people', stage_1_data['people']),
                        'planet': vllm_data.get('planet', stage_1_data['planet']),
                        'sentiment_positive': vllm_data.get('sentiment', {}).get('positive', stage_1_data['sentiment_positive']),
                        'sentiment_neutral': vllm_data.get('sentiment', {}).get('neutral', stage_1_data['sentiment_neutral']),
                        'sentiment_negative': vllm_data.get('sentiment', {}).get('negative', stage_1_data['sentiment_negative']),
                        'sentiment_label': vllm_data.get('sentiment', {}).get('label', stage_1_data['sentiment_label']),
                        'stage': 2,
                        'confidence_score': vllm_response.get('confidence', 0.8),
                        'model_version': f"stage2_v{settings.APP_VERSION}",
                        'classified_at': datetime.utcnow(),
                        'llm_response': vllm_response,
                        'llm_reasoning': vllm_response.get('reasoning')
                    }
                    
                    results.append((post, classification_data))
                else:
                    # Fallback to Stage 1 results
                    results.append((post, stage_1_data))
                    
            except Exception as e:
                # Fallback to Stage 1 results on error
                stage_1_data['llm_response'] = {'error': str(e)}
                results.append((post, stage_1_data))
    else:
        # No vLLM available or no low confidence items
        results.extend(low_confidence_items)
    
    return results


@celery_app.task(bind=True)
def classify_single_post(
    self,
    post_id: str,
    force_stage_2: bool = False
) -> Dict[str, Any]:
    """
    Classify a single post (useful for real-time classification)
    """
    db = SessionLocal()
    
    try:
        # Get the post
        post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
        if not post:
            raise ValueError(f"Post {post_id} not found")
        
        # Initialize classifiers
        nine_p_classifier = NinePClassifier()
        sentiment_analyzer = SentimentAnalyzer()
        
        # Stage 1 classification
        stage_1_results = classify_batch_stage_1([post], nine_p_classifier, sentiment_analyzer)
        post, classification_data = stage_1_results[0]
        
        # Stage 2 if needed or forced
        if force_stage_2 or classification_data['confidence_score'] < settings.CLASSIFICATION_CONFIDENCE_THRESHOLD:
            vllm_client = VLLMClient()
            stage_2_results = classify_batch_stage_2([(post, classification_data)], vllm_client)
            post, classification_data = stage_2_results[0]
        
        # Save classification
        existing = db.query(Classification).filter(
            Classification.social_post_id == post.id
        ).first()
        
        if existing:
            # Update existing
            for key, value in classification_data.items():
                setattr(existing, key, value)
        else:
            # Create new
            classification = Classification(
                id=uuid.uuid4(),
                social_post_id=post.id,
                brand_id=post.brand_id,
                **classification_data
            )
            db.add(classification)
        
        # Mark post as processed
        post.is_processed = True
        post.processing_error = None
        
        db.commit()
        
        return {
            'post_id': str(post.id),
            'stage': classification_data['stage'],
            'confidence_score': classification_data['confidence_score'],
            'classification': classification_data,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=30, max_retries=2)
    
    finally:
        db.close()
