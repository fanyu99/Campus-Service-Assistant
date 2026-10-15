import pytest
from pydantic import ValidationError

from app.core.config import get_settings


def test_defaults_without_env(monkeypatch: pytest.MonkeyPatch):
    for name in ("APP_PORT", "APP_ENV", "DATABASE_URL", "AGENTARTS_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    settings = get_settings()
    assert settings.app_port == 8000
    assert settings.app_env == "local"
    assert settings.database_url == "mysql+pymysql://app:app@db:3306/campus"
    assert settings.agentarts_api_key == ""


def test_env_overrides_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("APP_ENV", "production")
    settings = get_settings()
    assert settings.app_port == 9000
    assert settings.app_env == "production"


def test_invalid_app_env_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "staging")
    with pytest.raises(ValidationError):
        get_settings()


def test_invalid_port_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_PORT", "not-a-number")
    with pytest.raises(ValidationError):
        get_settings()


def test_get_settings_is_singleton():
    first = get_settings()
    second = get_settings()
    assert first is second