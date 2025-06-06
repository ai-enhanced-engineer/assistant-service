from assistant_factory.client_spec.leogv.assistants import ClientAssistantConfig
from assistant_factory.main import persist_config
from botbrew_commons.data_models import EngineAssistantConfig


def test__persist_config_independent(mocker):
    assistant_config = ClientAssistantConfig(
        client_id="test-client",
        instructions="Some instructions",
        model="test-model",
        functions=[],
        retrieval=False,
        code_interpreter=False,
        file_paths=[],
    )
    assistant_id = "asst_test"

    instances = {}

    class DummyRepo:
        def __init__(self, client_id, project_id, bucket_name):
            self.client_id = client_id
            self.project_id = project_id
            self.bucket_name = bucket_name
            instances["repo"] = self

        def write_config(self, config):
            self.written_config = config

    mocker.patch("assistant_factory.main.GCPConfigRepository", DummyRepo)

    persist_config(assistant_config, assistant_id)

    repo = instances["repo"]
    assert repo.client_id == assistant_config.client_id
    assert isinstance(repo.written_config, EngineAssistantConfig)
    assert repo.written_config.assistant_id == assistant_id
