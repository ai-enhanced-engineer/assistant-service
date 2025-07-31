# Assistant Service - Project-Specific Guidelines

This document contains project-specific patterns, workflows, and implementation details for the **Assistant Service** that integrates with OpenAI's Assistant API.

## Project Overview

This project is a production-ready **Assistant Service** that integrates with OpenAI's Assistant API to provide conversational AI capabilities with custom tool support and streaming responses. Released as open source in v1.5.0, it bridges the gap between foundation models and business logic.

## Architecture Overview

The system follows a **modular, layered architecture** with clear separation of concerns:

- **HTTP API Layer** (`ai_assistant_service/server/main.py`) - FastAPI-based REST and WebSocket endpoints
- **Business Logic Layer** (`ai_assistant_service/services/`) - Run processing, message handling, and OpenAI integration  
- **Configuration Layer** (`ai_assistant_service/entities/`, `ai_assistant_service/repositories/`) - Data models and repository patterns
- **Logging Layer** (`ai_assistant_service/structured_logging.py`) - Structured logging with correlation IDs
- **Tools Layer** (`ai_assistant_service/tools.py`) - Custom action registry and function mapping

## Project Structure

### Core Components
- `ai_assistant_service/` - **Main application engine**
  - `server/` - FastAPI application layer
    - `main.py` - REST and WebSocket endpoints (`/start`, `/chat`, `/ws/chat`)
    - `error_handlers.py` - Global error handling and exception mapping
  - `services/` - Business logic and streaming handlers
    - `openai_orchestrator.py` - OpenAI API integration and run management
    - `sse_stream_handler.py` - Server-sent events streaming
    - `ws_stream_handler.py` - WebSocket streaming handler
    - `tool_executor.py` - Custom function execution
    - `message_parser.py` - Message extraction and parsing
  - `entities/` - Data models and domain objects
    - `config.py` - Configuration schemas
    - `events.py` - OpenAI event models
    - `schemas.py` - Request/response models
    - `message_data.py`, `step_data.py` - Domain entities
  - `repositories/` - Storage abstraction layer
    - `base.py` - Repository interfaces
    - `local.py` - In-memory implementation for development
    - `gcp.py` - Google Cloud Storage/Secret Manager implementation
  - `bootstrap.py` - Application initialization and dependency injection
  - `structured_logging.py` - Structured logging with correlation IDs
  - `tools.py` - Custom action registry (TOOL_MAP)

- `scripts/` - **Utility scripts and tools**
  - `assistant_registration/` - Assistant creation and management
    - `register_assistant.py` - CLI for registering assistants
    - `registration.py` - Core registration logic
  - `conversation/` - Interactive chat clients
    - `http_chat.py` - HTTP-based chat client
    - `websocket.py` - WebSocket streaming client
  - `isolation/` - API isolation for testing
    - `api_layer.py` - Standalone API runner

### Configuration System
The system supports **multi-environment configuration**:
- **Local Development**: In-memory repositories for config and secrets
- **Production**: GCP Cloud Storage (config) + Secret Manager (secrets)  
- **Environment Variables**: Loaded from `.env` file or system
  - Required: `PROJECT_ID`, `BUCKET_ID`, `OPENAI_API_KEY`
  - Optional: `ASSISTANT_ID`, `ENVIRONMENT`, logging configuration

## Custom Make Targets

### Environment Management
- `make environment-create` - Set up Python environment with uv (Python 3.10-3.12)
- `make environment-sync` / `make sync-env` - Re-sync dependencies  
- `make environment-delete` - Remove virtual environment
- `make environment-list` - Show installed packages

### Code Quality  
- `make format` - Auto-format with Ruff
- `make lint` - Lint and auto-fix with Ruff
- `make type-check` - Type checking with MyPy
- `make validate-branch` - Run format, lint, and type checks (pre-commit validation)
- `make validate-branch-strict` - Full validation with environment sync

### Testing
- `make unit-test` - Run unit tests with verbose output
- `make functional-test` - Run functional tests  
- `make integration-test` - Run integration tests
- `make all-test` - All tests with 85% coverage requirement
- `make test-validate-branch` - Validate branch + unit tests
- `make all-test-validate-branch` - Full validation + all tests

### Service Management
- `make api-run` - Run locally with auto-reload (port 8000)
- `make api-kill` - Kill running API development server
- `make api-docs` - Open Swagger UI documentation  
- `make service-build` - Build Docker image for assistant service
- `make auth-gcloud` - Authenticate with Google Cloud

### Interactive Chat
- `make chat` - Start HTTP chat client
- `make chat-ws` - Start WebSocket streaming chat

### Assistant Management  
- `make register-assistant` - Register new assistant from config file

### Utilities
- `make clean-project` - Clean Python caches and artifacts

## CI/CD and Release Process

### GitHub Actions Workflows
The project uses GitHub Actions for continuous integration and automated releases:

#### CI Workflow (`.github/workflows/ci.yml`)
1. **Semantic PR Validation** - Ensures PR titles follow conventional commits
2. **Linting** - Runs Ruff checks on all code
3. **Testing** - Executes pytest test suite
4. **Merged Testing** - Tests the merged state of PRs
5. **Automated Releases** - Uses semantic-release for version bumping and publishing

#### Release Process
- **Automatic Version Bumping** - Based on conventional commit messages
- **Changelog Generation** - Automatically updated from commit history
- **Git Tag Creation** - Semantic version tags (e.g., v1.5.0)
- **GitHub Release Publishing** - With release notes

### Pre-commit Hooks
The project includes pre-commit hooks configured during environment setup:
```bash
make environment-create  # Automatically installs pre-commit hooks
```

### Commit Message Convention
Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New features (bumps minor version)
- `fix:` - Bug fixes (bumps patch version)  
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks

### Required Secrets
- `RELEASE_TOKEN` - GitHub token with push permissions for automated releases

## Key Features & Implementation Details

### Custom Tool Support
- Assistant-specific configurations stored in GCP or locally
- Custom functions registered in `ai_assistant_service/tools.py`
- Dynamic tool loading via `TOOL_MAP` dictionary
- Functions become OpenAI tools available during conversations

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
  - Response: `{"responses": ["..."]}` (JSON) or SSE stream (if Accept: text/event-stream)
- **WebSocket `/ws/chat`** - Real-time WebSocket streaming for assistant runs

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

### Configuration Loading
Environment variables can be set via:
1. `.env` file in project root (recommended for development)
2. System environment variables
3. Runtime parameters when starting the service

### Required Variables
| Variable | Description | Example | Notes |
|----------|-------------|---------|-------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` | Get from platform.openai.com |
| `PROJECT_ID` | GCP project ID | `my-project` | Can be dummy in development |
| `BUCKET_ID` | GCS bucket name | `my-bucket` | Can be dummy in development |

### Optional Variables  
| Variable | Description | Default | Options |
|----------|-------------|---------|---------|  
| `ENVIRONMENT` | Runtime environment | `development` | `development`, `production` |
| `ASSISTANT_ID` | Default assistant to load | - | `asst_...` from OpenAI |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account key | - | Only for production |

### Logging Configuration
| Variable | Description | Default | Options |
|----------|-------------|---------|---------|  
| `LOGGING_LEVEL` | Log verbosity | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | Output format | `keyvalue` | `json`, `keyvalue` |
| `STREAM` | Output stream | `stdout` | `stdout`, `stderr` |

## Testing Patterns

### Testing Philosophy
The project emphasizes practical testing with real implementations where possible:

1. **Monkeypatch** over mocks for method substitution
2. **Local repository implementations** for testing without external dependencies
3. **Fixtures** in conftest.py for shared test setup
4. **TestClient** for API and WebSocket testing

### Test Organization
- Tests mirror source structure under `tests/ai_assistant_service/`
- Comprehensive coverage requirement (85%)
- Test categories: unit, functional, integration
- Correlation ID validation in API tests

### Running Tests
```bash
# Quick validation before commits
make validate-branch      # Format, lint, type check
make test-validate-branch # Above + unit tests

# Comprehensive testing
make all-test            # All tests with coverage report
make all-test-validate-branch # Full validation + all tests
```

## Deployment

### Google Cloud Platform Integration
- **Cloud Run** - Serverless container deployment
- **Cloud Storage** - Configuration file storage
- **Secret Manager** - API key and sensitive data management
- **Artifact Registry** - Container image storage

### Container Configuration  
- Multi-stage Docker build optimized for production
- Python 3.10-3.12 support with slim base image
- Port 8000 exposure for FastAPI application
- Proper credential mounting for GCP services
- Built with: `make service-build`

## Development Workflow

### Adding Custom Tools
1. Define your function in `ai_assistant_service/tools.py`
2. Add comprehensive docstring and type hints
3. Register in `TOOL_MAP` dictionary
4. Create/update assistant configuration to include the tool
5. Test with `make api-run`

### Example Tool Implementation
```python
# In ai_assistant_service/tools.py
def search_database(query: str, limit: int = 10) -> str:
    """Search the product database for matching items."""
    # Your implementation here
    return f"Found {limit} results for '{query}'"

TOOL_MAP = {
    "search_database": search_database,
    # ... other tools
}
```

### Registering an Assistant
1. Create a configuration file (see README for schema)
2. Run `make register-assistant ARGS='config.json'`
3. Note the returned assistant ID
4. Set `ASSISTANT_ID` in `.env` or runtime

### Debugging Streaming Issues
1. Enable debug logging: `LOGGING_LEVEL=DEBUG make api-run`
2. Check correlation IDs in structured logs for request tracing
3. Monitor OpenAI event stream processing in service logs
4. Use WebSocket test client: `make chat-ws`
5. Check retry logic for tool submission failures

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

## Documentation References

### Project Documentation
- **[README.md](../README.md)** - Project overview, quick start, and usage examples
- **[scripts/README.md](../scripts/README.md)** - Detailed documentation for utility scripts
- **[ai_assistant_service/services/README.md](../ai_assistant_service/services/README.md)** - Technical documentation for service layer

### External Resources  
- **[OpenAI Assistant API](https://platform.openai.com/docs/assistants)** - Official OpenAI documentation
- **[FastAPI](https://fastapi.tiangolo.com/)** - Web framework documentation
- **[Conventional Commits](https://www.conventionalcommits.org/)** - Commit message specification

## Repository Information

- **GitHub**: [github.com/ai-enhanced-engineer/assistant-service](https://github.com/ai-enhanced-engineer/assistant-service)
- **Issues**: [github.com/ai-enhanced-engineer/assistant-service/issues](https://github.com/ai-enhanced-engineer/assistant-service/issues)
- **Latest Release**: v1.5.1 (Public release with documentation overhaul)