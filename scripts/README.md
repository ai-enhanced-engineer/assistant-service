# Assistant Service Scripts

This directory contains utility scripts for running and interacting with the assistant-service.

The service supports two streaming protocols:
- **WebSocket** (`/ws/chat`) - Full-duplex, bidirectional communication for interactive chat UIs
- **Server-Sent Events** (`/chat` with SSE) - One-way streaming for web applications

## Scripts Overview

### `assistant_registration/register_assistant.py`
Creates and configures new OpenAI assistants with custom actions and knowledge bases.

**Usage:**
```bash
# Register a new assistant from config file
python scripts/assistant_registration/register_assistant.py assistant-config.json

# Generate JSON schema for validation
python scripts/assistant_registration/register_assistant.py --generate-schema

# Use with make command (recommended)
make register-assistant ARGS='assistant-config.json'
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

### `isolation/api_layer.py`
Boots the assistant-service API in isolation for testing and development.

**Usage:**
```bash
# Basic usage (starts on localhost:8000)
python scripts/isolation/api_layer.py

# With custom options
python scripts/isolation/api_layer.py \
  --port 8080 \
  --reload \
  --log-level debug \
  --openai-key sk-your-key \
  --assistant-id asst_your_assistant_id
```

**Options:**
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 8000)
- `--reload`: Enable auto-reload for development
- `--log-level`: Set logging level (debug, info, warning, error)
- `--openai-key`: OpenAI API key (can also use OPENAI_API_KEY env var)
- `--assistant-id`: OpenAI Assistant ID to use
- `--client-id`: Client ID for multi-tenant configuration

### `conversation/websocket.py`
WebSocket-based client for real-time streaming chat via the `/ws/chat` endpoint.

**Usage:**
```bash
# Connect to local service
python scripts/conversation/websocket.py

# Connect to remote service
python scripts/conversation/websocket.py \
  --base-url ws://api.example.com:8000

# Continue existing conversation
python scripts/conversation/websocket.py \
  --thread-id thread_abc123
```

**Note:** The WebSocket client automatically connects to the `/ws/chat` endpoint.

**Features:**
- Real-time streaming responses
- Character-by-character output
- Automatic thread creation
- Graceful error handling
- Interactive command-line interface

### `conversation/http_chat.py`
HTTP-based client supporting both sequential and Server-Sent Events (SSE) streaming modes.

**Usage:**
```bash
# Connect to local service (sequential mode)
python scripts/conversation/http_chat.py

# Enable SSE streaming mode
python scripts/conversation/http_chat.py --stream

# Connect to remote service
python scripts/conversation/http_chat.py \
  --base-url http://api.example.com:8000

# Continue existing conversation
python scripts/conversation/http_chat.py \
  --thread-id thread_abc123
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

1. **Setup environment:**
   ```bash
   make environment-create
   ```

2. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   ```

3. **Start the API:**
   ```bash
   make local-run
   ```

4. **In another terminal, start chatting:**
   ```bash
   # Using WebSocket for real-time streaming
   make chat-ws
   
   # Using HTTP for sequential chat  
   make chat
   ```

## Direct Script Usage

If you prefer to run the scripts directly without make commands:

```bash
# Start API
python scripts/isolation/api_layer.py --reload

# Chat clients
python scripts/conversation/websocket.py  # WebSocket streaming
python scripts/conversation/http_chat.py   # HTTP (sequential or SSE)
python scripts/conversation/http_chat.py --stream  # HTTP with SSE streaming
```

## Example Session

```
$ python scripts/conversation/websocket.py

============================================================
New conversation started!
Thread ID: thread_xYz123aBc456
Assistant: Hello! How can I help you today?
============================================================

Connected! Type 'exit' or 'quit' to end the conversation.

You: What's the weather like?