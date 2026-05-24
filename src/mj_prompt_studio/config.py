from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "MJ Prompt Studio"
ENV_PREFIX = "MJPS_"


@dataclass(frozen=True)
class LLMModelConfig:
    default_model: str = "gpt-5.5"
    inline_model: str = "gpt-5.5"
    vision_model: str = "gpt-5.5"
    deep_review_model: str = "gpt-5.5"


@dataclass(frozen=True)
class RuntimeSettings:
    data_dir: Path
    llm_mode: str
    response_storage: str
    model_config: LLMModelConfig
    max_parallel_jobs: int = 3
    timeout_seconds: int = 120
    retry_count: int = 2

    @property
    def privacy_mode(self) -> bool:
        return self.response_storage.lower() == "privacy"


def default_data_dir() -> Path:
    override = os.environ.get(f"{ENV_PREFIX}DATA_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / "Library" / "Application Support" / "MJ Prompt Studio"


def load_runtime_settings() -> RuntimeSettings:
    return RuntimeSettings(
        data_dir=default_data_dir(),
        llm_mode=os.environ.get(f"{ENV_PREFIX}LLM_MODE", "mock").lower(),
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
