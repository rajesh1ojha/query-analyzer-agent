"""
Tests for agent implementations.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from app.agents.query_agent import QueryAgent
from app.agents.optimization_agent import OptimizationAgent
from app.agents.impact_analysis_agent import ImpactAnalysisAgent
from app.agents.coordinator_agent import CoordinatorAgent
from app.models.agent import AgentType, AgentState


class TestQueryAgent:
    """Test cases for QueryAgent."""
    
    @pytest.fixture
    def query_agent(self):
        """Create a QueryAgent instance for testing."""
        return QueryAgent("test_session", "test_request")
    
    @pytest.mark.asyncio
    async def test_analyze_query(self, query_agent):
        """Test query analysis functionality."""
        query = "What is the total revenue for Q1 2024?"
        context = {}
        
        analysis = await query_agent._analyze_query(query, context)
        
        assert analysis["intent"] == "data_retrieval"
        assert "revenue" in analysis["tables"]
        assert analysis["business_domain"] == "financial"
    
    @pytest.mark.asyncio
    async def test_generate_sql(self, query_agent):
        """Test SQL generation functionality."""
        query = "What is the total revenue?"
        analysis = {"tables": ["sales"], "complexity": "simple"}
        schema_info = {}
        context = {}
        
        sql = await query_agent._generate_sql(query, analysis, schema_info, context)
        
        assert "SELECT" in sql.upper()
        assert "FROM" in sql.upper()


class TestOptimizationAgent:
    """Test cases for OptimizationAgent."""
    
    @pytest.fixture
    def optimization_agent(self):
        """Create an OptimizationAgent instance for testing."""
        return OptimizationAgent("test_session", "test_request")
    
    @pytest.mark.asyncio
    async def test_analyze_query_structure(self, optimization_agent):
        """Test query structure analysis."""
        sql_query = "SELECT * FROM sales WHERE year = 2024"
        
        analysis = await optimization_agent._analyze_query_structure(sql_query)
        
        assert analysis["query_type"] == "SELECT"
        assert analysis["complexity_score"] >= 0
        assert not analysis["group_by"]
    
    @pytest.mark.asyncio
    async def test_identify_optimizations(self, optimization_agent):
        """Test optimization identification."""
        sql_query = "SELECT * FROM sales"
        query_analysis = {"query_type": "SELECT", "limit": None}
        
        opportunities = await optimization_agent._identify_optimizations(sql_query, query_analysis)
        
        assert len(opportunities) > 0
        assert any(opp["type"] == "select_columns" for opp in opportunities)


class TestImpactAnalysisAgent:
    """Test cases for ImpactAnalysisAgent."""
    
    @pytest.fixture
    def impact_agent(self):
        """Create an ImpactAnalysisAgent instance for testing."""
        return ImpactAnalysisAgent("test_session", "test_request")
    
    @pytest.mark.asyncio
    async def test_analyze_query_intent(self, impact_agent):
        """Test query intent analysis."""
        original_query = "What is the total revenue for this quarter?"
        sql_query = "SELECT SUM(revenue) FROM sales WHERE quarter = 'Q1'"
        context = {}
        
        intent = await impact_agent._analyze_query_intent(original_query, sql_query, context)
        
        assert intent["business_domain"] == "financial"
        assert "revenue" in intent["business_metrics"]
    
    @pytest.mark.asyncio
    async def test_extract_key_metrics(self, impact_agent):
        """Test key metrics extraction."""
        query_results = {
            "data": [{"total_revenue": 1500000.00}]
        }
        intent_analysis = {"business_metrics": ["revenue"]}
        
        metrics = await impact_agent._extract_key_metrics(query_results, intent_analysis)
        
        assert metrics["primary_metric"] is not None
        assert metrics["primary_metric"]["name"] == "total_revenue"


class TestCoordinatorAgent:
    """Test cases for CoordinatorAgent."""
    
    @pytest.fixture
    def coordinator_agent(self):
        """Create a CoordinatorAgent instance for testing."""
        return CoordinatorAgent("test_session", "test_request")
    
    @pytest.mark.asyncio
    async def test_initialize_workflow(self, coordinator_agent):
        """Test workflow initialization."""
        user_query = "What is the total revenue?"
        context = {}
        enable_optimization = True
        enable_impact_analysis = True
        
        workflow = await coordinator_agent._initialize_workflow(
            user_query, context, enable_optimization, enable_impact_analysis
        )
        
        assert workflow["workflow_id"] is not None
        assert workflow["agents_enabled"]["query_agent"] is True
        assert workflow["agents_enabled"]["optimization_agent"] is True
        assert workflow["agents_enabled"]["impact_analysis_agent"] is True
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_response(self, coordinator_agent):
        """Test comprehensive response generation."""
        synthesized_result = {
            "user_response": "The total revenue is $1,500,000.",
            "optimization_summary": {"cost_savings_percent": 15.5},
            "impact_summary": {"overall_impact_score": 0.75},
            "recommendations": [
                {"description": "Monitor revenue trends"},
                {"description": "Review pricing strategy"}
            ]
        }
        
        response = coordinator_agent._generate_comprehensive_response(synthesized_result)
        
        assert "total revenue" in response.lower()
        assert "15.5%" in response
        assert "75%" in response
        assert "monitor revenue trends" in response.lower()


@pytest.mark.asyncio
async def test_agent_execution_flow():
    """Test the complete agent execution flow."""
    # This is a high-level integration test
    coordinator = CoordinatorAgent("test_session", "test_request")
    
    input_data = {
        "query": "What is the total revenue?",
        "context": {},
        "enable_optimization": True,
        "enable_impact_analysis": True
    }
    
    # Mock the agent dependencies to avoid actual BigQuery calls
    with patch('app.agents.query_agent.BigQueryClient') as mock_bq:
        mock_bq.return_value.execute_query.return_value = {
            "success": True,
            "data": [{"total_revenue": 1500000.00}],
            "row_count": 1,
            "execution_time_ms": 1000
        }
        mock_bq.return_value.validate_query.return_value = {
            "valid": True,
            "total_bytes_processed": 1000000,
            "total_bytes_billed": 1000000
        }
        
        response = await coordinator.execute(input_data)
        
        assert response.agent_id is not None
        assert response.state in [AgentState.COMPLETED, AgentState.ERROR]
        assert response.result is not None

