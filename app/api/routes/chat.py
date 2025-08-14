"""
Chat API routes for handling user queries and responses.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.chat import ChatRequest, ChatResponse
from app.core.agent_manager import agent_manager
from app.core.session_manager import session_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Process a chat message and return agent response.
    
    Args:
        request: Chat request containing user message and context
        
    Returns:
        Chat response with agent's reply and analysis
    """
    try:
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = session_manager.create_session(request.user_id)
        
        # Validate session exists
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Prepare context
        context = request.context or {}
        context.update({
            "user_id": request.user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Execute query through agent manager
        agent_response = await agent_manager.execute_query(
            session_id=session_id,
            user_query=request.message,
            context=context,
            enable_optimization=True,
            enable_impact_analysis=True
        )
        
        # Extract results
        if not agent_response.is_successful():
            error_message = "An error occurred while processing your query."
            if agent_response.error:
                error_message = agent_response.error.error_message
            
            return ChatResponse(
                response=error_message,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                agent_metadata={
                    "agent_id": agent_response.agent_id,
                    "status": "error",
                    "error": agent_response.error.dict() if agent_response.error else None
                }
            )
        
        # Extract synthesized results
        synthesized_result = agent_response.result.get("synthesized_result", {})
        
        # Build response
        response = ChatResponse(
            response=synthesized_result.get("user_response", "Query processed successfully."),
            session_id=session_id,
            timestamp=datetime.utcnow(),
            agent_metadata={
                "agent_id": agent_response.agent_id,
                "agent_type": "coordinator_agent",
                "processing_steps": [step.step_name for step in agent_response.steps],
                "confidence": synthesized_result.get("metadata", {}).get("execution_success_rate", 0),
                "total_duration_ms": agent_response.total_duration_ms
            }
        )
        
        # Add query result if available
        if synthesized_result.get("query_summary"):
            response.query_result = {
                "sql_query": synthesized_result["query_summary"].get("sql_query", ""),
                "execution_time_ms": synthesized_result["query_summary"].get("execution_time_ms"),
                "row_count": synthesized_result["query_summary"].get("row_count"),
                "data_preview": synthesized_result["query_summary"].get("data_preview", [])
            }
        
        # Add impact analysis if available
        if synthesized_result.get("impact_summary"):
            response.impact_analysis = {
                "impact_score": synthesized_result["impact_summary"].get("overall_impact_score", 0),
                "impact_description": f"Business impact score: {synthesized_result['impact_summary'].get('overall_impact_score', 0):.1%}",
                "affected_metrics": ["business_metrics"],  # Simplified
                "recommendations": [rec.get("description", "") for rec in synthesized_result.get("recommendations", [])[:3]],
                "confidence_level": synthesized_result["impact_summary"].get("confidence_level", 0)
            }
        
        logger.info(
            "Chat request processed successfully",
            session_id=session_id,
            agent_id=agent_response.agent_id,
            response_length=len(response.response)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat request failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/session", response_model=Dict[str, Any])
async def create_session(user_id: Optional[str] = None):
    """
    Create a new chat session.
    
    Args:
        user_id: Optional user identifier
        
    Returns:
        Session information
    """
    try:
        session_id = session_manager.create_session(user_id)
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
    except Exception as e:
        logger.error("Failed to create session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/session/{session_id}", response_model=Dict[str, Any])
async def get_session_info(session_id: str):
    """
    Get information about a specific session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session information
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get conversation history
        history = session_manager.get_conversation_history(session_id, limit=50)
        
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "conversation_history": history,
            "context_variables": session.context_variables,
            "user_preferences": session.user_preferences,
            "schema_info": session.schema_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session info", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get session information")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a chat session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Deletion confirmation
    """
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.get("/session/{session_id}/history", response_model=Dict[str, Any])
async def get_conversation_history(session_id: str, limit: Optional[int] = 50):
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session identifier
        limit: Maximum number of messages to return
        
    Returns:
        Conversation history
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        history = session_manager.get_conversation_history(session_id, limit=limit)
        
        return {
            "session_id": session_id,
            "history": history,
            "total_messages": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get conversation history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get conversation history")


@router.get("/sessions", response_model=Dict[str, Any])
async def list_sessions():
    """
    Get list of active sessions.
    
    Returns:
        List of sessions with statistics
    """
    try:
        stats = session_manager.get_session_stats()
        
        return {
            "total_sessions": stats["total_sessions"],
            "active_sessions": stats["active_sessions"],
            "total_messages": stats["total_messages"],
            "session_timeout_hours": stats["session_timeout_hours"]
        }
        
    except Exception as e:
        logger.error("Failed to list sessions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list sessions")

