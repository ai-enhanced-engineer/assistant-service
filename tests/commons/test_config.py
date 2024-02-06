import pytest

from botbrew_commons.data_models import BaseConfig


def test__env_variables_are_loaded(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setenv("PROJECT_ID", "test-project")
        mp.setenv("CLIENT_ID", "test-client")
        mp.setenv("BUCKET_ID", "test-bucket")
        base_config = BaseConfig()
        assert base_config.project_id == "test-project"
        assert base_config.client_id == "test-client"
        assert base_config.bucket_id == "test-bucket"


def test__missing_attribute_raises(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setenv("PROJECT_ID", "test-project")
        with pytest.raises(ValueError):
            BaseConfig()
