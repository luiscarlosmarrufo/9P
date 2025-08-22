"""
Health check endpoints
"""

import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import boto3
from botocore.exceptions import ClientError

from control.core.database import get_db
from control.core.config import settings
from control.schemas import HealthResponse

router = APIRouter()

# Store startup time for uptime calculation
startup_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check for all system components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": settings.APP_VERSION,
        "database": "unknown",
        "redis": "unknown", 
        "s3": "unknown"
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check S3
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION
        )
        s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        health_status["s3"] = "healthy"
    except ClientError as e:
        health_status["s3"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["s3"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return HealthResponse(**health_status)


@router.get("/health/liveness")
async def liveness_check():
    """
    Simple liveness check for Kubernetes/container orchestration
    """
    return {"status": "alive", "timestamp": datetime.utcnow()}


@router.get("/health/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - ensures service can handle requests
    """
    try:
        # Quick database check
        db.execute(text("SELECT 1"))
        
        # Quick Redis check
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow(),
            "uptime_seconds": time.time() - startup_time
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
        )
