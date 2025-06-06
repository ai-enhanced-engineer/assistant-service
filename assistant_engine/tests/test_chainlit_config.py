from pathlib import Path

from chainlit.config import load_config


def test_custom_build_path(tmp_path, monkeypatch):
    """Ensure our Chainlit config sets the custom frontend build directory."""

    # Copy the repository config to a temporary Chainlit app root
    repo_root = Path(__file__).resolve().parents[2]
    tmp_app_root = tmp_path
    config = repo_root / ".chainlit" / "config.toml"
    (tmp_app_root / ".chainlit").mkdir()
    tmp_config = tmp_app_root / ".chainlit" / "config.toml"
    tmp_config.write_text(config.read_text())

    # Tell Chainlit to load config from this temporary root
    monkeypatch.setenv("CHAINLIT_APP_ROOT", str(tmp_app_root))

    loaded = load_config()
    assert loaded.ui.custom_build == "./frontend/dist"
