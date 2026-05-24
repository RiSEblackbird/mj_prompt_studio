from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ParameterKind = Literal["boolean", "integer", "number", "string", "enum"]


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    display_name: str
    kind: ParameterKind
    flag: str
    ui_visible: bool = True
    export_enabled: bool = True
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple[str, ...] = ()
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParameterSpec:
        choices = tuple(str(choice) for choice in data.get("choices", []))
        return cls(
            name=str(data["name"]),
            display_name=str(data.get("display_name", data["name"])),
            kind=data.get("kind", "string"),
            flag=str(data.get("flag", "")),
            ui_visible=bool(data.get("ui_visible", True)),
            export_enabled=bool(data.get("export_enabled", True)),
            minimum=_optional_float(data.get("minimum")),
            maximum=_optional_float(data.get("maximum")),
            choices=choices,
            description=str(data.get("description", "")),
        )


@dataclass(frozen=True)
class ReferenceModeSpec:
    name: str
    display_name: str
    enabled: bool
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReferenceModeSpec:
        return cls(
            name=str(data["name"]),
            display_name=str(data.get("display_name", data["name"])),
            enabled=bool(data.get("enabled", True)),
            description=str(data.get("description", "")),
        )


@dataclass(frozen=True)
class CompatibilityRule:
    rule_id: str
    severity: Literal["error", "warning", "info"]
    message: str
    parameter: str | None = None
    requires_capability: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompatibilityRule:
        return cls(
            rule_id=str(data["rule_id"]),
            severity=data.get("severity", "warning"),
            message=str(data["message"]),
            parameter=_optional_string(data.get("parameter")),
            requires_capability=_optional_string(data.get("requires_capability")),
        )


@dataclass(frozen=True)
class GenerationRuleset:
    ruleset_id: str
    display_name: str
    capabilities: dict[str, bool]
    parameters: dict[str, ParameterSpec]
    reference_modes: dict[str, ReferenceModeSpec]
    compatibility_rules: tuple[CompatibilityRule, ...] = ()
    output_order: tuple[str, ...] = ()
    ui_expose_identifier: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GenerationRuleset:
        parameters = {
            str(item["name"]): ParameterSpec.from_dict(item) for item in data.get("parameters", [])
        }
        reference_modes = {
            str(item["name"]): ReferenceModeSpec.from_dict(item)
            for item in data.get("reference_modes", [])
        }
        rules = tuple(
            CompatibilityRule.from_dict(item) for item in data.get("compatibility_rules", [])
        )
        return cls(
            ruleset_id=str(data["ruleset_id"]),
            display_name=str(data["display_name"]),
            capabilities={str(k): bool(v) for k, v in data.get("capabilities", {}).items()},
            parameters=parameters,
            reference_modes=reference_modes,
            compatibility_rules=rules,
            output_order=tuple(str(name) for name in data.get("output_order", parameters)),
            ui_expose_identifier=bool(data.get("ui_expose_identifier", False)),
            metadata=dict(data.get("metadata", {})),
        )

    def visible_parameters(self) -> list[ParameterSpec]:
        return [
            self.parameters[name]
            for name in self.output_order
            if name in self.parameters and self.parameters[name].ui_visible
        ]

    def supports_parameter(self, name: str) -> bool:
        spec = self.parameters.get(name)
        return bool(spec and spec.export_enabled)

    def supports_reference_mode(self, name: str) -> bool:
        mode = self.reference_modes.get(name)
        return bool(mode and mode.enabled)


def load_ruleset(path: Path) -> GenerationRuleset:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return GenerationRuleset.from_dict(data)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric value, got {type(value).__name__}")


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
