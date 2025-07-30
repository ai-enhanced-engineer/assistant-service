#!/usr/bin/env python3
"""HTTP-based chat client for the assistant-service API."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import httpx
from httpx_sse import aconnect_sse

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from assistant_service.entities import MESSAGE_DELTA_EVENT, RUN_COMPLETED_EVENT, RUN_FAILED_EVENT  # noqa: E402
from assistant_service.structured_logging import get_logger  # noqa: E402

logger = get_logger("http_client")


async def process_sse_with_httpx_sse(client: httpx.AsyncClient, url: str, payload: dict) -> str:
    """Process Server-Sent Events using httpx-sse for proper streaming."""
    chunks = []

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    async with aconnect_sse(client, "POST", url, json=payload, headers=headers, timeout=60.0) as event_source:
        async for sse in event_source.aiter_sse():
            try:
                # Debug: print raw SSE event
                # print(f"\n[DEBUG] Event: {sse.event}, Data length: {len(sse.data) if sse.data else 0}", flush=True)

                # Parse the SSE data
                event_data = json.loads(sse.data)

                # Handle message delta events
                if sse.event == MESSAGE_DELTA_EVENT:
                    delta = event_data.get("data", {}).get("delta", {})
                    content = delta.get("content", [])
                    for item in content:
                        if item.get("type") == "text":
                            text_value = item.get("text", {}).get("value", "")
                            chunks.append(text_value)
                            print(text_value, end="", flush=True)

                # Handle run completion
                elif sse.event == RUN_COMPLETED_EVENT:
                    break

                # Handle run failure
                elif sse.event == RUN_FAILED_EVENT:
                    logger.error("Run failed", event_data=event_data)
                    print("\n[Error: Run failed]")
                    break

            except json.JSONDecodeError as e:
                logger.error("JSON decode error in SSE", error=str(e), data=sse.data)
                continue

    return "".join(chunks)


async def process_streaming_response(response: httpx.Response) -> str:
    """Process a streaming response and return the final message."""
    chunks = []
    buffer = ""

    async for chunk in response.aiter_bytes(chunk_size=1024):
        if not chunk:
            continue

        try:
            # Try to decode the chunk
            buffer += chunk.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.warning("Partial UTF-8 sequence encountered", error=str(e))
            continue  # Wait for next chunk to complete the sequence

        # Process complete lines from the buffer
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue

            try:
                # Parse the JSON event
                data = json.loads(line)

                # Extract message content based on event type
                if "event" in data and data.get("event") == MESSAGE_DELTA_EVENT:
                    # Extract text delta from streaming events
                    if hasattr(data.get("data", {}), "delta") and hasattr(data["data"].delta, "content"):
                        for content_item in data["data"].delta.content:
                            if hasattr(content_item, "text") and hasattr(content_item.text, "value"):
                                chunks.append(content_item.text.value)
                                print(content_item.text.value, end="", flush=True)

                elif "responses" in data:
                    # Handle non-streaming response format
                    for response_text in data["responses"]:
                        chunks.append(response_text)

            except json.JSONDecodeError as e:
                logger.error("JSON decode error", error=str(e), line=line)
                continue

    # Process any remaining data in buffer
    if buffer.strip():
        try:
            data = json.loads(buffer)
            if "responses" in data:
                for response_text in data["responses"]:
                    chunks.append(response_text)
        except json.JSONDecodeError:
            pass

    return "".join(chunks)


async def start_conversation(base_url: str, thread_id: Optional[str] = None):
    """Run a sequential async chat session with the assistant."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            # Get or create a thread
            if not thread_id:
                response = await client.get("/start")
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
                        print(f"\nAssistant: {initial_message}")
                    print(f"{'=' * 60}\n")
                else:
                    logger.error("Failed to start conversation", status_code=response.status_code)
                    print(f"Failed to start conversation: {response.status_code}")
                    return
            else:
                print(f"\n{'=' * 60}")
                print(f"Continuing conversation with thread: {thread_id}")
                print(f"{'=' * 60}\n")

            print("Type 'exit' or 'quit' to end the conversation.")
            print("Type 'curl' to see the equivalent curl command.\n")

            while True:
                user_input = input("\nYou: ")
                if user_input.strip().lower() in {"exit", "quit"}:
                    break

                # Prepare the payload
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
                    # Send message with streaming
                    print("\nAssistant: ", end="", flush=True)

                    # Try SSE streaming first
                    try:
                        final_message = await process_sse_with_httpx_sse(client, "/chat", payload)
                        if not final_message:
                            print("[No response generated]")
                    except Exception as sse_error:
                        # Fallback to regular request if SSE fails
                        logger.debug("SSE failed, falling back to regular request", error=str(sse_error))

                        response = await client.post(
                            "/chat", json=payload, headers={"Accept": "application/json"}, timeout=httpx.Timeout(60.0)
                        )

                        if response.status_code == 200:
                            # Process regular JSON response
                            data = response.json()
                            responses = data.get("responses", [])
                            for resp in responses:
                                print(resp)
                        else:
                            print(f"\n[Error: {response.status_code}]")
                            logger.error("HTTP error", status_code=response.status_code, response=response.text)

                    print()  # New line after response

                except httpx.TimeoutException:
                    print("\n[Error: Request timed out]")
                    logger.error("Request timeout")
                except Exception as e:
                    print(f"\n[Error: {str(e)}]")
                    logger.error("Unexpected error", error=str(e))

        except KeyboardInterrupt:
            print("\n\nConversation interrupted.")


def main():
    """Main entry point for the async chat client."""
    parser = argparse.ArgumentParser(description="HTTP-based chat client for assistant-service")
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
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress debug logging output",
    )

    args = parser.parse_args()

    # Set logging level based on quiet flag
    if args.quiet:
        import logging

        logging.getLogger("http_client").setLevel(logging.ERROR)

    # Run the async conversation
    asyncio.run(start_conversation(args.base_url, args.thread_id))


if __name__ == "__main__":
    main()
