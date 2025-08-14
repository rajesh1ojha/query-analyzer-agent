"""
Agent manager for handling agent lifecycle and coordination.
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.coordinator_agent import CoordinatorAgent
from app.models.agent import AgentResponse
from app.utils.logger import get_logger
from app.core.session_manager import session_manager

logger = get_logger(__name__)


class AgentManager:
    """Manages agent lifecycle and coordination."""
    
    def __init__(self):
        """Initialize agent manager."""
        self.active_agents: Dict[str, CoordinatorAgent] = {}
        self.agent_history: Dict[str, AgentResponse] = {}
        
    async def execute_query(self, session_id: str, user_query: str, context: Dict[str, Any] = None,
                          enable_optimization: bool = True, enable_impact_analysis: bool = True) -> AgentResponse:
        """
        Execute a user query using the coordinator agent.
        
        Args:
            session_id: Session identifier
            user_query: User's natural language query
            context: Additional context
            enable_optimization: Whether to enable query optimization
            enable_impact_analysis: Whether to enable impact analysis
            
        Returns:
            Agent response
        """
        request_id = str(uuid.uuid4())
        context = context or {}
        
        try:
            # Create coordinator agent
            coordinator = CoordinatorAgent(session_id, request_id)
            self.active_agents[coordinator.agent_id] = coordinator
            
            # Prepare input data
            input_data = {
                "query": user_query,
                "context": context,
                "enable_optimization": enable_optimization,
                "enable_impact_analysis": enable_impact_analysis
            }
            
            # Execute agent
            response = await coordinator.run_with_timeout(input_data)
            
            # Store in history
            self.agent_history[coordinator.agent_id] = response
            
            # Remove from active agents
            if coordinator.agent_id in self.active_agents:
                del self.active_agents[coordinator.agent_id]
            
            # Update session with user message
            session_manager.add_message_to_history(session_id, "user", user_query)
            
            # Update session with agent response
            if response.result and response.result.get("synthesized_result"):
                user_response = response.result["synthesized_result"].get("user_response", "Query processed successfully.")
                session_manager.add_message_to_history(session_id, "assistant", user_response)
            
            logger.info(
                "Query execution completed",
                agent_id=coordinator.agent_id,
                session_id=session_id,
                request_id=request_id,
                success=response.is_successful()
            )
            
            return response
            
        except Exception as e:
            logger.error("Query execution failed", error=str(e), exc_info=True)
            
            # Create error response
            error_response = AgentResponse(
                agent_id=request_id,
                agent_type="coordinator_agent",
                state="error",
                session_id=session_id,
                request_id=request_id,
                error={
                    "error_type": "execution_error",
                    "error_message": str(e),
                    "error_code": "AGENT_MANAGER_ERROR"
                }
            )
            
            return error_response
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent status or None if not found
        """
        # Check active agents
        if agent_id in self.active_agents:
            agent = self.active_agents[agent_id]
            return {
                "agent_id": agent_id,
                "status": "active",
                "state": agent.state.value,
                "start_time": agent.start_time.isoformat() if agent.start_time else None,
                "duration_ms": agent.calculate_duration()
            }
        
        # Check history
        if agent_id in self.agent_history:
            response = self.agent_history[agent_id]
            return {
                "agent_id": agent_id,
                "status": "completed",
                "state": response.state.value,
                "start_time": response.created_at.isoformat(),
                "end_time": response.updated_at.isoformat(),
                "duration_ms": response.total_duration_ms,
                "success": response.is_successful()
            }
        
        return None
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of active agents.
        
        Returns:
            List of active agent statuses
        """
        active_agents = []
        
        for agent_id, agent in self.active_agents.items():
            active_agents.append({
                "agent_id": agent_id,
                "session_id": agent.session_id,
                "request_id": agent.request_id,
                "state": agent.state.value,
                "start_time": agent.start_time.isoformat() if agent.start_time else None,
                "duration_ms": agent.calculate_duration()
            })
        
        return active_agents
    
    def get_agent_history(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get agent execution history.
        
        Args:
            session_id: Optional session filter
            limit: Maximum number of results
            
        Returns:
            List of agent history entries
        """
        history = []
        
        for agent_id, response in self.agent_history.items():
            if session_id and response.session_id != session_id:
                continue
            
            history.append({
                "agent_id": agent_id,
                "session_id": response.session_id,
                "request_id": response.request_id,
                "agent_type": response.agent_type.value,
                "state": response.state.value,
                "created_at": response.created_at.isoformat(),
                "updated_at": response.updated_at.isoformat(),
                "duration_ms": response.total_duration_ms,
                "success": response.is_successful(),
                "error": response.error.dict() if response.error else None
            })
        
        # Sort by creation time (newest first) and limit results
        history.sort(key=lambda x: x["created_at"], reverse=True)
        return history[:limit]
    
    def cleanup_old_history(self, max_age_hours: int = 24) -> int:
        """
        Clean up old agent history.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of entries cleaned up
        """
        cutoff_time = datetime.utcnow().replace(hour=datetime.utcnow().hour - max_age_hours)
        cleaned_count = 0
        
        agent_ids_to_remove = []
        
        for agent_id, response in self.agent_history.items():
            if response.created_at < cutoff_time:
                agent_ids_to_remove.append(agent_id)
        
        for agent_id in agent_ids_to_remove:
            del self.agent_history[agent_id]
            cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old agent history entries")
        
        return cleaned_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get agent manager statistics.
        
        Returns:
            Statistics dictionary
        """
        total_agents = len(self.agent_history)
        active_agents = len(self.active_agents)
        
        # Calculate success rate
        successful_agents = sum(1 for response in self.agent_history.values() if response.is_successful())
        success_rate = (successful_agents / total_agents * 100) if total_agents > 0 else 0
        
        # Calculate average execution time
        execution_times = [response.total_duration_ms for response in self.agent_history.values() if response.total_duration_ms]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_agents_executed": total_agents,
            "active_agents": active_agents,
            "success_rate_percent": success_rate,
            "average_execution_time_ms": avg_execution_time,
            "history_size": len(self.agent_history)
        }


# Global agent manager instance
agent_manager = AgentManager()
