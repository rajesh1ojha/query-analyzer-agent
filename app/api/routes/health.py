"""
Health check endpoints for monitoring application status.
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any

from app.config.settings import settings
from app.utils.bigquery_client import BigQueryClient
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check including external dependencies."""
    try:
        # Test BigQuery connection
        bq_client = BigQueryClient()
        tables = bq_client.list_tables()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {
                "bigquery": "connected",
                "tables_available": len(tables)
            },
            "environment": settings.environment
        }
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {
                "bigquery": "disconnected",
                "error": str(e)
            },
            "environment": settings.environment
        }


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes health probes."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }

