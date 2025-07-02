# Instructions for AI Agents

Welcome AI agents! This document explains how to work effectively with this assistant service codebase.

## Project Context

You are working with a **multi-tenant Python assistant service** that integrates with OpenAI's Assistant API. This service allows deploying customized AI assistants with client-specific tools, personalities, and capabilities.

### Key Characteristics
- **Multi-tenant architecture** - Each client has isolated configurations and custom functions
- **OpenAI integration** - Uses OpenAI's Assistant API with streaming responses
- **Custom tool support** - Python functions are exposed as tools to assistants
- **Cloud-native** - Deployed on Google Cloud Platform with proper configuration management
- **Type-safe** - Comprehensive use of Pydantic models and type hints

## Codebase Structure Understanding

When working with this codebase, understand these core areas:

### Core Components
- `assistant_engine/` - **Main runtime service** (FastAPI app, OpenAI integration, message processing)
- `assistant_factory/` - **Assistant creation system** (builds new assistants with custom tools)
- `botbrew_commons/` - **Shared infrastructure** (data models, configuration repositories)
- `client_spec/` directories - **Client customizations** (custom functions, instructions, configurations)

### Configuration Pattern
- **Environment-based config** - Uses Pydantic Settings with environment variables
- **Repository pattern** - Abstract storage for configs and secrets (GCP + local implementations)
- **Client isolation** - Each client has separate configuration namespace

## Development Workflow for AI Agents

### 🚨 CRITICAL AI AGENT RULES

**NEVER CREATE PULL REQUESTS WITHOUT USER PERMISSION**
- Always ask the user: "Should I create a pull request for these changes?"
- Wait for explicit approval before using `gh pr create` or any PR creation commands
- The user must give clear permission before any PR is created

### Before Making Changes
1. **Always run linting and type checking first**:
   ```bash
   make lint   # REQUIRED - must pass
   make format # Format code
   python -m pytest # REQUIRED - all tests must pass
   ```

2. **CRITICAL: Pre-PR Validation**:
   ```bash
   # Comprehensive validation (recommended):
   make validate-branch  # Runs linting + tests automatically
   
   # Or individual commands:
   make lint           # Fix all linting errors
   python -m pytest   # Ensure all tests pass
   ```

   **Automated Protection**: Pre-commit hooks automatically run validation before commits.

### When Adding New Features
1. **Follow existing patterns** - Look at similar implementations before writing new code
2. **Use type hints consistently** - All functions should have proper type annotations
3. **Add Pydantic models** for any new data structures
4. **Update tests** - Both unit and integration tests for new functionality

### When Working with Client Configurations
- **Client-specific code** goes in `assistant_factory/client_spec/{CLIENT_ID}/`
- **Custom functions** should be added to the client's `functions.py` and `TOOL_MAP`
- **Agent instructions** go in the client's `instructions.py` file
- **Test configurations locally** before deploying

### When Modifying APIs
- **Maintain backward compatibility** - This is a service with existing clients
- **Update both REST and WebSocket endpoints** if changes affect both
- **Add proper error handling** - Use existing error response patterns
- **Test streaming functionality** - Many features rely on real-time responses

### Pull Request Creation Workflow
**MANDATORY PROCESS** - Follow this exact sequence:

1. **Create feature branch** from main:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/descriptive-feature-name
   ```

2. **Implement changes** with comprehensive tests

3. **REQUIRED: Run validation** (must all pass):
   ```bash
   make validate-branch  # Comprehensive validation (recommended)
   # OR individual commands:
   make lint           # Must pass with no errors
   python -m pytest   # All tests must pass
   make format        # Apply consistent formatting
   ```
   
   **Note**: Pre-commit hooks will automatically run validation, preventing commits that fail quality checks.

4. **Fix any issues** from step 3 before proceeding

5. **Commit and push**:
   ```bash
   git add .
   git commit -m "descriptive commit message"
   git push -u origin feat/descriptive-feature-name
   ```

6. **ASK USER BEFORE CREATING PR** - Never create PRs without explicit permission

7. **Create PR** (only after user approval) with comprehensive description including:
   - Summary of changes
   - Technical implementation details
   - Test coverage
   - Benefits and impact

**⚠️ CRITICAL: Always ask the user for permission before creating any pull request. Never create PRs automatically.**

**⚠️ PRs that don't pass `make lint` and `python -m pytest` will be rejected.**

## Common Tasks and Patterns

### Adding a New Custom Function/Tool
1. Define function in `client_spec/{CLIENT_ID}/functions.py`
2. Add to `TOOL_MAP` dictionary in same file
3. Create tool specification dictionary (see existing examples)
4. Update client assistant configuration to include the function
5. Test tool execution during assistant runs

### Creating New Client Configuration
1. Create new directory under `client_spec/{CLIENT_ID}/`
2. Add `assistants.py`, `functions.py`, `instructions.py` files
3. Follow existing client patterns (see `leogv` example)
4. Test configuration loading and assistant creation

### Debugging Assistant Issues
- **Check logs** - Structured logging shows OpenAI API interactions
- **Verify configuration** - Ensure client config is properly loaded
- **Test tool execution** - Verify custom functions work independently
- **Check OpenAI API responses** - Look for API errors or rate limits

## Code Quality Standards

### Required Practices
- **Comprehensive error handling** - Especially for external API calls
- **Input validation** - Use Pydantic models for all data validation
- **Security awareness** - Never hardcode credentials, sanitize error messages
- **Documentation** - Add docstrings for complex functions and classes

### Testing Expectations
- **Mock external dependencies** - Especially OpenAI API calls
- **Test error conditions** - Not just happy path scenarios
- **Integration tests** - Test full request/response cycles
- **Configuration tests** - Verify config loading and validation

## Understanding the Data Flow

When debugging or extending functionality, understand this flow:
```
Client Request → FastAPI Endpoint → OpenAI API → Streaming Events → 
Tool Execution → Response Processing → Client Response
```

Key processing points:
- **Message creation** in OpenAI threads
- **Event stream processing** for real-time responses
- **Tool call interception** for custom function execution
- **Response extraction** from assistant messages

## Working with Dependencies

### Core Dependencies
- **FastAPI** - Web framework and async support
- **OpenAI** - Official OpenAI API client
- **Pydantic** - Data validation and settings management
- **Google Cloud libraries** - Storage and secret management

### Development Tools
- **uv** - Package management (faster than pip)
- **ruff** - Linting and formatting
- **pytest** - Testing framework
- **mypy** - Type checking

## Environment and Deployment Context

### Local Development
- Uses in-memory repositories for config/secrets
- Docker Compose for container testing
- Environment variables for configuration

### Production Deployment
- Google Cloud Run for serverless deployment
- Cloud Storage for configuration persistence
- Secret Manager for credential management

## Common Pitfalls to Avoid

1. **Don't hardcode client IDs** - Use configuration system for client isolation
2. **Don't skip error handling** - OpenAI API calls can fail
3. **Don't forget type hints** - Code quality depends on proper typing
4. **Don't break existing patterns** - Follow established architectural patterns
5. **Don't commit secrets** - Use environment variables and Secret Manager

## Getting Help

When working on this codebase:
- **Check existing implementations** - Similar functionality probably exists
- **Review test files** - They show expected usage patterns  
- **Look at client configurations** - See how features are actually used
- **Run the full test suite** - Ensures your changes don't break existing functionality

Remember: This is a production service with real clients. Always prioritize stability and backward compatibility when making changes.

