"""
Data ingestion endpoints for Twitter/X and Reddit
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from celery import current_app as celery_app

from control.core.database import get_db
from control.schemas import TwitterIngestRequest, RedditIngestRequest, TaskResponse
from control.models import Brand

router = APIRouter()


@router.post("/ingest/twitter", response_model=TaskResponse)
async def ingest_twitter(
    request: TwitterIngestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger Twitter/X data ingestion for a brand
    """
    # Verify brand exists
    brand = db.query(Brand).filter(Brand.id == request.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    if not brand.is_active:
        raise HTTPException(status_code=400, detail="Brand is not active")
    
    # Queue ingestion task
    task = celery_app.send_task(
        'worker.tasks.ingest_twitter',
        args=[
            str(request.brand_id),
            request.query,
            request.start_date.isoformat() if request.start_date else None,
            request.end_date.isoformat() if request.end_date else None,
            request.max_results,
            request.include_retweets
        ]
    )
    
    return TaskResponse(
        task_id=task.id,
        status="queued",
        message=f"Twitter ingestion queued for brand '{brand.name}'"
    )


@router.post("/ingest/reddit", response_model=TaskResponse)
async def ingest_reddit(
    request: RedditIngestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger Reddit data ingestion for a brand
    """
    # Verify brand exists
    brand = db.query(Brand).filter(Brand.id == request.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    if not brand.is_active:
        raise HTTPException(status_code=400, detail="Brand is not active")
    
    # Queue ingestion task
    task = celery_app.send_task(
        'worker.tasks.ingest_reddit',
        args=[
            str(request.brand_id),
            request.subreddits,
            request.query,
            request.start_date.isoformat() if request.start_date else None,
            request.end_date.isoformat() if request.end_date else None,
            request.max_results,
            request.sort
        ]
    )
    
    return TaskResponse(
        task_id=task.id,
        status="queued",
        message=f"Reddit ingestion queued for brand '{brand.name}'"
    )


@router.get("/ingest/status/{task_id}")
async def get_ingestion_status(task_id: str):
    """
    Get status of an ingestion task
    """
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'task_id': task_id,
            'status': 'pending',
            'message': 'Task is waiting to be processed'
        }
    elif task.state == 'PROGRESS':
        response = {
            'task_id': task_id,
            'status': 'in_progress',
            'message': task.info.get('message', 'Processing...'),
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1)
        }
    elif task.state == 'SUCCESS':
        response = {
            'task_id': task_id,
            'status': 'completed',
            'message': 'Task completed successfully',
            'result': task.result
        }
    else:  # FAILURE
        response = {
            'task_id': task_id,
            'status': 'failed',
            'message': str(task.info),
            'error': str(task.traceback) if hasattr(task, 'traceback') else None
        }
    
    return response
