from mj_prompt_studio.app.app_context import AppContext
from mj_prompt_studio.config import LLMFeatureProfile, LLMModelConfig, RuntimeSettings


def test_app_context_persists_feature_level_llm_profiles(tmp_path) -> None:
    settings = RuntimeSettings(
        data_dir=tmp_path,
        llm_mode="mock",
        response_storage="normal",
        model_config=LLMModelConfig(),
    )
    context = AppContext(settings)

    context.set_llm_feature_profiles(
        {
            "PromptDoctorAgent": LLMFeatureProfile(
                model="gpt-5.4-mini",
                reasoning_effort="high",
                vocabulary_amount="rich",
            )
        }
    )
    context.shutdown()

    reloaded = AppContext(settings)
    profile = reloaded.settings.feature_profile_for("PromptDoctorAgent")

    assert profile.model == "gpt-5.4-mini"
    assert profile.reasoning_effort == "high"
    assert profile.vocabulary_amount == "rich"
    reloaded.shutdown()
