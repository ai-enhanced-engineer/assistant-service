#!/usr/bin/env python3
"""WebSocket-based streaming chat client for the assistant-service API."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import websockets

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from assistant_service.structured_logging import get_logger  # noqa: E402

logger = get_logger("websocket_client")


async def chat_session(base_url: str, thread_id: Optional[str] = None):
    """Run an interactive chat session with the assistant via WebSocket."""
    # First, get a thread ID if not provided
    if not thread_id:
        import httpx

        start_url = f"http://{base_url.replace('ws://', '').replace('wss://', '')}/start"
        async with httpx.AsyncClient() as client:
            response = await client.get(start_url)
            if response.status_code == 200:
                data = response.json()
                thread_id = data["thread_id"]
                initial_message = data.get("initial_message", "")
                print(f"\n{'=' * 60}")
                print("New conversation started!")
                print(f"Thread ID: {thread_id}")
                if initial_message:
                    print(f"Assistant: {initial_message}")
                print(f"{'=' * 60}\n")
            else:
                print(f"Failed to start conversation: {response.status_code}")
                return

    # Connect to WebSocket
    ws_url = f"{base_url}/ws/chat"
    print(f"Connecting to {ws_url}...")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("Connected! Type 'exit' or 'quit' to end the conversation.\n")

            while True:
                # Get user input
                user_input = input("You: ")
                if user_input.strip().lower() in {"exit", "quit"}:
                    logger.info("Ending conversation")
                    break

                # Send message
                message_data = {"thread_id": thread_id, "message": user_input}

                await websocket.send(json.dumps(message_data))
                logger.info("Sent message", thread_id=thread_id, message=user_input)

                print("\nAssistant: ", end="", flush=True)

                # Receive streaming response
                assistant_messages = []
                try:
                    while True:
                        response = await websocket.recv()
                        event = json.loads(response)

                        # Handle different event types
                        if event.get("event") == "thread.message.delta":
                            # Extract text delta
                            delta = event.get("data", {}).get("delta", {})
                            content = delta.get("content", [])
                            for item in content:
                                if item.get("type") == "text":
                                    text_value = item.get("text", {}).get("value", "")
                                    print(text_value, end="", flush=True)
                                    assistant_messages.append(text_value)

                        elif event.get("event") == "thread.run.completed":
                            # Run completed
                            print("\n")
                            break

                        elif event.get("event") == "thread.run.failed":
                            # Run failed
                            print("\n[Error: Run failed]")
                            logger.error("Run failed", event=event)
                            break

                        elif event.get("error"):
                            # Error response
                            print(f"\n[Error: {event.get('error')}]")
                            logger.error("WebSocket error", error=event.get("error"))
                            break

                except websockets.exceptions.ConnectionClosed:
                    print("\n[Connection closed]")
                    break
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse response", error=str(e))
                    print("\n[Error parsing response]")

                # Log the complete assistant response
                full_response = "".join(assistant_messages)
                if full_response:
                    logger.info("Assistant response", response=full_response)

    except websockets.exceptions.WebSocketException as e:
        print(f"WebSocket error: {e}")
        logger.error("WebSocket connection error", error=str(e))
    except KeyboardInterrupt:
        print("\n\nConversation interrupted.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.error("Unexpected error", error=str(e))


def main():
    """Main entry point for the WebSocket client."""
    parser = argparse.ArgumentParser(description="WebSocket-based streaming chat client for assistant-service")
    parser.add_argument(
        "--base-url",
        type=str,
        default="ws://localhost:8000",
        help="Base WebSocket URL (default: ws://localhost:8000)",
    )
    parser.add_argument(
        "--thread-id",
        type=str,
        default=None,
        help="Existing thread ID to continue conversation (optional)",
    )

    args = parser.parse_args()

    # Run the async chat session
    asyncio.run(chat_session(args.base_url, args.thread_id))


if __name__ == "__main__":
    main()
