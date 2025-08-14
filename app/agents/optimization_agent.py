"""
Optimization agent for SQL query analysis and optimization.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.models.agent import AgentType, AgentResponse
from app.utils.bigquery_client import BigQueryClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OptimizationAgent(BaseAgent):
    """Agent responsible for analyzing and optimizing SQL queries."""
    
    def __init__(self, session_id: str, request_id: str):
        """Initialize optimization agent."""
        super().__init__(AgentType.OPTIMIZATION_AGENT, session_id, request_id)
        self.bq_client = BigQueryClient()
        
    async def execute(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Execute the optimization agent's main logic.
        
        Args:
            input_data: Input data containing SQL query and context
            
        Returns:
            Agent response with optimization recommendations
        """
        try:
            # Extract input data
            sql_query = input_data.get("sql_query", "")
            original_query = input_data.get("original_query", "")
            context = input_data.get("context", {})
            
            if not sql_query:
                self.set_error("invalid_input", "No SQL query provided", "MISSING_SQL_QUERY")
                return self.to_response()
            
            # Step 1: Analyze query structure
            self.add_step("query_analysis", "sql_analysis")
            query_analysis = await self._analyze_query_structure(sql_query)
            self.update_step("query_analysis", "success", output=query_analysis)
            
            # Step 2: Estimate query cost
            self.add_step("cost_estimation", "cost_analysis")
            cost_analysis = await self._estimate_query_cost(sql_query)
            self.update_step("cost_estimation", "success", output=cost_analysis)
            
            # Step 3: Identify optimization opportunities
            self.add_step("optimization_identification", "pattern_analysis")
            optimization_opportunities = await self._identify_optimizations(sql_query, query_analysis)
            self.update_step("optimization_identification", "success", output=optimization_opportunities)
            
            # Step 4: Generate optimized query
            self.add_step("query_optimization", "sql_optimization")
            optimized_query = await self._generate_optimized_query(sql_query, optimization_opportunities)
            self.update_step("query_optimization", "success", output={"optimized_sql": optimized_query})
            
            # Step 5: Compare performance
            self.add_step("performance_comparison", "benchmark_analysis")
            performance_comparison = await self._compare_performance(sql_query, optimized_query)
            self.update_step("performance_comparison", "success", output=performance_comparison)
            
            # Step 6: Generate recommendations
            self.add_step("recommendation_generation", "insight_generation")
            recommendations = await self._generate_recommendations(
                sql_query, optimized_query, query_analysis, cost_analysis, 
                optimization_opportunities, performance_comparison
            )
            self.update_step("recommendation_generation", "success", output=recommendations)
            
            # Set final result
            self.result = {
                "original_query": original_query,
                "original_sql": sql_query,
                "optimized_sql": optimized_query,
                "query_analysis": query_analysis,
                "cost_analysis": cost_analysis,
                "optimization_opportunities": optimization_opportunities,
                "performance_comparison": performance_comparison,
                "recommendations": recommendations
            }
            
            return self.to_response()
            
        except Exception as e:
            logger.error("Optimization agent execution failed", error=str(e), exc_info=True)
            self.set_error("execution_error", str(e), "OPTIMIZATION_AGENT_ERROR")
            return self.to_response()
    
    async def _analyze_query_structure(self, sql_query: str) -> Dict[str, Any]:
        """
        Analyze the structure of the SQL query.
        
        Args:
            sql_query: SQL query to analyze
            
        Returns:
            Query structure analysis
        """
        analysis = {
            "query_type": "SELECT",
            "complexity_score": 0,
            "joins": [],
            "aggregations": [],
            "filters": [],
            "group_by": False,
            "order_by": False,
            "limit": None,
            "subqueries": 0,
            "ctes": 0
        }
        
        query_upper = sql_query.upper()
        
        # Count complexity factors
        if "JOIN" in query_upper:
            analysis["joins"] = re.findall(r'JOIN\s+(\w+)', query_upper)
            analysis["complexity_score"] += len(analysis["joins"]) * 2
        
        if "GROUP BY" in query_upper:
            analysis["group_by"] = True
            analysis["complexity_score"] += 1
        
        if "ORDER BY" in query_upper:
            analysis["order_by"] = True
            analysis["complexity_score"] += 1
        
        if "LIMIT" in query_upper:
            limit_match = re.search(r'LIMIT\s+(\d+)', query_upper)
            if limit_match:
                analysis["limit"] = int(limit_match.group(1))
        
        # Count aggregations
        agg_functions = ["SUM", "COUNT", "AVG", "MAX", "MIN"]
        for func in agg_functions:
            if func in query_upper:
                analysis["aggregations"].append(func)
                analysis["complexity_score"] += 1
        
        # Count subqueries
        analysis["subqueries"] = query_upper.count("SELECT") - 1
        
        # Count CTEs
        analysis["ctes"] = query_upper.count("WITH")
        
        # Determine query type
        if "INSERT" in query_upper:
            analysis["query_type"] = "INSERT"
        elif "UPDATE" in query_upper:
            analysis["query_type"] = "UPDATE"
        elif "DELETE" in query_upper:
            analysis["query_type"] = "DELETE"
        
        return analysis
    
    async def _estimate_query_cost(self, sql_query: str) -> Dict[str, Any]:
        """
        Estimate the cost of executing the query.
        
        Args:
            sql_query: SQL query to analyze
            
        Returns:
            Cost analysis
        """
        try:
            # Use BigQuery dry run to get cost estimates
            validation_result = self.bq_client.validate_query(sql_query)
            
            if validation_result.get("valid"):
                bytes_processed = validation_result.get("total_bytes_processed", 0)
                bytes_billed = validation_result.get("total_bytes_billed", 0)
                estimated_cost = validation_result.get("estimated_cost", 0)
                
                return {
                    "bytes_processed": bytes_processed,
                    "bytes_billed": bytes_billed,
                    "estimated_cost_usd": estimated_cost,
                    "cost_category": self._categorize_cost(estimated_cost),
                    "efficiency_score": self._calculate_efficiency_score(bytes_processed, bytes_billed)
                }
            else:
                return {
                    "error": validation_result.get("error", "Query validation failed"),
                    "bytes_processed": 0,
                    "bytes_billed": 0,
                    "estimated_cost_usd": 0,
                    "cost_category": "unknown",
                    "efficiency_score": 0
                }
                
        except Exception as e:
            logger.error("Failed to estimate query cost", error=str(e))
            return {
                "error": str(e),
                "bytes_processed": 0,
                "bytes_billed": 0,
                "estimated_cost_usd": 0,
                "cost_category": "unknown",
                "efficiency_score": 0
            }
    
    async def _identify_optimizations(self, sql_query: str, query_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify potential optimization opportunities.
        
        Args:
            sql_query: SQL query to analyze
            query_analysis: Query structure analysis
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        # Check for SELECT *
        if "SELECT *" in sql_query.upper():
            opportunities.append({
                "type": "select_columns",
                "priority": "high",
                "description": "Use specific column names instead of SELECT *",
                "impact": "Reduces data transfer and improves performance",
                "recommendation": "Replace SELECT * with specific column names"
            })
        
        # Check for missing LIMIT
        if query_analysis["query_type"] == "SELECT" and not query_analysis["limit"]:
            opportunities.append({
                "type": "add_limit",
                "priority": "medium",
                "description": "Add LIMIT clause to prevent large result sets",
                "impact": "Prevents excessive data transfer",
                "recommendation": "Add LIMIT clause with appropriate value"
            })
        
        # Check for inefficient JOINs
        if len(query_analysis["joins"]) > 2:
            opportunities.append({
                "type": "join_optimization",
                "priority": "medium",
                "description": "Multiple JOINs detected - consider query structure",
                "impact": "May improve query performance",
                "recommendation": "Review JOIN order and consider denormalization"
            })
        
        # Check for missing WHERE clauses
        if "WHERE" not in sql_query.upper() and query_analysis["query_type"] == "SELECT":
            opportunities.append({
                "type": "add_filters",
                "priority": "low",
                "description": "No WHERE clause detected",
                "impact": "May reduce data scanned",
                "recommendation": "Add appropriate WHERE clauses to filter data"
            })
        
        # Check for complex aggregations
        if len(query_analysis["aggregations"]) > 3:
            opportunities.append({
                "type": "aggregation_optimization",
                "priority": "medium",
                "description": "Multiple aggregations detected",
                "impact": "May improve performance with proper indexing",
                "recommendation": "Consider materialized views for complex aggregations"
            })
        
        return opportunities
    
    async def _generate_optimized_query(self, sql_query: str, opportunities: List[Dict[str, Any]]) -> str:
        """
        Generate an optimized version of the query.
        
        Args:
            sql_query: Original SQL query
            opportunities: Optimization opportunities
            
        Returns:
            Optimized SQL query
        """
        optimized_query = sql_query
        
        # Apply optimizations based on opportunities
        for opportunity in opportunities:
            if opportunity["type"] == "select_columns" and "SELECT *" in optimized_query.upper():
                # Replace SELECT * with common columns (simplified)
                optimized_query = optimized_query.replace("SELECT *", "SELECT id, name, created_at")
            
            elif opportunity["type"] == "add_limit" and "LIMIT" not in optimized_query.upper():
                # Add LIMIT clause
                optimized_query += " LIMIT 1000"
        
        return optimized_query
    
    async def _compare_performance(self, original_query: str, optimized_query: str) -> Dict[str, Any]:
        """
        Compare performance between original and optimized queries.
        
        Args:
            original_query: Original SQL query
            optimized_query: Optimized SQL query
            
        Returns:
            Performance comparison
        """
        try:
            # Get cost estimates for both queries
            original_cost = await self._estimate_query_cost(original_query)
            optimized_cost = await self._estimate_query_cost(optimized_query)
            
            original_cost_usd = original_cost.get("estimated_cost_usd", 0)
            optimized_cost_usd = optimized_cost.get("estimated_cost_usd", 0)
            
            if original_cost_usd > 0:
                cost_savings = ((original_cost_usd - optimized_cost_usd) / original_cost_usd) * 100
            else:
                cost_savings = 0
            
            return {
                "original_cost_usd": original_cost_usd,
                "optimized_cost_usd": optimized_cost_usd,
                "cost_savings_percent": cost_savings,
                "bytes_saved": original_cost.get("bytes_processed", 0) - optimized_cost.get("bytes_processed", 0),
                "improvement_category": self._categorize_improvement(cost_savings)
            }
            
        except Exception as e:
            logger.error("Failed to compare performance", error=str(e))
            return {
                "error": str(e),
                "original_cost_usd": 0,
                "optimized_cost_usd": 0,
                "cost_savings_percent": 0,
                "bytes_saved": 0,
                "improvement_category": "unknown"
            }
    
    async def _generate_recommendations(self, original_query: str, optimized_query: str,
                                      query_analysis: Dict[str, Any], cost_analysis: Dict[str, Any],
                                      opportunities: List[Dict[str, Any]], 
                                      performance_comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate optimization recommendations.
        
        Args:
            original_query: Original SQL query
            optimized_query: Optimized SQL query
            query_analysis: Query structure analysis
            cost_analysis: Cost analysis
            opportunities: Optimization opportunities
            performance_comparison: Performance comparison
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Add recommendations based on opportunities
        for opportunity in opportunities:
            recommendations.append({
                "type": opportunity["type"],
                "priority": opportunity["priority"],
                "description": opportunity["description"],
                "impact": opportunity["impact"],
                "action": opportunity["recommendation"]
            })
        
        # Add cost-based recommendations
        if cost_analysis.get("cost_category") == "high":
            recommendations.append({
                "type": "cost_optimization",
                "priority": "high",
                "description": "Query has high estimated cost",
                "impact": "Significant cost savings possible",
                "action": "Consider query optimization or data partitioning"
            })
        
        # Add performance improvement recommendations
        if performance_comparison.get("cost_savings_percent", 0) > 10:
            recommendations.append({
                "type": "performance_improvement",
                "priority": "high",
                "description": f"Optimized query shows {performance_comparison['cost_savings_percent']:.1f}% cost savings",
                "impact": "Significant performance improvement",
                "action": "Use optimized query version"
            })
        
        # Add general recommendations based on query complexity
        if query_analysis.get("complexity_score", 0) > 5:
            recommendations.append({
                "type": "complexity_reduction",
                "priority": "medium",
                "description": "Query has high complexity score",
                "impact": "May improve maintainability and performance",
                "action": "Consider breaking down into smaller queries or using views"
            })
        
        return recommendations
    
    def _categorize_cost(self, cost_usd: float) -> str:
        """Categorize query cost."""
        if cost_usd < 0.01:
            return "low"
        elif cost_usd < 0.10:
            return "medium"
        else:
            return "high"
    
    def _calculate_efficiency_score(self, bytes_processed: int, bytes_billed: int) -> float:
        """Calculate query efficiency score (0-1)."""
        if bytes_processed == 0:
            return 0.0
        
        # Higher score means more efficient (less waste)
        efficiency = bytes_billed / bytes_processed
        return min(1.0, efficiency)
    
    def _categorize_improvement(self, cost_savings_percent: float) -> str:
        """Categorize performance improvement."""
        if cost_savings_percent > 50:
            return "excellent"
        elif cost_savings_percent > 20:
            return "good"
        elif cost_savings_percent > 5:
            return "moderate"
        else:
            return "minimal"

