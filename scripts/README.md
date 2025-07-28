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

### `conversation/websocket.py`
WebSocket-based client for real-time streaming chat.

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

**Features:**
- Real-time streaming responses
- Character-by-character output
- Automatic thread creation
- Graceful error handling
- Interactive command-line interface

### `conversation/http_chat.py`
HTTP-based client for sequential request/response chat.

**Usage:**
```bash
# Connect to local service
python scripts/conversation/http_chat.py

# Connect to remote service
python scripts/conversation/http_chat.py \
  --base-url http://api.example.com:8000

# Continue existing conversation
python scripts/conversation/http_chat.py \
  --thread-id thread_abc123
```

**Features:**
- Sequential request/response flow
- Complete message delivery
- Shows curl command equivalent (type 'curl')
- Clean error handling
- Structured logging with correlation IDs

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
   # Using WebSocket for real-time streaming
   python scripts/conversation/websocket.py
   
   # Using HTTP for sequential chat
   python scripts/conversation/http_chat.py
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