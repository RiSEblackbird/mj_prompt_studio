from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectCreateRequest(APIModel):
    name: str = Field(min_length=1, max_length=160)
    title: str = Field(default="Untitled Prompt", max_length=160)


class BlocksUpdateRequest(APIModel):
    user_brief: str = ""
    blocks: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
    tags: list[str] = Field(default_factory=list)


class PatchApplyRequest(APIModel):
    patch: dict[str, Any]
    confirmed: bool = False


class AgentRequest(APIModel):
    document_id: str | None = None
    project_id: str | None = None
    reference_id: str | None = None
    result_image_id: str | None = None
    brief: str = ""
    text: str = ""
    mode: str = ""
    field_name: str = ""
    source_text: str = ""
    objective: str = ""


class ReferenceTagsRequest(APIModel):
    tags: list[str] = Field(default_factory=list)


class MatrixGenerateRequest(APIModel):
    project_id: str
    plan: dict[str, Any]
    base_prompt: str = ""


class MatrixExportRequest(APIModel):
    plan: dict[str, Any] | None = None
    variants: list[dict[str, Any]] = Field(default_factory=list)


class ResultCompareRequest(APIModel):
    project_id: str


class LLMProfilesRequest(APIModel):
    profiles: dict[str, dict[str, str]]


class ResponseStorageRequest(APIModel):
    response_storage: Literal["normal", "privacy"]


class APIKeyRequest(APIModel):
    api_key: str = Field(min_length=1)


class ExportRequest(APIModel):
    document_id: str
    mode: Literal[
        "prompt",
        "markdown_record",
        "json_snapshot",
        "matrix_csv",
        "matrix_markdown",
    ]
    matrix_plan: dict[str, Any] | None = None
    matrix_variants: list[dict[str, Any]] = Field(default_factory=list)

