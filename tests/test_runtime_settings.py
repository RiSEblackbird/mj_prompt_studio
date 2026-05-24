from mj_prompt_studio.config import (
    LLMFeatureProfile,
    default_feature_profiles,
    load_runtime_settings,
    normalize_feature_profiles,
    read_openai_api_key_from_environment,
)
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


def test_feature_profiles_default_to_requested_model_and_medium_reasoning() -> None:
    profiles = default_feature_profiles()

    assert all(profile.model == "gpt-5.5" for profile in profiles.values())
    assert all(profile.reasoning_effort == "medium" for profile in profiles.values())
    assert all(profile.vocabulary_amount == "standard" for profile in profiles.values())


def test_feature_profile_normalization_rejects_unknown_choices() -> None:
    profiles = normalize_feature_profiles(
        {
            "VocabularyAgent": {
                "model": "unknown",
                "reasoning_effort": "extreme",
                "vocabulary_amount": "verbose",
            },
            "PromptDoctorAgent": LLMFeatureProfile(
                model="gpt-5.4-mini",
                reasoning_effort="high",
                vocabulary_amount="rich",
            ),
            "PromptCompilerAgent": {
                "model": "gpt-5.4-nano",
                "reasoning_effort": "none",
                "vocabulary_amount": "compact",
            },
        }
    )

    assert profiles["VocabularyAgent"] == LLMFeatureProfile()
    assert profiles["PromptDoctorAgent"].model == "gpt-5.4-mini"
    assert profiles["PromptDoctorAgent"].reasoning_effort == "high"
    assert profiles["PromptDoctorAgent"].vocabulary_amount == "rich"
    assert profiles["PromptCompilerAgent"].reasoning_effort == "none"
