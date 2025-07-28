import logging
import sys

import pytest
from pytest import LogCaptureFixture, MonkeyPatch
from structlog.stdlib import BoundLogger

from assistant_engine.structured_logging import (
    LoggingContext,
    clear_context_fields,
    configure_structlog,
    get_logger,
    get_logging_level,
    get_stream,
    set_context_fields,
)


@pytest.mark.unit
def test__configure_structlog__default_context_binding(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    logger = get_logger("test_logger")
    logger.info("Test message")

    log_output: str = caplog.records[0].message
    assert '"stream": "stdout"' in log_output
    assert '"level": "info"' in log_output


@pytest.mark.unit
def test__configure_structlog__custom_context_binding(caplog: LogCaptureFixture, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("STREAM", "stderr")
    monkeypatch.setenv("LOGGING_LEVEL", "DEBUG")

    custom_context = LoggingContext()
    configure_structlog(context=custom_context)
    logger = get_logger("test_logger")
    logger.debug("Test message")

    log_output: str = caplog.records[0].message
    assert '"stream": "stderr"' in log_output
    assert '"level": "debug"' in log_output


@pytest.mark.unit
def test__configure_structlog__keyvalue_format(caplog: LogCaptureFixture, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_FORMAT", "keyvalue")
    configure_structlog()
    logger = get_logger("kv_logger")
    logger.info("Format test")

    log_output: str = caplog.records[0].message
    assert "message='Format test'" in log_output
    assert '"message":' not in log_output


@pytest.mark.unit
def test__log_format__includes_all_expected_fields(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    logger = get_logger("test_logger")

    logger.info(
        "Formatted log test",
        thread="test-thread",
        trace_id="test-trace-id",
        trace_flags="test-flags",
        span_id="test-span-id",
    )
    log_output_with_all_fields: str = caplog.records[0].message

    assert '"message": "Formatted log test"' in log_output_with_all_fields
    assert '"thread": "test-thread"' in log_output_with_all_fields
    assert '"trace_id": "test-trace-id"' in log_output_with_all_fields
    assert '"trace_flags": "test-flags"' in log_output_with_all_fields
    assert '"span_id": "test-span-id"' in log_output_with_all_fields


@pytest.mark.unit
def test__clear_context_fields__removes_all_context(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    set_context_fields(LoggingContext(stream="stderr", logging_level="DEBUG"))
    clear_context_fields()

    logger = get_logger("test_logger")
    logger.info("Test after clearing")

    log_output: str = caplog.records[0].message
    assert "stream" not in log_output
    assert "logging_level" not in log_output


@pytest.mark.unit
def test__get_logger__uses_correct_logger_name(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    logger = get_logger("custom_logger")
    logger.info("Test logger name")

    log_output: str = caplog.records[0].message
    assert '"logger": "custom_logger"' in log_output


@pytest.mark.unit
def test__process_log_fields__conditionally_adds_thread_and_trace_fields(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    logger: BoundLogger = get_logger("test_logger")

    logger.info(
        "Health check with thread and trace",
        thread="test-thread",
        trace_id="test-trace-id",
        trace_flags="test-flags",
        span_id="test-span-id",
    )
    log_output_with_thread_and_trace: str = caplog.records[0].message

    assert '"thread": "test-thread"' in log_output_with_thread_and_trace
    assert '"trace_id": "test-trace-id"' in log_output_with_thread_and_trace
    assert '"trace_flags": "test-flags"' in log_output_with_thread_and_trace
    assert '"span_id": "test-span-id"' in log_output_with_thread_and_trace


@pytest.mark.unit
def test__process_log_fields__handles_extra_fields(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    logger: BoundLogger = get_logger("test_logger")

    logger.info(
        "Log with extra fields",
        custom_field_1="extra_value_1",
        custom_field_2="extra_value_2",
    )

    log_output: str = caplog.records[0].message

    assert '"extra": {' in log_output
    assert '"custom_field_1": "extra_value_1"' in log_output
    assert '"custom_field_2": "extra_value_2"' in log_output
    assert '"message": "Log with extra fields"' in log_output
    assert '"logger": "test_logger"' in log_output


@pytest.mark.unit
def test__logging_context__extracts_environment_variables(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("STREAM", "stderr")
    monkeypatch.setenv("LOGGING_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_FORMAT", "keyvalue")

    context = LoggingContext()

    assert context.stream == "stderr"
    assert context.logging_level == "DEBUG"
    assert context.log_format == "keyvalue"


@pytest.mark.unit
def test__logging_context__uses_defaults(monkeypatch: MonkeyPatch) -> None:
    # Clear the environment variables to prevent overrides
    monkeypatch.delenv("LOGGING_LEVEL", raising=False)
    monkeypatch.delenv("STREAM", raising=False)
    monkeypatch.delenv("LOG_FORMAT", raising=False)

    context = LoggingContext()

    assert context.stream == "stdout"
    assert context.logging_level == "INFO"
    assert context.log_format == "json"


@pytest.mark.unit
def test__get_logging_level__valid_levels() -> None:
    assert get_logging_level("DEBUG") == logging.DEBUG
    assert get_logging_level("INFO") == logging.INFO
    assert get_logging_level("WARNING") == logging.WARNING
    assert get_logging_level("ERROR") == logging.ERROR
    assert get_logging_level("CRITICAL") == logging.CRITICAL


@pytest.mark.unit
def test__get_logging_level__case_insensitive() -> None:
    assert get_logging_level("debug") == logging.DEBUG
    assert get_logging_level("info") == logging.INFO
    assert get_logging_level("warning") == logging.WARNING
    assert get_logging_level("error") == logging.ERROR
    assert get_logging_level("critical") == logging.CRITICAL


@pytest.mark.unit
def test__get_logging_level__invalid_level() -> None:
    with pytest.raises(ValueError, match="Unsupported logging level: INVALID"):
        get_logging_level("INVALID")


@pytest.mark.unit
def test__get_stream__valid_streams() -> None:
    assert get_stream("stdout") is sys.stdout
    assert get_stream("stderr") is sys.stderr
    assert get_stream("STDOUT") is sys.stdout
    assert get_stream("STDERR") is sys.stderr


@pytest.mark.unit
def test__get_stream__invalid_stream() -> None:
    with pytest.raises(ValueError, match="Unsupported stream: invalid-stream"):
        get_stream("invalid-stream")


@pytest.mark.unit
def test__configure_structlog__logs_correct_level_and_stream(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("LOGGING_LEVEL", "DEBUG")
    monkeypatch.setenv("STREAM", "stdout")

    custom_context = LoggingContext()
    configure_structlog(context=custom_context)

    python_logger = logging.getLogger("test_logger")
    assert python_logger.getEffectiveLevel() == logging.DEBUG


@pytest.mark.unit
def test__get_logger__uses_module_name_when_empty(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    logger = get_logger("")
    logger.info("Test empty name")

    log_output: str = caplog.records[0].message
    assert '"logger": "assistant_engine.structured_logging"' in log_output


@pytest.mark.unit
def test__get_logger__default_name_fallback(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    logger = get_logger()
    logger.info("Test default name")

    log_output: str = caplog.records[0].message
    assert '"logger": "assistant_engine.structured_logging"' in log_output


@pytest.mark.unit
def test__configure_structlog__context_default_fallback(caplog: LogCaptureFixture) -> None:
    configure_structlog(context=None)
    logger = get_logger("test_logger")
    logger.info("Test with None context")

    log_output: str = caplog.records[0].message
    assert '"stream": "stdout"' in log_output
    assert '"level": "info"' in log_output


@pytest.mark.unit
def test__set_context_fields__binds_stream_context(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    context = LoggingContext(stream="stderr", logging_level="DEBUG")
    set_context_fields(context)

    logger = get_logger("test_logger")
    logger.info("Test context binding")

    log_output: str = caplog.records[0].message
    assert '"stream": "stderr"' in log_output


@pytest.mark.unit
def test__logging_context__pydantic_validation() -> None:
    # Test that LoggingContext properly validates fields
    context = LoggingContext(stream="stdout", logging_level="INFO", log_format="json")

    assert context.stream == "stdout"
    assert context.logging_level == "INFO"
    assert context.log_format == "json"


@pytest.mark.unit
def test__process_log_fields__handles_missing_trace_fields(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    logger: BoundLogger = get_logger("test_logger")

    # Log without any trace fields
    logger.info("Simple log message")

    log_output: str = caplog.records[0].message
    assert '"message": "Simple log message"' in log_output
    assert '"logger": "test_logger"' in log_output
    assert '"context": "default"' in log_output
    # Trace fields should not be present
    assert '"thread":' not in log_output
    assert '"trace_id":' not in log_output
    assert '"trace_flags":' not in log_output
    assert '"span_id":' not in log_output


@pytest.mark.unit
def test__process_log_fields__mixed_extra_and_trace_fields(caplog: LogCaptureFixture) -> None:
    configure_structlog()
    logger: BoundLogger = get_logger("test_logger")

    logger.info(
        "Mixed fields test",
        thread="test-thread",
        custom_field="custom_value",
        trace_id="test-trace",
        another_custom="another_value",
    )

    log_output: str = caplog.records[0].message

    # Trace fields should be at top level
    assert '"thread": "test-thread"' in log_output
    assert '"trace_id": "test-trace"' in log_output

    # Custom fields should be in extra
    assert '"extra": {' in log_output
    assert '"custom_field": "custom_value"' in log_output
    assert '"another_custom": "another_value"' in log_output


@pytest.mark.unit
def test__configure_structlog__json_vs_keyvalue_renderer() -> None:
    # Test JSON renderer
    json_context = LoggingContext(log_format="json")
    configure_structlog(context=json_context)

    # Test KeyValue renderer
    kv_context = LoggingContext(log_format="keyvalue")
    configure_structlog(context=kv_context)

    # Both should configure without errors
    logger = get_logger("test_logger")
    # Check that logger has the expected method (indicating proper configuration)
    assert hasattr(logger, "info")
    assert hasattr(logger, "debug")
    assert hasattr(logger, "error")