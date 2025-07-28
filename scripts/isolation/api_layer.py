#!/usr/bin/env python3
"""Script to run the assistant-service API in isolation for testing and development."""

import argparse
import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load .env file from project root
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Set default environment variables for assistant-service
os.environ.setdefault("SERVICE_NAME", "assistant-service")
os.environ.setdefault("SERVICE_VERSION", "1.1.2")
os.environ.setdefault("LOGGING_LEVEL", "INFO")
os.environ.setdefault("LOG_FORMAT", "json")
os.environ.setdefault("STREAM", "stdout")
os.environ.setdefault("CONTEXT", "development")

# Ensure we're in development mode
os.environ.setdefault("ENVIRONMENT", "development")

# Default test configuration
os.environ.setdefault("PROJECT_ID", "test-project")
os.environ.setdefault("BUCKET_ID", "test-bucket")
os.environ.setdefault("CLIENT_ID", "test-client")


def main():
    """Main entry point for the API runner."""
    parser = argparse.ArgumentParser(description="Run the Assistant Service API in isolation for testing.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the service on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the service on (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging level (default: info)",
    )
    parser.add_argument(
        "--openai-key",
        type=str,
        default=None,
        help="OpenAI API key (can also use OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--assistant-id",
        type=str,
        default=None,
        help="OpenAI Assistant ID to use",
    )
    parser.add_argument(
        "--client-id",
        type=str,
        default="test-client",
        help="Client ID for multi-tenant configuration (default: test-client)",
    )

    args = parser.parse_args()

    # Override logging level if provided
    if args.log_level:
        os.environ["LOGGING_LEVEL"] = args.log_level.upper()

    # Set OpenAI API key if provided
    if args.openai_key:
        os.environ["OPENAI_API_KEY"] = args.openai_key
    elif not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: No OpenAI API key provided. Set OPENAI_API_KEY or use --openai-key")

    # Set assistant ID if provided
    if args.assistant_id:
        os.environ["ASSISTANT_ID"] = args.assistant_id

    # Set client ID
    os.environ["CLIENT_ID"] = args.client_id

    print(f"\n{'=' * 60}")
    print(f"Starting Assistant Service API on {args.host}:{args.port}")
    print(f"{'=' * 60}")
    print(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f"Logging level: {os.environ.get('LOGGING_LEVEL', 'INFO')}")
    print(f"Client ID: {os.environ.get('CLIENT_ID', 'test-client')}")
    print(f"OpenAI API Key: {'Set' if os.environ.get('OPENAI_API_KEY') else 'Not Set'}")
    print(f"\n{'=' * 60}")
    print("Endpoints:")
    print(f"  API Documentation: http://localhost:{args.port}/docs")
    print(f"  Health check: http://localhost:{args.port}/")
    print(f"  Start conversation: http://localhost:{args.port}/start")
    print(f"  Send message: http://localhost:{args.port}/chat")
    print(f"  WebSocket stream: ws://localhost:{args.port}/stream")
    print(f"\n{'=' * 60}")
    print("Example usage:")
    print("  1. Start a conversation:")
    print(f'     curl -X GET "http://localhost:{args.port}/start"')
    print("  2. Send a message:")
    print(f'     curl -X POST "http://localhost:{args.port}/chat" \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"thread_id": "thread_abc123", "message": "Hello!"}\'')
    print(f"{'=' * 60}\n")

    # Run the FastAPI application
    uvicorn.run(
        "assistant_service.main:get_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
