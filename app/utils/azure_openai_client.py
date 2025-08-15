"""
Azure OpenAI client for LLM integration.
"""

import asyncio
from typing import Dict, Any, List, Optional
from openai import AzureOpenAI
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AzureOpenAIClient:
    """Azure OpenAI client for LLM operations."""
    
    def __init__(self):
        """Initialize Azure OpenAI client."""
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint
        )
        self.deployment_name = settings.azure_openai_deployment_name
        
    async def analyze_query_intent(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze user query to understand intent and requirements using LLM.
        
        Args:
            query: User's natural language query
            context: Additional context
            
        Returns:
            Query analysis with intent, entities, and requirements
        """
        system_prompt = """You are an expert data analyst assistant. Analyze the user's query to understand:
1. Intent (what they want to know)
2. Entities (tables, columns, metrics mentioned)
3. Time period (if any)
4. Aggregation type (sum, count, average, etc.)
5. Filters or conditions
6. Complexity level
7. Business context and domain

Respond with a JSON object containing:
{
    "intent": "string",
    "entities": ["table1", "table2"],
    "metrics": ["metric1", "metric2"],
    "time_period": "string or null",
    "aggregation": "string or null",
    "filters": ["filter1", "filter2"],
    "complexity": "simple|moderate|complex",
    "estimated_cost": "low|medium|high",
    "business_domain": "sales|marketing|finance|operations|customer|general"
}"""

        user_prompt = f"Query: {query}\nContext: {context or {}}"
        
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        # Parse JSON response
        import json
        analysis = json.loads(content)
        
        logger.info("Query intent analysis completed", query=query, analysis=analysis)
        return analysis
    
    async def generate_sql_query(self, query: str, schema_info: Dict[str, Any], 
                                analysis: Dict[str, Any]) -> str:
        """
        Generate SQL query from natural language using LLM.
        
        Args:
            query: Natural language query
            schema_info: Database schema information
            analysis: Query analysis
            
        Returns:
            Generated SQL query
        """
        system_prompt = """You are an expert SQL developer specializing in BigQuery. Generate a BigQuery SQL query based on the user's request.
Use the provided schema information to ensure table and column names are correct.
Follow BigQuery syntax and best practices.
Return ONLY the SQL query, no explanations."""

        schema_context = self._format_schema_for_prompt(schema_info)
        
        user_prompt = f"""User Query: {query}

Schema Information:
{schema_context}

Query Analysis: {analysis}

Generate a BigQuery SQL query:"""

        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up the response (remove markdown if present)
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        sql_query = sql_query.strip()
        
        logger.info("SQL query generated", original_query=query, sql_query=sql_query)
        return sql_query
    
    async def generate_insights(self, query_result: Dict[str, Any], original_query: str) -> List[str]:
        """
        Generate insights from query results using LLM.
        
        Args:
            query_result: Query execution results
            original_query: Original user query
            
        Returns:
            List of insights
        """
        system_prompt = """You are a data analyst. Analyze the query results and provide 2-3 key insights.
Focus on trends, patterns, anomalies, or business implications.
Keep insights concise and actionable."""

        data_summary = self._format_data_for_insights(query_result)
        
        user_prompt = f"""Original Query: {original_query}

Query Results:
{data_summary}

Provide 2-3 key insights:"""

        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        insights_text = response.choices[0].message.content.strip()
        insights = [insight.strip() for insight in insights_text.split('\n') if insight.strip()]
        
        logger.info("Insights generated", insights_count=len(insights))
        return insights
    
    async def generate_summary(self, query_result: Dict[str, Any], original_query: str) -> str:
        """
        Generate natural language summary of query results.
        
        Args:
            query_result: Query execution results
            original_query: Original user query
            
        Returns:
            Natural language summary
        """
        system_prompt = """You are a data analyst. Provide a concise, natural language summary of the query results.
Focus on answering the user's original question in a clear, business-friendly way."""

        data_summary = self._format_data_for_summary(query_result)
        
        user_prompt = f"""Original Query: {original_query}

Query Results:
{data_summary}

Provide a natural language summary:"""

        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=200
        )
        
        summary = response.choices[0].message.content.strip()
        
        logger.info("Summary generated", summary_length=len(summary))
        return summary
    
    def _format_schema_for_prompt(self, schema_info: Dict[str, Any]) -> str:
        """Format schema information for LLM prompt using comprehensive schema data."""
        if not schema_info or not schema_info.get("tables"):
            return "No schema information available"
        
        schema_text = []
        schema_text.append(f"Database: {schema_info.get('project', 'unknown')}.{schema_info.get('dataset', 'unknown')}")
        schema_text.append("=" * 50)
        
        for table_name, table_info in schema_info["tables"].items():
            schema_text.append(f"\nTable: {table_name}")
            if "column_count" in table_info:
                schema_text.append(f"Columns: {table_info['column_count']}")
            
            # Add table metadata if available
            if "row_count" in table_info:
                schema_text.append(f"Rows: {table_info['row_count']:,}")
            if "size_mb" in table_info:
                schema_text.append(f"Size: {table_info['size_mb']:.2f} MB")
            if "description" in table_info and table_info["description"]:
                schema_text.append(f"Description: {table_info['description']}")
            
            # Add partitioning and clustering info
            if "partitioning_column" in table_info and table_info["partitioning_column"]:
                schema_text.append(f"Partitioned by: {table_info['partitioning_column']}")
            if "clustering_fields" in table_info and table_info["clustering_fields"]:
                schema_text.append(f"Clustered by: {', '.join(table_info['clustering_fields'])}")
            
            schema_text.append("\nColumns:")
            
            # Check if we have comprehensive schema (from INFORMATION_SCHEMA)
            if "columns" in table_info and isinstance(table_info["columns"], list):
                # Comprehensive schema format
                for col in table_info["columns"]:
                    col_desc = f"  - {col['name']}: {col['type']}"
                    if col.get('description'):
                        col_desc += f" ({col['description']})"
                    if col.get('nullable') is False:
                        col_desc += " [NOT NULL]"
                    if col.get('default'):
                        col_desc += f" [DEFAULT: {col['default']}]"
                    schema_text.append(col_desc)
            else:
                # Basic schema format (fallback)
                for col_name, col_info in table_info.get("columns", {}).items():
                    col_desc = f"  - {col_name}: {col_info.get('data_type', 'unknown')}"
                    if col_info.get('description'):
                        col_desc += f" ({col_info['description']})"
                    schema_text.append(col_desc)
            
            schema_text.append("")
        
        return "\n".join(schema_text)
    
    def _format_data_for_insights(self, query_result: Dict[str, Any]) -> str:
        """Format query results for insights generation."""
        data = query_result.get("data", [])
        if not data:
            return "No data returned"
        
        # Show first few rows and summary stats
        summary = f"Rows returned: {len(data)}\n"
        if data:
            summary += f"Columns: {list(data[0].keys())}\n"
            summary += "Sample data:\n"
            for i, row in enumerate(data[:3]):
                summary += f"  Row {i+1}: {row}\n"
        
        return summary
    
    def _format_data_for_summary(self, query_result: Dict[str, Any]) -> str:
        """Format query results for summary generation."""
        data = query_result.get("data", [])
        if not data:
            return "No data returned"
        
        summary = f"Total rows: {len(data)}\n"
        if data:
            summary += f"Columns: {list(data[0].keys())}\n"
            # Show key metrics if available
            for key, value in data[0].items():
                if isinstance(value, (int, float)):
                    summary += f"{key}: {value}\n"
        
        return summary
