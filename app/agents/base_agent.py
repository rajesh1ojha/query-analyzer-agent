"""
Base agent class for all agent implementations.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from app.models.agent import AgentState, AgentType, AgentResponse, AgentStep, AgentError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, agent_type: AgentType, session_id: str, request_id: str):
        """
        Initialize base agent.
        
        Args:
            agent_type: Type of agent
            session_id: Session identifier
            request_id: Request identifier
        """
        self.agent_id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.session_id = session_id
        self.request_id = request_id
        self.state = AgentState.IDLE
        self.status = AgentStatus.PENDING
        self.steps: List[AgentStep] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[AgentError] = None
        self.metadata: Dict[str, Any] = {}
        
        logger.debug(
            "Initialized agent",
            agent_id=self.agent_id,
            agent_type=agent_type,
            session_id=session_id,
            request_id=request_id
        )
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Execute the agent's main logic.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Agent response
        """
        pass
    
    def add_step(self, step_name: str, step_type: str, status: str = "in_progress", 
                 output: Optional[Dict[str, Any]] = None, error: Optional[AgentError] = None) -> str:
        """
        Add a processing step to the agent.
        
        Args:
            step_name: Name of the step
            step_type: Type of step
            status: Step status
            output: Step output
            error: Step error if any
            
        Returns:
            Step ID
        """
        step = AgentStep(
            step_name=step_name,
            step_type=step_type,
            start_time=datetime.utcnow(),
            status=status,
            output=output,
            error=error
        )
        
        self.steps.append(step)
        logger.debug("Added agent step", agent_id=self.agent_id, step_name=step_name, status=status)
        return step.step_name
    
    def update_step(self, step_name: str, status: str, output: Optional[Dict[str, Any]] = None,
                   error: Optional[AgentError] = None) -> bool:
        """
        Update an existing step.
        
        Args:
            step_name: Name of the step to update
            status: New status
            output: Step output
            error: Step error if any
            
        Returns:
            True if updated successfully
        """
        for step in self.steps:
            if step.step_name == step_name:
                step.status = status
                step.end_time = datetime.utcnow()
                if step.start_time:
                    step.duration_ms = (step.end_time - step.start_time).total_seconds() * 1000
                step.output = output
                step.error = error
                
                logger.debug("Updated agent step", agent_id=self.agent_id, step_name=step_name, status=status)
                return True
        
        return False
    
    def set_state(self, state: AgentState) -> None:
        """
        Set agent state.
        
        Args:
            state: New agent state
        """
        self.state = state
        logger.debug("Agent state changed", agent_id=self.agent_id, state=state)
    
    def set_error(self, error_type: str, error_message: str, error_code: Optional[str] = None,
                  context: Optional[Dict[str, Any]] = None) -> None:
        """
        Set agent error.
        
        Args:
            error_type: Type of error
            error_message: Error message
            error_code: Error code
            context: Error context
        """
        self.error = AgentError(
            error_type=error_type,
            error_message=error_message,
            error_code=error_code,
            context=context or {}
        )
        
        self.state = AgentState.ERROR
        self.status = AgentStatus.FAILED
        
        logger.error(
            "Agent error set",
            agent_id=self.agent_id,
            error_type=error_type,
            error_message=error_message
        )
    
    def calculate_duration(self) -> Optional[float]:
        """
        Calculate total execution duration.
        
        Returns:
            Duration in milliseconds or None if not started
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None
    
    def to_response(self) -> AgentResponse:
        """
        Convert agent to response model.
        
        Returns:
            Agent response
        """
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            state=self.state,
            session_id=self.session_id,
            request_id=self.request_id,
            steps=self.steps,
            total_duration_ms=self.calculate_duration(),
            result=self.result,
            error=self.error,
            metadata=self.metadata
        )
    
    async def run_with_timeout(self, input_data: Dict[str, Any], timeout_seconds: int = 300) -> AgentResponse:
        """
        Run agent with timeout.
        
        Args:
            input_data: Input data for the agent
            timeout_seconds: Timeout in seconds
            
        Returns:
            Agent response
        """
        try:
            self.start_time = datetime.utcnow()
            self.state = AgentState.PROCESSING
            self.status = AgentStatus.RUNNING
            
            logger.info("Starting agent execution", agent_id=self.agent_id, agent_type=self.agent_type)
            
            # Run with timeout
            response = await asyncio.wait_for(
                self.execute(input_data),
                timeout=timeout_seconds
            )
            
            self.end_time = datetime.utcnow()
            self.state = AgentState.COMPLETED
            self.status = AgentStatus.COMPLETED
            
            logger.info(
                "Agent execution completed",
                agent_id=self.agent_id,
                duration_ms=self.calculate_duration()
            )
            
            return response
            
        except asyncio.TimeoutError:
            self.end_time = datetime.utcnow()
            self.state = AgentState.TIMEOUT
            self.status = AgentStatus.TIMEOUT
            
            self.set_error(
                "timeout_error",
                f"Agent execution timed out after {timeout_seconds} seconds",
                "AGENT_TIMEOUT"
            )
            
            logger.error("Agent execution timed out", agent_id=self.agent_id, timeout_seconds=timeout_seconds)
            return self.to_response()
            
        except Exception as e:
            self.end_time = datetime.utcnow()
            
            self.set_error(
                "execution_error",
                str(e),
                "AGENT_EXECUTION_ERROR",
                {"exception_type": type(e).__name__}
            )
            
            logger.error("Agent execution failed", agent_id=self.agent_id, error=str(e), exc_info=True)
            return self.to_response()
    
    def get_step_by_name(self, step_name: str) -> Optional[AgentStep]:
        """
        Get a step by name.
        
        Args:
            step_name: Name of the step
            
        Returns:
            Step or None if not found
        """
        for step in self.steps:
            if step.step_name == step_name:
                return step
        return None
    
    def get_steps_by_type(self, step_type: str) -> List[AgentStep]:
        """
        Get all steps of a specific type.
        
        Args:
            step_type: Type of step
            
        Returns:
            List of steps
        """
        return [step for step in self.steps if step.step_type == step_type]
    
    def is_completed(self) -> bool:
        """
        Check if agent execution is completed.
        
        Returns:
            True if completed
        """
        return self.status in [AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.TIMEOUT]
    
    def is_successful(self) -> bool:
        """
        Check if agent execution was successful.
        
        Returns:
            True if successful
        """
        return self.status == AgentStatus.COMPLETED and self.error is None

