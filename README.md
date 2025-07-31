# Assistant Service

A production-ready service for deploying AI assistants with custom actions. Built on [OpenAI's Assistant API](https://platform.openai.com/docs/assistants/overview), this service bridges the gap between foundation models and your business logic, enabling assistants that can execute code, query databases, call APIs, and more.

## Why This Project?

OpenAI Assistants are incredibly powerful, but integrating them with custom business logic in production can be complex. This service solves that by providing:

- **Custom Actions** - Turn any Python function into an assistant capability
- **Real-Time Streaming** - Get responses as they're generated via SSE or WebSocket
- **Production-Ready** - Comprehensive error handling, structured logging, correlation IDs
- **Cloud-Native** - Deploy to GCP, AWS, or any container platform
- **Fully Async** - Built on FastAPI for high-performance concurrent operations
- **Knowledge Bases** - Combine custom actions with document search

## Use Cases

Build assistants that can:
- **Customer Support** - Query order databases, check inventory, create tickets
- **Data Analysis** - Connect to SQL databases, run queries, generate reports  
- **DevOps Assistant** - Execute scripts, check system status, manage deployments
- **Sales Assistant** - Access CRM data, update opportunities, send emails
- **Research Assistant** - Search documents, summarize findings, cite sources

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

The Assistant Service acts as intelligent middleware between your applications and OpenAI's Assistant API. When your app sends a message, the service creates a streaming run with OpenAI, processing events in real-time. As the assistant generates responses, it may invoke your custom actions (Python functions) to query databases, call APIs, or interact with file systems. These function results are seamlessly fed back into the assistant's context, allowing it to provide informed, actionable responses. The entire flow is event-driven, supporting both REST/SSE and WebSocket protocols for real-time streaming.

## Project Structure

```
assistant-service/
├── assistant_service/       # Core service implementation
│   ├── entities/           # Data models and configuration schemas
│   ├── repositories/       # Storage abstraction (local/GCP)
│   ├── server/            # FastAPI application and endpoints
│   ├── services/          # Business logic and streaming (see services/README.md)
│   ├── bootstrap.py       # Application initialization and dependency injection
│   ├── structured_logging.py  # Structured logging with correlation IDs
│   └── tools.py           # Custom action registry - add your functions here
├── scripts/               # Utility scripts (see scripts/README.md)
│   ├── assistant_registration/  # Tools for creating and managing assistants
│   └── conversation/      # Interactive chat clients for testing
├── tests/                 # Comprehensive test suite
├── Makefile              # Development workflow commands
├── pyproject.toml        # Project dependencies and configuration
├── Dockerfile            # Container configuration for deployment
└── README.md             # This file
```

**Key files to know:**
- `assistant_service/tools.py` - Register your custom Python functions here
- `assistant_service/services/` - Core streaming and OpenAI integration ([detailed docs](assistant_service/services/README.md))
- `scripts/` - Utility scripts for registration and testing ([detailed docs](scripts/README.md))

## Quick Start

Get your first assistant with custom actions running in 5 minutes:

### Prerequisites
- Python 3.10-3.12
- OpenAI account and API key (get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys))
- [`uv`](https://github.com/astral-sh/uv) package manager (`pip install uv`)

### 1. Setup

Set up your Python environment:
```bash
make environment-create
make validate-branch  # Verify environment is correctly configured
```

> **Note**: If you don't have the code yet, first clone the repository:
> ```bash
> git clone https://github.com/yourusername/assistant-service
> cd assistant-service
> ```

### 2. Configure

Create a `.env` file in the project root with the required environment variables:

**Example .env file:**
```bash
# Required: Your OpenAI API key from platform.openai.com/api-keys
OPENAI_API_KEY="your-openai-api-key"

# Required: GCP configuration (dummy values work for local development)
PROJECT_ID="dummy-project"
BUCKET_ID="dummy-bucket"

# Optional: Default assistant to load (add after creating your assistant)
# ASSISTANT_ID="asst_xxxxxxxxxxxxxx"

# Optional: Environment and logging configuration
# ENVIRONMENT="development"
# LOGGING_LEVEL="INFO"
```

> **Note**: This quick start stores assistant configurations on your local disk while creating the actual assistants in your OpenAI account at [platform.openai.com/assistants](https://platform.openai.com/assistants/). You'll be able to see and manage your assistants there.

### 3. Create Custom Action

Register custom actions (functions) that your assistant can call. These functions become tools available to your assistant during conversations. When the assistant determines it needs to use a tool, the function will be executed within this service (not by OpenAI), giving you full control over the execution environment.

Edit `assistant_service/tools.py`:
```python
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    # Your weather API integration here
    return f"The weather in {location} is sunny and 72°F"

TOOL_MAP = {"get_weather": get_weather}
```

### 4. Register Assistant

Define your assistant's behavior and capabilities in a configuration file (see [Assistant Configuration](#assistant-configuration) for all options).

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

Register your assistant with OpenAI (this creates the assistant in your OpenAI account at [platform.openai.com/assistants](https://platform.openai.com/assistants/)):
```bash
make register-assistant ARGS='assistant-config.json'
# Output: Assistant created with ID: asst_xxxxxxxxxxxxxx
```

### 5. Run & Test

Start the API server and interact with your assistant using the provided chat client:

```bash
# Terminal 1: Start the API server with your assistant
ASSISTANT_ID=asst_xxxxxxxxxxxxxx make api-run

# Terminal 2: Chat with your assistant
make chat
```

> **Tip**: Add `ASSISTANT_ID=asst_xxxxxxxxxxxxxx` to your `.env` file to avoid specifying it each time.

The chat client provides an interactive conversation interface. You can also use `make chat-ws` for WebSocket streaming, which provides real-time responses as they're generated.


## API Usage

While the chat clients (`make chat` and `make chat-ws`) provide the easiest way to interact with your assistant, you can also use the REST API directly for integration with your applications.

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

For applications that need real-time responses as they're generated:

- **Server-Sent Events (SSE)** - Add `Accept: text/event-stream` header to `/chat` endpoint for web applications
- **WebSocket** - Connect to `/ws/chat` for bidirectional streaming in interactive applications

For detailed implementation, code examples, and technical documentation, see [assistant_service/services/README.md](assistant_service/services/README.md).

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

Assistants are configured via JSON files that define their behavior, capabilities, and knowledge base. Each assistant runs independently with its own configuration.

#### Complete Configuration Example

```json
{
  "assistant_name": "Customer Support Assistant",
  "instructions": "You are a helpful customer support assistant. Use the available tools to help customers with their inquiries. Always be polite and professional.",
  "initial_message": "Hello! I'm here to help with your questions. How can I assist you today?",
  "model": "gpt-4-turbo-preview",
  "function_names": ["search_orders", "check_inventory", "create_ticket"],
  "code_interpreter": false,
  "file_search": true,
  "vector_store_name": "Support Documentation",
  "vector_store_file_paths": [
    "docs/user_manual.pdf",
    "docs/faq.md",
    "docs/troubleshooting_guide.txt"
  ]
}
```

#### Configuration Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `assistant_name` | string | Yes | Display name for your assistant | `"Customer Support Assistant"` |
| `instructions` | string | Yes | System prompt that defines the assistant's behavior and personality | `"You are a helpful assistant..."` |
| `initial_message` | string | Yes | Greeting message shown when a conversation starts | `"Hello! How can I help?"` |
| `model` | string | Yes | OpenAI model to use | `"gpt-4-turbo-preview"`, `"gpt-3.5-turbo"` |
| `function_names` | array | No | List of custom actions from TOOL_MAP the assistant can use | `["search_orders", "check_inventory"]` |
| `code_interpreter` | boolean | No | Enable OpenAI's code execution capability | `false` |
| `file_search` | boolean | No | Enable document search capability | `true` |
| `vector_store_name` | string | No | Name for the document knowledge base | `"Product Documentation"` |
| `vector_store_file_paths` | array | No | Paths to documents to include in knowledge base | `["docs/manual.pdf", "docs/faq.md"]` |

## Advanced Usage

### Working with Knowledge Bases

OpenAI's file search capability allows your assistant to answer questions from uploaded documents. This is perfect for creating assistants that can reference product documentation, policies, or any text-based knowledge base alongside your custom actions:

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

Large organizations often need different assistants for different departments or use cases. You can deploy multiple specialized assistants, each with its own configuration and tools:

```bash
# Customer Support Assistant
make register-assistant ARGS='assistants/support-assistant.json'

# Sales Assistant
make register-assistant ARGS='assistants/sales-assistant.json'

# Technical Assistant
make register-assistant ARGS='assistants/tech-assistant.json'
```

### Schema Generation

To ensure your assistant configurations are valid, you can generate a JSON schema for validation in your CI/CD pipeline:

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
make api-run             # Start with auto-reload (port 8000)

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

### Docker Deployment

The service includes a production-ready Dockerfile for containerized deployment:

```bash
# Build the Docker image
make service-build

# Run locally with Docker
docker run -p 8000:8000 \
  --env-file .env \
  assistant-service:latest
```

### Cloud Deployment

The service is designed to run on any container platform:

#### Google Cloud Run
```bash
gcloud run deploy assistant-service \
  --image gcr.io/your-project/assistant-service:latest \
  --port 8000 \
  --set-env-vars OPENAI_API_KEY="$OPENAI_API_KEY"
```

#### AWS ECS / Kubernetes
The containerized service works with any orchestration platform. Ensure you configure environment variables through your platform's secret management system.

### Production Considerations

- Store API keys in secret management systems (AWS Secrets Manager, GCP Secret Manager, etc.)
- Use structured logging for monitoring and debugging
- Set appropriate resource limits based on your expected load
- Consider implementing rate limiting for public-facing deployments

## Troubleshooting

### Debugging Tips
- **Check logs** - The service uses structured logging with correlation IDs. Set `LOGGING_LEVEL=DEBUG` for verbose output
- **Connection issues** - Verify the API server is running on port 8000 with the health endpoint: `curl http://localhost:8000/health`
- **OpenAI errors** - These return 502 status codes. Check your API key and OpenAI service status
- **Tool execution failures** - Tool errors include correlation IDs. Search logs for the ID to trace the full request

### Common Issues
- **"API server not running"** - Start the server with `make api-run` before using chat clients
- **Missing environment variables** - Ensure all required variables are in your `.env` file
- **Assistant not found** - Verify the assistant_id matches one created in your OpenAI account

## Documentation

- **[scripts/README.md](scripts/README.md)** - Detailed documentation for utility scripts including chat clients and assistant registration
- **[assistant_service/services/README.md](assistant_service/services/README.md)** - Technical documentation for the service layer architecture, streaming handlers, and event processing

## License

TBA
