from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal

from mj_prompt_studio.domain.prompt_document import new_id, utc_now

ReferenceType = Literal[
    "image_reference", "style_reference", "moodboard", "personalization_profile", "palette"
]


@dataclass
class ReferenceAnalysis:
    summary: str = ""
    colors: list[str] = field(default_factory=list)
    lighting: str = ""
    composition: str = ""
    material_texture: str = ""
    suggested_mode: ReferenceType = "image_reference"
    extracted_vocabulary: list[str] = field(default_factory=list)
    confidence: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReferenceAnalysis:
        return cls(
            summary=str(data.get("summary", "")),
            colors=[str(item) for item in data.get("colors", [])],
            lighting=str(data.get("lighting", "")),
            composition=str(data.get("composition", "")),
            material_texture=str(data.get("material_texture", "")),
            suggested_mode=data.get("suggested_mode", "image_reference"),
            extracted_vocabulary=[str(item) for item in data.get("extracted_vocabulary", [])],
            confidence=float(data.get("confidence", 0.0)),
        )


@dataclass
class ReferenceAsset:
    id: str
    project_id: str
    type: ReferenceType
    name: str
    local_path: str | None = None
    external_url: str | None = None
    tags: list[str] = field(default_factory=list)
    ai_analysis: ReferenceAnalysis = field(default_factory=ReferenceAnalysis)
    notes: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(
        cls,
        project_id: str,
        name: str,
        reference_type: ReferenceType,
        local_path: str | None = None,
        external_url: str | None = None,
    ) -> ReferenceAsset:
        return cls(
            id=new_id("ref"),
            project_id=project_id,
            type=reference_type,
            name=name,
            local_path=local_path,
            external_url=external_url,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReferenceAsset:
        return cls(
            id=str(data["id"]),
            project_id=str(data["project_id"]),
            type=data.get("type", "image_reference"),
            name=str(data.get("name", "")),
            local_path=_optional_string(data.get("local_path")),
            external_url=_optional_string(data.get("external_url")),
            tags=[str(item) for item in data.get("tags", [])],
            ai_analysis=ReferenceAnalysis.from_dict(dict(data.get("ai_analysis", {}))),
            notes=str(data.get("notes", "")),
            created_at=_parse_datetime(str(data.get("created_at"))),
            updated_at=_parse_datetime(str(data.get("updated_at"))),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data


@dataclass
class ResultImage:
    id: str
    project_id: str
    prompt_document_id: str
    local_path: str
    prompt_snapshot: str
    parameters_snapshot: dict[str, Any]
    created_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(
        cls,
        project_id: str,
        prompt_document_id: str,
        local_path: str,
        prompt_snapshot: str,
        parameters_snapshot: dict[str, Any],
    ) -> ResultImage:
        return cls(
            id=new_id("result"),
            project_id=project_id,
            prompt_document_id=prompt_document_id,
            local_path=local_path,
            prompt_snapshot=prompt_snapshot,
            parameters_snapshot=parameters_snapshot,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResultImage:
        return cls(
            id=str(data["id"]),
            project_id=str(data["project_id"]),
            prompt_document_id=str(data["prompt_document_id"]),
            local_path=str(data["local_path"]),
            prompt_snapshot=str(data["prompt_snapshot"]),
            parameters_snapshot=dict(data.get("parameters_snapshot", {})),
            created_at=_parse_datetime(str(data.get("created_at"))),
        )


@dataclass
class ResultReview:
    id: str
    result_image_id: str
    scores: dict[str, float]
    strengths: list[str]
    issues: list[str]
    next_prompt_candidates: list[str]
    ai_summary: str
    reviewer: str = "AI Assistant"
    created_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(
        cls,
        result_image_id: str,
        scores: dict[str, float],
        strengths: list[str],
        issues: list[str],
        next_prompt_candidates: list[str],
        ai_summary: str,
    ) -> ResultReview:
        return cls(
            id=new_id("review"),
            result_image_id=result_image_id,
            scores=scores,
            strengths=strengths,
            issues=issues,
            next_prompt_candidates=next_prompt_candidates,
            ai_summary=ai_summary,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResultReview:
        return cls(
            id=str(data["id"]),
            result_image_id=str(data["result_image_id"]),
            scores={key: float(value) for key, value in data.get("scores", {}).items()},
            strengths=[str(item) for item in data.get("strengths", [])],
            issues=[str(item) for item in data.get("issues", [])],
            next_prompt_candidates=[str(item) for item in data.get("next_prompt_candidates", [])],
            ai_summary=str(data.get("ai_summary", "")),
            reviewer=str(data.get("reviewer", "AI Assistant")),
            created_at=_parse_datetime(str(data.get("created_at"))),
        )


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _parse_datetime(value: str) -> datetime:
    if not value or value == "None":
        return utc_now()
    return datetime.fromisoformat(value)
