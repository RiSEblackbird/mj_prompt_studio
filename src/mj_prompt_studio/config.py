from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

APP_NAME = "MJ Prompt Studio"
ENV_PREFIX = "MJPS_"
OPENAI_API_KEY_ENV_NAMES = ("OPENAI_API_KEY", "OPENAI_KEY", f"{ENV_PREFIX}OPENAI_API_KEY")
LLM_FEATURE_PROFILES_SETTING_KEY = "llm_feature_profiles"

AVAILABLE_LLM_MODELS = ("gpt-5.5", "gpt-5.4-mini", "gpt-5.4-nano")
DEFAULT_LLM_MODEL = "gpt-5.5"
REASONING_EFFORTS = ("none", "low", "medium", "high", "xhigh")
DEFAULT_REASONING_EFFORT = "medium"
VOCABULARY_AMOUNTS = ("compact", "standard", "rich")
DEFAULT_VOCABULARY_AMOUNT = "standard"
VOCABULARY_AMOUNT_LABELS = {
    "compact": "少なめ",
    "standard": "標準",
    "rich": "多め",
}
LLM_FEATURE_IDS = (
    "IntentIntakeAgent",
    "VocabularyAgent",
    "PromptCompilerAgent",
    "PromptDoctorAgent",
    "ParameterAdvisorAgent",
    "ReferenceAnalyzerAgent",
    "MatrixPlannerAgent",
    "ResultReviewAgent",
    "FinalAuditorAgent",
)
LLM_FEATURE_DISPLAY_NAMES = {
    "IntentIntakeAgent": "AI Brief",
    "VocabularyAgent": "語彙補助",
    "PromptCompilerAgent": "Prompt Compiler",
    "PromptDoctorAgent": "Prompt Doctor",
    "ParameterAdvisorAgent": "Parameter Advisor",
    "ReferenceAnalyzerAgent": "Reference Analysis",
    "MatrixPlannerAgent": "Matrix Lab",
    "ResultReviewAgent": "Result Review",
    "FinalAuditorAgent": "Final Audit",
}


@dataclass(frozen=True)
class LLMModelConfig:
    default_model: str = DEFAULT_LLM_MODEL
    inline_model: str = DEFAULT_LLM_MODEL
    vision_model: str = DEFAULT_LLM_MODEL
    deep_review_model: str = DEFAULT_LLM_MODEL


@dataclass(frozen=True)
class LLMFeatureProfile:
    model: str = DEFAULT_LLM_MODEL
    reasoning_effort: str = DEFAULT_REASONING_EFFORT
    vocabulary_amount: str = DEFAULT_VOCABULARY_AMOUNT

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LLMFeatureProfile:
        model = _validated_choice(
            str(data.get("model", DEFAULT_LLM_MODEL)),
            AVAILABLE_LLM_MODELS,
            DEFAULT_LLM_MODEL,
        )
        reasoning_effort = _validated_choice(
            str(data.get("reasoning_effort", DEFAULT_REASONING_EFFORT)),
            REASONING_EFFORTS,
            DEFAULT_REASONING_EFFORT,
        )
        vocabulary_amount = _validated_choice(
            str(data.get("vocabulary_amount", DEFAULT_VOCABULARY_AMOUNT)),
            VOCABULARY_AMOUNTS,
            DEFAULT_VOCABULARY_AMOUNT,
        )
        return cls(
            model=model,
            reasoning_effort=reasoning_effort,
            vocabulary_amount=vocabulary_amount,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "vocabulary_amount": self.vocabulary_amount,
        }


@dataclass(frozen=True)
class RuntimeSettings:
    data_dir: Path
    llm_mode: str
    response_storage: str
    model_config: LLMModelConfig
    feature_profiles: dict[str, LLMFeatureProfile] = field(
        default_factory=lambda: default_feature_profiles()
    )
    max_parallel_jobs: int = 3
    timeout_seconds: int = 120
    retry_count: int = 2

    @property
    def privacy_mode(self) -> bool:
        return self.response_storage.lower() == "privacy"

    def feature_profile_for(self, agent_name: str) -> LLMFeatureProfile:
        return self.feature_profiles.get(agent_name, LLMFeatureProfile())

    def with_feature_profiles(
        self, profiles: Mapping[str, LLMFeatureProfile | Mapping[str, Any]]
    ) -> RuntimeSettings:
        return replace(self, feature_profiles=normalize_feature_profiles(profiles))


def default_data_dir() -> Path:
    override = os.environ.get(f"{ENV_PREFIX}DATA_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / "Library" / "Application Support" / "MJ Prompt Studio"


def load_runtime_settings() -> RuntimeSettings:
    configured_llm_mode = os.environ.get(f"{ENV_PREFIX}LLM_MODE")
    return RuntimeSettings(
        data_dir=default_data_dir(),
        llm_mode=(configured_llm_mode or _default_llm_mode()).lower(),
        response_storage=os.environ.get(f"{ENV_PREFIX}RESPONSE_STORAGE", "normal").lower(),
        model_config=LLMModelConfig(
            default_model=os.environ.get(f"{ENV_PREFIX}MODEL_DEFAULT", "gpt-5.5"),
            inline_model=os.environ.get(f"{ENV_PREFIX}MODEL_INLINE", "gpt-5.5"),
            vision_model=os.environ.get(f"{ENV_PREFIX}MODEL_VISION", "gpt-5.5"),
            deep_review_model=os.environ.get(f"{ENV_PREFIX}MODEL_DEEP_REVIEW", "gpt-5.5"),
        ),
        max_parallel_jobs=int(os.environ.get(f"{ENV_PREFIX}MAX_PARALLEL_JOBS", "3")),
        timeout_seconds=int(os.environ.get(f"{ENV_PREFIX}TIMEOUT_SECONDS", "120")),
        retry_count=int(os.environ.get(f"{ENV_PREFIX}RETRY_COUNT", "2")),
    )


def read_openai_api_key_from_environment() -> str | None:
    for name in OPENAI_API_KEY_ENV_NAMES:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _default_llm_mode() -> str:
    return "real" if read_openai_api_key_from_environment() else "mock"


def default_feature_profiles() -> dict[str, LLMFeatureProfile]:
    return {feature_id: LLMFeatureProfile() for feature_id in LLM_FEATURE_IDS}


def normalize_feature_profiles(
    profiles: Mapping[str, LLMFeatureProfile | Mapping[str, Any]]
) -> dict[str, LLMFeatureProfile]:
    normalized = default_feature_profiles()
    for feature_id, profile in profiles.items():
        if feature_id not in normalized:
            continue
        if isinstance(profile, LLMFeatureProfile):
            normalized[feature_id] = LLMFeatureProfile.from_dict(profile.to_dict())
        elif isinstance(profile, Mapping):
            normalized[feature_id] = LLMFeatureProfile.from_dict(profile)
    return normalized


def serialize_feature_profiles(
    profiles: Mapping[str, LLMFeatureProfile | Mapping[str, Any]]
) -> dict[str, dict[str, str]]:
    normalized = normalize_feature_profiles(profiles)
    return {feature_id: profile.to_dict() for feature_id, profile in normalized.items()}


def _validated_choice(value: str, choices: tuple[str, ...], fallback: str) -> str:
    return value if value in choices else fallback
