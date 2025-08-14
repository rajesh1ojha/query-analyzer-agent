# API Documentation

## Overview

The Agentic BigQuery App provides a RESTful API for natural language query processing, session management, and agent monitoring.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms.

## Response Format

All API responses follow this format:

```json
{
  "data": {...},
  "message": "Success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Handling

Errors are returned with appropriate HTTP status codes:

```json
{
  "error": "Error message",
  "request_id": "uuid",
  "status_code": 400
}
```

## Endpoints

### Health Check

#### GET /health/

Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "development"
}
```

#### GET /health/ready

Readiness check including external dependencies.

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2024-01-15T10:30:00Z",
  "dependencies": {
    "bigquery": "connected",
    "tables_available": 5
  },
  "environment": "development"
}
```

#### GET /health/live

Liveness check for Kubernetes health probes.

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Chat API

#### POST /api/v1/chat/

Process a natural language query and return agent response.

**Request Body:**
```json
{
  "message": "What is the total revenue for Q1 2024?",
  "session_id": "optional-session-id",
  "context": {
    "department": "sales",
    "region": "US"
  },
  "user_id": "optional-user-id"
}
```

**Response:**
```json
{
  "response": "The total revenue for Q1 2024 is $1,500,000. This represents a 15% increase compared to Q1 2023.",
  "query_result": {
    "sql_query": "SELECT SUM(revenue) FROM sales WHERE quarter = 'Q1' AND year = 2024",
    "execution_time_ms": 1250.5,
    "row_count": 1,
    "data_preview": [{"total_revenue": 1500000.00}]
  },
  "impact_analysis": {
    "impact_score": 0.85,
    "impact_description": "High impact on revenue metrics",
    "affected_metrics": ["total_revenue", "average_order_value"],
    "recommendations": ["Monitor sales trends", "Review pricing strategy"],
    "confidence_level": 0.92
  },
  "session_id": "session_123",
  "timestamp": "2024-01-15T10:30:00Z",
  "agent_metadata": {
    "agent_id": "agent_456",
    "agent_type": "coordinator_agent",
    "processing_steps": ["query_understanding", "sql_generation", "query_execution"],
    "confidence": 0.95,
    "total_duration_ms": 15000.0
  }
}
```

#### POST /api/v1/chat/session

Create a new chat session.

**Request Body:**
```json
{
  "user_id": "optional-user-id"
}
```

**Response:**
```json
{
  "session_id": "session_123",
  "user_id": "user_456",
  "created_at": "2024-01-15T10:30:00Z",
  "status": "active"
}
```

#### GET /api/v1/chat/session/{session_id}

Get information about a specific session.

**Response:**
```json
{
  "session_id": "session_123",
  "user_id": "user_456",
  "conversation_history": [
    {
      "role": "user",
      "content": "What is the total revenue for Q1?",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "The total revenue for Q1 is $1,500,000.",
      "timestamp": "2024-01-15T10:30:15Z"
    }
  ],
  "context_variables": {
    "current_quarter": "Q1",
    "current_year": 2024
  },
  "user_preferences": {
    "language": "en",
    "timezone": "UTC"
  },
  "schema_info": {
    "tables": ["sales", "customers", "products"],
    "columns": {"sales": ["revenue", "date", "product_id"]}
  }
}
```

#### DELETE /api/v1/chat/session/{session_id}

Delete a chat session.

**Response:**
```json
{
  "message": "Session deleted successfully",
  "session_id": "session_123"
}
```

#### GET /api/v1/chat/session/{session_id}/history

Get conversation history for a session.

**Query Parameters:**
- `limit` (optional): Maximum number of messages to return (default: 50)

**Response:**
```json
{
  "session_id": "session_123",
  "history": [
    {
      "role": "user",
      "content": "What is the total revenue for Q1?",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "The total revenue for Q1 is $1,500,000.",
      "timestamp": "2024-01-15T10:30:15Z"
    }
  ],
  "total_messages": 2
}
```

#### GET /api/v1/chat/sessions

Get list of active sessions.

**Response:**
```json
{
  "total_sessions": 10,
  "active_sessions": 5,
  "total_messages": 150,
  "session_timeout_hours": 24
}
```

### Agents API

#### GET /api/v1/agents/

Get overview of all agents and their status.

**Response:**
```json
{
  "overview": {
    "total_agents_executed": 100,
    "active_agents": 2,
    "success_rate_percent": 95.5,
    "average_execution_time_ms": 2500.0
  },
  "active_agents": [
    {
      "agent_id": "agent_123",
      "session_id": "session_456",
      "request_id": "req_789",
      "state": "processing",
      "start_time": "2024-01-15T10:30:00Z",
      "duration_ms": 1500.0
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /api/v1/agents/{agent_id}

Get status of a specific agent.

**Response:**
```json
{
  "agent_id": "agent_123",
  "status": {
    "status": "completed",
    "state": "completed",
    "start_time": "2024-01-15T10:30:00Z",
    "end_time": "2024-01-15T10:30:15Z",
    "duration_ms": 15000.0,
    "success": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /api/v1/agents/history

Get agent execution history.

**Query Parameters:**
- `session_id` (optional): Filter by session ID
- `limit` (optional): Maximum number of results (default: 50)

**Response:**
```json
{
  "history": [
    {
      "agent_id": "agent_123",
      "session_id": "session_456",
      "request_id": "req_789",
      "agent_type": "coordinator_agent",
      "state": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:15Z",
      "duration_ms": 15000.0,
      "success": true,
      "error": null
    }
  ],
  "total_entries": 1,
  "session_filter": null,
  "limit": 50,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /api/v1/agents/active

Get list of currently active agents.

**Response:**
```json
{
  "active_agents": [
    {
      "agent_id": "agent_123",
      "session_id": "session_456",
      "request_id": "req_789",
      "state": "processing",
      "start_time": "2024-01-15T10:30:00Z",
      "duration_ms": 1500.0
    }
  ],
  "count": 1,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### POST /api/v1/agents/cleanup

Clean up old agent history.

**Query Parameters:**
- `max_age_hours` (optional): Maximum age in hours (default: 24)

**Response:**
```json
{
  "cleaned_entries": 10,
  "max_age_hours": 24,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /api/v1/agents/statistics

Get detailed agent statistics.

**Response:**
```json
{
  "statistics": {
    "total_agents_executed": 100,
    "active_agents": 2,
    "success_rate_percent": 95.5,
    "average_execution_time_ms": 2500.0,
    "history_size": 100
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Data Models

### ChatRequest

```json
{
  "message": "string (required)",
  "session_id": "string (optional)",
  "context": "object (optional)",
  "user_id": "string (optional)"
}
```

### ChatResponse

```json
{
  "response": "string (required)",
  "query_result": "QueryResult (optional)",
  "impact_analysis": "ImpactAnalysis (optional)",
  "session_id": "string (required)",
  "timestamp": "datetime (required)",
  "agent_metadata": "object (required)"
}
```

### QueryResult

```json
{
  "sql_query": "string (required)",
  "optimized_sql": "string (optional)",
  "execution_time_ms": "float (optional)",
  "row_count": "integer (optional)",
  "data_preview": "array (optional)",
  "error_message": "string (optional)"
}
```

### ImpactAnalysis

```json
{
  "impact_score": "float (required)",
  "impact_description": "string (required)",
  "affected_metrics": "array (required)",
  "recommendations": "array (required)",
  "confidence_level": "float (required)"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## CORS

CORS is enabled for all origins in development. Configure appropriately for production.

## Headers

### Request Headers

- `Content-Type: application/json` (for POST requests)
- `Accept: application/json`

### Response Headers

- `X-Request-ID`: Unique request identifier for tracking
- `X-Process-Time`: Request processing time in seconds
- `Content-Type: application/json`

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input data |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Service temporarily unavailable |

## Examples

### Complete Chat Flow

1. Create a session:
```bash
curl -X POST "http://localhost:8000/api/v1/chat/session" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123"}'
```

2. Send a query:
```bash
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the total revenue for Q1 2024?",
    "session_id": "session_123",
    "context": {"department": "sales"}
  }'
```

3. Check agent status:
```bash
curl -X GET "http://localhost:8000/api/v1/agents/agent_456"
```

4. Get conversation history:
```bash
curl -X GET "http://localhost:8000/api/v1/chat/session/session_123/history"
```

## SDK Examples

### Python

```python
import requests

# Base URL
base_url = "http://localhost:8000"

# Create session
session_response = requests.post(f"{base_url}/api/v1/chat/session")
session_id = session_response.json()["session_id"]

# Send query
query_data = {
    "message": "What is the total revenue for Q1 2024?",
    "session_id": session_id,
    "context": {"department": "sales"}
}

response = requests.post(f"{base_url}/api/v1/chat/", json=query_data)
result = response.json()

print(f"Response: {result['response']}")
print(f"SQL Query: {result['query_result']['sql_query']}")
```

### JavaScript

```javascript
const baseUrl = 'http://localhost:8000';

// Create session
const sessionResponse = await fetch(`${baseUrl}/api/v1/chat/session`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
});
const sessionData = await sessionResponse.json();
const sessionId = sessionData.session_id;

// Send query
const queryData = {
  message: 'What is the total revenue for Q1 2024?',
  session_id: sessionId,
  context: { department: 'sales' }
};

const response = await fetch(`${baseUrl}/api/v1/chat/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(queryData)
});

const result = await response.json();
console.log('Response:', result.response);
console.log('SQL Query:', result.query_result.sql_query);
```

