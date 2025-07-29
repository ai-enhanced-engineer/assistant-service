# Multi-Tenant Assistant Service

A production-ready Python service for deploying customized AI assistants with client-specific tools, personalities, and capabilities using OpenAI's Assistant API.

## Features

- **🏗️ Multi-Tenant Architecture** - Isolated configurations and custom functions per client
- **⚡ Real-Time Streaming** - WebSocket and HTTP endpoints with streaming OpenAI responses  
- **🔧 Custom Tool Integration** - Python functions automatically exposed as assistant tools
- **☁️ Cloud-Native** - Built for Google Cloud Platform with proper secret management
- **🛡️ Type-Safe** - Comprehensive Pydantic validation and type hints throughout
- **🔄 Event-Driven Processing** - Real-time tool execution and message processing
- **📊 Structured Logging** - Correlation IDs and configurable output formats
- **🔌 Dependency Injection** - Clean separation of concerns with factory patterns
- **🧪 Test-First Design** - Comprehensive test coverage with custom testing patterns

## Architecture Overview

The service follows a **modular, layered architecture** with clear separation of concerns:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client Apps   │───▶│  FastAPI Service │───▶│   OpenAI API    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │   Custom Tool Execution  │
                    │   (Client-specific Tools)│
                    └──────────────────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │  Configuration Storage   │
                    │  (GCP Cloud / Local)     │
                    └──────────────────────────┘
```

### Key Components

- **Server Layer** (`server/`) - REST API and WebSocket endpoints
- **Processors Layer** (`processors/`) - Business logic for message and tool processing, OpenAI integration
- **Entities Layer** (`entities/`) - Data models and configuration
- **Repositories Layer** (`repositories/`) - Storage abstraction for configs/secrets
- **Bootstrap** (`bootstrap.py`) - Dependency injection and initialization

## Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key
- Google Cloud Platform account (for production)

### Local Development Setup

1. **Clone and install dependencies:**
   ```bash
   git clone <repository-url>
   cd assistant-service
   uv sync  # Install dependencies
   ```

2. **Set environment variables:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export PROJECT_ID="your-gcp-project"
   export BUCKET_ID="your-config-bucket" 
   export CLIENT_ID="your-client-id"
   ```

3. **Run the service:**
   ```bash
   python -m assistant_service.server.main
   # or
   make local-run
   ```

4. **Access the API:**
   - **API**: `http://localhost:8000`
   - **Docs**: `http://localhost:8000/docs`
   - **Health**: `http://localhost:8000/health`

### Using Docker

```bash
docker-compose up
```

## API Usage

### Create a Conversation
```bash
curl -X GET "http://localhost:8000/start"
# Returns: {"thread_id": "thread_abc123"}
```

### Send Messages
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "thread_abc123", "message": "What's the weather like?"}'
# Returns: {"responses": ["The current weather is..."]}
```

### Real-Time Streaming
```javascript
// WebSocket connection for live responses
const ws = new WebSocket('ws://localhost:8000/stream');
ws.send(JSON.stringify({thread_id: "thread_abc123", message: "Hello!"}));
```

## Project Structure

```
assistant-service/
├── assistant_service/            # Main runtime service
│   ├── server/                  # HTTP/WebSocket API layer
│   │   ├── main.py             # FastAPI application and routes
│   │   ├── schemas.py          # Request/response models
│   │   └── error_handlers.py   # Global error handling
│   ├── processors/              # Business logic layer
│   │   ├── run_processor.py    # OpenAI run orchestration
│   │   ├── message_processor.py # Message extraction
│   │   ├── tool_executor.py    # Tool execution engine
│   │   └── websocket_processor.py # WebSocket handling
│   ├── entities/                # Data models and configuration
│   │   └── config.py           # All configuration classes
│   ├── repositories/            # Storage abstraction layer
│   │   ├── base.py             # Repository interfaces
│   │   ├── gcp.py              # GCP implementation
│   │   └── local.py            # Local/dev implementation
│   ├── bootstrap.py             # Application initialization
│   ├── structured_logging.py    # Logging with correlation IDs
│   └── tools.py                 # Tool registry (client-specific)
├── assistant_factory/            # Assistant creation system
│   ├── main.py                  # Assistant factory
│   ├── tool_builder.py          # Tool definition builder
│   └── client_spec/             # Client-specific configurations
│       └── {CLIENT_ID}/
│           ├── assistants.py    # Assistant configurations
│           ├── tools.py         # Custom tool implementations
│           └── instructions.py  # Assistant personalities
└── tests/                       # Comprehensive test suite
```

## Configuration System

### Environment Variables

The service uses Pydantic Settings for configuration management:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENVIRONMENT` | Environment mode (`development`/`production`) | ❌ | `development` |
| `OPENAI_API_KEY` | OpenAI API authentication | ✅ | - |
| `PROJECT_ID` | Google Cloud project ID | ✅ | - |
| `BUCKET_ID` | GCS bucket for configurations | ✅ | - |
| `CLIENT_ID` | Client identifier | ✅ | - |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account key | Production | - |
| `LOGGING_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) | ❌ | `INFO` |
| `STREAM` | Log output stream (stdout, stderr) | ❌ | `stdout` |
| `LOG_FORMAT` | Log format (json, keyvalue) | ❌ | `keyvalue` |

### Multi-Environment Support

The service automatically configures itself based on the `ENVIRONMENT` variable:

- **Development Mode** (`ENVIRONMENT=development`):
  - Uses in-memory repositories for configs/secrets
  - No GCP dependencies required
  - Ideal for local testing

- **Production Mode** (`ENVIRONMENT=production`):
  - GCP Cloud Storage for configuration files
  - GCP Secret Manager for sensitive data
  - Requires proper GCP authentication

## Creating Custom Assistants

### 1. Client Configuration
Create a new client directory under `assistant_factory/client_spec/{CLIENT_ID}/`:

```python
# assistants.py
personal_assistant = ClientAssistantConfig(
    client_id="myclient",
    assistant_name="My Assistant",
    instructions="You are a helpful assistant...",
    model="gpt-4-1106-preview",
    functions=[my_custom_function_dict],
    retrieval=True,
    file_paths=["knowledge.pdf"]
)
```

### 2. Custom Functions
```python
# tools.py
def my_custom_function(query: str) -> str:
    """Custom function that the assistant can call."""
    return f"Processed: {query}"

TOOL_MAP = {
    "my_custom_function": my_custom_function
}

my_custom_function_dict = {
    "name": "my_custom_function",
    "description": "Processes queries",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Query to process"}
        },
        "required": ["query"]
    }
}
```

### 3. Deploy Assistant
```bash
# Create and deploy the assistant
python -m assistant_factory.main
```

## Development

### Development Commands

The project uses a comprehensive Makefile for development workflows:

```bash
# Environment setup
make environment-create    # Set up Python environment with uv
make environment-sync      # Re-sync dependencies

# Code quality
make format               # Auto-format with Ruff
make lint                 # Lint and auto-fix
make type-check           # Type checking with MyPy
make validate-branch      # Run all checks before commit

# Testing
make unit-test            # Run unit tests
make functional-test      # Run functional tests
make integration-test     # Run integration tests
make all-test            # Run all tests with coverage

# Run service locally
make local-run           # Start with auto-reload (port 8000)

# Docker
make service-build       # Build Docker image
```

### Testing

The project has comprehensive test coverage with custom testing patterns:

```bash
# Run all tests with coverage
make all-test

# Run specific test types
make unit-test         # Unit tests only
make functional-test   # Functional tests
make integration-test  # Integration tests

# Validate before committing
make validate-branch   # Lint + unit tests
```

**Testing Patterns:**
- Custom `DummyClient` pattern for OpenAI mocking
- Local repository implementations for isolated testing
- Correlation ID validation in all API tests
- WebSocket testing with TestClient

## Deployment

### Google Cloud Run

1. **Authenticate with GCP:**
   ```bash
   make auth-gcloud
   ```

2. **Build and push container:**
   ```bash
   make service-build CLIENT_ID=your-client
   # Then push to your container registry
   ```

3. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy assistant-service \
     --image gcr.io/your-project/assistant-service:latest \
     --set-env-vars PROJECT_ID=your-project,BUCKET_ID=your-bucket,CLIENT_ID=your-client \
     --port 8000
   ```

### Environment Setup
- **GCP Service Account** with Cloud Storage and Secret Manager permissions
- **Cloud Storage bucket** for configuration storage
- **Secret Manager** entries for API keys

## Security

- **No hardcoded credentials** - All secrets via environment variables or GCP Secret Manager
- **Input validation** - Comprehensive Pydantic model validation
- **Error sanitization** - Prevents information leakage in error responses
- **Client isolation** - Each client has separate configuration namespace

## Monitoring & Debugging

### Structured Logging
- **Native structured logging** with `structlog`
- **Correlation IDs** for request tracing across components
- **Configurable output** - JSON or key-value format
- **Environment-based configuration** for log level and stream

### API Endpoints
- **GET `/`** - Service status
- **GET `/start`** - Create new conversation thread
- **POST `/chat`** - Send message and get responses
- **WebSocket `/stream`** - Real-time streaming responses

### Error Handling
- **Comprehensive error types** with correlation IDs
- **OpenAI errors** → 502 Bad Gateway
- **Validation errors** → 400 Bad Request
- **Server errors** → 500 Internal Server Error
- **Retry logic** with exponential backoff for transient failures

## Contributing

1. **Follow coding standards** - Use `ruff` for formatting and linting
2. **Write tests** - Both unit and integration tests required
3. **Type safety** - Comprehensive type hints mandatory
4. **Documentation** - Update relevant docs with changes

See `AGENTS.md` for AI agent contribution guidelines.

## License

[License information]

## Support

For questions and support:
- Check existing GitHub issues
- Review the documentation in `CLAUDE.md`
- See agent-specific guidelines in `AGENTS.md`
