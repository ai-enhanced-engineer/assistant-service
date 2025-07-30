# Assistant Service - Project-Specific Guidelines

This document contains project-specific patterns, workflows, and implementation details for the **Python assistant service** that integrates with OpenAI's Assistant API.

## Project Overview

This project is a **Python assistant service** that integrates with OpenAI's Assistant API to provide conversational AI capabilities with custom tool support and streaming responses.

## Architecture Overview

The system follows a **modular, layered architecture** with clear separation of concerns:

- **HTTP API Layer** (`assistant_service/server/main.py`) - FastAPI-based REST and WebSocket endpoints
- **Business Logic Layer** (`assistant_service/processors/`) - Run processing, message handling, and OpenAI integration
- **Configuration Layer** (`assistant_service/entities/`, `assistant_service/repositories/`) - Data models and repository patterns
- **Factory Layer** (`assistant_factory/`) - Assistant creation and tool building
- **Logging Layer** (`assistant_service/structured_logging.py`) - Structured logging with correlation IDs

## Project Structure

### Core Components
- `assistant_service/` - **Main application engine**
  - `server/main.py` - FastAPI application with `/start`, `/chat`, `/stream` endpoints
  - `processors/` - Run processing, tool execution, and WebSocket handling
  - `bootstrap.py` - Configuration building and dependency injection
  - `structured_logging.py` - Structured logging with structlog
  - `correlation.py` - Correlation ID management for request tracking

- `assistant_factory/` - **Assistant creation and management**
  - `main.py` - Factory for creating new assistants with custom tools
  - `tool_builder.py` - Converts Python functions to OpenAI tool definitions
  - `client_spec/` - Client-specific configurations and custom functions

- `assistant_service/` - **Also contains shared infrastructure**
  - `data_models/` - Pydantic models for configuration and requests
  - `repositories/` - Repository pattern for config/secret storage (GCP + local)

### Configuration System
The system supports **multi-environment configuration**:
- **Local Development**: In-memory repositories for config and secrets
- **Production**: GCP Cloud Storage (config) + Secret Manager (secrets)
- **Environment Variables**: `PROJECT_ID`, `BUCKET_ID`, `OPENAI_API_KEY`

## Custom Make Targets

### Environment Management
- `make environment-create` - Set up Python 3.10 environment with uv
- `make environment-sync` / `make sync-env` - Re-sync dependencies
- `make environment-delete` - Remove virtual environment
- `make environment-list` - Show installed packages

### Code Quality
- `make format` - Auto-format with Ruff
- `make lint` - Lint and auto-fix with Ruff
- `make type-check` - Type checking with MyPy
- `make validate-branch` - Combined lint + tests for pre-commit
- `make validate-branch-strict` - Full validation including format

### Testing
- `make unit-test` - Run unit tests with verbose output
- `make functional-test` - Run functional tests
- `make integration-test` - Run integration tests
- `make all-test` - All tests with 80% coverage requirement
- `make test-validate-branch` - Lint + unit tests
- `make all-test-validate-branch` - Full validation + all tests

### Service Management
- `make local-run` - Run locally with auto-reload (port 8000)
- `make service-build` - Build Docker image for assistant service
- `make auth-gcloud` - Authenticate with Google Cloud

### Utilities
- `make clean-project` - Clean Python caches and artifacts

## Key Features & Implementation Details

### Custom Tool Support
- Assistant-specific configurations stored in GCP or locally
- Custom functions in `assistants/` directories
- Dynamic tool loading via `TOOL_MAP` dictionary

### Streaming Architecture
- Real-time responses via OpenAI streaming API
- WebSocket support for live conversation updates
- Event-driven processing of tool calls and messages

### Function/Tool Calling
- Custom Python functions exposed as OpenAI tools
- Automatic tool definition generation from function signatures
- In-process tool execution during assistant runs

### Structured Logging
- Native structured logging with `structlog`
- Automatic correlation ID tracking across requests
- Configurable output format (JSON or key-value)
- Environment-based configuration for log level and stream

### Error Handling Strategy
- **OpenAI API errors** → 502 Bad Gateway responses
- **General exceptions** → 500 Internal Server Error
- **Retry logic** with exponential backoff for tool submissions
- Comprehensive logging at all levels with correlation IDs

## API Endpoints

- **GET `/start`** - Creates new conversation thread, returns `thread_id`
- **POST `/chat`** - Processes user message, returns assistant responses
  - Request: `{"thread_id": "...", "message": "..."}`
  - Response: `{"responses": ["..."]}`
- **WebSocket `/stream`** - Real-time event streaming for assistant runs

## Data Flow

```
HTTP Request → AssistantEngineAPI → OpenAI API → Event Stream → 
Tool Processing → Message Processing → HTTP Response
```

1. Client sends request to `/chat` endpoint
2. System creates OpenAI thread message and streaming run
3. Event stream processes tool calls and message creation
4. Custom functions executed via `TOOL_MAP` during tool calls
5. Assistant responses extracted and returned to client

## Environment Variables

### Required
- `PROJECT_ID` - GCP project ID (can be dummy value in development)
- `BUCKET_ID` - GCP bucket for configurations (can be dummy value in development)
- `OPENAI_API_KEY` - OpenAI API key

### Optional
- `ENVIRONMENT` - Environment mode (development/production), defaults to development
- `ASSISTANT_ID` - Default assistant to load
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to GCP credentials (only needed for production)

### Optional (Logging)
- `LOGGING_LEVEL` - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `STREAM` - Log output stream (stdout, stderr)
- `LOG_FORMAT` - Log format (json, keyvalue)

## Testing Patterns

### Custom Abstractions Over Mocks
The project avoids `unittest.mock` in favor of:

1. **DummyClient** pattern for OpenAI client mocking
2. **Local repository implementations** for testing
3. **Monkeypatch** for method substitution
4. **Fixtures** in conftest.py

### Test Organization
- Tests mirror source structure
- Comprehensive coverage for API endpoints
- WebSocket testing with TestClient
- Correlation ID validation in all tests

## Deployment

### Google Cloud Platform Integration
- **Cloud Run** - Serverless container deployment
- **Cloud Storage** - Configuration file storage
- **Secret Manager** - API key and sensitive data management
- **Artifact Registry** - Container image storage

### Container Configuration
- Multi-stage Docker build optimized for production
- Python 3.10 slim base image
- Port 8000 exposure for FastAPI application
- Proper credential mounting for GCP services

## Development Workflow

### Adding Custom Tools
1. Create directory: `assistant_factory/assistants/{assistant_name}/`
2. Add `tools.py` with custom tool implementations
3. Update `TOOL_MAP` in `assistant_service/tools.py`
4. Configure assistant in GCP or local config
5. Test with `make local-run`

### Implementing New Tools
1. Define function in assistant's `tools.py`
2. Add comprehensive docstring and type hints
3. Register in `TOOL_MAP` dictionary
4. Test tool execution through API
5. Add unit tests for the function

### Debugging Streaming Issues
1. Check WebSocket connection logs
2. Verify correlation IDs in structured logs
3. Monitor OpenAI event stream processing
4. Use `logger.debug()` for detailed tracing
5. Check retry logic for tool submissions

## Performance Considerations

### Optimization Points
- Connection pooling for OpenAI client
- Async/await throughout for concurrency
- Streaming responses to reduce latency
- Efficient event processing loop
- Minimal memory footprint per request

### Monitoring
- Structured logs with performance metrics
- Correlation IDs for request tracing
- Error rates by error type
- Tool execution timing
- WebSocket connection metrics

## Security Considerations

### API Key Management
- Never hardcode keys
- Use GCP Secret Manager in production
- Environment variables for local development
- Key rotation support

### Input Validation
- Pydantic models for all inputs
- Message length limits
- Thread ID validation
- Content sanitization

### Assistant Isolation
- Assistant-specific configurations
- Separate tool namespaces
- Configuration validation

## Common Issues & Solutions

### WebSocket Disconnections
- Implement reconnection logic client-side
- Check for proper error handling
- Monitor connection duration
- Use correlation IDs for debugging

### Tool Execution Failures
- Comprehensive error messages
- Retry logic for transient failures
- Proper exception handling
- Detailed logging of failures

### Configuration Issues
- Validate environment variables
- Check GCP permissions
- Verify bucket/secret access
- Test with local repositories first

## Future Enhancements

### Planned Features
- Authentication layer integration
- Rate limiting per client
- Tool execution sandboxing
- Conversation history storage
- Analytics and metrics collection

### Architecture Improvements
- Message queue for async processing
- Caching layer for responses
- Database for conversation persistence
- Load balancing for scaling
- Circuit breakers for external calls