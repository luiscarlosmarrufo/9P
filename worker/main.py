"""
Celery application configuration for the 9P Social Analytics Platform
"""

from celery import Celery
from control.core.config import settings

# Create Celery app
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "worker.tasks.ingest_twitter",
        "worker.tasks.ingest_reddit", 
        "worker.tasks.classify_posts",
        "worker.tasks.aggregate_monthly",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "worker.tasks.ingest_twitter": {"queue": "ingestion"},
        "worker.tasks.ingest_reddit": {"queue": "ingestion"},
        "worker.tasks.classify_posts": {"queue": "classification"},
        "worker.tasks.aggregate_monthly": {"queue": "aggregation"},
    },
    task_annotations={
        "worker.tasks.ingest_twitter": {"rate_limit": "10/m"},
        "worker.tasks.ingest_reddit": {"rate_limit": "10/m"},
        "worker.tasks.classify_posts": {"rate_limit": "5/m"},
    }
)

if __name__ == "__main__":
    celery_app.start()
