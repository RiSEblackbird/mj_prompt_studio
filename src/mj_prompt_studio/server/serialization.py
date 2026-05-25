from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mj_prompt_studio.app.app_context import AppContext
from mj_prompt_studio.config import (
    AVAILABLE_LLM_MODELS,
    LLM_FEATURE_DISPLAY_NAMES,
    REASONING_EFFORTS,
    VOCABULARY_AMOUNT_LABELS,
    VOCABULARY_AMOUNTS,
)
from mj_prompt_studio.domain.matrix import MatrixPlan, MatrixVariant
from mj_prompt_studio.domain.prompt_document import PromptDocument
from mj_prompt_studio.domain.reference import ReferenceAsset, ResultImage, ResultReview
from mj_prompt_studio.infra.sqlite_repository import ProjectRecord
from mj_prompt_studio.llm.job_queue import LLMJob


def public_project(project: ProjectRecord) -> dict[str, Any]:
    return asdict(project)


def public_document(document: PromptDocument) -> dict[str, Any]:
    return document.to_dict()


def public_reference(reference: ReferenceAsset) -> dict[str, Any]:
    data = reference.to_dict()
    data.pop("local_path", None)
    data["asset_url"] = f"/api/assets/references/{reference.id}"
    return data


def public_result_image(result: ResultImage) -> dict[str, Any]:
    data = result.to_dict()
    data.pop("local_path", None)
    data["asset_url"] = f"/api/assets/results/{result.id}"
    return data


def public_review(review: ResultReview) -> dict[str, Any]:
    return review.to_dict()


def public_matrix_plan(plan: MatrixPlan) -> dict[str, Any]:
    return plan.to_dict()


def public_matrix_variant(variant: MatrixVariant) -> dict[str, Any]:
    return {
        "id": variant.id,
        "index": variant.index,
        "parameters": variant.parameters,
        "prompt": variant.prompt,
        "notes": variant.notes,
    }


def public_job(job: LLMJob) -> dict[str, Any]:
    data = job.to_dict()
    data["input_snapshot"] = _redact_sensitive(data.get("input_snapshot", {}))
    data["output_json"] = _redact_sensitive(data.get("output_json", {}))
    return data


def public_ruleset(context: AppContext) -> dict[str, Any]:
    ruleset = context.ruleset
    return {
        "display_name": ruleset.display_name,
        "ui_expose_identifier": ruleset.ui_expose_identifier,
        "capabilities": ruleset.capabilities,
        "parameters": [asdict(spec) for spec in ruleset.visible_parameters()],
        "reference_modes": [
            asdict(mode) for mode in ruleset.reference_modes.values() if mode.enabled
        ],
    }


def public_settings(context: AppContext) -> dict[str, Any]:
    profiles = {
        feature_id: profile.to_dict()
        for feature_id, profile in context.settings.feature_profiles.items()
    }
    return {
        "llm_mode": context.settings.llm_mode,
        "response_storage": context.settings.response_storage,
        "privacy_mode": context.settings.privacy_mode,
        "api_key_configured": context.orchestrator.api_key is not None,
        "feature_profiles": profiles,
        "feature_display_names": LLM_FEATURE_DISPLAY_NAMES,
        "available_models": list(AVAILABLE_LLM_MODELS),
        "reasoning_efforts": list(REASONING_EFFORTS),
        "vocabulary_amounts": list(VOCABULARY_AMOUNTS),
        "vocabulary_amount_labels": VOCABULARY_AMOUNT_LABELS,
        "ruleset": public_ruleset(context),
    }


def public_health(context: AppContext) -> dict[str, Any]:
    health = context.repository.healthcheck()
    return {
        "db_path": health["db_path"],
        "schema_version": health["schema_version"],
        "user_version": health["user_version"],
        "llm_mode": context.settings.llm_mode,
        "api_key_configured": context.orchestrator.api_key is not None,
        "response_storage": context.settings.response_storage,
    }


def _redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if "key" in key_text or "token" in key_text or "secret" in key_text:
                redacted[str(key)] = "<redacted>"
            else:
                redacted[str(key)] = _redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    return value

