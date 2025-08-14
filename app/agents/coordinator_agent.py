"""
Coordinator agent for orchestrating other agents and managing workflows.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.agents.query_agent import QueryAgent
from app.agents.optimization_agent import OptimizationAgent
from app.agents.impact_analysis_agent import ImpactAnalysisAgent
from app.models.agent import AgentType, AgentResponse
from app.utils.logger import get_logger
from app.core.session_manager import session_manager

logger = get_logger(__name__)


class CoordinatorAgent(BaseAgent):
    """Agent responsible for orchestrating other agents and managing workflows."""
    
    def __init__(self, session_id: str, request_id: str):
        """Initialize coordinator agent."""
        super().__init__(AgentType.COORDINATOR_AGENT, session_id, request_id)
        
    async def execute(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Execute the coordinator agent's main logic.
        
        Args:
            input_data: Input data containing user query and context
            
        Returns:
            Agent response with coordinated results
        """
        try:
            # Extract input data
            user_query = input_data.get("query", "")
            context = input_data.get("context", {})
            enable_optimization = input_data.get("enable_optimization", True)
            enable_impact_analysis = input_data.get("enable_impact_analysis", True)
            
            if not user_query:
                self.set_error("invalid_input", "No query provided", "MISSING_QUERY")
                return self.to_response()
            
            # Step 1: Initialize workflow
            self.add_step("workflow_initialization", "coordination_setup")
            workflow_config = await self._initialize_workflow(user_query, context, enable_optimization, enable_impact_analysis)
            self.update_step("workflow_initialization", "success", output=workflow_config)
            
            # Step 2: Execute query agent
            self.add_step("query_execution", "agent_orchestration")
            query_result = await self._execute_query_agent(user_query, context)
            if not query_result.is_successful():
                self.update_step("query_execution", "error", error=query_result.error)
                self.set_error("query_agent_failed", "Query agent execution failed", "QUERY_AGENT_ERROR")
                return self.to_response()
            self.update_step("query_execution", "success", output={"query_agent_id": query_result.agent_id})
            
            # Step 3: Execute optimization agent (if enabled)
            optimization_result = None
            if enable_optimization and query_result.result:
                self.add_step("optimization_execution", "agent_orchestration")
                optimization_result = await self._execute_optimization_agent(query_result.result, context)
                if optimization_result and optimization_result.is_successful():
                    self.update_step("optimization_execution", "success", output={"optimization_agent_id": optimization_result.agent_id})
                else:
                    self.update_step("optimization_execution", "warning", output={"message": "Optimization agent failed or disabled"})
            
            # Step 4: Execute impact analysis agent (if enabled)
            impact_result = None
            if enable_impact_analysis and query_result.result:
                self.add_step("impact_analysis_execution", "agent_orchestration")
                impact_result = await self._execute_impact_analysis_agent(query_result.result, context)
                if impact_result and impact_result.is_successful():
                    self.update_step("impact_analysis_execution", "success", output={"impact_agent_id": impact_result.agent_id})
                else:
                    self.update_step("impact_analysis_execution", "warning", output={"message": "Impact analysis agent failed or disabled"})
            
            # Step 5: Synthesize results
            self.add_step("result_synthesis", "coordination_synthesis")
            synthesized_result = await self._synthesize_results(query_result, optimization_result, impact_result, context)
            self.update_step("result_synthesis", "success", output=synthesized_result)
            
            # Step 6: Update session context
            self.add_step("session_update", "context_management")
            await self._update_session_context(synthesized_result, context)
            self.update_step("session_update", "success")
            
            # Set final result
            self.result = {
                "workflow_config": workflow_config,
                "query_result": query_result.result if query_result else None,
                "optimization_result": optimization_result.result if optimization_result else None,
                "impact_result": impact_result.result if impact_result else None,
                "synthesized_result": synthesized_result,
                "agent_execution_summary": {
                    "query_agent": {
                        "agent_id": query_result.agent_id,
                        "status": query_result.state.value,
                        "duration_ms": query_result.total_duration_ms
                    },
                    "optimization_agent": {
                        "agent_id": optimization_result.agent_id if optimization_result else None,
                        "status": optimization_result.state.value if optimization_result else "not_executed",
                        "duration_ms": optimization_result.total_duration_ms if optimization_result else None
                    },
                    "impact_analysis_agent": {
                        "agent_id": impact_result.agent_id if impact_result else None,
                        "status": impact_result.state.value if impact_result else "not_executed",
                        "duration_ms": impact_result.total_duration_ms if impact_result else None
                    }
                }
            }
            
            return self.to_response()
            
        except Exception as e:
            logger.error("Coordinator agent execution failed", error=str(e), exc_info=True)
            self.set_error("execution_error", str(e), "COORDINATOR_AGENT_ERROR")
            return self.to_response()
    
    async def _initialize_workflow(self, user_query: str, context: Dict[str, Any], 
                                 enable_optimization: bool, enable_impact_analysis: bool) -> Dict[str, Any]:
        """
        Initialize the workflow configuration.
        
        Args:
            user_query: User's natural language query
            context: Additional context
            enable_optimization: Whether to enable query optimization
            enable_impact_analysis: Whether to enable impact analysis
            
        Returns:
            Workflow configuration
        """
        workflow_config = {
            "workflow_id": f"workflow_{self.agent_id}",
            "session_id": self.session_id,
            "request_id": self.request_id,
            "agents_enabled": {
                "query_agent": True,
                "optimization_agent": enable_optimization,
                "impact_analysis_agent": enable_impact_analysis
            },
            "execution_plan": [
                "query_agent",
                "optimization_agent" if enable_optimization else None,
                "impact_analysis_agent" if enable_impact_analysis else None
            ],
            "context": context,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Remove None values from execution plan
        workflow_config["execution_plan"] = [step for step in workflow_config["execution_plan"] if step is not None]
        
        return workflow_config
    
    async def _execute_query_agent(self, user_query: str, context: Dict[str, Any]) -> AgentResponse:
        """
        Execute the query agent.
        
        Args:
            user_query: User's natural language query
            context: Additional context
            
        Returns:
            Query agent response
        """
        try:
            query_agent = QueryAgent(self.session_id, self.request_id)
            input_data = {
                "query": user_query,
                "context": context
            }
            
            return await query_agent.run_with_timeout(input_data)
            
        except Exception as e:
            logger.error("Failed to execute query agent", error=str(e))
            raise
    
    async def _execute_optimization_agent(self, query_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[AgentResponse]:
        """
        Execute the optimization agent.
        
        Args:
            query_result: Results from query agent
            context: Additional context
            
        Returns:
            Optimization agent response or None if failed
        """
        try:
            optimization_agent = OptimizationAgent(self.session_id, self.request_id)
            input_data = {
                "sql_query": query_result.get("sql_query", ""),
                "original_query": query_result.get("original_query", ""),
                "context": context
            }
            
            return await optimization_agent.run_with_timeout(input_data)
            
        except Exception as e:
            logger.error("Failed to execute optimization agent", error=str(e))
            return None
    
    async def _execute_impact_analysis_agent(self, query_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[AgentResponse]:
        """
        Execute the impact analysis agent.
        
        Args:
            query_result: Results from query agent
            context: Additional context
            
        Returns:
            Impact analysis agent response or None if failed
        """
        try:
            impact_agent = ImpactAnalysisAgent(self.session_id, self.request_id)
            input_data = {
                "query_results": query_result.get("formatted_result", {}),
                "original_query": query_result.get("original_query", ""),
                "sql_query": query_result.get("sql_query", ""),
                "context": context
            }
            
            return await impact_agent.run_with_timeout(input_data)
            
        except Exception as e:
            logger.error("Failed to execute impact analysis agent", error=str(e))
            return None
    
    async def _synthesize_results(self, query_result: AgentResponse, optimization_result: Optional[AgentResponse], 
                                impact_result: Optional[AgentResponse], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize results from all agents.
        
        Args:
            query_result: Query agent response
            optimization_result: Optimization agent response
            impact_result: Impact analysis agent response
            context: Additional context
            
        Returns:
            Synthesized results
        """
        synthesized_result = {
            "user_response": "",
            "query_summary": {},
            "optimization_summary": {},
            "impact_summary": {},
            "recommendations": [],
            "insights": [],
            "metadata": {
                "total_agents_executed": 1,  # At least query agent
                "execution_success_rate": 1.0,
                "synthesis_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Extract query results
        if query_result and query_result.result:
            query_data = query_result.result
            synthesized_result["query_summary"] = {
                "sql_query": query_data.get("sql_query", ""),
                "data_preview": query_data.get("formatted_result", {}).get("data", [])[:5],
                "row_count": query_data.get("formatted_result", {}).get("row_count", 0),
                "execution_time_ms": query_data.get("formatted_result", {}).get("execution_time_ms", 0)
            }
            
            # Generate user response from query results
            formatted_result = query_data.get("formatted_result", {})
            synthesized_result["user_response"] = formatted_result.get("summary", "Query executed successfully.")
        
        # Extract optimization results
        if optimization_result and optimization_result.result:
            opt_data = optimization_result.result
            synthesized_result["optimization_summary"] = {
                "optimized_sql": opt_data.get("optimized_sql", ""),
                "cost_savings_percent": opt_data.get("performance_comparison", {}).get("cost_savings_percent", 0),
                "recommendations": opt_data.get("recommendations", [])
            }
            synthesized_result["metadata"]["total_agents_executed"] += 1
            
            # Add optimization recommendations
            synthesized_result["recommendations"].extend(opt_data.get("recommendations", []))
        
        # Extract impact analysis results
        if impact_result and impact_result.result:
            impact_data = impact_result.result
            synthesized_result["impact_summary"] = {
                "overall_impact_score": impact_data.get("overall_impact_score", 0),
                "risk_level": impact_data.get("impact_scores", {}).get("risk_level", "low"),
                "confidence_level": impact_data.get("confidence_level", 0)
            }
            synthesized_result["metadata"]["total_agents_executed"] += 1
            
            # Add impact insights and recommendations
            synthesized_result["insights"].extend(impact_data.get("insights", []))
            synthesized_result["recommendations"].extend(impact_data.get("recommendations", []))
        
        # Calculate execution success rate
        total_agents = 1  # Query agent
        successful_agents = 1 if query_result and query_result.is_successful() else 0
        
        if optimization_result:
            total_agents += 1
            if optimization_result.is_successful():
                successful_agents += 1
        
        if impact_result:
            total_agents += 1
            if impact_result.is_successful():
                successful_agents += 1
        
        synthesized_result["metadata"]["execution_success_rate"] = successful_agents / total_agents if total_agents > 0 else 0
        
        # Generate comprehensive user response
        synthesized_result["user_response"] = self._generate_comprehensive_response(synthesized_result)
        
        return synthesized_result
    
    async def _update_session_context(self, synthesized_result: Dict[str, Any], context: Dict[str, Any]) -> None:
        """
        Update session context with results.
        
        Args:
            synthesized_result: Synthesized results
            context: Additional context
        """
        try:
            # Update session with query results
            if synthesized_result.get("query_summary"):
                session_manager.set_context_variable(
                    self.session_id, 
                    "last_query_results", 
                    synthesized_result["query_summary"]
                )
            
            # Update session with recommendations
            if synthesized_result.get("recommendations"):
                session_manager.set_context_variable(
                    self.session_id,
                    "pending_recommendations",
                    synthesized_result["recommendations"]
                )
            
            # Update session with insights
            if synthesized_result.get("insights"):
                session_manager.set_context_variable(
                    self.session_id,
                    "recent_insights",
                    synthesized_result["insights"]
                )
            
        except Exception as e:
            logger.error("Failed to update session context", error=str(e))
    
    def _generate_comprehensive_response(self, synthesized_result: Dict[str, Any]) -> str:
        """
        Generate a comprehensive user response from all agent results.
        
        Args:
            synthesized_result: Synthesized results
            
        Returns:
            Comprehensive user response
        """
        response_parts = []
        
        # Add query response
        if synthesized_result.get("user_response"):
            response_parts.append(synthesized_result["user_response"])
        
        # Add optimization insights
        optimization_summary = synthesized_result.get("optimization_summary", {})
        if optimization_summary.get("cost_savings_percent", 0) > 10:
            response_parts.append(
                f"Query optimization could save {optimization_summary['cost_savings_percent']:.1f}% in costs."
            )
        
        # Add impact insights
        impact_summary = synthesized_result.get("impact_summary", {})
        if impact_summary.get("overall_impact_score", 0) > 0.5:
            response_parts.append(
                f"This query has a {impact_summary['overall_impact_score']:.1%} business impact score."
            )
        
        # Add recommendations
        recommendations = synthesized_result.get("recommendations", [])
        if recommendations:
            response_parts.append("Key recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):  # Limit to top 3
                response_parts.append(f"{i}. {rec.get('description', '')}")
        
        return " ".join(response_parts) if response_parts else "Analysis completed successfully."

