from typing import Any

from assistant_service.models import EngineAssistantConfig
from assistant_service.repositories import LocalConfigRepository, LocalSecretRepository


def test_local_config_repository_roundtrip() -> None:
    repo = LocalConfigRepository()
    config = EngineAssistantConfig(
        assistant_id="a1",
        assistant_name="test",
        initial_message="hi",
    )
    repo.write_config(config)
    assert repo.read_config() is config


def test_local_secret_repository_writes_and_reads(capsys: Any) -> None:
    repo = LocalSecretRepository(client_id="cid", project_id="pid")
    repo.write_secret("sfx")
    secret = repo.access_secret("foo")
    # access_secret should print the suffix
    captured = capsys.readouterr()
    assert "foo" in captured.out
    assert secret == "pid/cid-sfx"
