"""
FastAPI main application for 9P Social Analytics Platform
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import make_asgi_app

from control.core.config import settings
from control.core.database import engine
from control.routers import health, ingest, classify, summary, items, export, metrics


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events"""
    # Startup
    print("Starting 9P Social Analytics API...")
    yield
    # Shutdown
    print("Shutting down 9P Social Analytics API...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade social analytics platform with 9P classification",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else ["localhost", "127.0.0.1"],
)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(ingest.router, prefix=settings.API_V1_STR, tags=["ingestion"])
app.include_router(classify.router, prefix=settings.API_V1_STR, tags=["classification"])
app.include_router(summary.router, prefix=settings.API_V1_STR, tags=["summary"])
app.include_router(items.router, prefix=settings.API_V1_STR, tags=["items"])
app.include_router(export.router, prefix=settings.API_V1_STR, tags=["export"])
app.include_router(metrics.router, prefix=settings.API_V1_STR, tags=["metrics"])

# Add Prometheus metrics endpoint
if settings.METRICS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "9P Social Analytics API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "control.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
