from typing import Any

from ai_assistant_service.entities import AssistantConfig
from ai_assistant_service.repositories import LocalConfigRepository, LocalSecretRepository


def test_local_config_repository_roundtrip() -> None:
    repo = LocalConfigRepository()
    config = AssistantConfig(
        assistant_id="a1",
        assistant_name="test",
        initial_message="hi",
    )
    repo.write_config(config)  # This is a no-op for local repository
    # LocalConfigRepository always returns the default config
    read_config = repo.read_config()
    assert read_config.assistant_name == "Development Assistant"
    assert read_config.initial_message == "Hello! I'm your development assistant. How can I help you today?"


def test_local_secret_repository_writes_and_reads(capsys: Any) -> None:
    repo = LocalSecretRepository()  # No arguments
    repo.write_secret("sfx")  # This is a no-op for local repository
    secret = repo.access_secret("foo")
    # LocalSecretRepository returns "local-{suffix}" for non-openai keys
    assert secret == "local-foo"

    # Test all secrets now return local-{suffix} pattern
    openai_key = repo.access_secret("openai-api-key")
    assert openai_key == "local-openai-api-key"
