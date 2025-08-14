# Agentic BigQuery App

An intelligent agent-based application for BigQuery data analysis that combines natural language processing, query optimization, and business impact analysis.

## Features

- **Natural Language to SQL**: Convert natural language queries to BigQuery SQL
- **Query Optimization**: Automatically analyze and optimize SQL queries for better performance
- **Business Impact Analysis**: Analyze the business impact of query results
- **Multi-Agent Architecture**: Coordinated workflow with specialized agents
- **Session Management**: Maintain conversation context and user preferences
- **Real-time Monitoring**: Track agent performance and execution metrics

## Architecture

The application uses a multi-agent architecture with the following components:

### Agents

1. **Query Agent**: Converts natural language to SQL and executes queries
2. **Optimization Agent**: Analyzes and optimizes SQL queries for performance
3. **Impact Analysis Agent**: Analyzes business impact of query results
4. **Coordinator Agent**: Orchestrates the workflow between agents

### Core Components

- **Session Manager**: Handles user sessions and conversation context
- **Agent Manager**: Manages agent lifecycle and coordination
- **BigQuery Client**: Handles BigQuery operations and query execution

## Quick Start

### Prerequisites

- Python 3.8+
- Google Cloud Project with BigQuery enabled
- Azure OpenAI API access (for advanced NLP features)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic_bigquery_app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env_example.txt .env
# Edit .env with your configuration
```

4. Run the application:
```bash
python -m app.main
```

The application will be available at `http://localhost:8000`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
BIGQUERY_DATASET=your_dataset_name

# Vertex AI Configuration
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_PROJECT_ID=your-gcp-project-id

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## API Usage

### Chat Endpoint

Send natural language queries to the chat endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the total revenue for Q1 2024?",
    "session_id": "optional-session-id",
    "context": {"department": "sales"}
  }'
```

### Session Management

Create a new session:
```bash
curl -X POST "http://localhost:8000/api/v1/chat/session"
```

Get session information:
```bash
curl -X GET "http://localhost:8000/api/v1/chat/session/{session_id}"
```

### Agent Monitoring

Get agent overview:
```bash
curl -X GET "http://localhost:8000/api/v1/agents/"
```

Get agent history:
```bash
curl -X GET "http://localhost:8000/api/v1/agents/history"
```

## API Documentation

Once the application is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Project Structure

```
agentic_bigquery_app/
├── app/
│   ├── agents/           # Agent implementations
│   ├── api/             # API routes
│   ├── config/          # Configuration management
│   ├── core/            # Core business logic
│   ├── models/          # Data models
│   └── utils/           # Utility functions
├── docs/                # Documentation
├── tests/               # Test files
├── requirements.txt     # Python dependencies
└── env_example.txt      # Environment variables template
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black app/ tests/
flake8 app/ tests/
```

## Agent Workflow

1. **User Query**: User sends natural language query
2. **Query Analysis**: Query agent analyzes intent and requirements
3. **SQL Generation**: Converts natural language to SQL
4. **Query Execution**: Executes query against BigQuery
5. **Optimization**: Optimization agent analyzes and suggests improvements
6. **Impact Analysis**: Impact analysis agent evaluates business impact
7. **Result Synthesis**: Coordinator agent combines all results
8. **Response**: Returns comprehensive response to user

## Monitoring and Observability

The application includes comprehensive logging and monitoring:

- **Request Tracking**: Each request gets a unique ID for tracing
- **Agent Metrics**: Track agent performance and success rates
- **Execution Times**: Monitor query and agent execution times
- **Error Handling**: Detailed error logging and reporting

## Security Considerations

- Environment-based configuration
- Request ID tracking for audit trails
- Input validation and sanitization
- Error message sanitization
- Session timeout management

## Performance Optimization

- Query caching and optimization
- Connection pooling for BigQuery
- Asynchronous agent execution
- Result caching and memoization
- Resource cleanup and management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation
- Review the logs for debugging information

## Roadmap

- [ ] Advanced NLP with Azure OpenAI integration
- [ ] Query result visualization
- [ ] Automated report generation
- [ ] Integration with other data sources
- [ ] Advanced caching strategies
- [ ] Real-time streaming capabilities
- [ ] Multi-tenant support
- [ ] Advanced security features
