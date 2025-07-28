# Development Guide

Project-agnostic development guidelines for efficient, maintainable software engineering.

## ⚡ First-Time Setup Instructions for Claude

**IMPORTANT**: When encountering this CLAUDE.md file in a new project for the first time, you should:

1. **Analyze the project structure** to understand its type (API service, ML/research, CLI tool, library, etc.)
2. **Offer to help adapt these guidelines** by asking the user:
   > "I notice this is the first time working with CLAUDE.md in this project. Would you like me to:
   > 1. Review and update CLAUDE.md to mark which sections apply to this specific project type?
   > 2. Create a CLAUDE-project.md with project-specific guidelines, workflows, and patterns?
   > 
   > This will help me better understand your project's conventions and provide more accurate assistance."

3. If the user agrees, create a plan that includes:
   - Identifying which optional sections in CLAUDE.md apply (API, containerization, ML/research, etc.)
   - Creating CLAUDE-project.md with:
     - Project overview and architecture
     - Specific development workflows
     - Custom Make targets and their purposes
     - Project-specific conventions and patterns
     - Integration guides for project components

## Project-Specific Guidelines

For project-specific patterns and workflows, see [CLAUDE-project.md](./CLAUDE-project.md)

## 🚨 Critical Reminders & Common Pitfalls

### ALWAYS Remember
1. **Run validation before ANY commit**: `make validate-branch` is non-negotiable
2. **Never assume dependencies exist**: Check `pyproject.toml` or equivalent before imports
3. **Test modifications immediately**: Don't accumulate changes without validation
4. **Read existing code patterns first**: Match the project's style, don't impose your own
5. **Check for existing implementations**: Search before creating new utilities/helpers

### Common Pitfalls to Avoid
- **Creating duplicate functionality**: Always search for existing implementations first
- **Ignoring type hints**: MyPy errors are failures, not warnings
- **Skipping error handling**: Every external call needs try/except
- **Hardcoding values**: Use configuration files or environment variables
- **Breaking existing tests**: Run tests BEFORE and AFTER changes
- **Assuming file locations**: Use proper path resolution, not hardcoded paths

## 📋 Development Workflow & Priorities

### When Starting a Task
1. **Understand the request fully** - Ask clarifying questions if needed
2. **Search existing code** - Use Grep/Glob to find similar patterns
3. **Read related tests** - Understand expected behavior
4. **Plan the approach** - Use TodoWrite for multi-step tasks
5. **Implement incrementally** - Test each change immediately

### Decision Priority Order
When making implementation decisions, prioritize in this order:
1. **Existing patterns in the codebase** - Consistency over perfection
2. **Explicit project conventions** - Check CLAUDE-project.md
3. **Team standards** - As documented in configs/docs
4. **Industry best practices** - Only if no project precedent exists

### Before Making Changes
- ✅ Have I searched for existing implementations?
- ✅ Will this break existing functionality?
- ✅ Am I following the project's patterns?
- ✅ Have I checked the test suite?
- ✅ Is this the minimal change needed?

## Quick Start

### Essential Development Commands

Most modern projects use Make as a task runner. The following patterns are common across projects:

#### Environment Management
- **`make environment-create`**: Initial setup that typically:
  - Installs package manager (e.g., `uv`, `poetry`, `pip-tools`)
  - Creates virtual environment with correct Python version
  - Installs all dependencies including dev dependencies
  - Sets up pre-commit hooks for code quality
- **`make environment-sync`**: Re-sync dependencies after `pyproject.toml` or similar changes
- **`make environment-delete`**: Clean removal of virtual environment
- **`make environment-list`**: Show installed packages and versions

#### Code Quality Workflow
- **`make format`**: Auto-format code (typically with Ruff, Black, or similar)
- **`make lint`**: Run linters and auto-fix issues where possible
- **`make type-check`**: Static type checking (MyPy or similar)
- **`make validate-branch`**: Combined format + lint + type-check for pre-commit validation

#### Testing Commands
- **`make unit-test`**: Run unit tests only
- **`make functional-test`**: Run functional/integration tests
- **`make integration-test`**: Run tests requiring external dependencies
- **`make all-test`**: Run entire test suite with coverage reporting
- **`make test-validate-branch`**: Validate code quality + run tests
- **`make all-test-validate-branch`**: Complete validation + all tests

#### Development Helpers (API Projects)
*For projects with API/web services:*
- **`make api-run`**: Start development server with hot-reload
- **`make api-validate`**: Run API-specific tests and validations
- **`make api-docs`**: Start server with interactive API documentation

#### Service Management (Containerized Projects)
*For projects with Docker/container deployment:*
- **`make service-build`**: Build production container/package
- **`make service-start`**: Start production service locally
- **`make service-stop`**: Stop running service
- **`make service-quick-start`**: One-command build and start
- **`make service-validate`**: Validate service configuration and health

#### Cleanup Commands
- **`make clean-project`**: Remove Python caches, build artifacts, etc.
- **`make clean-research`**: Clean experiment outputs *(for ML/research projects)*

### Python Version Management
- Python version typically specified in `.python-version` file
- Modern tools like `uv` can auto-install the correct Python version
- Virtual environment should match this version exactly

### Development Best Practices
- Always run `make validate-branch` before committing
- Use `make environment-sync` after pulling changes with dependency updates
- Run appropriate test suites based on change scope
- Line length: Follow project standards (typically 120 characters)

## Common Project Structure

### Expected File Organization
```
project_root/
├── src/ or {package_name}/     # Main source code
│   ├── __init__.py
│   ├── api/                    # API endpoints (if applicable)
│   ├── core/                   # Business logic
│   ├── models/                 # Data models/schemas
│   ├── services/               # External service integrations
│   └── utils/                  # Shared utilities
├── tests/                      # Test files mirroring src structure
│   ├── unit/
│   ├── functional/
│   └── integration/
├── scripts/                    # Development/deployment scripts
├── docs/                       # Documentation
├── research/                   # Experiments (ML projects)
├── registry/                   # Production artifacts
├── .python-version            # Python version specification
├── pyproject.toml             # Project configuration
├── Makefile                   # Task automation
├── CLAUDE.md                  # This file
└── CLAUDE-project.md          # Project-specific guidelines
```

### Key Files to Check First
1. **`pyproject.toml`** - Dependencies, project metadata, tool configs
2. **`Makefile`** - Available commands and workflows
3. **`.python-version`** - Required Python version
4. **`README.md`** - Project overview and setup
5. **Test files** - Understand expected behavior and patterns

## Architecture Overview

### Design Principles
**Modular, workflow-based architecture** with clean separation of concerns:

1. **Configuration-Driven** - Components instantiated via config files + dependency injection
2. **Plugin-Based** - Multiple implementations through factory pattern
3. **Extensibility** - Components registered via enums and factories
4. **Abstraction** - Pluggable implementations via abstract interfaces
5. **Type Safety** - Pydantic models + strict MyPy
6. **Observability** - Structured logging and tracing

### Core Components
- **Application Layer** - HTTP API or CLI interface
- **Business Logic** - Core functionality and workflows
- **Configuration** - Pydantic models with validation
- **Registry** - Factory functions for dependency injection
- **Bootstrap** - Application initialization logic

## Core Engineering Principles

### 1. Clarity and Maintainability
- Function and test names must be descriptive and self-explanatory
- **Inline comments**: Only add when explaining non-obvious logic or highlighting important business logic steps
  - Never explain what the code does (redundant with readable code)
  - Only explain why the code does something unexpected or complex
  - Use for important algorithm steps (e.g., `# Rule 1: Perfect Setosa separation`)
  - Avoid obvious comments like `# Initialize variables` or `# Return result`
- **Docstrings**: Follow strict guidelines to avoid redundancy and maintain value
  - **NEVER add docstrings to trivial functions** like `__init__`, simple getters/setters, or self-explanatory methods
  - **NEVER include Args/Returns sections** unless absolutely crucial for understanding complex behavior
  - **ONLY add docstrings** when they provide clear, non-obvious content that supports understanding
  - **Focus on domain knowledge** like business rules, EDA insights, architectural patterns, or complex algorithms
  - **Examples of good docstrings**: Document specific business logic rules, explain domain-specific thresholds, describe architectural patterns
  - **Examples to avoid**: Restating what the function name conveys, obvious parameter descriptions, redundant return value descriptions
- Follow consistent naming conventions:
  - For tests: `test__{function_name}__{what_is_being_tested}`

### 2. Strong Typing and Static Guarantees
- All code must be fully MyPy-compliant
- Use precise type annotations for all functions and data structures
- Never remove `# type: ignore` comments; these are intentional and must be preserved

### 3. Structured and Observable Code
- Use structured logging with semantic key-value pairs:
  - `logger.debug("event", key1=value1, key2=value2)`
- Avoid unstructured logs or print statements
- Log relevant inputs, outputs, and failure details to support debugging and observability

### 4. Explicit and Minimal Interfaces
- Prefer explicit arguments and flat configuration structures
- Avoid nested or dynamic magic in configurations unless strictly necessary
- Ensure all functions and classes have a clear, single responsibility

### 5. Separation of Concerns
- Maintain a clean modular structure across services, pipelines, or libraries
- Each module or class should encapsulate a distinct, well-defined purpose
- Do not mix unrelated responsibilities within the same abstraction

### 6. Production Readiness by Default
- Assume all code is production-bound:
  - Handle errors defensively
  - Fail loudly and early when assumptions are violated
  - Validate inputs and sanitize outputs as needed
- Include tests for all logic paths, including edge cases

### 7. Tool-Agnostic Logic
- Core logic should not be tightly coupled to third-party tools
- External dependencies must be abstracted behind clear interfaces where possible
- Design systems to allow easy substitution or mocking of dependencies

## Coding Conventions

### Naming & Style
- **Classes**: `PascalCase` (`ServiceConfig`, `DataProcessor`)
- **Functions/Variables**: `snake_case` (`get_config`, `user_id`)
- **Constants**: `UPPER_SNAKE_CASE` (`DEFAULT_TIMEOUT`)
- **Enums**: `PascalCase` class, `UPPER_SNAKE_CASE` values
- **Files**: `snake_case` (`data_processor.py`)

### Configuration Patterns
- **String enums** for registration (`RegisteredComponents`)
- **Pydantic validation** with `Field(description="...")`
- **Custom validators** with `@field_validator`
- **Environment mapping** via `alias` parameter

### Component Development
1. Add to relevant enum for registration
2. Implement with proper interface/signature
3. Add to factory function in registry
4. Create config subclass if needed

## Testing Guidelines

### Test Architecture & Organization

#### Test Classification
1. **Unit Tests** (`@pytest.mark.unit`) - Test individual components in isolation
2. **Functional Tests** (`@pytest.mark.functional`) - Test complete workflows
3. **Integration Tests** (`@pytest.mark.integration`) - Test with external dependencies

### Testing Standards
- **Markers**: `@pytest.mark.{unit,functional,integration}`
- **Fixtures** in `conftest.py`
- **Custom Abstractions**: Avoid mock libraries, use project-specific implementations
- **Async testing** with `pytest-asyncio` *(for async/await codebases)*
- **Mirror source structure** in test organization

### Custom Abstractions Over Mocks

**CRITICAL: Use Custom Abstractions, Not Mock Libraries**

This project **AVOIDS** explicit mock libraries like `unittest.mock.MagicMock` and `AsyncMock`. Instead, it prioritizes custom abstractions and real implementations designed for testing.

**Preferred Approaches (in order of preference):**

1. **Monkeypatch** (preferred method):
```python
def test_function(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_method(self, user_input: str) -> tuple[str, str]:
        return "EXPECTED_RESULT", "EXPECTED_MESSAGE"
    
    monkeypatch.setattr(TargetClass, "method_name", mock_method)
```

2. **Fake implementations**:
```python
# Use project-specific fake classes
fake_processor = FakeDataProcessor()  # Instead of MagicMock
```

3. **Local implementations with controlled data** (most preferred):
```python
# Use project-specific Local* implementations
local_service = LocalDataService(sample_response={"data": [...]})
```

4. **Custom test classes extending local implementations**:
```python
class FailingService(LocalDataService):
    def process_data(self, data: str) -> str:
        raise RuntimeError("Service failure")
```

### Test Function Naming
```python
def test__component_or_method__specific_behavior_or_scenario() -> None:
    # Use double underscores to clearly separate:
    # 1. Component/method being tested
    # 2. Specific behavior being validated
```

## Error Handling and Patterns

### Error Handling Philosophy
- Fail fast and loud - don't hide errors
- Provide context in error messages
- Use standard exceptions unless custom ones exist
- Always preserve the error chain with `from e`

### Common Error Patterns

#### API/Service Errors
```python
try:
    response = await external_service.call()
except RequestException as e:
    logger.error("External service failed", exc_info=e, service="service_name", url=url)
    raise ValueError(f"Failed to fetch data from {service_name}") from e
```

#### File Operations
```python
try:
    with open(file_path, 'r') as f:
        data = f.read()
except FileNotFoundError as e:
    logger.error("Required file missing", file_path=file_path)
    raise ValueError(f"Configuration file not found: {file_path}") from e
except IOError as e:
    logger.error("File read failed", exc_info=e, file_path=file_path)
    raise RuntimeError(f"Unable to read file: {file_path}") from e
```

#### Validation Errors
```python
def validate_input(data: dict) -> None:
    if not data.get("required_field"):
        raise ValueError("Missing required field: 'required_field'")
    
    if data["number_field"] < 0:
        raise ValueError(f"Invalid value for number_field: {data['number_field']} (must be positive)")
```

### Configuration Validation
Always validate configuration at startup:
```python
def validate_config(config: AppConfig) -> None:
    if not config.required_field:
        raise ValueError("Required field must be provided")
```

### Resource Management
Use context managers for all resources:
```python
async with get_resource() as resource:  # For async projects
    await resource.process()
    # Automatic cleanup
```

## Security Considerations
*For applications handling sensitive data or external access:*

### Input Validation
- All user inputs validated through Pydantic models
- Content filtering and sanitization
- Maximum input length enforcement

### API Key Management *(for services with external integrations)*
- Environment variable-based configuration
- No hardcoded secrets in code
- Key rotation support

### Data Protection *(for multi-tenant applications)*
- Session-based data isolation
- Cross-tenant data protection
- Secure data handling practices

## Deployment and Environment

### Environment Variables
- Use descriptive names with project prefix
- Document all required variables
- Provide sensible defaults where possible
- Use environment aliasing in Pydantic configs

### Monitoring and Observability *(for production services)*
- Structured logging with correlation IDs
- Health check endpoints
- Performance monitoring
- Error tracking and alerting

## Communication and Collaboration

### Commit Message Structure

#### General Structure
```
type: brief description

- Detailed bullet points of changes
- Performance improvements with metrics
- Quality assurance notes (tests, linting, type safety)
- Impact on architecture or future development
```

**Commit Types:**
- `feat`: New features or functionality
- `fix`: Bug fixes
- `refactor`: Code restructuring without functional changes
- `test`: Testing improvements or additions
- `docs`: Documentation updates

#### Feature Integration Template
For major feature additions like new predictors, use this concrete structure:

```
feat: integrate {FeatureName} with {MainBenefit}

- Implement {ComponentName} class with {TechnicalDetails}
- Add comprehensive test suite with {TestCount} test cases covering {Coverage}%
- Register {feature_name} in configuration and factory with {Integration}
- Promote {artifact} to {location} for {purpose}
- Refactor {system} with {improvement} for {benefit}
- Fix {issue} for {resolution}
- Update {component} to {change} for {reason}

{FeatureName} Performance: {metrics} on {dataset}
{SystemImprovement}: {description}
All Tests Pass: {coverage} test coverage maintained, {validation} verified
```

**Example:**
```
feat: implement caching layer for improved performance

- Add Redis-based caching with TTL configuration
- Implement cache invalidation strategies for data consistency
- Add comprehensive test suite with 15 test cases covering cache hits/misses
- Update configuration to support cache enabling/disabling
- Add performance monitoring for cache effectiveness
- Document cache key patterns and eviction policies

Performance: 3x improvement in response time for cached queries
Memory Usage: Optimized with 100MB cache size limit
All Tests Pass: 98% coverage maintained, integration tests verified
```

### PR Description Template
**Important**: Always create the PR description in a .md file first (e.g., `pr_description.md`) so the user can review it. Delete this file after the PR is created.

- **Overview**: High-level summary of changes that focuses on the main feature, fix or experiment being pushed. Ask the user for clarification if needed
- **Key changes**: Main introduced abstractions and supported changes, communicated in a feature-focused way with changes grouped by functionality. Mention the file where each key change happened in each bullet point
- **Tests**: Describe the tests added and their focus, mention the coverage if new tests are added
- **Next steps**: Future work or enhancements planned

### Validation Checklist
- [ ] All tests pass (existing + new)
- [ ] Linter clean (`make lint`)
- [ ] Type checker clean (`make type-check`)
- [ ] Pre-commit hooks pass
- [ ] Performance benchmarks *(for performance-critical changes)*
- [ ] Documentation updated

## Extension Points

### Adding New Components
- Create enum entry for registration
- Implement interface or abstract base class
- Add factory function to registry
- Create configuration model
- Add comprehensive tests

### Configuration Management
- Use Pydantic models with validation
- Environment variable mapping
- Hierarchical configuration support
- Runtime configuration updates

This guide provides comprehensive information needed for effective development, combining architectural understanding, implementation details, testing strategies, and operational considerations.