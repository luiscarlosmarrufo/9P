"""
Classification endpoints for 9P and sentiment analysis
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from celery import current_app as celery_app

from control.core.database import get_db
from control.schemas import ClassificationRequest, TaskResponse
from control.models import Brand

router = APIRouter()


@router.post("/classify/run", response_model=TaskResponse)
async def run_classification(
    request: ClassificationRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger classification job for social media posts
    """
    # Verify brand exists if specified
    if request.brand_id:
        brand = db.query(Brand).filter(Brand.id == request.brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        if not brand.is_active:
            raise HTTPException(status_code=400, detail="Brand is not active")
    
    # Queue classification task
    task = celery_app.send_task(
        'worker.tasks.classify_posts',
        args=[
            str(request.brand_id) if request.brand_id else None,
            request.platform,
            request.start_date.isoformat() if request.start_date else None,
            request.end_date.isoformat() if request.end_date else None,
            request.force_reprocess,
            request.batch_size
        ]
    )
    
    brand_name = brand.name if request.brand_id and brand else "all brands"
    platform_text = f" on {request.platform}" if request.platform else ""
    
    return TaskResponse(
        task_id=task.id,
        status="queued",
        message=f"Classification queued for {brand_name}{platform_text}"
    )


@router.get("/classify/status/{task_id}")
async def get_classification_status(task_id: str):
    """
    Get status of a classification task
    """
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'task_id': task_id,
            'status': 'pending',
            'message': 'Classification task is waiting to be processed'
        }
    elif task.state == 'PROGRESS':
        response = {
            'task_id': task_id,
            'status': 'in_progress',
            'message': task.info.get('message', 'Classifying posts...'),
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'stage_1_processed': task.info.get('stage_1_processed', 0),
            'stage_2_processed': task.info.get('stage_2_processed', 0)
        }
    elif task.state == 'SUCCESS':
        response = {
            'task_id': task_id,
            'status': 'completed',
            'message': 'Classification completed successfully',
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


@router.post("/classify/aggregate", response_model=TaskResponse)
async def run_monthly_aggregation(
    brand_id: str = None,
    year: int = None,
    month: int = None,
    db: Session = Depends(get_db)
):
    """
    Trigger monthly aggregation calculation
    """
    # Verify brand exists if specified
    if brand_id:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
    
    # Queue aggregation task
    task = celery_app.send_task(
        'worker.tasks.calculate_monthly_aggregates',
        args=[brand_id, year, month]
    )
    
    return TaskResponse(
        task_id=task.id,
        status="queued",
        message="Monthly aggregation calculation queued"
    )
