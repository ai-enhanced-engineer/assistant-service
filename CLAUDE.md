# Claude Instructions

This project is a **multi-tenant Python assistant service** that integrates with OpenAI's Assistant API to provide conversational AI capabilities with custom tool support and streaming responses.

## Architecture Overview

The system follows a **modular, layered architecture** with clear separation of concerns:

- **HTTP API Layer** (`assistant_engine/main.py`) - FastAPI-based REST and WebSocket endpoints
- **Business Logic Layer** (`assistant_engine/processors.py`) - Run processing and message handling  
- **Integration Layer** (`assistant_engine/openai_helpers.py`) - OpenAI API interactions with retry logic
- **Configuration Layer** (`botbrew_commons/`) - Shared data models and repository patterns
- **Factory Layer** (`assistant_factory/`) - Assistant creation and tool building

## Project Structure

### Core Components
- `assistant_engine/` - **Main application engine**
  - `main.py` - FastAPI application with `/start`, `/chat`, `/stream` endpoints
  - `processors.py` - Tool and message processing logic
  - `openai_helpers.py` - OpenAI API integration with error handling
  - `config.py` - Configuration building and injection

- `assistant_factory/` - **Assistant creation and management**
  - `main.py` - Factory for creating new assistants with custom tools
  - `tool_builder.py` - Converts Python functions to OpenAI tool definitions
  - `client_spec/` - Client-specific configurations and custom functions

- `botbrew_commons/` - **Shared infrastructure**
  - `data_models/` - Pydantic models for configuration and requests
  - `repositories/` - Repository pattern for config/secret storage (GCP + local)



### Configuration System
The system supports **multi-environment configuration**:
- **Local Development**: In-memory repositories for config and secrets
- **Production**: GCP Cloud Storage (config) + Secret Manager (secrets)
- **Environment Variables**: `PROJECT_ID`, `BUCKET_ID`, `CLIENT_ID`, `OPENAI_API_KEY`

## Development Commands

### Basic Operations
- Install dependencies: `uv sync`
- Run tests: `python -m pytest`
- Lint code: `ruff check`
- Format code: `ruff format`
- Type check: `mypy .`

### Running the Service
- Local development: `python -m assistant_engine.main`
- Docker: `docker-compose up`
- Production: Deploy to Google Cloud Run

### Testing Strategy
- **Unit Tests**: Component isolation with comprehensive mocking
- **Integration Tests**: Full API endpoint testing with TestClient
- **WebSocket Tests**: Real-time streaming validation
- Test paths: `assistant_factory/tests/`, `assistant_engine/tests/`

## Key Features

### Multi-Tenant Support
- Client-specific configurations stored in GCP
- Custom functions per client in `client_spec/` directories
- Dynamic tool loading via `TOOL_MAP` dictionary

### Streaming Architecture
- Real-time responses via OpenAI streaming API
- WebSocket support for live conversation updates
- Event-driven processing of tool calls and messages

### Function/Tool Calling
- Custom Python functions exposed as OpenAI tools
- Automatic tool definition generation from function signatures
- In-process tool execution during assistant runs

### Error Handling
- **OpenAI API errors** → 502 Bad Gateway responses
- **General exceptions** → 500 Internal Server Error
- **Retry logic** with exponential backoff for tool submissions
- Comprehensive logging at all levels

## API Endpoints

- **GET `/start`** - Creates new conversation thread, returns `thread_id`
- **POST `/chat`** - Processes user message, returns assistant responses
  - Request: `{"thread_id": "...", "message": "..."}`
  - Response: `{"responses": ["..."]}`
- **WebSocket `/stream`** - Real-time event streaming for assistant runs

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

## Configuration Files

### Core Configuration
- **`pyproject.toml`** - Project metadata, dependencies (FastAPI, OpenAI, Pydantic, GCP libraries)
- **`docker-compose.yml`** - Local development environment with GCP credentials
- **`Dockerfile`** - Production container with `uv` package manager
- **`Makefile`** - Build and deployment automation

### Environment Setup
```bash
# Required environment variables
export PROJECT_ID=your-gcp-project
export BUCKET_ID=your-config-bucket
export CLIENT_ID=your-client-id
export OPENAI_API_KEY=your-openai-key
export GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

## Design Patterns

- **Repository Pattern** - Abstract config/secret storage with GCP and local implementations
- **Factory Pattern** - Assistant creation with client-specific configurations
- **Configuration Pattern** - Environment-based config with Pydantic validation
- **Strategy Pattern** - Pluggable function implementations and processing strategies

## Deployment

### Google Cloud Platform Integration
- **Cloud Run** - Serverless container deployment
- **Cloud Storage** - Configuration file storage
- **Secret Manager** - API key and sensitive data management
- **Artifact Registry** - Container image storage

### Container Configuration
- Multi-stage Docker build optimized for production
- Python 3.10 slim base image
- Port 8000 exposure for FastAPI application
- Proper credential mounting for GCP services

## System Capabilities

### Strengths
- **Multi-tenant architecture** with client-specific configurations
- **Real-time streaming** responses via WebSocket
- **Custom tool integration** with OpenAI assistants
- **Cloud-native design** with GCP integration
- **Type safety** with comprehensive Pydantic validation
- **Error resilience** with retry logic and proper error handling

### Limitations
- **Single assistant per instance** - each deployment serves one assistant
- **No built-in authentication** - requires external auth layer
- **In-process tool execution** - no sandboxing for custom functions
- **GCP dependency** - tightly coupled to Google Cloud services
- **Stateless design** - no server-side conversation persistence

## Best Practices for Development

1. **Always run linting and type checking** after code changes
2. **Use repository pattern** for any new storage requirements
3. **Follow client-specific structure** in `client_spec/` directories
4. **Implement comprehensive error handling** for external API calls
5. **Use Pydantic models** for all data validation
6. **Write tests** for both unit and integration scenarios
7. **Follow existing patterns** for configuration and dependency injection

## Pull Request Workflow

### 🚨 CRITICAL AI AGENT RULE: ASK BEFORE CREATING PRS

**NEVER CREATE PULL REQUESTS WITHOUT USER PERMISSION**
- Always ask the user: "Should I create a pull request for these changes?"
- Wait for explicit approval before using `gh pr create` or any PR creation commands
- The user must give clear permission before any PR is created

**CRITICAL**: Before creating any pull request, you MUST run and pass these validation steps:

### Pre-PR Validation Checklist
```bash
# 1. Run comprehensive validation - MUST pass without errors
make all-test-validate-branch  # Runs linting + tests automatically

# Alternative: Run individual commands
make lint             # Check linting only
make unit test     # Run tests only
make format          # Apply formatting
```

**Note**: Pre-commit hooks are configured to automatically run `make validate-branch` before each commit, ensuring code quality.

### Required Workflow
1. **Create feature branch** from main: `git checkout -b feat/feature-name`
2. **Implement changes** with proper error handling and tests
3. **Run validation commands** and fix any issues:
   - `make validate-branch` - Comprehensive validation
   - `make lint` - Fix all linting errors
   - `python -m pytest` - Ensure all tests pass
   - Add new tests for new functionality
4. **Commit changes** with descriptive messages
5. **Push branch** to remote repository
6. **ASK USER PERMISSION** before creating any pull request
7. **Create pull request** (only after user approval) with comprehensive description:
   - Summary of changes
   - Technical implementation details
   - Test coverage information
   - Benefits and impact

**🚨 CRITICAL RULE: Never create pull requests without explicit user permission. Always ask first.**

### PR Quality Standards
- **All linting must pass** - No exceptions
- **All tests must pass** - Both existing and new tests
- **Code coverage** - New functionality must include tests
- **Documentation** - Update relevant documentation
- **Backward compatibility** - Maintain existing API contracts

## Security Considerations

- **Secrets management** via GCP Secret Manager in production
- **Environment-based configuration** to avoid hardcoded credentials
- **Input validation** through Pydantic models
- **Error message sanitization** to prevent information leakage
- **Proper credential handling** in containers and deployments