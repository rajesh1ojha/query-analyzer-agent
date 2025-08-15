"""
Query agent for natural language to SQL conversion and execution.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.models.agent import AgentType, AgentResponse
from app.utils.bigquery_client import BigQueryClient
from app.utils.azure_openai_client import AzureOpenAIClient
from app.utils.logger import get_logger
from app.core.session_manager import session_manager

logger = get_logger(__name__)


class QueryAgent(BaseAgent):
    """Agent responsible for converting natural language to SQL and executing queries."""
    
    def __init__(self, session_id: str, request_id: str):
        """Initialize query agent."""
        super().__init__(AgentType.QUERY_AGENT, session_id, request_id)
        self.bq_client = BigQueryClient()
        self.llm_client = AzureOpenAIClient()
        
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
            
            # Step 1: Understand the query using LLM
            self.add_step("query_understanding", "nlp_analysis")
            query_analysis = await self._analyze_query(user_query, context)
            self.update_step("query_understanding", "success", output=query_analysis)
            
            # Step 2: Get schema information if needed
            if query_analysis.get("entities") or query_analysis.get("needs_schema", True):
                self.add_step("schema_retrieval", "schema_lookup")
                schema_info = await self._get_schema_info(query_analysis.get("entities", []))
                self.update_step("schema_retrieval", "success", output=schema_info)
                
                # Update session with schema info
                session_manager.update_schema_info(self.session_id, schema_info)
            else:
                schema_info = session_manager.get_session(self.session_id).schema_info
            
            # Step 3: Generate SQL query using LLM
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
            
            # Step 6: Format results using LLM
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
        Analyze the user query to understand intent and requirements using LLM.
        
        Args:
            query: User's natural language query
            context: Additional context
            
        Returns:
            Query analysis
        """
        # Use LLM for advanced query analysis - no fallback to hardcoded patterns
        analysis = await self.llm_client.analyze_query_intent(query, context)
        
        # Add additional metadata
        analysis["needs_schema"] = len(analysis.get("entities", [])) > 0
        analysis["timestamp"] = datetime.utcnow().isoformat()
        
        return analysis
    
    async def _get_schema_info(self, table_names: List[str]) -> Dict[str, Any]:
        """
        Get comprehensive schema information for specified tables using INFORMATION_SCHEMA.
        
        Args:
            table_names: List of table names
            
        Returns:
            Comprehensive schema information
        """
        try:
            # Get comprehensive schema info from INFORMATION_SCHEMA
            schema_info = self.bq_client.get_comprehensive_schema_info(table_names)
            
            if "error" in schema_info:
                logger.warning("Failed to get comprehensive schema, falling back to basic schema", error=schema_info["error"])
                # Fallback to basic schema info
                schema_info = {
                    "tables": {},
                    "available_tables": self.bq_client.list_tables()
                }
                
                for table_name in table_names:
                    try:
                        table_schema = self.bq_client._get_basic_schema_info(table_name)
                        if "error" not in table_schema:
                            schema_info["tables"][table_name] = table_schema
                    except Exception as e:
                        logger.warning(f"Failed to get basic schema for table {table_name}", error=str(e))
            
            # Add available tables list if not present
            if "available_tables" not in schema_info:
                schema_info["available_tables"] = self.bq_client.list_tables()
            
            return schema_info
            
        except Exception as e:
            logger.error("Schema retrieval failed", error=str(e))
            return {
                "tables": {},
                "available_tables": self.bq_client.list_tables(),
                "error": str(e)
            }
    
    async def _generate_sql(self, query: str, analysis: Dict[str, Any], 
                           schema_info: Optional[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Generate SQL query from natural language using LLM.
        
        Args:
            query: Natural language query
            analysis: Query analysis
            schema_info: Database schema information
            context: Additional context
            
        Returns:
            Generated SQL query
        """
        # Use LLM for SQL generation - no fallback to hardcoded patterns
        sql_query = await self.llm_client.generate_sql_query(query, schema_info or {}, analysis)
        return sql_query
    
    async def _format_results(self, query_result: Dict[str, Any], original_query: str, 
                             context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format query results for user consumption using LLM.
        
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
        
        # Use LLM for summary and insights generation - no fallback
        summary = await self.llm_client.generate_summary(query_result, original_query)
        insights = await self.llm_client.generate_insights(query_result, original_query)
        
        return {
            "summary": summary,
            "data": data,
            "insights": insights,
            "row_count": len(data),
            "execution_time_ms": query_result.get("execution_time_ms")
        }
    
    def _create_error(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """Create error object for agent steps."""
        return {
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }

