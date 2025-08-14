"""
Agents API routes for managing and monitoring agents.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.agent_manager import agent_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_agents_overview():
    """
    Get overview of all agents and their status.
    
    Returns:
        Agents overview with statistics
    """
    try:
        stats = agent_manager.get_statistics()
        active_agents = agent_manager.get_active_agents()
        
        return {
            "overview": {
                "total_agents_executed": stats["total_agents_executed"],
                "active_agents": stats["active_agents"],
                "success_rate_percent": stats["success_rate_percent"],
                "average_execution_time_ms": stats["average_execution_time_ms"]
            },
            "active_agents": active_agents,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get agents overview", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agents overview")


@router.get("/{agent_id}", response_model=Dict[str, Any])
async def get_agent_status(agent_id: str):
    """
    Get status of a specific agent.
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        Agent status information
    """
    try:
        status = agent_manager.get_agent_status(agent_id)
        if not status:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "agent_id": agent_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent status")


@router.get("/history", response_model=Dict[str, Any])
async def get_agent_history(session_id: Optional[str] = None, limit: Optional[int] = 50):
    """
    Get agent execution history.
    
    Args:
        session_id: Optional session filter
        limit: Maximum number of results
        
    Returns:
        Agent execution history
    """
    try:
        history = agent_manager.get_agent_history(session_id=session_id, limit=limit)
        
        return {
            "history": history,
            "total_entries": len(history),
            "session_filter": session_id,
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get agent history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent history")


@router.get("/active", response_model=Dict[str, Any])
async def get_active_agents():
    """
    Get list of currently active agents.
    
    Returns:
        List of active agents
    """
    try:
        active_agents = agent_manager.get_active_agents()
        
        return {
            "active_agents": active_agents,
            "count": len(active_agents),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get active agents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get active agents")


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_agent_history(max_age_hours: Optional[int] = 24):
    """
    Clean up old agent history.
    
    Args:
        max_age_hours: Maximum age in hours for history entries
        
    Returns:
        Cleanup results
    """
    try:
        cleaned_count = agent_manager.cleanup_old_history(max_age_hours)
        
        return {
            "cleaned_entries": cleaned_count,
            "max_age_hours": max_age_hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to cleanup agent history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to cleanup agent history")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_agent_statistics():
    """
    Get detailed agent statistics.
    
    Returns:
        Detailed agent statistics
    """
    try:
        stats = agent_manager.get_statistics()
        
        return {
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get agent statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get agent statistics")

