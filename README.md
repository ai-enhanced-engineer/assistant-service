# Assistant Service

A production-ready service for deploying AI assistants with custom actions. Built on OpenAI's Assistant API, this service bridges the gap between language models and your business logic, enabling assistants that can execute code, query databases, call APIs, and more.

## Why This Project?

OpenAI Assistants are incredibly powerful, but integrating them with custom business logic can be complex. This service solves that by providing:

- **🚀 Easy Custom Actions** - Write Python functions that become assistant capabilities
- **⚡ Production-Ready** - Built-in streaming, error handling, and logging
- **🔧 Flexible Integration** - Connect to databases, APIs, or any Python code
- **📚 Knowledge Bases** - Combine custom actions with document search via vector stores

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
    "custom_actions": ["search_customers"],
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

## Features

- **🔧 Custom Actions** - Turn any Python function into an assistant capability
- **🤖 Assistant Management** - Create and configure assistants programmatically with JSON
- **📚 Knowledge Integration** - Combine custom actions with document search via vector stores
- **⚡ Real-Time Streaming** - Get responses as they're generated via WebSocket or HTTP
- **🔄 Async Everything** - Built on FastAPI for high-performance concurrent operations
- **🛡️ Production-Ready** - Comprehensive error handling, logging, and monitoring
- **☁️ Cloud-Native** - Deploy to GCP, AWS, or any container platform
- **🧪 Testable** - Mock OpenAI calls and test your custom actions locally
- **📊 Structured Logging** - Track every action with correlation IDs
- **🔌 Extensible** - Clean architecture for adding new capabilities

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

## How It Works

1. **Define Custom Actions**: Write Python functions for your business logic
2. **Create an Assistant**: Configure an OpenAI Assistant with your custom actions
3. **Deploy**: Run the service to expose your assistant via REST API or WebSocket
4. **Interact**: Your assistant intelligently uses custom actions to answer queries

## Quick Start

Get your first assistant running in 5 minutes:

### Prerequisites
- Python 3.10-3.12
- OpenAI API key
- `uv` package manager (`pip install uv`)

### 1. Install

```bash
git clone https://github.com/yourusername/custom-assistant-service
cd custom-assistant-service
make environment-create  # Or: uv sync
```

### 2. Configure

Create a `.env` file:
```bash
OPENAI_API_KEY="your-openai-api-key"
```

### 3. Create Your First Assistant

Create `assistant-config.json`:
```json
{
  "assistant_name": "My First Assistant",
  "instructions": "You are a helpful assistant that can perform calculations.",
  "initial_message": "Hello! I'm ready to help you with calculations. What would you like me to compute?",
  "model": "gpt-4-turbo-preview",
  "code_interpreter": true
}
```

Register your assistant:
```bash
make register-assistant ARGS='assistant-config.json'
# Note the assistant_id in the output
```

### 4. Run

```bash
make local-run  # Starts on http://localhost:8000
```

### 5. Test Your Assistant

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "new",
    "message": "Calculate the square root of 144"
  }'
```

## Creating Custom Actions

The real power comes from adding custom actions to your assistants:

### 1. Define Your Actions

Create a file `my_actions.py`:
```python
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    # Your weather API integration here
    return f"The weather in {location} is sunny and 72°F"

def query_inventory(product_id: str) -> str:
    """Check product inventory levels."""
    # Your database query here
    inventory = db.get_inventory(product_id)
    return f"Product {product_id} has {inventory} units in stock"

# Map function names to implementations
TOOL_MAP = {
    "get_weather": get_weather,
    "query_inventory": query_inventory
}
```

### 2. Register Actions with Your Assistant

Update your assistant configuration:
```json
{
  "assistant_name": "Business Assistant",
  "instructions": "Help users with weather and inventory queries.",
  "initial_message": "Welcome! I can help you check the weather or look up inventory. What would you like to know?",
  "model": "gpt-4-turbo-preview",
  "function_names": ["get_weather", "query_inventory"]
}
```

### 3. Connect Your Actions

Place your actions in the appropriate directory structure:
```
assistant_factory/
└── assistants/
    └── my_business/
        └── tools.py  # Your my_actions.py content here
```

Now your assistant can answer questions like:
- "What's the weather in New York?"
- "How many units of product ABC123 do we have?"
- "Is it good weather for shipping to Boston today?"

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
custom-assistant-service/
├── assistant_service/            # Core service runtime
│   ├── server/                  # HTTP/WebSocket API layer
│   │   ├── main.py             # FastAPI application
│   │   ├── schemas.py          # Request/response models
│   │   └── error_handlers.py   # Error handling
│   ├── processors/              # Assistant logic processing
│   │   ├── openai_orchestrator.py # OpenAI integration
│   │   ├── message_parser.py    # Message processing
│   │   ├── tool_executor.py    # Custom action execution
│   │   └── stream_handler.py    # Real-time streaming
│   ├── entities/                # Data models
│   │   └── config.py           # Configuration classes
│   ├── repositories/            # Storage abstraction
│   │   ├── base.py             # Repository interfaces
│   │   ├── gcp.py              # GCP implementation
│   │   └── local.py            # Local/dev implementation
│   ├── bootstrap.py             # Service initialization
│   ├── structured_logging.py    # Structured logging
│   └── tools.py                 # Action registry
├── assistant_factory/            # Assistant creation tools
│   ├── main.py                  # Assistant factory
│   ├── tool_builder.py          # Action definition builder
│   └── assistants/              # Assistant-specific code
│       └── {assistant_name}/
│           ├── config.py        # Assistant configuration
│           ├── tools.py         # Custom actions
│           └── prompts.py       # Assistant instructions
├── scripts/                      # Utility scripts
│   └── assistant_registration/  # Assistant registration
│       ├── register_assistant.py # Registration script
│       ├── registration.py       # Config models
│       ├── example-config.json   # Example configuration
│       └── sample_data/          # Sample knowledge base
└── tests/                       # Test suite
```

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

Assistants are configured via JSON files with these options:

```json
{
  "assistant_name": "Assistant Name",
  "instructions": "System prompt for the assistant",
  "initial_message": "Initial greeting message for users",
  "model": "gpt-4-turbo-preview",
  "code_interpreter": true,
  "file_search": true,
  "function_names": ["custom_action_1", "custom_action_2"],
  "vector_store_files": ["knowledge_base.pdf"]
}
```

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

# Assistant management
make register-assistant   # Register new assistant from config file

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
