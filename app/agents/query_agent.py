"""
Query agent for natural language to SQL conversion and execution.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.models.agent import AgentType, AgentResponse
from app.utils.bigquery_client import BigQueryClient
from app.utils.logger import get_logger
from app.core.session_manager import session_manager

logger = get_logger(__name__)


class QueryAgent(BaseAgent):
    """Agent responsible for converting natural language to SQL and executing queries."""
    
    def __init__(self, session_id: str, request_id: str):
        """Initialize query agent."""
        super().__init__(AgentType.QUERY_AGENT, session_id, request_id)
        self.bq_client = BigQueryClient()
        
    async def execute(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Execute the query agent's main logic.
        
        Args:
            input_data: Input data containing user query and context
            
        Returns:
            Agent response with query results
        """
        try:
            # Extract input data
            user_query = input_data.get("query", "")
            context = input_data.get("context", {})
            
            if not user_query:
                self.set_error("invalid_input", "No query provided", "MISSING_QUERY")
                return self.to_response()
            
            # Step 1: Understand the query
            self.add_step("query_understanding", "nlp_analysis")
            query_analysis = await self._analyze_query(user_query, context)
            self.update_step("query_understanding", "success", output=query_analysis)
            
            # Step 2: Get schema information if needed
            if query_analysis.get("needs_schema"):
                self.add_step("schema_retrieval", "schema_lookup")
                schema_info = await self._get_schema_info(query_analysis.get("tables", []))
                self.update_step("schema_retrieval", "success", output=schema_info)
                
                # Update session with schema info
                session_manager.update_schema_info(self.session_id, schema_info)
            else:
                schema_info = session_manager.get_session(self.session_id).schema_info
            
            # Step 3: Generate SQL query
            self.add_step("sql_generation", "nlp_to_sql")
            sql_query = await self._generate_sql(user_query, query_analysis, schema_info, context)
            self.update_step("sql_generation", "success", output={"sql_query": sql_query})
            
            # Step 4: Validate SQL query
            self.add_step("sql_validation", "query_validation")
            validation_result = self.bq_client.validate_query(sql_query)
            if not validation_result.get("valid"):
                self.update_step("sql_validation", "error", 
                               error=self._create_error("sql_validation_error", validation_result.get("error", "Unknown validation error")))
                self.set_error("sql_validation_error", validation_result.get("error", "SQL validation failed"), "SQL_VALIDATION_FAILED")
                return self.to_response()
            self.update_step("sql_validation", "success", output=validation_result)
            
            # Step 5: Execute query
            self.add_step("query_execution", "bigquery_execution")
            query_result = self.bq_client.execute_query(sql_query)
            if not query_result.get("success"):
                self.update_step("query_execution", "error",
                               error=self._create_error("query_execution_error", query_result.get("error", "Query execution failed")))
                self.set_error("query_execution_error", query_result.get("error", "Query execution failed"), "QUERY_EXECUTION_FAILED")
                return self.to_response()
            self.update_step("query_execution", "success", output=query_result)
            
            # Step 6: Format results
            self.add_step("result_formatting", "data_formatting")
            formatted_result = await self._format_results(query_result, user_query, context)
            self.update_step("result_formatting", "success", output=formatted_result)
            
            # Set final result
            self.result = {
                "original_query": user_query,
                "sql_query": sql_query,
                "query_result": query_result,
                "formatted_result": formatted_result,
                "analysis": query_analysis
            }
            
            return self.to_response()
            
        except Exception as e:
            logger.error("Query agent execution failed", error=str(e), exc_info=True)
            self.set_error("execution_error", str(e), "QUERY_AGENT_ERROR")
            return self.to_response()
    
    async def _analyze_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the user query to understand intent and requirements.
        
        Args:
            query: User's natural language query
            context: Additional context
            
        Returns:
            Query analysis
        """
        # Simple keyword-based analysis (in a real implementation, this would use NLP)
        analysis = {
            "intent": "data_retrieval",
            "tables": [],
            "needs_schema": True,
            "complexity": "simple",
            "estimated_cost": "low"
        }
        
        # Extract potential table names (simple heuristic)
        table_keywords = ["sales", "customers", "orders", "products", "revenue", "transactions"]
        found_tables = []
        
        for keyword in table_keywords:
            if keyword.lower() in query.lower():
                found_tables.append(keyword)
        
        analysis["tables"] = found_tables
        analysis["needs_schema"] = len(found_tables) > 0
        
        # Determine complexity
        if any(word in query.lower() for word in ["join", "group by", "having", "subquery"]):
            analysis["complexity"] = "complex"
        elif any(word in query.lower() for word in ["sum", "count", "average", "max", "min"]):
            analysis["complexity"] = "moderate"
        
        return analysis
    
    async def _get_schema_info(self, table_names: List[str]) -> Dict[str, Any]:
        """
        Get schema information for specified tables.
        
        Args:
            table_names: List of table names
            
        Returns:
            Schema information
        """
        schema_info = {
            "tables": {},
            "available_tables": self.bq_client.list_tables()
        }
        
        for table_name in table_names:
            try:
                table_schema = self.bq_client.get_schema_info(table_name)
                if "error" not in table_schema:
                    schema_info["tables"][table_name] = table_schema
            except Exception as e:
                logger.warning(f"Failed to get schema for table {table_name}", error=str(e))
        
        return schema_info
    
    async def _generate_sql(self, query: str, analysis: Dict[str, Any], 
                           schema_info: Optional[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Generate SQL query from natural language.
        
        Args:
            query: Natural language query
            analysis: Query analysis
            schema_info: Database schema information
            context: Additional context
            
        Returns:
            Generated SQL query
        """
        # This is a simplified implementation
        # In a real system, this would use a language model like GPT-4
        
        query_lower = query.lower()
        
        # Simple pattern matching for common queries
        if "total" in query_lower and "revenue" in query_lower:
            return "SELECT SUM(revenue) as total_revenue FROM sales"
        elif "count" in query_lower and "customers" in query_lower:
            return "SELECT COUNT(*) as customer_count FROM customers"
        elif "average" in query_lower and "order" in query_lower:
            return "SELECT AVG(order_value) as average_order_value FROM orders"
        elif "top" in query_lower and "sales" in query_lower:
            return "SELECT product_name, SUM(quantity) as total_sold FROM sales GROUP BY product_name ORDER BY total_sold DESC LIMIT 10"
        else:
            # Default fallback query
            return "SELECT * FROM sales LIMIT 10"
    
    async def _format_results(self, query_result: Dict[str, Any], original_query: str, 
                             context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format query results for user consumption.
        
        Args:
            query_result: Raw query results
            original_query: Original user query
            context: Additional context
            
        Returns:
            Formatted results
        """
        data = query_result.get("data", [])
        
        if not data:
            return {
                "summary": "No data found for your query.",
                "data": [],
                "insights": []
            }
        
        # Generate summary
        summary = self._generate_summary(data, original_query)
        
        # Extract insights
        insights = self._extract_insights(data, original_query)
        
        return {
            "summary": summary,
            "data": data,
            "insights": insights,
            "row_count": len(data),
            "execution_time_ms": query_result.get("execution_time_ms")
        }
    
    def _generate_summary(self, data: List[Dict[str, Any]], query: str) -> str:
        """Generate a natural language summary of the results."""
        if not data:
            return "No data found for your query."
        
        # Simple summary generation
        if len(data) == 1:
            row = data[0]
            if "total_revenue" in row:
                return f"The total revenue is ${row['total_revenue']:,.2f}"
            elif "customer_count" in row:
                return f"There are {row['customer_count']} customers"
            elif "average_order_value" in row:
                return f"The average order value is ${row['average_order_value']:,.2f}"
        
        return f"Found {len(data)} results for your query."
    
    def _extract_insights(self, data: List[Dict[str, Any]], query: str) -> List[str]:
        """Extract insights from the data."""
        insights = []
        
        if not data:
            return insights
        
        # Simple insight extraction
        if len(data) > 1:
            insights.append(f"Query returned {len(data)} records")
        
        # Look for patterns in the data
        for row in data[:5]:  # Analyze first 5 rows
            for key, value in row.items():
                if isinstance(value, (int, float)) and value > 1000:
                    insights.append(f"High value found in {key}: {value}")
        
        return insights
    
    def _create_error(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """Create an error object for step tracking."""
        return {
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
