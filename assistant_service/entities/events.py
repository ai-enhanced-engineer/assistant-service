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
