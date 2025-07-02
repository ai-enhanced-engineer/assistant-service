"""Tests for consistent logging configuration and levels."""

import logging
from unittest.mock import patch

import pytest

from assistant_engine.logging_config import (
    ComponentLogger,
    ComponentLogLevels,
    LogLevel,
    StructuredLoggingConfig,
    configure_application_logging,
    get_component_logger,
)


def test_log_level_enum():
    """Test LogLevel enum values."""
    assert LogLevel.CRITICAL == "CRITICAL"
    assert LogLevel.ERROR == "ERROR"
    assert LogLevel.WARNING == "WARNING"
    assert LogLevel.INFO == "INFO"
    assert LogLevel.DEBUG == "DEBUG"


def test_component_log_levels():
    """Test ComponentLogLevels has appropriate levels for different operations."""
    # API operations should be at INFO level
    assert ComponentLogLevels.API_REQUESTS == LogLevel.INFO
    assert ComponentLogLevels.API_ERRORS == LogLevel.ERROR
    
    # OpenAI operations should have DEBUG for requests, ERROR for failures
    assert ComponentLogLevels.OPENAI_REQUESTS == LogLevel.DEBUG
    assert ComponentLogLevels.OPENAI_ERRORS == LogLevel.ERROR
    assert ComponentLogLevels.OPENAI_RETRIES == LogLevel.WARNING
    
    # Tool execution should be INFO for success, ERROR for failures
    assert ComponentLogLevels.TOOL_EXECUTION_SUCCESS == LogLevel.INFO
    assert ComponentLogLevels.TOOL_EXECUTION_ERROR == LogLevel.ERROR
    assert ComponentLogLevels.TOOL_VALIDATION_ERROR == LogLevel.WARNING
    
    # Critical system events should be appropriately leveled
    assert ComponentLogLevels.SYSTEM_STARTUP == LogLevel.INFO
    assert ComponentLogLevels.CRITICAL_ERRORS == LogLevel.CRITICAL


def test_structured_logging_config_default():
    """Test StructuredLoggingConfig with default values."""
    config = StructuredLoggingConfig()
    assert config.log_level == LogLevel.INFO.value
    assert config.get_log_level() == logging.INFO
    assert "%(asctime)s: %(levelname)s: %(name)s: %(message)s" in config.log_format


def test_structured_logging_config_custom_level():
    """Test StructuredLoggingConfig with custom log level."""
    config = StructuredLoggingConfig("DEBUG")
    assert config.log_level == "DEBUG"
    assert config.get_log_level() == logging.DEBUG


def test_structured_logging_config_invalid_level():
    """Test StructuredLoggingConfig with invalid level defaults to INFO."""
    config = StructuredLoggingConfig("INVALID")
    assert config.get_log_level() == logging.INFO


def test_component_logger_initialization():
    """Test ComponentLogger initialization."""
    logger = ComponentLogger("TEST")
    assert logger.name == "TEST"
    assert logger.logger.name == "TEST"


def test_component_logger_context_logging():
    """Test ComponentLogger logs with context."""
    logger = ComponentLogger("TEST")
    
    with patch.object(logger.logger, 'log') as mock_log:
        logger.info("Test message", thread_id="123", run_id="456")
        
        # Verify log was called with context
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        level, message = args
        assert level == logging.INFO
        assert "Test message" in message
        assert "thread_id=123" in message
        assert "run_id=456" in message


def test_component_logger_no_context():
    """Test ComponentLogger works without context."""
    logger = ComponentLogger("TEST")
    
    with patch.object(logger.logger, 'log') as mock_log:
        logger.warning("Simple warning")
        
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        level, message = args
        assert level == logging.WARNING
        assert message == "Simple warning"


def test_component_logger_filters_none_values():
    """Test ComponentLogger filters out None values from context."""
    logger = ComponentLogger("TEST")
    
    with patch.object(logger.logger, 'log') as mock_log:
        logger.error("Error occurred", thread_id="123", run_id=None, status="failed")
        
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        level, message = args
        assert level == logging.ERROR
        assert "thread_id=123" in message
        assert "status=failed" in message
        assert "run_id=None" not in message


def test_get_component_logger():
    """Test get_component_logger factory function."""
    logger = get_component_logger("FACTORY_TEST")
    assert isinstance(logger, ComponentLogger)
    assert logger.name == "FACTORY_TEST"


def test_configure_application_logging():
    """Test application logging configuration."""
    with patch('assistant_engine.logging_config.logging.getLogger') as mock_get_logger:
        mock_root_logger = mock_get_logger.return_value
        mock_root_logger.handlers = []
        
        configure_application_logging("DEBUG")
        
        # Verify root logger was configured (may be called multiple times due to external loggers)
        assert mock_root_logger.setLevel.called
        mock_root_logger.addHandler.assert_called_once()


def test_configure_external_loggers():
    """Test external logger configuration."""
    from assistant_engine.logging_config import configure_external_loggers
    
    with patch('assistant_engine.logging_config.logging.getLogger') as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        
        configure_external_loggers(logging.INFO)
        
        # Verify external loggers were configured
        assert mock_get_logger.call_count >= 6  # At least 6 external loggers
        mock_logger.setLevel.assert_called()


@pytest.mark.parametrize("log_level,expected_int", [
    ("CRITICAL", logging.CRITICAL),
    ("ERROR", logging.ERROR), 
    ("WARNING", logging.WARNING),
    ("INFO", logging.INFO),
    ("DEBUG", logging.DEBUG),
    ("invalid", logging.INFO),  # Should default to INFO
])
def test_log_level_conversion(log_level, expected_int):
    """Test log level string to int conversion."""
    config = StructuredLoggingConfig(log_level)
    assert config.get_log_level() == expected_int


def test_openai_filter():
    """Test OpenAI filter removes noisy logs."""
    from assistant_engine.logging_config import OpenAIFilter
    
    filter_obj = OpenAIFilter()
    
    # Mock log record for HTTP request (should be filtered)
    class MockRecord:
        def getMessage(self):
            return "HTTP Request: GET https://api.openai.com"
    
    assert filter_obj.filter(MockRecord()) is False
    
    # Mock log record for normal message (should pass)
    class MockRecord2:
        def getMessage(self):
            return "Function executed successfully"
    
    assert filter_obj.filter(MockRecord2()) is True


def test_backward_compatibility():
    """Test backward compatible get_logger function."""
    from assistant_engine.logging_config import get_logger
    
    logger = get_logger("COMPAT_TEST")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "COMPAT_TEST"


def test_component_logger_all_levels():
    """Test ComponentLogger supports all log levels."""
    logger = ComponentLogger("ALL_LEVELS")
    
    with patch.object(logger.logger, 'log') as mock_log:
        logger.critical("Critical message")
        logger.error("Error message")
        logger.warning("Warning message")
        logger.info("Info message")
        logger.debug("Debug message")
        
        assert mock_log.call_count == 5
        
        # Verify correct levels were used
        calls = mock_log.call_args_list
        levels = [call[0][0] for call in calls]
        expected_levels = [
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            logging.DEBUG
        ]
        assert levels == expected_levels