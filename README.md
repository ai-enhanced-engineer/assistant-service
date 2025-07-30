# Assistant Service

A production-ready service for deploying AI assistants with custom actions. Built on OpenAI's Assistant API, this service bridges the gap between language models and your business logic, enabling assistants that can execute code, query databases, call APIs, and more.

## Why This Project?

OpenAI Assistants are incredibly powerful, but integrating them with custom business logic can be complex. This service solves that by providing:

- **🚀 Custom Actions** - Write Python functions that become assistant capabilities
- **⚡ Production-Ready** - Built-in streaming, error handling, and logging
- **🔧 Flexible Integration** - Connect to databases, APIs, or any Python code
- **📚 Knowledge Bases** - Combine custom actions with document search

## Quick Example

Create an assistant that can query your database and search documentation:

```python
# Define a custom action
def search_customers(query: str) -> str:
    """Search customer database for information."""
    # Your database logic here
    results = db.search(query)
    return f"Found {len(results)} customers matching '{query}'"

# Register it with your assistant
assistant_config = {
    "assistant_name": "Customer Support Assistant",
    "instructions": "Help users with customer inquiries using our database.",
    "initial_message": "Hello! I'm here to help with any customer inquiries. How can I assist you today?",
    "function_names": ["search_customers"],
    "vector_store_files": ["docs/product_guide.pdf", "docs/faq.md"]
}
```

Your assistant can now intelligently combine OpenAI's language understanding with your business data!

## Use Cases

Build assistants that can:
- **Customer Support** - Query order databases, check inventory, create tickets
- **Data Analysis** - Connect to SQL databases, run queries, generate reports  
- **DevOps Assistant** - Execute scripts, check system status, manage deployments
- **Sales Assistant** - Access CRM data, update opportunities, send emails
- **Research Assistant** - Search documents, summarize findings, cite sources

## Key Features

- **Custom Actions** - Turn any Python function into an assistant capability
- **Real-Time Streaming** - Get responses as they're generated via SSE or WebSocket
- **Production-Ready** - Comprehensive error handling, structured logging, correlation IDs
- **Cloud-Native** - Deploy to GCP, AWS, or any container platform
- **Fully Async** - Built on FastAPI for high-performance concurrent operations
- **Testable** - Mock OpenAI calls and test your custom actions locally

## Architecture

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│   Your Apps     │────▶│  Assistant Service  │────▶│   OpenAI API     │
│   (REST/WS)     │     │                     │     │   (Assistants)   │
└─────────────────┘     └──────────┬──────────┘     └──────────────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   Custom Actions    │
                        │  ┌───────────────┐  │
                        │  │ Your Database │  │
                        │  ├───────────────┤  │
                        │  │ External APIs │  │
                        │  ├───────────────┤  │
                        │  │ File Systems  │  │
                        │  └───────────────┘  │
                        └─────────────────────┘
```


## Quick Start

Get your first assistant with custom actions running in 5 minutes:

### Prerequisites
- Python 3.10-3.12
- OpenAI API key
- `uv` package manager (`pip install uv`)

### 1. Setup

```bash
git clone https://github.com/yourusername/custom-assistant-service
cd custom-assistant-service
make environment-create
```

### 2. Configure

Create `.env` file:
```bash
OPENAI_API_KEY="your-openai-api-key"
```

### 3. Create Custom Action

Create `assistant_factory/assistants/my_assistant/tools.py`:
```python
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    # Your weather API integration here
    return f"The weather in {location} is sunny and 72°F"

TOOL_MAP = {"get_weather": get_weather}
```

### 4. Register Assistant

Create `assistant-config.json`:
```json
{
  "assistant_name": "Weather Assistant",
  "instructions": "You are a helpful assistant that can check weather conditions.",
  "initial_message": "Hello! I can help you check the weather. Just ask me about any location!",
  "model": "gpt-4-turbo-preview",
  "function_names": ["get_weather"]
}
```

Register:
```bash
make register-assistant ARGS='assistant-config.json'
# Save the assistant_id from output
```

### 5. Run & Test

```bash
# Terminal 1: Start the service
make local-run

# Terminal 2: Test your assistant
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "new", "message": "What is the weather in New York?"}'
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

### Streaming

See [Streaming Protocols](#streaming-protocols) section below for real-time streaming options.

## Streaming Protocols

The assistant service provides real-time streaming through two protocols:

### HTTP with Server-Sent Events (SSE) - `/chat` endpoint

**Use this when**: Building web applications, need one-way streaming, working behind proxies/firewalls.

**Features**:
- Streams assistant responses as they're generated
- Sends metadata events with timing information
- Automatic reconnection with 5-second retry intervals
- Periodic heartbeats to detect stale connections

### WebSocket - `/ws/chat` endpoint

**Use this when**: Building interactive chat UIs, need persistent connections, require bidirectional communication.

**Features**:
- Maintains connection for entire conversation
- Lower latency for real-time updates
- Handles multiple message exchanges without reconnecting

**Example**:
```python
import websockets
import json

async with websockets.connect('ws://localhost:8000/ws/chat') as ws:
    await ws.send(json.dumps({
        'thread_id': 'thread_abc123',
        'message': 'Hello!'
    }))
    async for message in ws:
        data = json.loads(message)
        # Handle streaming events
```

Both protocols stream the same OpenAI Assistant events:
- `thread.message.delta` - Incremental message content
- `thread.run.completed` - Run finished
- `metadata` - Performance metrics
- `error` - Error information

For technical implementation details of the streaming protocols, see [assistant_service/services/README.md](assistant_service/services/README.md).

## Project Structure

```
custom-assistant-service/
├── assistant_service/            # Core service runtime
│   ├── server/                  # FastAPI application & API endpoints
│   ├── services/                # Service layer (see services/README.md)
│   ├── repositories/            # Configuration storage (local/GCP)
│   └── tools.py                 # Custom action registry
├── assistant_factory/
│   └── assistants/
│       └── {your_assistant}/    # Your custom actions go here
│           └── tools.py
├── scripts/                     # Utility scripts (see scripts/README.md)
│   └── assistant_registration/  # Assistant creation tools
└── tests/                       # Test suite
```

## Documentation

- **[scripts/README.md](scripts/README.md)** - Detailed documentation for utility scripts including chat clients and assistant registration
- **[assistant_service/services/README.md](assistant_service/services/README.md)** - Technical documentation for the service layer architecture, streaming handlers, and event processing

## Configuration

### Environment Variables

#### Required Variables

The service requires these environment variables to start:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `PROJECT_ID` | GCP project ID (can be dummy in development) | `my-project` |
| `BUCKET_ID` | GCS bucket name (can be dummy in development) | `my-bucket` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | `development` or `production` | `development` |
| `ASSISTANT_ID` | Default assistant to load | - |
| `LOGGING_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `LOG_FORMAT` | `json` or `keyvalue` | `keyvalue` |

### Assistant Configuration

Assistants are configured via JSON files. Key options include:
- `assistant_name` - Display name for your assistant
- `instructions` - System prompt defining assistant behavior
- `initial_message` - Greeting shown when conversation starts
- `model` - OpenAI model to use (e.g., `gpt-4-turbo-preview`)
- `function_names` - List of custom actions the assistant can use
- `code_interpreter` - Enable code execution capability
- `file_search` - Enable document search capability
- `vector_store_files` - Documents for knowledge base

## Advanced Usage

### Working with Knowledge Bases

Combine custom actions with document search:

```json
{
  "assistant_name": "Support Assistant",
  "instructions": "Help users with product questions using our documentation.",
  "initial_message": "Hello! I'm your support assistant. I can help with product questions, warranty checks, or create support tickets. How can I help?",
  "function_names": ["check_warranty", "create_ticket"],
  "vector_store_name": "Product Documentation",
  "vector_store_file_paths": [
    "docs/user_manual.pdf",
    "docs/troubleshooting.md",
    "docs/warranty_policy.txt"
  ]
}
```

### Multi-Assistant Deployment

Deploy multiple specialized assistants:

```bash
# Customer Support Assistant
make register-assistant ARGS='assistants/support-assistant.json'

# Sales Assistant
make register-assistant ARGS='assistants/sales-assistant.json'

# Technical Assistant
make register-assistant ARGS='assistants/tech-assistant.json'
```

### Schema Generation

Generate a JSON schema for validation:

```bash
make register-assistant ARGS='--generate-schema' > assistant-schema.json
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

# Interactive chat (see scripts/README.md for details)
make chat                # HTTP chat client
make chat-ws             # WebSocket streaming client

# Assistant management
make register-assistant   # Register new assistant from config file

# Docker
make service-build       # Build Docker image
```

### Testing

```bash
# Run all tests with coverage
make all-test

# Validate before committing
make validate-branch   # Lint + unit tests
```

## Deployment

### Cloud Deployment

Deploy to any container platform:

```bash
# Build container
docker build -t assistant-service .

# Run with environment variables
docker run -p 8000:8000 \
  -e OPENAI_API_KEY="your-key" \
  assistant-service
```

#### Google Cloud Run
```bash
gcloud run deploy assistant-service \
  --image gcr.io/your-project/assistant-service:latest \
  --set-env-vars OPENAI_API_KEY="your-key" \
  --port 8000
```

#### AWS ECS / Kubernetes
The service works with any container orchestration platform. See `deployment/` for examples.

## Security Best Practices

- **API Key Management** - Use environment variables or secret managers
- **Input Validation** - All inputs validated with Pydantic
- **Error Handling** - Errors sanitized to prevent information leakage
- **Assistant Isolation** - Each assistant runs in its own context

## Monitoring & Debugging

### Structured Logging
- **Native structured logging** with `structlog`
- **Correlation IDs** for request tracing across components
- **Configurable output** - JSON or key-value format
- **Environment-based configuration** for log level and stream

### API Endpoints
- **GET `/`** - Service status
- **GET `/health`** - Health check endpoint
- **GET `/start`** - Create new conversation thread
- **POST `/chat`** - Send message and get responses (supports SSE streaming)
- **WebSocket `/ws/chat`** - Real-time WebSocket streaming

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
5. **Project guidelines** - Check `CLAUDE.md` for project-specific patterns

See `CONTRIBUTING.md` for contribution guidelines and `CLAUDE.md` for detailed development patterns.

## License

MIT License - see LICENSE file for details

## Support & Community

- **Documentation**: Full docs at [docs-link]
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join our Discord community
- **Examples**: See `examples/` directory for more use cases

## Acknowledgments

Built with ❤️ using:
- [OpenAI Assistant API](https://platform.openai.com/docs/assistants)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
