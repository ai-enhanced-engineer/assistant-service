"""Enhanced logging configuration with consistent levels and structured output."""

import logging
import os
from enum import Enum
from typing import Optional


class LogLevel(str, Enum):
    """Standardized log levels for the application."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class ComponentLogLevels:
    """Consistent log levels for different components."""
    
    # Core API operations
    API_REQUESTS = LogLevel.INFO
    API_ERRORS = LogLevel.ERROR
    API_DEBUG = LogLevel.DEBUG
    
    # OpenAI interactions
    OPENAI_REQUESTS = LogLevel.DEBUG
    OPENAI_RESPONSES = LogLevel.DEBUG
    OPENAI_ERRORS = LogLevel.ERROR
    OPENAI_RETRIES = LogLevel.WARNING
    
    # Tool execution
    TOOL_EXECUTION_START = LogLevel.DEBUG
    TOOL_EXECUTION_SUCCESS = LogLevel.INFO
    TOOL_EXECUTION_ERROR = LogLevel.ERROR
    TOOL_VALIDATION_ERROR = LogLevel.WARNING
    
    # Message processing
    MESSAGE_PROCESSING = LogLevel.DEBUG
    MESSAGE_RETRIEVAL_SUCCESS = LogLevel.DEBUG
    MESSAGE_RETRIEVAL_ERROR = LogLevel.ERROR
    
    # Run lifecycle
    RUN_CREATION = LogLevel.INFO
    RUN_COMPLETION = LogLevel.INFO
    RUN_FAILURE = LogLevel.ERROR
    RUN_CANCELLATION = LogLevel.WARNING
    
    # WebSocket operations
    WEBSOCKET_CONNECTION = LogLevel.INFO
    WEBSOCKET_ERROR = LogLevel.ERROR
    WEBSOCKET_DEBUG = LogLevel.DEBUG
    
    # Critical system events
    SYSTEM_STARTUP = LogLevel.INFO
    SYSTEM_SHUTDOWN = LogLevel.INFO
    CONFIGURATION_LOAD = LogLevel.INFO
    CRITICAL_ERRORS = LogLevel.CRITICAL


class StructuredLoggingConfig:
    """Configuration for structured logging with consistent formatting."""
    
    def __init__(self, log_level: Optional[str] = None):
        self.log_level = log_level or os.getenv("LOG_LEVEL", LogLevel.INFO.value)
        self.log_format = os.getenv(
            "LOG_FORMAT",
            "%(asctime)s: %(levelname)s: %(name)s: %(message)s"
        )
        self.date_format = "%m/%d/%Y %I:%M:%S %p"
        
    def get_log_level(self) -> int:
        """Convert string log level to logging constant."""
        level_mapping = {
            LogLevel.CRITICAL.value: logging.CRITICAL,
            LogLevel.ERROR.value: logging.ERROR,
            LogLevel.WARNING.value: logging.WARNING,
            LogLevel.INFO.value: logging.INFO,
            LogLevel.DEBUG.value: logging.DEBUG,
        }
        return level_mapping.get(self.log_level.upper(), logging.INFO)


class ComponentLogger:
    """Enhanced logger with component-specific configurations."""
    
    def __init__(self, name: str, config: Optional[StructuredLoggingConfig] = None):
        self.name = name
        self.config = config or StructuredLoggingConfig()
        self.logger = logging.getLogger(name)
        self._configure_logger()
    
    def _configure_logger(self):
        """Configure logger with appropriate handlers and formatters."""
        # Don't add handlers if logger already has them (avoid duplicates)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt=self.config.log_format,
                datefmt=self.config.date_format
            )
            handler.setFormatter(formatter)
            handler.addFilter(OpenAIFilter())
            self.logger.addHandler(handler)
        
        # Set level based on environment or default
        self.logger.setLevel(self.config.get_log_level())
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message with context."""
        if args:
            # Standard logger format with args
            self.logger.critical(message, *args)
        else:
            self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message with context."""
        if args:
            # Standard logger format with args
            self.logger.error(message, *args)
        else:
            self._log_with_context(logging.ERROR, message, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message with context."""
        if args:
            # Standard logger format with args
            self.logger.warning(message, *args)
        else:
            self._log_with_context(logging.WARNING, message, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message with context."""
        if args:
            # Standard logger format with args
            self.logger.info(message, *args)
        else:
            self._log_with_context(logging.INFO, message, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message with context."""
        if args:
            # Standard logger format with args
            self.logger.debug(message, *args)
        else:
            self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with additional context if provided."""
        if kwargs:
            context_parts = [f"{k}={v}" for k, v in kwargs.items() if v is not None]
            if context_parts:
                context_str = " | ".join(context_parts)
                message = f"{message} | {context_str}"
        
        self.logger.log(level, message)


class OpenAIFilter(logging.Filter):
    """Filter to remove noisy OpenAI HTTP request logs."""
    
    def filter(self, record):
        message = record.getMessage()
        # Filter out noisy HTTP request logs
        noisy_patterns = [
            "HTTP Request:",
            "HTTP Response:",
            "Starting new HTTPS connection",
            "urllib3.connectionpool"
        ]
        return not any(pattern in message for pattern in noisy_patterns)


def get_component_logger(component_name: str) -> ComponentLogger:
    """Get a properly configured logger for a component."""
    return ComponentLogger(component_name)


def configure_application_logging(log_level: Optional[str] = None):
    """Configure application-wide logging settings."""
    config = StructuredLoggingConfig(log_level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.get_log_level())
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our configured handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt=config.log_format,
        datefmt=config.date_format
    )
    handler.setFormatter(formatter)
    handler.addFilter(OpenAIFilter())
    handler.setLevel(config.get_log_level())
    
    root_logger.addHandler(handler)
    
    # Configure specific loggers for external libraries
    configure_external_loggers(config.get_log_level())


def configure_external_loggers(log_level: int):
    """Configure logging levels for external libraries."""
    external_loggers = {
        "httpx": logging.WARNING,
        "urllib3": logging.WARNING,
        "openai": logging.WARNING,
        "asyncio": logging.WARNING,
        "fastapi": logging.INFO,
        "uvicorn": logging.INFO,
    }
    
    for logger_name, level in external_loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(max(level, log_level))  # Use higher of default or configured level


# Maintain backward compatibility
def get_logger(name: str) -> logging.Logger:
    """Backward compatible logger getter."""
    return ComponentLogger(name).logger