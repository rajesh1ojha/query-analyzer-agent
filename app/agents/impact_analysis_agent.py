"""
Impact analysis agent for analyzing business impact of query results.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.models.agent import AgentType, AgentResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ImpactAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing business impact of query results."""
    
    def __init__(self, session_id: str, request_id: str):
        """Initialize impact analysis agent."""
        super().__init__(AgentType.IMPACT_ANALYSIS_AGENT, session_id, request_id)
        
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
            query_results = input_data.get("query_results", {})
            original_query = input_data.get("original_query", "")
            sql_query = input_data.get("sql_query", "")
            context = input_data.get("context", {})
            
            if not query_results:
                self.set_error("invalid_input", "No query results provided", "MISSING_QUERY_RESULTS")
                return self.to_response()
            
            # Step 1: Analyze query intent
            self.add_step("intent_analysis", "business_intent_analysis")
            intent_analysis = await self._analyze_query_intent(original_query, sql_query, context)
            self.update_step("intent_analysis", "success", output=intent_analysis)
            
            # Step 2: Extract key metrics
            self.add_step("metric_extraction", "data_metric_analysis")
            key_metrics = await self._extract_key_metrics(query_results, intent_analysis)
            self.update_step("metric_extraction", "success", output=key_metrics)
            
            # Step 3: Calculate impact scores
            self.add_step("impact_calculation", "business_impact_analysis")
            impact_scores = await self._calculate_impact_scores(key_metrics, intent_analysis, context)
            self.update_step("impact_calculation", "success", output=impact_scores)
            
            # Step 4: Generate insights
            self.add_step("insight_generation", "business_insight_analysis")
            insights = await self._generate_insights(key_metrics, impact_scores, intent_analysis)
            self.update_step("insight_generation", "success", output=insights)
            
            # Step 5: Generate recommendations
            self.add_step("recommendation_generation", "action_recommendation_analysis")
            recommendations = await self._generate_recommendations(insights, impact_scores, context)
            self.update_step("recommendation_generation", "success", output=recommendations)
            
            # Step 6: Assess confidence
            self.add_step("confidence_assessment", "analysis_confidence_evaluation")
            confidence_level = await self._assess_confidence(intent_analysis, key_metrics, insights)
            self.update_step("confidence_assessment", "success", output={"confidence_level": confidence_level})
            
            # Set final result
            self.result = {
                "original_query": original_query,
                "intent_analysis": intent_analysis,
                "key_metrics": key_metrics,
                "impact_scores": impact_scores,
                "insights": insights,
                "recommendations": recommendations,
                "confidence_level": confidence_level,
                "overall_impact_score": self._calculate_overall_impact(impact_scores)
            }
            
            return self.to_response()
            
        except Exception as e:
            logger.error("Impact analysis agent execution failed", error=str(e), exc_info=True)
            self.set_error("execution_error", str(e), "IMPACT_ANALYSIS_AGENT_ERROR")
            return self.to_response()
    
    async def _analyze_query_intent(self, original_query: str, sql_query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the business intent behind the query.
        
        Args:
            original_query: Original natural language query
            sql_query: Generated SQL query
            context: Additional context
            
        Returns:
            Intent analysis
        """
        intent_analysis = {
            "business_domain": "unknown",
            "query_type": "data_retrieval",
            "business_metrics": [],
            "time_dimension": None,
            "comparison_type": None,
            "urgency_level": "normal"
        }
        
        query_lower = original_query.lower()
        
        # Determine business domain
        if any(word in query_lower for word in ["revenue", "sales", "profit", "income"]):
            intent_analysis["business_domain"] = "financial"
            intent_analysis["business_metrics"].append("revenue")
        elif any(word in query_lower for word in ["customers", "users", "clients"]):
            intent_analysis["business_domain"] = "customer"
            intent_analysis["business_metrics"].append("customer_count")
        elif any(word in query_lower for word in ["orders", "transactions", "purchases"]):
            intent_analysis["business_domain"] = "operational"
            intent_analysis["business_metrics"].append("transaction_volume")
        
        # Determine time dimension
        if any(word in query_lower for word in ["today", "yesterday", "this week"]):
            intent_analysis["time_dimension"] = "recent"
        elif any(word in query_lower for word in ["this month", "this quarter", "this year"]):
            intent_analysis["time_dimension"] = "periodic"
        elif any(word in query_lower for word in ["trend", "growth", "over time"]):
            intent_analysis["time_dimension"] = "trend"
        
        # Determine comparison type
        if any(word in query_lower for word in ["vs", "versus", "compared", "difference"]):
            intent_analysis["comparison_type"] = "comparative"
        elif any(word in query_lower for word in ["trend", "growth", "increase", "decrease"]):
            intent_analysis["comparison_type"] = "trend"
        
        # Determine urgency
        if any(word in query_lower for word in ["urgent", "critical", "immediate", "now"]):
            intent_analysis["urgency_level"] = "high"
        
        return intent_analysis
    
    async def _extract_key_metrics(self, query_results: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key business metrics from query results.
        
        Args:
            query_results: Query execution results
            intent_analysis: Intent analysis
            
        Returns:
            Key metrics
        """
        data = query_results.get("data", [])
        key_metrics = {
            "primary_metric": None,
            "secondary_metrics": [],
            "trend_indicators": [],
            "anomalies": [],
            "data_quality": "good"
        }
        
        if not data:
            return key_metrics
        
        # Extract primary metric based on intent
        business_metrics = intent_analysis.get("business_metrics", [])
        
        for row in data:
            for key, value in row.items():
                if isinstance(value, (int, float)):
                    # Check if this matches expected business metrics
                    if any(metric in key.lower() for metric in business_metrics):
                        if key_metrics["primary_metric"] is None:
                            key_metrics["primary_metric"] = {
                                "name": key,
                                "value": value,
                                "type": "primary"
                            }
                    else:
                        key_metrics["secondary_metrics"].append({
                            "name": key,
                            "value": value,
                            "type": "secondary"
                        })
        
        # Detect anomalies (simplified)
        if key_metrics["primary_metric"]:
            primary_value = key_metrics["primary_metric"]["value"]
            if isinstance(primary_value, (int, float)):
                if primary_value < 0:
                    key_metrics["anomalies"].append("Negative value detected")
                elif primary_value == 0:
                    key_metrics["anomalies"].append("Zero value detected")
        
        return key_metrics
    
    async def _calculate_impact_scores(self, key_metrics: Dict[str, Any], intent_analysis: Dict[str, Any], 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate business impact scores.
        
        Args:
            key_metrics: Extracted key metrics
            intent_analysis: Intent analysis
            context: Additional context
            
        Returns:
            Impact scores
        """
        impact_scores = {
            "financial_impact": 0.0,
            "operational_impact": 0.0,
            "strategic_impact": 0.0,
            "risk_level": "low",
            "opportunity_score": 0.0
        }
        
        primary_metric = key_metrics.get("primary_metric")
        if not primary_metric:
            return impact_scores
        
        value = primary_metric["value"]
        metric_name = primary_metric["name"].lower()
        
        # Calculate financial impact
        if intent_analysis["business_domain"] == "financial":
            if "revenue" in metric_name or "profit" in metric_name or "income" in metric_name:
                if isinstance(value, (int, float)):
                    if value > 1000000:
                        impact_scores["financial_impact"] = 0.9
                    elif value > 100000:
                        impact_scores["financial_impact"] = 0.7
                    elif value > 10000:
                        impact_scores["financial_impact"] = 0.5
                    else:
                        impact_scores["financial_impact"] = 0.3
        
        # Calculate operational impact
        if intent_analysis["business_domain"] == "operational":
            if "transaction" in metric_name or "order" in metric_name:
                if isinstance(value, (int, float)):
                    if value > 10000:
                        impact_scores["operational_impact"] = 0.8
                    elif value > 1000:
                        impact_scores["operational_impact"] = 0.6
                    else:
                        impact_scores["operational_impact"] = 0.4
        
        # Calculate strategic impact based on urgency and comparison type
        if intent_analysis["urgency_level"] == "high":
            impact_scores["strategic_impact"] = 0.8
        elif intent_analysis["comparison_type"] == "trend":
            impact_scores["strategic_impact"] = 0.6
        
        # Calculate risk level
        anomalies = key_metrics.get("anomalies", [])
        if len(anomalies) > 0:
            impact_scores["risk_level"] = "medium"
        if impact_scores["financial_impact"] > 0.7:
            impact_scores["risk_level"] = "high"
        
        # Calculate opportunity score
        if impact_scores["financial_impact"] > 0.5 or impact_scores["operational_impact"] > 0.5:
            impact_scores["opportunity_score"] = 0.7
        
        return impact_scores
    
    async def _generate_insights(self, key_metrics: Dict[str, Any], impact_scores: Dict[str, Any], 
                               intent_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate business insights from the analysis.
        
        Args:
            key_metrics: Key metrics
            impact_scores: Impact scores
            intent_analysis: Intent analysis
            
        Returns:
            List of insights
        """
        insights = []
        
        primary_metric = key_metrics.get("primary_metric")
        if not primary_metric:
            return insights
        
        value = primary_metric["value"]
        metric_name = primary_metric["name"]
        
        # Financial insights
        if intent_analysis["business_domain"] == "financial":
            if isinstance(value, (int, float)):
                if value > 1000000:
                    insights.append({
                        "type": "financial_performance",
                        "category": "positive",
                        "description": f"Strong financial performance with {metric_name} of ${value:,.2f}",
                        "confidence": "high"
                    })
                elif value < 0:
                    insights.append({
                        "type": "financial_concern",
                        "category": "negative",
                        "description": f"Financial concern: {metric_name} is negative ({value})",
                        "confidence": "high"
                    })
        
        # Operational insights
        if intent_analysis["business_domain"] == "operational":
            if isinstance(value, (int, float)):
                if value > 1000:
                    insights.append({
                        "type": "operational_volume",
                        "category": "positive",
                        "description": f"High operational volume: {value} {metric_name}",
                        "confidence": "medium"
                    })
        
        # Trend insights
        if intent_analysis["comparison_type"] == "trend":
            insights.append({
                "type": "trend_analysis",
                "category": "informational",
                "description": "Query indicates trend analysis intent",
                "confidence": "medium"
            })
        
        # Risk insights
        anomalies = key_metrics.get("anomalies", [])
        for anomaly in anomalies:
            insights.append({
                "type": "data_anomaly",
                "category": "warning",
                "description": f"Data anomaly detected: {anomaly}",
                "confidence": "high"
            })
        
        return insights
    
    async def _generate_recommendations(self, insights: List[Dict[str, Any]], impact_scores: Dict[str, Any], 
                                      context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations based on insights.
        
        Args:
            insights: Generated insights
            impact_scores: Impact scores
            context: Additional context
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # High financial impact recommendations
        if impact_scores["financial_impact"] > 0.7:
            recommendations.append({
                "type": "financial_monitoring",
                "priority": "high",
                "description": "Monitor financial metrics closely due to high impact",
                "action": "Set up automated alerts for financial thresholds",
                "expected_outcome": "Early detection of financial issues"
            })
        
        # Risk mitigation recommendations
        if impact_scores["risk_level"] == "high":
            recommendations.append({
                "type": "risk_mitigation",
                "priority": "high",
                "description": "High risk level detected - implement risk controls",
                "action": "Review and update risk management procedures",
                "expected_outcome": "Reduced exposure to financial and operational risks"
            })
        
        # Data quality recommendations
        for insight in insights:
            if insight["type"] == "data_anomaly":
                recommendations.append({
                    "type": "data_quality",
                    "priority": "medium",
                    "description": "Data quality issues detected",
                    "action": "Investigate and resolve data anomalies",
                    "expected_outcome": "Improved data reliability and decision-making"
                })
                break
        
        # Opportunity recommendations
        if impact_scores["opportunity_score"] > 0.5:
            recommendations.append({
                "type": "opportunity_exploration",
                "priority": "medium",
                "description": "High opportunity score detected",
                "action": "Conduct deeper analysis to identify growth opportunities",
                "expected_outcome": "Identification of new business opportunities"
            })
        
        return recommendations
    
    async def _assess_confidence(self, intent_analysis: Dict[str, Any], key_metrics: Dict[str, Any], 
                               insights: List[Dict[str, Any]]) -> float:
        """
        Assess confidence level of the analysis.
        
        Args:
            intent_analysis: Intent analysis
            key_metrics: Key metrics
            insights: Generated insights
            
        Returns:
            Confidence level (0-1)
        """
        confidence_factors = []
        
        # Intent clarity
        if intent_analysis["business_domain"] != "unknown":
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.3)
        
        # Data quality
        if key_metrics["data_quality"] == "good":
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.5)
        
        # Metric availability
        if key_metrics["primary_metric"]:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.2)
        
        # Insight quality
        if len(insights) > 0:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.4)
        
        # Calculate average confidence
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.5
    
    def _calculate_overall_impact(self, impact_scores: Dict[str, Any]) -> float:
        """
        Calculate overall impact score.
        
        Args:
            impact_scores: Individual impact scores
            
        Returns:
            Overall impact score (0-1)
        """
        weights = {
            "financial_impact": 0.4,
            "operational_impact": 0.3,
            "strategic_impact": 0.3
        }
        
        overall_score = 0.0
        for impact_type, weight in weights.items():
            overall_score += impact_scores.get(impact_type, 0.0) * weight
        
        return min(1.0, overall_score)
