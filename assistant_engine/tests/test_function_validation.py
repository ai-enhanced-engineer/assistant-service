import importlib
import types


def load_main(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", "p")
    monkeypatch.setenv("BUCKET_ID", "b")
    monkeypatch.setenv("CLIENT_ID", "c")
    monkeypatch.setenv("ASSISTANT_ID", "a")

    from botbrew_commons import repositories as repos

    class DummySecretRepo:
        def __init__(self, project_id: str, client_id: str):
            pass

        def write_secret(self, _):
            pass

        def access_secret(self, _):
            return "sk"

    class DummyConfigRepo:
        def __init__(self, client_id: str, project_id: str, bucket_name: str):
            pass

        def write_config(self, _config):
            pass

        def read_config(self):
            return types.SimpleNamespace(
                assistant_id="a",
                assistant_name="name",
                initial_message="hi",
                openai_apikey="sk",
            )

    monkeypatch.setattr(repos, "GCPSecretRepository", DummySecretRepo)
    monkeypatch.setattr(repos, "GCPConfigRepository", DummyConfigRepo)

    return importlib.reload(importlib.import_module("assistant_engine.main"))


def test_unknown_function_is_skipped(monkeypatch, mocker):
    main = load_main(monkeypatch)
    tool_call = types.SimpleNamespace(function=types.SimpleNamespace(name="missing", arguments="{}"))
    log_error = mocker.patch.object(main.logger, "error")
    result = main.handle_function_tool_call(tool_call)
    assert result is None
    log_error.assert_called_once()


def test_missing_parameters_skipped(monkeypatch, mocker):
    main = load_main(monkeypatch)

    def sample(a, b):
        return a + b

    monkeypatch.setattr(main, "TOOL_MAP", {"sample": sample})
    tool_call = types.SimpleNamespace(function=types.SimpleNamespace(name="sample", arguments='{"a": 1}'))
    log_error = mocker.patch.object(main.logger, "error")
    result = main.handle_function_tool_call(tool_call)
    assert result is None
    log_error.assert_called_once()


def test_valid_function_invoked(monkeypatch):
    main = load_main(monkeypatch)

    def sample(a, b):
        return a + b

    monkeypatch.setattr(main, "TOOL_MAP", {"sample": sample})
    tool_call = types.SimpleNamespace(function=types.SimpleNamespace(name="sample", arguments='{"a": 1, "b": 2}'))
    result = main.handle_function_tool_call(tool_call)
    assert result == 3
