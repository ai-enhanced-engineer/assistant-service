import pytest

from botbrew_commons.data_models import BaseConfig


def test__env_variables_are_loaded(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setenv("PROJECT_ID", "my-project")
        mp.setenv("CLIENT_ID", "my-client")
        base_config = BaseConfig()
        assert base_config.project_id == "my-project"
        assert base_config.client_id == "my-client"


def test__missing_attribute_raises(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setenv("PROJECT_ID", "my-project")
        with pytest.raises(ValueError):
            BaseConfig()
