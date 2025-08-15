"""
Health check endpoints for monitoring application status.
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any, List, Optional

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


@router.get("/schema")
async def get_schema_info(table_names: Optional[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive schema information from INFORMATION_SCHEMA.
    
    Args:
        table_names: Comma-separated list of table names (optional)
        
    Returns:
        Comprehensive schema information
    """
    try:
        bq_client = BigQueryClient()
        
        # Parse table names if provided
        tables = None
        if table_names:
            tables = [name.strip() for name in table_names.split(",")]
        
        # Get comprehensive schema information
        schema_info = bq_client.get_comprehensive_schema_info(tables)
        
        if "error" in schema_info:
            return {
                "success": False,
                "error": schema_info["error"],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "success": True,
            "schema_info": schema_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Schema info retrieval failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/schema/summary")
async def get_schema_summary(table_names: Optional[str] = None) -> Dict[str, Any]:
    """
    Get schema summary optimized for LLM context.
    
    Args:
        table_names: Comma-separated list of table names (optional)
        
    Returns:
        Schema summary for LLM prompts
    """
    try:
        bq_client = BigQueryClient()
        
        # Parse table names if provided
        tables = None
        if table_names:
            tables = [name.strip() for name in table_names.split(",")]
        
        # Get schema summary
        schema_summary = bq_client.get_table_schema_summary(tables)
        
        if "error" in schema_summary:
            return {
                "success": False,
                "error": schema_summary["error"],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "success": True,
            "schema_summary": schema_summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Schema summary retrieval failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/metadata")
async def get_table_metadata(table_names: Optional[str] = None) -> Dict[str, Any]:
    """
    Get table metadata including row counts, sizes, and creation dates.
    
    Args:
        table_names: Comma-separated list of table names (optional)
        
    Returns:
        Table metadata information
    """
    try:
        bq_client = BigQueryClient()
        
        # Parse table names if provided
        tables = None
        if table_names:
            tables = [name.strip() for name in table_names.split(",")]
        
        # Get table metadata
        metadata = bq_client.get_table_metadata(tables)
        
        if "error" in metadata:
            return {
                "success": False,
                "error": metadata["error"],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "success": True,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Table metadata retrieval failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

