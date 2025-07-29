"""Main application module for the Assistant Engine.

This module bootstraps the FastAPI application with all necessary components.
"""

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional, Union

from fastapi import FastAPI, HTTPException, WebSocket
from openai import AsyncOpenAI

from assistant_service.repositories import (
    GCPConfigRepository,
    GCPSecretRepository,
    LocalConfigRepository,
    LocalSecretRepository,
)

from ..config import build_engine_config
from ..core.run_processor import RunProcessor
from ..core.tool_executor import ToolExecutor
from ..infrastructure.openai_client import OpenAIClientFactory
from ..structured_logging import configure_structlog, get_logger
from .endpoints import APIEndpoints
from .schemas import ChatRequest, ChatResponse

# Use new structured logger
logger = get_logger("MAIN")


def create_lifespan(api_instance: "AssistantEngineAPI") -> Any:
    """Create a lifespan context manager for the API instance."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Manage application startup and shutdown."""
        logger.info("Application starting up...")
        created_client = False
        if api_instance.client is None:
            api_instance.client = OpenAIClientFactory.create_from_config(api_instance.engine_config)
            created_client = True
            # Initialize components now that client is available
            api_instance.run_processor = RunProcessor(
                api_instance.client, api_instance.engine_config, api_instance.tool_executor
            )
            api_instance.api_endpoints = APIEndpoints(
                api_instance.client, api_instance.engine_config, api_instance.run_processor
            )
        yield
        logger.info("Application shutting down...")
        if created_client and api_instance.client:
            await api_instance.client.close()

    return lifespan


class AssistantEngineAPI:
    """Main API class for the assistant engine."""

    def __init__(self) -> None:
        """Initialize the assistant engine with configuration."""
        # Set up repositories based on environment
        project_id = os.getenv("PROJECT_ID", "")
        bucket_id = os.getenv("BUCKET_ID", "")
        client_id = os.getenv("CLIENT_ID", "")
        environment = os.getenv("ENVIRONMENT", "development")

        # Use local repositories for development/testing
        if environment == "development" or not project_id or not bucket_id:
            logger.info("Using local repositories for development")
            secret_repository: Union[LocalSecretRepository, GCPSecretRepository] = LocalSecretRepository()
            config_repository: Union[LocalConfigRepository, GCPConfigRepository] = LocalConfigRepository()
        else:
            logger.info("Using GCP repositories for production")
            secret_repository = GCPSecretRepository(project_id=project_id, client_id=client_id)
            config_repository = GCPConfigRepository(client_id=client_id, project_id=project_id, bucket_name=bucket_id)

        self.engine_config = build_engine_config(secret_repository, config_repository)
        self.client: Optional[AsyncOpenAI] = None

        # Log configuration (without sensitive data)
        logger.info(
            "Booting with config",
            assistant_id=self.engine_config.assistant_id,
            assistant_name=self.engine_config.assistant_name,
            initial_message=self.engine_config.initial_message,
            code_interpreter=self.engine_config.code_interpreter,
            retrieval=self.engine_config.retrieval,
            function_names=self.engine_config.function_names,
            openai_apikey="sk" if self.engine_config.openai_apikey else None,
        )

        # Initialize components (client will be set in lifespan)
        self.tool_executor = ToolExecutor()
        # Create placeholders that will be updated in lifespan
        self.run_processor: Optional[RunProcessor] = None
        self.api_endpoints: Optional[APIEndpoints] = None

        # Create FastAPI app
        self.app = FastAPI(title="Assistant Engine", lifespan=create_lifespan(self))

        # Routes will be added after components are initialized
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up routes after components are initialized."""

        @self.app.get("/")
        async def root() -> dict[str, str]:
            if self.api_endpoints:
                return await self.api_endpoints.root()
            return {"message": "Assistant Engine is running"}

        @self.app.get("/start")
        async def start() -> Any:
            if not self.api_endpoints:
                raise HTTPException(status_code=503, detail="Service not initialized")
            return await self.api_endpoints.start_endpoint()

        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest) -> ChatResponse:
            if not self.api_endpoints:
                raise HTTPException(status_code=503, detail="Service not initialized")
            return await self.api_endpoints.chat_endpoint(request)

        @self.app.websocket("/stream")
        async def stream(websocket: WebSocket) -> None:
            if not self.api_endpoints:
                await websocket.close(code=1013, reason="Service not initialized")
                return
            await self.api_endpoints.stream_endpoint(websocket)


def get_app() -> FastAPI:
    """Return a fully configured FastAPI application."""
    # Configure structured logging
    configure_structlog()

    # Use the singleton pattern to avoid re-initialization
    api_instance = _ensure_api_initialized()
    return api_instance.app


# Create a singleton instance for backward compatibility
# Note: Instantiation is deferred to avoid initialization errors during imports
api: Optional[AssistantEngineAPI] = None
app: Optional[FastAPI] = None


def _ensure_api_initialized() -> AssistantEngineAPI:
    """Ensure the API singleton is initialized."""
    global api, app
    if api is None:
        api = AssistantEngineAPI()
        app = api.app
    return api


async def process_run(thread_id: str, human_query: str) -> list[str]:
    """Proxy to the API instance for backward compatibility."""
    api_instance = _ensure_api_initialized()
    if api_instance.run_processor is None:
        raise RuntimeError("Run processor not initialized")
    return await api_instance.run_processor.process_run(thread_id, human_query)


async def process_run_stream(thread_id: str, human_query: str) -> AsyncGenerator[Any, None]:
    """Proxy streaming run for backward compatibility."""
    api_instance = _ensure_api_initialized()
    if api_instance.run_processor is None:
        raise RuntimeError("Run processor not initialized")
    async for event in api_instance.run_processor.process_run_stream(thread_id, human_query):
        yield event


# Export for backward compatibility
__all__ = ["get_app", "AssistantEngineAPI", "process_run", "process_run_stream"]
