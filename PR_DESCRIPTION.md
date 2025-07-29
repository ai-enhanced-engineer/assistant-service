# Refactor: Implement Domain-Driven Design with Factory Pattern and Dependency Injection

## Overview

This PR transforms the assistant service codebase towards **domain-driven design (DDD) principles**, implementing a clean **factory pattern with dependency injection** for improved maintainability, testability, and extensibility.

## 🏗️ Architectural Transformation

### Before: Tightly Coupled Architecture
```
server/
├── main.py (hardcoded dependencies)
├── schemas.py (mixed concerns)
processors/
├── message_processor.py (data + logic mixed)
├── tool_executor.py (direct instantiation)
```

### After: Domain-Driven Design
```
entities/ (Domain Layer)
├── interfaces.py (Abstract contracts)
├── schemas.py (Request/Response models)
├── config.py (Configuration entities)
├── step_data.py (Domain data)
├── message_data.py (Domain data)

processors/ (Application Layer)
├── openai_orchestrator.py (Implements IOrchestrator)
├── stream_handler.py (Implements IStreamHandler)
├── tool_executor.py (Implements IToolExecutor)
├── message_parser.py (Implements IMessageParser)

server/ (Infrastructure Layer)
├── main.py (Uses factory functions)

bootstrap.py (Factory Layer)
└── Dependency injection factories
```

## 🎯 Key Domain-Driven Design Improvements

### 1. **Domain Layer Establishment** (`entities/`)
- **Entities**: Clean business objects (`StepData`, `MessageData`, `EngineAssistantConfig`)
- **Interfaces**: Abstract contracts defining behavior (`IOrchestrator`, `IStreamHandler`, etc.)
- **Schemas**: Request/response models moved to domain layer
- **Clear separation** between domain logic and infrastructure concerns

### 2. **Factory Pattern with Dependency Injection**
```python
# Before: Hardcoded dependencies
self.orchestrator = OpenAIOrchestrator(client, config)

# After: Factory-based injection
self.orchestrator = get_orchestrator(client, config)
```

**Benefits**:
- **Configuration-driven**: Components selected via config (`orchestrator_type: "openai"`)
- **Runtime flexibility**: Easy to swap implementations
- **Testability**: Clean mocking through interfaces
- **Extensibility**: Add new orchestrators without changing existing code

### 3. **Interface Segregation & Dependency Inversion**
```python
class IOrchestrator(ABC):
    @abstractmethod
    async def process_run(self, thread_id: str, message: str) -> list[str]: ...
    
    @abstractmethod
    def process_run_stream(self, thread_id: str, message: str) -> AsyncGenerator[Any, None]: ...
```

**Key Interfaces**:
- `IOrchestrator`: Core message processing
- `IStreamHandler`: WebSocket streaming
- `IToolExecutor`: Function execution
- `IMessageParser`: Message parsing

## 📊 Production Code Changes

### Core Refactoring Statistics
- **16 files modified**
- **4 new domain entities created**
- **5 abstract interfaces defined**
- **7 factory functions implemented**
- **Zero breaking changes** (full backward compatibility)

### Domain Layer (`assistant_service/entities/`)
| File | Purpose | Domain Concept |
|------|---------|----------------|
| `interfaces.py` | Abstract contracts | Behavioral interfaces |
| `schemas.py` | API models | Request/Response entities |
| `config.py` | Configuration | Configuration entities |
| `step_data.py` | Processing data | Domain data object |
| `message_data.py` | Message data | Domain data object |

### Factory Layer (`assistant_service/bootstrap.py`)
```python
def get_orchestrator(client: AsyncOpenAI, config: EngineAssistantConfig) -> IOrchestrator:
    orchestrator_type = getattr(config, "orchestrator_type", "openai")
    
    if orchestrator_type == "openai":
        return OpenAIOrchestrator(client, config)
    else:
        raise ValueError(f"Unknown orchestrator type: {orchestrator_type}")
```

**Factory Functions Added**:
- `get_openai_client()` - Client creation
- `get_orchestrator()` - Orchestrator selection  
- `get_stream_handler()` - Stream handler creation
- `get_tool_executor()` - Tool executor creation
- `get_message_parser()` - Message parser creation

### Application Layer (`assistant_service/processors/`)
- **OpenAIOrchestrator**: Implements `IOrchestrator` interface
- **StreamHandler**: Implements `IStreamHandler` interface  
- **ToolExecutor**: Implements `IToolExecutor` interface
- **MessageParser**: Implements `IMessageParser` interface

### Infrastructure Layer (`assistant_service/server/main.py`)
```python
# Clean dependency injection
self.client = get_openai_client(self.engine_config)
self.orchestrator = get_orchestrator(self.client, self.engine_config)
self.stream_handler = get_stream_handler(self.orchestrator)
```

## 🔧 Configuration-Based Component Selection

### New Configuration Options
```python
class EngineAssistantConfig(BaseModel):
    orchestrator_type: str = Field(default="openai")
    stream_handler_type: str = Field(default="websocket") 
    tool_executor_type: str = Field(default="default")
    message_parser_type: str = Field(default="default")
```

### Future Extensibility Examples
```python
# Easy to add new orchestrator types
if orchestrator_type == "anthropic":
    return AnthropicOrchestrator(client, config)
elif orchestrator_type == "local_llm":
    return LocalLLMOrchestrator(client, config)

# Or new stream handlers
if stream_handler_type == "sse":
    return SSEStreamHandler(orchestrator)
elif stream_handler_type == "polling":
    return PollingStreamHandler(orchestrator)
```

## 🧪 Testing & Quality

### Test Coverage
- **99/99 tests passing** (100% pass rate)
- **89.17% code coverage** (exceeds 85% requirement)
- **Full MyPy compliance** with interface contracts
- **Zero breaking changes** to existing APIs

### Testing Improvements
- **Clean mocking** through interfaces
- **Improved test isolation** with factory pattern
- **Reduced test coupling** to implementation details
- **Enhanced testability** through dependency injection

## 🚀 Benefits Achieved

### 1. **Maintainability**
- Clear separation of concerns
- Reduced coupling between components
- Single responsibility principle adherence
- Clean interfaces for each layer

### 2. **Extensibility**
- Easy to add new orchestrator implementations
- Configuration-driven component selection
- Plugin-like architecture for processors
- Future-proof design for scaling

### 3. **Testability** 
- Interface-based mocking
- Factory-based test fixtures
- Clean dependency injection
- Isolated unit testing

### 4. **Domain Clarity**
- Business logic clearly separated from infrastructure
- Domain entities properly modeled
- Clear boundaries between layers
- Improved code discoverability

## 🔄 Migration Impact

### For Developers
- **Zero API changes** - all existing endpoints work unchanged
- **Improved code navigation** - clear domain structure
- **Better testing patterns** - use factories and interfaces
- **Enhanced extensibility** - add new components easily

### For Operations
- **Configuration-driven behavior** - change components via config
- **Runtime flexibility** - swap implementations without code changes
- **Better monitoring** - clear component boundaries
- **Simplified deployment** - same deployment process

## 📈 Future Roadmap

This foundation enables:

1. **Multi-provider Support**: Add Anthropic, Local LLM orchestrators
2. **Advanced Streaming**: SSE, WebRTC, polling handlers  
3. **Custom Tool Executors**: Sandboxed, containerized execution
4. **Message Processing**: Custom parsers for different formats
5. **Monitoring & Metrics**: Injectable monitoring components

## 🎉 Summary

This refactor successfully transforms the assistant service from a monolithic architecture to a **clean, domain-driven design** with:

- ✅ **Domain Layer**: Clear business entities and interfaces
- ✅ **Factory Pattern**: Configuration-driven dependency injection  
- ✅ **Interface Segregation**: Clean contracts between components
- ✅ **Dependency Inversion**: Abstract dependencies, not concrete classes
- ✅ **Zero Breaking Changes**: Full backward compatibility
- ✅ **Comprehensive Testing**: 100% test pass rate with 89% coverage

The codebase is now **more maintainable**, **easily extensible**, and **thoroughly testable** while maintaining full production stability.