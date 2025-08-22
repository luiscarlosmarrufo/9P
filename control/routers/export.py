"""
Data export endpoints for CSV and JSON formats
"""

import csv
import json
from io import StringIO
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from control.core.database import get_db
from control.schemas import ExportRequest, TaskResponse
from control.models import SocialPost, Classification, Brand

router = APIRouter()


@router.get("/export/csv")
async def export_csv(
    brand_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None, regex="^(twitter|reddit)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    include_raw_data: bool = Query(False),
    include_classifications: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Export data as CSV file
    """
    # Build query
    query = db.query(SocialPost, Classification, Brand.name.label('brand_name'))
    
    if include_classifications:
        query = query.join(Classification, SocialPost.id == Classification.social_post_id)
    
    query = query.join(Brand, SocialPost.brand_id == Brand.id)
    
    # Apply filters
    filters = []
    
    if brand_id:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        filters.append(SocialPost.brand_id == brand_id)
    
    if platform:
        filters.append(SocialPost.platform == platform)
    
    if start_date:
        filters.append(SocialPost.posted_at >= start_date)
    
    if end_date:
        filters.append(SocialPost.posted_at <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Execute query
    results = query.order_by(desc(SocialPost.posted_at)).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No data found for export")
    
    # Create CSV
    output = StringIO()
    
    # Define CSV headers
    headers = [
        'id', 'platform', 'platform_id', 'brand_name', 'text', 'author', 
        'posted_at', 'scraped_at', 'likes', 'shares', 'comments', 'language'
    ]
    
    if include_classifications:
        headers.extend([
            'product', 'place', 'price', 'publicity', 'postconsumption',
            'purpose', 'partnerships', 'people', 'planet',
            'sentiment_label', 'sentiment_positive', 'sentiment_neutral', 'sentiment_negative',
            'classification_stage', 'confidence_score', 'model_version', 'classified_at'
        ])
    
    if include_raw_data:
        headers.append('raw_data')
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    
    # Write data rows
    for row in results:
        if include_classifications:
            post, classification, brand_name = row
        else:
            post, brand_name = row
            classification = None
        
        csv_row = {
            'id': str(post.id),
            'platform': post.platform,
            'platform_id': post.platform_id,
            'brand_name': brand_name,
            'text': post.text,
            'author': post.author,
            'posted_at': post.posted_at.isoformat(),
            'scraped_at': post.scraped_at.isoformat(),
            'likes': post.likes,
            'shares': post.shares,
            'comments': post.comments,
            'language': post.language
        }
        
        if include_classifications and classification:
            csv_row.update({
                'product': classification.product,
                'place': classification.place,
                'price': classification.price,
                'publicity': classification.publicity,
                'postconsumption': classification.postconsumption,
                'purpose': classification.purpose,
                'partnerships': classification.partnerships,
                'people': classification.people,
                'planet': classification.planet,
                'sentiment_label': classification.sentiment_label,
                'sentiment_positive': classification.sentiment_positive,
                'sentiment_neutral': classification.sentiment_neutral,
                'sentiment_negative': classification.sentiment_negative,
                'classification_stage': classification.stage,
                'confidence_score': classification.confidence_score,
                'model_version': classification.model_version,
                'classified_at': classification.classified_at.isoformat() if classification.classified_at else None
            })
        
        if include_raw_data and post.raw_data:
            csv_row['raw_data'] = json.dumps(post.raw_data)
        
        writer.writerow(csv_row)
    
    # Return CSV response
    csv_content = output.getvalue()
    output.close()
    
    # Generate filename
    filename_parts = ['9p_export']
    if brand_id:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        filename_parts.append(brand.name.replace(' ', '_').lower())
    if platform:
        filename_parts.append(platform)
    filename_parts.append('data.csv')
    filename = '_'.join(filename_parts)
    
    return Response(
        content=csv_content,
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@router.get("/export/json")
async def export_json(
    brand_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None, regex="^(twitter|reddit)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    include_raw_data: bool = Query(False),
    include_classifications: bool = Query(True),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """
    Export data as JSON file
    """
    # Build query (similar to CSV export)
    query = db.query(SocialPost, Classification, Brand.name.label('brand_name'))
    
    if include_classifications:
        query = query.join(Classification, SocialPost.id == Classification.social_post_id)
    
    query = query.join(Brand, SocialPost.brand_id == Brand.id)
    
    # Apply filters
    filters = []
    
    if brand_id:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        filters.append(SocialPost.brand_id == brand_id)
    
    if platform:
        filters.append(SocialPost.platform == platform)
    
    if start_date:
        filters.append(SocialPost.posted_at >= start_date)
    
    if end_date:
        filters.append(SocialPost.posted_at <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Execute query with limit
    results = query.order_by(desc(SocialPost.posted_at)).limit(limit).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No data found for export")
    
    # Build JSON structure
    export_data = {
        "metadata": {
            "export_timestamp": "2024-01-01T00:00:00Z",  # Will be replaced with actual timestamp
            "total_records": len(results),
            "filters": {
                "brand_id": brand_id,
                "platform": platform,
                "start_date": start_date,
                "end_date": end_date
            },
            "options": {
                "include_raw_data": include_raw_data,
                "include_classifications": include_classifications
            }
        },
        "data": []
    }
    
    # Process results
    for row in results:
        if include_classifications:
            post, classification, brand_name = row
        else:
            post, brand_name = row
            classification = None
        
        item = {
            "id": str(post.id),
            "platform": post.platform,
            "platform_id": post.platform_id,
            "brand_name": brand_name,
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
            }
        }
        
        if include_classifications and classification:
            item["classification"] = {
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
                    "classified_at": classification.classified_at.isoformat() if classification.classified_at else None,
                    "llm_reasoning": classification.llm_reasoning
                }
            }
        
        if include_raw_data and post.raw_data:
            item["raw_data"] = post.raw_data
        
        export_data["data"].append(item)
    
    # Generate filename
    filename_parts = ['9p_export']
    if brand_id:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        filename_parts.append(brand.name.replace(' ', '_').lower())
    if platform:
        filename_parts.append(platform)
    filename_parts.append('data.json')
    filename = '_'.join(filename_parts)
    
    return Response(
        content=json.dumps(export_data, indent=2),
        media_type='application/json',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
