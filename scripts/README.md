# Scripts

Utility scripts for managing assistants and testing interactions. All scripts can be run directly with `uv run python` or through the convenient `make` commands.

## Overview

### Assistant Registration

Creates and configures new OpenAI assistants with custom actions and knowledge bases.

**Usage:**
```bash
# Register a new assistant from config file
make register-assistant ARGS='assistant-config.json'

# Generate JSON schema for validation
make register-assistant ARGS='--generate-schema'

# Direct usage (if needed)
uv run python scripts/assistant_registration/register_assistant.py assistant-config.json
```

**Example Configuration:**
```json
{
  "assistant_name": "My Assistant",
  "instructions": "You are a helpful assistant with custom capabilities.",
  "initial_message": "Hello! How can I help you today?",
  "model": "gpt-4-turbo-preview",
  "function_names": ["my_custom_action"],
  "vector_store_files": ["docs/knowledge_base.pdf"]
}
```

**Features:**
- Creates OpenAI assistant with specified configuration
- Uploads documents to vector store for knowledge base
- Registers custom actions (functions) with the assistant
- Returns assistant ID for use with the service
- Supports schema generation for config validation

### API Service (Development)

The API can be started for development and testing:

**Usage:**
```bash
# Recommended: Use make command
make api-run

# With environment variables
ASSISTANT_ID=asst_xxx make api-run

# Direct usage with custom options
uv run python scripts/isolation/api_layer.py \
  --port 8080 \
  --reload \
  --log-level debug
```

**Options:**
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 8000)
- `--reload`: Enable auto-reload for development
- `--log-level`: Set logging level (debug, info, warning, error)
- `--openai-key`: OpenAI API key (can also use OPENAI_API_KEY env var)
- `--assistant-id`: OpenAI Assistant ID to use
- `--client-id`: Client ID for multi-tenant configuration

### WebSocket Chat Client

Real-time streaming chat client using WebSocket protocol for interactive conversations.

**Usage:**
```bash
# Recommended: Use make command
make chat-ws

# Continue existing conversation
make chat-ws ARGS='--thread-id thread_abc123'

# Direct usage for remote service
uv run python scripts/conversation/websocket.py \
  --base-url ws://api.example.com:8000
```

**Features:**
- Real-time streaming responses
- Character-by-character output
- Automatic thread creation
- Graceful error handling
- Interactive command-line interface

### HTTP Chat Client

HTTP-based chat client supporting both traditional request/response and Server-Sent Events (SSE) streaming.

**Usage:**
```bash
# Recommended: Use make command (sequential mode)
make chat

# Enable SSE streaming mode
make chat ARGS='--stream'

# Continue existing conversation
make chat ARGS='--thread-id thread_abc123'

# Direct usage for remote service
uv run python scripts/conversation/http_chat.py \
  --base-url http://api.example.com:8000
```

**Features:**
- Sequential request/response flow (default)
- SSE streaming mode with `--stream` flag
- Real-time character-by-character output in SSE mode
- Shows curl command equivalent (type 'curl')
- Clean error handling
- Structured logging with correlation IDs
- Metadata events showing response times (SSE mode)

## Quick Start

Get up and running with interactive chat in minutes:

```bash
# Terminal 1: Start the API server
make api-run

# Terminal 2: Start chatting
make chat-ws    # WebSocket real-time streaming (recommended)
make chat       # HTTP sequential mode
```

For SSE streaming mode:
```bash
make chat ARGS='--stream'
```

## Advanced Usage

### Direct Script Execution

For advanced use cases or debugging, you can run scripts directly:

```bash
# Start API with custom options
uv run python scripts/isolation/api_layer.py --reload --log-level debug

# Chat clients with specific configurations
uv run python scripts/conversation/websocket.py --base-url ws://localhost:8080
uv run python scripts/conversation/http_chat.py --stream --thread-id thread_abc123
```

### Example Chat Session

```
$ make chat-ws

============================================================
New conversation started!
Thread ID: thread_xYz123aBc456
Assistant: Hello! How can I help you today?
============================================================

Connected! Type 'exit' or 'quit' to end the conversation.

You: What's the weather like?
Assistant: I'd be happy to help you check the weather! However, I need to know which location you're interested in. Could you please tell me the city or area you'd like to know about?

You: exit
Goodbye!
```

## Streaming Protocols

The service supports two streaming protocols, each suited for different use cases:

### WebSocket (`/ws/chat`)
- **Best for**: Interactive chat applications, real-time UIs
- **Protocol**: Full-duplex, bidirectional communication
- **Client**: `make chat-ws`

### Server-Sent Events (`/chat` with SSE)
- **Best for**: Web applications, unidirectional streaming
- **Protocol**: HTTP-based, server-to-client only
- **Client**: `make chat ARGS='--stream'`

Both protocols deliver the same real-time streaming experience with character-by-character output.