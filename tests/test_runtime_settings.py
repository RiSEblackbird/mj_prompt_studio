from mj_prompt_studio.config import load_runtime_settings, read_openai_api_key_from_environment
from mj_prompt_studio.infra.secret_store import SecretStore


def test_load_runtime_settings_uses_real_mode_when_terminal_api_key_exists(
    monkeypatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("MJPS_LLM_MODE", raising=False)

    settings = load_runtime_settings()

    assert settings.llm_mode == "real"
    assert read_openai_api_key_from_environment() == "test-key"


def test_explicit_mock_mode_overrides_terminal_api_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("MJPS_LLM_MODE", "mock")

    settings = load_runtime_settings()

    assert settings.llm_mode == "mock"


def test_secret_store_reads_windows_or_shell_alias(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_KEY", "alias-key")

    assert SecretStore().read_openai_api_key() == "alias-key"
