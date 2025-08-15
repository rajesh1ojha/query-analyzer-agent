"""
Impact analysis agent for analyzing business impact of query results.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.models.agent import AgentType, AgentResponse
from app.utils.azure_openai_client import AzureOpenAIClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ImpactAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing business impact of query results."""
    
    def __init__(self, session_id: str, request_id: str):
        """Initialize impact analysis agent."""
        super().__init__(AgentType.IMPACT_ANALYSIS_AGENT, session_id, request_id)
        self.llm_client = AzureOpenAIClient()
        
    async def execute(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Execute the impact analysis agent's main logic.
        
        Args:
            input_data: Input data containing query results and context
            
        Returns:
            Agent response with impact analysis
        """
        try:
            # Extract input data
            original_query = input_data.get("original_query", "")
            sql_query = input_data.get("sql_query", "")
            query_result = input_data.get("query_result", {})
            context = input_data.get("context", {})
            
            if not original_query or not query_result:
                self.set_error("invalid_input", "Missing query or results", "MISSING_DATA")
                return self.to_response()
            
            # Step 1: Analyze query intent and business context
            self.add_step("intent_analysis", "business_intent")
            intent_analysis = await self._analyze_query_intent(original_query, sql_query, context)
            self.update_step("intent_analysis", "success", output=intent_analysis)
            
            # Step 2: Extract key metrics and KPIs
            self.add_step("metric_extraction", "kpi_identification")
            key_metrics = await self._extract_key_metrics(query_result, intent_analysis)
            self.update_step("metric_extraction", "success", output=key_metrics)
            
            # Step 3: Calculate impact scores
            self.add_step("impact_calculation", "impact_scoring")
            impact_scores = await self._calculate_impact_scores(key_metrics, intent_analysis, context)
            self.update_step("impact_calculation", "success", output=impact_scores)
            
            # Step 4: Generate business insights
            self.add_step("insight_generation", "business_insights")
            insights = await self._generate_insights(query_result, intent_analysis, key_metrics, context)
            self.update_step("insight_generation", "success", output=insights)
            
            # Step 5: Generate actionable recommendations
            self.add_step("recommendation_generation", "action_items")
            recommendations = await self._generate_recommendations(insights, impact_scores, context)
            self.update_step("recommendation_generation", "success", output=recommendations)
            
            # Step 6: Assess confidence and reliability
            self.add_step("confidence_assessment", "reliability_check")
            confidence = await self._assess_confidence(query_result, intent_analysis, context)
            self.update_step("confidence_assessment", "success", output=confidence)
            
            # Set final result
            self.result = {
                "intent_analysis": intent_analysis,
                "key_metrics": key_metrics,
                "impact_scores": impact_scores,
                "insights": insights,
                "recommendations": recommendations,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return self.to_response()
            
        except Exception as e:
            logger.error("Impact analysis agent execution failed", error=str(e), exc_info=True)
            self.set_error("execution_error", str(e), "IMPACT_ANALYSIS_ERROR")
            return self.to_response()
    
    async def _analyze_query_intent(self, original_query: str, sql_query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the business intent behind the query using LLM with enhanced schema context.
        
        Args:
            original_query: Original user query
            sql_query: Generated SQL query
            context: Additional context including schema information
            
        Returns:
            Intent analysis
        """
        # Use LLM for business intent analysis with enhanced context
        system_prompt = """You are a business analyst with deep understanding of data structures and business intelligence. 
Analyze the user's query to understand:

1. Business objective (what business question they're trying to answer)
2. Stakeholder (who would care about this data - executives, analysts, operations, etc.)
3. Decision impact (what decisions could be made from this data)
4. Business domain (sales, marketing, operations, finance, customer service, etc.)
5. Urgency level (high/medium/low)
6. Data complexity (simple aggregation, complex joins, time-series analysis, etc.)
7. Business metrics involved (revenue, customer count, conversion rates, etc.)

Consider the schema context to understand the data structure and business meaning of tables and columns.

Respond with a JSON object containing:
{
    "business_objective": "string",
    "stakeholder": "string",
    "decision_impact": "string",
    "business_domain": "string",
    "urgency_level": "high|medium|low",
    "strategic_importance": "high|medium|low",
    "data_complexity": "simple|moderate|complex",
    "business_metrics": ["metric1", "metric2"],
    "time_dimension": "historical|current|trending|forecasting",
    "comparison_type": "absolute|relative|trend|benchmark"
}"""

        # Extract schema context if available
        schema_context = ""
        if context and "schema_info" in context:
            schema_context = f"\nSchema Context:\n{self._format_schema_context(context['schema_info'])}"

        user_prompt = f"""Original Query: {original_query}
SQL Query: {sql_query}
Context: {context}{schema_context}

Analyze the business intent:"""

        response = await self.llm_client.client.chat.completions.create(
            model=self.llm_client.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        import json
        intent_analysis = json.loads(content)
        
        logger.info("Business intent analysis completed", intent=intent_analysis)
        return intent_analysis
    
    async def _extract_key_metrics(self, query_result: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key metrics and KPIs from query results using LLM.
        
        Args:
            query_result: Query execution results
            intent_analysis: Business intent analysis
            
        Returns:
            Key metrics analysis
        """
        # Use LLM for metric extraction
        system_prompt = """You are a data analyst. Extract key metrics and KPIs from the query results.
Identify:
1. Primary metrics (main numbers/values)
2. Trends or patterns
3. Anomalies or outliers
4. Performance indicators
5. Business implications

Respond with a JSON object containing:
{
    "primary_metrics": [{"name": "string", "value": "number", "trend": "up|down|stable"}],
    "trends": ["trend1", "trend2"],
    "anomalies": ["anomaly1", "anomaly2"],
    "performance_indicators": ["kpi1", "kpi2"],
    "business_implications": ["implication1", "implication2"]
}"""

        data_summary = self._format_data_for_metrics(query_result)
        
        user_prompt = f"""Query Results:
{data_summary}

Business Intent: {intent_analysis}

Extract key metrics:"""

        response = await self.llm_client.client.chat.completions.create(
            model=self.llm_client.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        import json
        metrics = json.loads(content)
        
        logger.info("Key metrics extracted", metrics_count=len(metrics.get("primary_metrics", [])))
        return metrics
    
    async def _calculate_impact_scores(self, key_metrics: Dict[str, Any], intent_analysis: Dict[str, Any], 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate business impact scores using LLM.
        
        Args:
            key_metrics: Extracted key metrics
            intent_analysis: Business intent analysis
            context: Additional context
            
        Returns:
            Impact scores
        """
        # Use LLM for impact scoring
        system_prompt = """You are a business impact analyst. Calculate impact scores for the query results.
Consider:
1. Financial impact (revenue, cost, profit implications)
2. Operational impact (efficiency, productivity, process changes)
3. Strategic impact (long-term business goals, competitive advantage)
4. Risk impact (potential risks or opportunities)

Score each dimension from 1-10 (10 being highest impact).

Respond with a JSON object containing:
{
    "financial_impact": {"score": 1-10, "reasoning": "string"},
    "operational_impact": {"score": 1-10, "reasoning": "string"},
    "strategic_impact": {"score": 1-10, "reasoning": "string"},
    "risk_impact": {"score": 1-10, "reasoning": "string"},
    "overall_impact": "high|medium|low"
}"""

        user_prompt = f"""Key Metrics: {key_metrics}
Business Intent: {intent_analysis}
Context: {context}

Calculate impact scores:"""

        response = await self.llm_client.client.chat.completions.create(
            model=self.llm_client.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=400
        )
        
        content = response.choices[0].message.content
        import json
        impact_scores = json.loads(content)
        
        logger.info("Impact scores calculated", overall_impact=impact_scores.get("overall_impact"))
        return impact_scores
    
    async def _generate_insights(self, query_result: Dict[str, Any], intent_analysis: Dict[str, Any], 
                               key_metrics: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """
        Generate business insights using LLM.
        
        Args:
            query_result: Query execution results
            intent_analysis: Business intent analysis
            key_metrics: Extracted key metrics
            context: Additional context
            
        Returns:
            List of business insights
        """
        # Use LLM for insight generation
        system_prompt = """You are a business analyst. Generate 3-5 key business insights from the data.
Focus on:
- What the data reveals about business performance
- Unexpected findings or patterns
- Implications for decision-making
- Opportunities or risks identified

Keep insights concise and actionable."""

        data_summary = self._format_data_for_insights(query_result)
        
        user_prompt = f"""Query Results:
{data_summary}

Business Intent: {intent_analysis}
Key Metrics: {key_metrics}

Generate business insights:"""

        response = await self.llm_client.client.chat.completions.create(
            model=self.llm_client.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        
        insights_text = response.choices[0].message.content.strip()
        insights = [insight.strip() for insight in insights_text.split('\n') if insight.strip()]
        
        logger.info("Business insights generated", insights_count=len(insights))
        return insights
    
    async def _generate_recommendations(self, insights: List[str], impact_scores: Dict[str, Any], 
                                      context: Dict[str, Any]) -> List[str]:
        """
        Generate actionable recommendations using LLM.
        
        Args:
            insights: Business insights
            impact_scores: Impact scores
            context: Additional context
            
        Returns:
            List of recommendations
        """
        # Use LLM for recommendation generation
        system_prompt = """You are a business consultant. Generate 3-5 actionable recommendations based on the insights.
Focus on:
- Specific actions to take
- Who should take them
- Expected outcomes
- Timeline considerations

Make recommendations practical and implementable."""

        user_prompt = f"""Business Insights: {insights}
Impact Scores: {impact_scores}
Context: {context}

Generate actionable recommendations:"""

        response = await self.llm_client.client.chat.completions.create(
            model=self.llm_client.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        
        recommendations_text = response.choices[0].message.content.strip()
        recommendations = [rec.strip() for rec in recommendations_text.split('\n') if rec.strip()]
        
        logger.info("Recommendations generated", recommendations_count=len(recommendations))
        return recommendations
    
    async def _assess_confidence(self, query_result: Dict[str, Any], intent_analysis: Dict[str, Any], 
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess confidence and reliability of the analysis using LLM.
        
        Args:
            query_result: Query execution results
            intent_analysis: Business intent analysis
            context: Additional context
            
        Returns:
            Confidence assessment
        """
        # Use LLM for confidence assessment
        system_prompt = """You are a data quality analyst. Assess the confidence and reliability of the analysis.
Consider:
1. Data quality (completeness, accuracy, timeliness)
2. Sample size adequacy
3. Methodology reliability
4. Context completeness
5. Potential biases

Score confidence from 1-10 (10 being highest confidence).

Respond with a JSON object containing:
{
    "data_quality_score": 1-10,
    "sample_adequacy_score": 1-10,
    "methodology_score": 1-10,
    "overall_confidence": "high|medium|low",
    "limitations": ["limitation1", "limitation2"],
    "recommendations_for_improvement": ["rec1", "rec2"]
}"""

        data_summary = self._format_data_for_confidence(query_result)
        
        user_prompt = f"""Query Results:
{data_summary}

Business Intent: {intent_analysis}

Assess confidence and reliability:"""

        response = await self.llm_client.client.chat.completions.create(
            model=self.llm_client.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=400
        )
        
        content = response.choices[0].message.content
        import json
        confidence = json.loads(content)
        
        logger.info("Confidence assessment completed", overall_confidence=confidence.get("overall_confidence"))
        return confidence
    
    def _format_data_for_metrics(self, query_result: Dict[str, Any]) -> str:
        """Format query results for metric extraction."""
        data = query_result.get("data", [])
        if not data:
            return "No data returned"
        
        summary = f"Rows returned: {len(data)}\n"
        if data:
            summary += f"Columns: {list(data[0].keys())}\n"
            summary += "Sample data:\n"
            for i, row in enumerate(data[:5]):
                summary += f"  Row {i+1}: {row}\n"
        
        return summary
    
    def _format_data_for_insights(self, query_result: Dict[str, Any]) -> str:
        """Format query results for insight generation."""
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
    
    def _format_data_for_confidence(self, query_result: Dict[str, Any]) -> str:
        """Format query results for confidence assessment."""
        data = query_result.get("data", [])
        if not data:
            return "No data returned"
        
        summary = f"Data points: {len(data)}\n"
        if data:
            summary += f"Columns: {list(data[0].keys())}\n"
            summary += f"Data types: {[type(val).__name__ for val in data[0].values()]}\n"
        
        return summary
    
    def _format_schema_context(self, schema_info: Dict[str, Any]) -> str:
        """Format schema information for business context analysis."""
        if not schema_info or not schema_info.get("tables"):
            return "No schema information available"
        
        context_lines = []
        context_lines.append("Available Tables and Their Business Context:")
        
        for table_name, table_info in schema_info["tables"].items():
            context_lines.append(f"\n{table_name}:")
            
            # Add table description if available
            if "description" in table_info and table_info["description"]:
                context_lines.append(f"  Purpose: {table_info['description']}")
            
            # Add key business columns
            if "columns" in table_info:
                if isinstance(table_info["columns"], list):
                    # Comprehensive schema format
                    business_columns = []
                    for col in table_info["columns"]:
                        if col.get('description') and any(keyword in col['description'].lower() 
                                                        for keyword in ['revenue', 'customer', 'order', 'date', 'amount', 'count']):
                            business_columns.append(f"{col['name']} ({col['description']})")
                    
                    if business_columns:
                        context_lines.append(f"  Key Business Columns: {', '.join(business_columns[:5])}")
                else:
                    # Basic schema format
                    business_columns = []
                    for col_name, col_info in table_info["columns"].items():
                        if col_info.get('description') and any(keyword in col_info['description'].lower() 
                                                             for keyword in ['revenue', 'customer', 'order', 'date', 'amount', 'count']):
                            business_columns.append(f"{col_name} ({col_info['description']})")
                    
                    if business_columns:
                        context_lines.append(f"  Key Business Columns: {', '.join(business_columns[:5])}")
        
        return "\n".join(context_lines)

