#!/usr/bin/env python3
"""HTTP client for interacting with the assistant-service chat endpoint."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import httpx

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from assistant_service.structured_logging import get_logger  # noqa: E402

logger = get_logger("http_client")


def start_conversation(base_url: str, thread_id: Optional[str] = None):
    """Run an interactive chat session with the assistant via HTTP."""
    client = httpx.Client(base_url=base_url, timeout=30.0)

    try:
        # First, get a thread ID if not provided
        if not thread_id:
            response = client.get("/start")
            if response.status_code == 200:
                data = response.json()
                thread_id = data["thread_id"]
                initial_message = data.get("initial_message", "")
                correlation_id = data.get("correlation_id", "")
                print(f"\n{'=' * 60}")
                print("New conversation started!")
                print(f"Thread ID: {thread_id}")
                print(f"Correlation ID: {correlation_id}")
                if initial_message:
                    print(f"Assistant: {initial_message}")
                print(f"{'=' * 60}\n")
            else:
                print(f"Failed to start conversation: {response.status_code}")
                print(f"Response: {response.text}")
                return

        print("Type 'exit' or 'quit' to end the conversation.")
        print("Type 'curl' to see the equivalent curl command.\n")

        while True:
            user_input = input("You: ")
            if user_input.strip().lower() in {"exit", "quit"}:
                logger.info("Ending conversation")
                break

            # Prepare the request
            payload = {"thread_id": thread_id, "message": user_input}

            # Show curl command if requested
            if user_input.strip().lower() == "curl":
                curl_cmd = f'''curl -X POST "{base_url}/chat" \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(payload, indent=2)}'
'''
                print(f"\nEquivalent curl command:\n{curl_cmd}")
                continue

            try:
                # Send the message
                logger.info("Sending message", thread_id=thread_id, message=user_input)
                response = client.post("/chat", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    responses = data.get("responses", [])

                    print("\nAssistant:")
                    for resp in responses:
                        print(f"  {resp}")
                    print()

                    logger.info("Received responses", count=len(responses))
                else:
                    print(f"\nError: {response.status_code}")
                    print(f"Response: {response.text}\n")
                    logger.error("HTTP error", status_code=response.status_code, response=response.text)

            except httpx.TimeoutException:
                print("\nError: Request timed out. The assistant might be processing a complex request.")
                print("Try again or use the WebSocket client for streaming responses.\n")
                logger.error("Request timeout")
            except httpx.RequestError as e:
                print(f"\nError: Failed to send request: {e}\n")
                logger.error("Request error", error=str(e))
            except json.JSONDecodeError as e:
                print(f"\nError: Failed to parse response: {e}\n")
                logger.error("JSON decode error", error=str(e))
            except Exception as e:
                print(f"\nUnexpected error: {e}\n")
                logger.error("Unexpected error", error=str(e))

    except KeyboardInterrupt:
        print("\n\nConversation interrupted.")
    finally:
        client.close()


def main():
    """Main entry point for the HTTP client."""
    parser = argparse.ArgumentParser(description="HTTP client for chatting with assistant-service")
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base HTTP URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--thread-id",
        type=str,
        default=None,
        help="Existing thread ID to continue conversation (optional)",
    )

    args = parser.parse_args()

    # Run the chat session
    start_conversation(args.base_url, args.thread_id)


if __name__ == "__main__":
    main()
