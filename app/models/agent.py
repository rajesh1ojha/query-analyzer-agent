"""
Agent-related data models for the agentic application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """Enumeration of possible agent states."""
    
    IDLE = "idle"
    PROCESSING = "processing"
    EXECUTING_QUERY = "executing_query"
    ANALYZING_IMPACT = "analyzing_impact"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


class AgentType(str, Enum):
    """Enumeration of agent types."""
    
    QUERY_AGENT = "query_agent"
    OPTIMIZATION_AGENT = "optimization_agent"
    IMPACT_ANALYSIS_AGENT = "impact_analysis_agent"
    COORDINATOR_AGENT = "coordinator_agent"


class AgentError(BaseModel):
    """Model for agent errors."""
    
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Detailed error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    context: Dict[str, Any] = Field(default_factory=dict, description="Error context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_type": "query_execution_error",
                "error_message": "BigQuery table not found: sales_data",
                "error_code": "BQ_TABLE_NOT_FOUND",
                "timestamp": "2024-01-15T10:30:00Z",
                "context": {"table_name": "sales_data", "project": "my-project"}
            }
        }


class AgentStep(BaseModel):
    """Model for individual agent processing steps."""
    
    step_name: str = Field(..., description="Name of the processing step")
    step_type: str = Field(..., description="Type of step")
    start_time: datetime = Field(..., description="Step start time")
    end_time: Optional[datetime] = Field(None, description="Step end time")
    duration_ms: Optional[float] = Field(None, description="Step duration in milliseconds")
    status: str = Field(..., description="Step status (success, error, in_progress)")
    output: Optional[Dict[str, Any]] = Field(None, description="Step output")
    error: Optional[AgentError] = Field(None, description="Step error if any")
    
    class Config:
        json_schema_extra = {
            "example": {
                "step_name": "sql_generation",
                "step_type": "nlp_to_sql",
                "start_time": "2024-01-15T10:30:00Z",
                "end_time": "2024-01-15T10:30:05Z",
                "duration_ms": 5000.0,
                "status": "success",
                "output": {"sql_query": "SELECT * FROM sales WHERE year = 2024"}
            }
        }


class AgentResponse(BaseModel):
    """Model for agent responses."""
    
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: AgentType = Field(..., description="Type of agent")
    state: AgentState = Field(..., description="Current agent state")
    session_id: str = Field(..., description="Session identifier")
    request_id: str = Field(..., description="Request identifier")
    
    # Processing information
    steps: List[AgentStep] = Field(default_factory=list, description="Processing steps")
    total_duration_ms: Optional[float] = Field(None, description="Total processing time")
    
    # Results
    result: Optional[Dict[str, Any]] = Field(None, description="Agent result")
    error: Optional[AgentError] = Field(None, description="Agent error if any")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_123",
                "agent_type": "query_agent",
                "state": "completed",
                "session_id": "session_456",
                "request_id": "req_789",
                "total_duration_ms": 15000.0,
                "result": {
                    "sql_query": "SELECT SUM(revenue) FROM sales WHERE year = 2024",
                    "data": [{"total_revenue": 1500000.00}]
                },
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:15Z"
            }
        }


class AgentContext(BaseModel):
    """Model for agent context and memory."""
    
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    schema_info: Optional[Dict[str, Any]] = Field(None, description="Database schema information")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    context_variables: Dict[str, Any] = Field(default_factory=dict, description="Context variables")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_123",
                "user_id": "user_456",
                "conversation_history": [
                    {"role": "user", "content": "What is the revenue for Q1?"},
                    {"role": "assistant", "content": "The revenue for Q1 is $500,000."}
                ],
                "schema_info": {
                    "tables": ["sales", "customers", "products"],
                    "columns": {"sales": ["revenue", "date", "product_id"]}
                },
                "user_preferences": {"language": "en", "timezone": "UTC"},
                "context_variables": {"current_quarter": "Q1", "current_year": 2024}
            }
        }
