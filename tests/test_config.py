import pytest

from prolific_mcp import config as config_module
from prolific_mcp.errors import ConfigurationError


def test_load_config_reads_token_and_default_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROLIFIC_TOKEN", "abc")
    monkeypatch.delenv("PROLIFIC_URL", raising=False)

    cfg = config_module.load_config()

    assert cfg.token == "abc"
    assert cfg.base_url == config_module.DEFAULT_PROLIFIC_URL


def test_load_config_strips_trailing_slash_from_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROLIFIC_TOKEN", "abc")
    monkeypatch.setenv("PROLIFIC_URL", "https://api.example.com/")

    cfg = config_module.load_config()

    assert cfg.base_url == "https://api.example.com"


def test_load_config_raises_when_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROLIFIC_TOKEN", raising=False)

    with pytest.raises(ConfigurationError):
        config_module.load_config()


def test_masked_token_hides_middle() -> None:
    cfg = config_module.Config(token="abcdefghijklmnop", base_url="https://x")
    assert cfg.masked_token() == "abcd…mnop"


def test_masked_token_for_short_token() -> None:
    cfg = config_module.Config(token="short", base_url="https://x")
    assert cfg.masked_token() == "****"
