"""
Chat-related data models for the agentic application.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    
    message: str = Field(..., description="User's natural language query")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation continuity")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    user_id: Optional[str] = Field(None, description="User identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the total revenue for Q1 2024?",
                "session_id": "session_123",
                "context": {"department": "sales", "region": "US"},
                "user_id": "user_456"
            }
        }


class QueryResult(BaseModel):
    """Model for query execution results."""
    
    sql_query: str = Field(..., description="Generated SQL query")
    optimized_sql: Optional[str] = Field(None, description="Optimized SQL query")
    execution_time_ms: Optional[float] = Field(None, description="Query execution time in milliseconds")
    row_count: Optional[int] = Field(None, description="Number of rows returned")
    data_preview: Optional[List[Dict[str, Any]]] = Field(None, description="Preview of query results")
    error_message: Optional[str] = Field(None, description="Error message if query failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql_query": "SELECT SUM(revenue) FROM sales WHERE quarter = 'Q1' AND year = 2024",
                "optimized_sql": "SELECT SUM(revenue) FROM sales WHERE quarter = 'Q1' AND year = 2024",
                "execution_time_ms": 1250.5,
                "row_count": 1,
                "data_preview": [{"total_revenue": 1500000.00}]
            }
        }


class ImpactAnalysis(BaseModel):
    """Model for impact analysis results."""
    
    impact_score: float = Field(..., description="Impact score (0-1)")
    impact_description: str = Field(..., description="Description of the impact")
    affected_metrics: List[str] = Field(default_factory=list, description="List of affected metrics")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations based on analysis")
    confidence_level: float = Field(..., description="Confidence level of the analysis (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "impact_score": 0.85,
                "impact_description": "High impact on revenue metrics",
                "affected_metrics": ["total_revenue", "average_order_value"],
                "recommendations": ["Monitor sales trends", "Review pricing strategy"],
                "confidence_level": 0.92
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    
    response: str = Field(..., description="AI agent's response to the user query")
    query_result: Optional[QueryResult] = Field(None, description="Query execution results if applicable")
    impact_analysis: Optional[ImpactAnalysis] = Field(None, description="Impact analysis if applicable")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    agent_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata about agent processing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "The total revenue for Q1 2024 is $1,500,000. This represents a 15% increase compared to Q1 2023.",
                "session_id": "session_123",
                "timestamp": "2024-01-15T10:30:00Z",
                "agent_metadata": {
                    "agent_type": "query_agent",
                    "processing_steps": ["nlp_understanding", "sql_generation", "query_execution"],
                    "confidence": 0.95
                }
            }
        }
