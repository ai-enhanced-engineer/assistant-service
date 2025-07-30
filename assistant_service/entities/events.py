"""OpenAI Assistant API event type constants."""

# Event types streamed via SSE
SSE_STREAM_EVENTS = {
    # Run lifecycle events
    "thread.run.created",
    "thread.run.queued",
    "thread.run.in_progress",
    "thread.run.requires_action",
    "thread.run.completed",
    "thread.run.failed",
    # Message events
    "thread.message.created",
    "thread.message.in_progress",
    "thread.message.delta",
    "thread.message.completed",
    # Step events
    "thread.run.step.created",
    "thread.run.step.in_progress",
    "thread.run.step.delta",
    "thread.run.step.completed",
}

# Common event types used in clients
MESSAGE_DELTA_EVENT = "thread.message.delta"
RUN_COMPLETED_EVENT = "thread.run.completed"
RUN_FAILED_EVENT = "thread.run.failed"
RUN_CREATED_EVENT = "thread.run.created"
RUN_STEP_COMPLETED_EVENT = "thread.run.step.completed"
RUN_REQUIRES_ACTION_EVENT = "thread.run.requires_action"

# Step detail types
STEP_TYPE_TOOL_CALLS = "tool_calls"
STEP_TYPE_MESSAGE_CREATION = "message_creation"

# Action types
ACTION_TYPE_SUBMIT_TOOL_OUTPUTS = "submit_tool_outputs"

# Custom events for SSE/WebSocket streaming
METADATA_EVENT = "metadata"
ERROR_EVENT = "error"
