# Assistant Service Scripts

This directory contains utility scripts for running and interacting with the assistant-service.

## Scripts Overview

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

### `conversation/websocket_client.py`
Interactive chat client using WebSocket for real-time streaming responses.

**Usage:**
```bash
# Connect to local service
python scripts/conversation/websocket_client.py

# Connect to remote service
python scripts/conversation/websocket_client.py \
  --base-url ws://api.example.com:8000

# Continue existing conversation
python scripts/conversation/websocket_client.py \
  --thread-id thread_abc123
```

**Features:**
- Real-time streaming responses
- Automatic thread creation
- Graceful error handling
- Interactive command-line interface

### `conversation/http_client.py`
Interactive chat client using HTTP endpoints.

**Usage:**
```bash
# Connect to local service
python scripts/conversation/http_client.py

# Connect to remote service
python scripts/conversation/http_client.py \
  --base-url http://api.example.com:8000

# Continue existing conversation
python scripts/conversation/http_client.py \
  --thread-id thread_abc123
```

**Features:**
- Simple HTTP-based communication
- Shows equivalent curl commands (type 'curl')
- Automatic thread creation
- Error handling with timeouts

## Quick Start

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   ```

3. **Start the API:**
   ```bash
   python scripts/isolation/api_layer.py --reload
   ```

4. **In another terminal, start chatting:**
   ```bash
   # Using WebSocket (recommended for streaming)
   python scripts/conversation/websocket_client.py
   
   # Or using HTTP
   python scripts/conversation/http_client.py
   ```

## Example Session

```
$ python scripts/conversation/websocket_client.py

============================================================
New conversation started!
Thread ID: thread_xYz123aBc456
Assistant: Hello! How can I help you today?
============================================================

Connected! Type 'exit' or 'quit' to end the conversation.

You: What's the weather like?