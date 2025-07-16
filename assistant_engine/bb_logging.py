import logging
from typing import Any, Optional

from .correlation import get_correlation_id

LEVEL = "INFO"


class CorrelationFormatter(logging.Formatter):
    """Formatter that includes correlation ID in log messages."""
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
        
    def format(self, record: logging.LogRecord) -> str:
        # Add correlation ID to the record
        correlation_id = get_correlation_id()
        if correlation_id:
            record.correlation_id = correlation_id[:8]  # Use first 8 characters for brevity
        else:
            record.correlation_id = "--------"
        return super().format(record)


FORMATTER = CorrelationFormatter(
    fmt="%(asctime)s: %(levelname)s: [%(correlation_id)s] %(name)s: %(message)s", 
    datefmt="%m/%d/%Y %I:%M:%S %p"
)


class OpenAIFilter(logging.Filter):
    def filter(self, record):
        # print(f"Filtering record: {record.msg}")
        return not record.getMessage().startswith("HTTP Request:")


def configure_root_logger():
    logger = logging.getLogger()
    handler = logger.handlers[0]
    handler.setFormatter(FORMATTER)
    handler.addFilter(OpenAIFilter())
    handler.setLevel(LEVEL)


def get_logger(name):
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: int, msg: str, 
                    thread_id: Optional[str] = None, 
                    run_id: Optional[str] = None, 
                    **kwargs: Any) -> None:
    """Log a message with additional context information."""
    context_parts = []
    
    if thread_id:
        context_parts.append(f"thread_id={thread_id}")
    if run_id:
        context_parts.append(f"run_id={run_id}")
    
    # Add any additional context from kwargs
    for key, value in kwargs.items():
        if value is not None:
            context_parts.append(f"{key}={value}")
    
    if context_parts:
        context_str = " | ".join(context_parts)
        msg = f"{msg} | {context_str}"
    
    logger.log(level, msg)


configure_root_logger()
