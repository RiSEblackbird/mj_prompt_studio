from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


@dataclass
class PromptBlocks:
    intent: str = ""
    subject: str = ""
    action_state: str = ""
    environment: str = ""
    composition: str = ""
    camera_lens: str = ""
    lighting: str = ""
    material_texture: str = ""
    color_palette: str = ""
    style: str = ""
    text_in_image: list[str] = field(default_factory=list)
    positive_constraints: str = ""
    notes: str = ""

    def as_ordered_items(self) -> list[tuple[str, str | list[str]]]:
        return [
            ("intent", self.intent),
            ("subject", self.subject),
            ("action_state", self.action_state),
            ("environment", self.environment),
            ("composition", self.composition),
            ("camera_lens", self.camera_lens),
            ("lighting", self.lighting),
            ("material_texture", self.material_texture),
            ("color_palette", self.color_palette),
            ("style", self.style),
            ("text_in_image", self.text_in_image),
            ("positive_constraints", self.positive_constraints),
            ("notes", self.notes),
        ]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptBlocks:
        text = data.get("text_in_image", [])
        if isinstance(text, str):
            text = [text]
        return cls(
            intent=str(data.get("intent", "")),
            subject=str(data.get("subject", "")),
            action_state=str(data.get("action_state", "")),
            environment=str(data.get("environment", "")),
            composition=str(data.get("composition", "")),
            camera_lens=str(data.get("camera_lens", "")),
            lighting=str(data.get("lighting", "")),
            material_texture=str(data.get("material_texture", "")),
            color_palette=str(data.get("color_palette", "")),
            style=str(data.get("style", "")),
            text_in_image=[str(item) for item in text],
            positive_constraints=str(data.get("positive_constraints", "")),
            notes=str(data.get("notes", "")),
        )


@dataclass
class PromptParameters:
    aspect_ratio: str | None = None
    raw: bool | None = None
    stylize: int | None = None
    chaos: int | None = None
    weird: int | None = None
    experimental: int | None = None
    tile: bool | None = None
    seed: int | None = None
    speed_mode: str | None = None
    custom: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptParameters:
        return cls(
            aspect_ratio=_optional_string(data.get("aspect_ratio")),
            raw=_optional_bool(data.get("raw")),
            stylize=_optional_int(data.get("stylize")),
            chaos=_optional_int(data.get("chaos")),
            weird=_optional_int(data.get("weird")),
            experimental=_optional_int(data.get("experimental")),
            tile=_optional_bool(data.get("tile")),
            seed=_optional_int(data.get("seed")),
            speed_mode=_optional_string(data.get("speed_mode")),
            custom=dict(data.get("custom", {})),
        )

    def iter_values(self) -> dict[str, Any]:
        values = asdict(self)
        custom = values.pop("custom", {})
        return {**values, **custom}


@dataclass
class PromptReferences:
    image_references: list[str] = field(default_factory=list)
    style_references: list[str] = field(default_factory=list)
    moodboards: list[str] = field(default_factory=list)
    personalization_profiles: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptReferences:
        return cls(
            image_references=_string_list(data.get("image_references", [])),
            style_references=_string_list(data.get("style_references", [])),
            moodboards=_string_list(data.get("moodboards", [])),
            personalization_profiles=_string_list(data.get("personalization_profiles", [])),
        )


@dataclass
class LLMContext:
    latest_response_id: str | None = None
    last_agent: str | None = None
    model: str = "gpt-5.5"
    reasoning_effort: str = "medium"
    user_vocab_snapshot_id: str | None = None
    project_style_profile_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LLMContext:
        return cls(
            latest_response_id=_optional_string(data.get("latest_response_id")),
            last_agent=_optional_string(data.get("last_agent")),
            model=str(data.get("model", "gpt-5.5")),
            reasoning_effort=str(data.get("reasoning_effort", "medium")),
            user_vocab_snapshot_id=_optional_string(data.get("user_vocab_snapshot_id")),
            project_style_profile_id=_optional_string(data.get("project_style_profile_id")),
        )


@dataclass
class ValidationIssue:
    severity: Literal["error", "warning", "info"]
    code: str
    message: str
    field_path: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidationIssue:
        return cls(
            severity=data.get("severity", "info"),
            code=str(data.get("code", "")),
            message=str(data.get("message", "")),
            field_path=_optional_string(data.get("field_path")),
        )


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    def add(
        self,
        severity: Literal["error", "warning", "info"],
        code: str,
        message: str,
        field_path: str | None = None,
    ) -> None:
        self.issues.append(ValidationIssue(severity, code, message, field_path))

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ValidationReport | None:
        if data is None:
            return None
        return cls([ValidationIssue.from_dict(item) for item in data.get("issues", [])])


@dataclass
class PromptPatch:
    field_path: str
    old_value: Any
    new_value: Any
    reason: str
    confidence: float
    requires_user_confirmation: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptPatch:
        return cls(
            field_path=str(data["field_path"]),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            reason=str(data.get("reason", "")),
            confidence=float(data.get("confidence", 0.0)),
            requires_user_confirmation=bool(data.get("requires_user_confirmation", True)),
        )


@dataclass
class PromptDocument:
    id: str
    project_id: str
    title: str
    ruleset_id: str
    user_brief: str = ""
    blocks: PromptBlocks = field(default_factory=PromptBlocks)
    parameters: PromptParameters = field(default_factory=PromptParameters)
    references: PromptReferences = field(default_factory=PromptReferences)
    compiled_prompt: str = ""
    validation_report: ValidationReport | None = None
    llm_context: LLMContext = field(default_factory=LLMContext)
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(cls, project_id: str, title: str, ruleset_id: str) -> PromptDocument:
        return cls(id=new_id("prompt"), project_id=project_id, title=title, ruleset_id=ruleset_id)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptDocument:
        report_data = data.get("validation_report")
        return cls(
            id=str(data["id"]),
            project_id=str(data["project_id"]),
            title=str(data["title"]),
            ruleset_id=str(data["ruleset_id"]),
            user_brief=str(data.get("user_brief", "")),
            blocks=PromptBlocks.from_dict(dict(data.get("blocks", {}))),
            parameters=PromptParameters.from_dict(dict(data.get("parameters", {}))),
            references=PromptReferences.from_dict(dict(data.get("references", {}))),
            compiled_prompt=str(data.get("compiled_prompt", "")),
            validation_report=ValidationReport.from_dict(report_data)
            if isinstance(report_data, dict)
            else None,
            llm_context=LLMContext.from_dict(dict(data.get("llm_context", {}))),
            notes=str(data.get("notes", "")),
            tags=_string_list(data.get("tags", [])),
            created_at=_parse_datetime(str(data.get("created_at"))),
            updated_at=_parse_datetime(str(data.get("updated_at"))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "ruleset_id": self.ruleset_id,
            "user_brief": self.user_brief,
            "blocks": asdict(self.blocks),
            "parameters": asdict(self.parameters),
            "references": asdict(self.references),
            "compiled_prompt": self.compiled_prompt,
            "validation_report": asdict(self.validation_report)
            if self.validation_report is not None
            else None,
            "llm_context": asdict(self.llm_context),
            "notes": self.notes,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def touch(self) -> None:
        self.updated_at = utc_now()


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float | str):
        return int(value)
    raise TypeError(f"Expected integer-compatible value, got {type(value).__name__}")


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _parse_datetime(value: str) -> datetime:
    if not value or value == "None":
        return utc_now()
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
