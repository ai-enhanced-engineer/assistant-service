# Multi-Tenant Assistant Service

A production-ready Python service for deploying customized AI assistants with client-specific tools, personalities, and capabilities using OpenAI's Assistant API.

## Features

- **🏗️ Multi-Tenant Architecture** - Isolated configurations and custom functions per client
- **⚡ Real-Time Streaming** - WebSocket and HTTP endpoints with streaming OpenAI responses  
- **🔧 Custom Tool Integration** - Python functions automatically exposed as assistant tools
- **☁️ Cloud-Native** - Built for Google Cloud Platform with proper secret management
- **🛡️ Type-Safe** - Comprehensive Pydantic validation and type hints throughout
- **🔄 Event-Driven Processing** - Real-time tool execution and message processing

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client Apps   │───▶│  FastAPI Service │───▶│   OpenAI API    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │   Custom Tool Execution  │
                    │   (Weather, Files, etc.) │
                    └──────────────────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │  Configuration Storage   │
                    │     (GCP Cloud)          │
                    └──────────────────────────┘
```

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
   python -m assistant_engine.main
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
├── assistant_engine/          # Main runtime service
│   ├── main.py               # FastAPI application
│   ├── processors.py         # Message and tool processing
│   └── openai_helpers.py     # OpenAI API integration
├── assistant_factory/         # Assistant creation system
│   ├── main.py               # Assistant factory
│   ├── tool_builder.py       # Tool definition builder
│   └── client_spec/          # Client-specific configurations
│       └── {CLIENT_ID}/
│           ├── assistants.py # Agent configurations
│           ├── functions.py  # Custom tool functions
│           └── instructions.py # Agent personalities
├── botbrew_commons/          # Shared infrastructure
│   ├── data_models/          # Pydantic models
│   └── repositories/         # Config/secret storage
└── tests/                    # Test suites
```

## Configuration System

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API authentication | ✅ |
| `PROJECT_ID` | Google Cloud project ID | ✅ |
| `BUCKET_ID` | GCS bucket for configurations | ✅ |
| `CLIENT_ID` | Client identifier | ✅ |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account key | Production |

### Multi-Environment Support
- **Local Development**: In-memory repositories
- **Production**: GCP Cloud Storage + Secret Manager

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
# functions.py
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
```bash
# Install dependencies
uv sync

# Run tests
python -m pytest

# Lint and format
ruff check      # Lint
ruff format     # Format
mypy .          # Type check

# Run service locally
python -m assistant_engine.main
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test modules
python -m pytest assistant_engine/tests/
python -m pytest assistant_factory/tests/

# Run with coverage
python -m pytest --cov=assistant_engine --cov=assistant_factory
```

## Deployment

### Google Cloud Run
1. **Build and push container:**
   ```bash
   make build CLIENT_ID=your-client
   make push CLIENT_ID=your-client
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy assistant-service \
     --image gcr.io/your-project/assistant-service:latest \
     --set-env-vars PROJECT_ID=your-project,BUCKET_ID=your-bucket,CLIENT_ID=your-client
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

### Logging
- **Structured logging** with timestamps and levels
- **OpenAI API interaction** logging (filtered for noise reduction)
- **Tool execution** tracking and error reporting

### Health Checks
- `/health` endpoint for service monitoring
- Configuration validation on startup
- OpenAI API connectivity verification

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
