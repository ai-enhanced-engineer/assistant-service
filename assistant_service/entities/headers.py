"""HTTP header constants for the assistant service."""

# Headers for Server-Sent Events (SSE) responses
# These headers ensure proper streaming behavior across different proxy servers and browsers
SSE_RESPONSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",  # Prevent caching of event stream
    "X-Accel-Buffering": "no",  # Disable nginx buffering for real-time streaming
    "Connection": "keep-alive",  # Maintain persistent connection for streaming
    "X-Content-Type-Options": "nosniff",  # Security: Prevent MIME type sniffing
}

# Header keys as constants for consistent usage
HEADER_CORRELATION_ID = "X-Correlation-ID"
HEADER_CACHE_CONTROL = "Cache-Control"
HEADER_CONNECTION = "Connection"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_ACCEPT = "Accept"

# Common header values
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_EVENT_STREAM = "text/event-stream"
