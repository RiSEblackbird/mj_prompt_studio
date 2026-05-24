from __future__ import annotations

import csv
import io
from dataclasses import asdict, dataclass
from itertools import product
from typing import Any
from uuid import uuid4


@dataclass
class MatrixAxis:
    name: str
    values: list[Any]
    description: str = ""


@dataclass
class MatrixPlan:
    id: str
    objective: str
    fixed_conditions: dict[str, Any]
    axes: list[MatrixAxis]
    evaluation_points: list[str]
    max_variants: int = 24

    @classmethod
    def create(
        cls,
        objective: str,
        fixed_conditions: dict[str, Any],
        axes: list[MatrixAxis],
        evaluation_points: list[str],
        max_variants: int = 24,
    ) -> MatrixPlan:
        return cls(
            id=f"matrix_{uuid4().hex}",
            objective=objective,
            fixed_conditions=fixed_conditions,
            axes=axes,
            evaluation_points=evaluation_points,
            max_variants=max_variants,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MatrixPlan:
        return cls(
            id=str(data["id"]),
            objective=str(data["objective"]),
            fixed_conditions=dict(data.get("fixed_conditions", {})),
            axes=[
                MatrixAxis(
                    name=str(axis["name"]),
                    values=list(axis.get("values", [])),
                    description=str(axis.get("description", "")),
                )
                for axis in data.get("axes", [])
            ],
            evaluation_points=[str(item) for item in data.get("evaluation_points", [])],
            max_variants=int(data.get("max_variants", 24)),
        )


@dataclass
class MatrixVariant:
    id: str
    index: int
    parameters: dict[str, Any]
    prompt: str
    notes: str = ""

    def to_row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "index": self.index,
            "prompt": self.prompt,
            "notes": self.notes,
            **self.parameters,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MatrixVariant:
        parameters = {
            key: value
            for key, value in data.items()
            if key not in {"id", "index", "prompt", "notes"}
        }
        return cls(
            id=str(data["id"]),
            index=int(data["index"]),
            parameters=parameters,
            prompt=str(data["prompt"]),
            notes=str(data.get("notes", "")),
        )


class MatrixGenerator:
    def generate(self, plan: MatrixPlan, base_prompt: str) -> list[MatrixVariant]:
        if not plan.axes:
            return [
                MatrixVariant(
                    id=f"{plan.id}_001",
                    index=1,
                    parameters=dict(plan.fixed_conditions),
                    prompt=base_prompt,
                    notes="固定条件のみ",
                )
            ]
        value_sets = [axis.values for axis in plan.axes]
        variants: list[MatrixVariant] = []
        for index, combination in enumerate(product(*value_sets), start=1):
            if index > plan.max_variants:
                break
            variable_parameters = {
                axis.name: combination[axis_index] for axis_index, axis in enumerate(plan.axes)
            }
            parameters = {**plan.fixed_conditions, **variable_parameters}
            suffix = " ".join(_render_parameter(name, value) for name, value in parameters.items())
            variants.append(
                MatrixVariant(
                    id=f"{plan.id}_{index:03d}",
                    index=index,
                    parameters=parameters,
                    prompt=f"{base_prompt} {suffix}".strip(),
                    notes=", ".join(f"{key}={value}" for key, value in variable_parameters.items()),
                )
            )
        return variants


def export_variants_csv(variants: list[MatrixVariant]) -> str:
    if not variants:
        return ""
    fieldnames = sorted({key for variant in variants for key in variant.to_row()})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for variant in variants:
        writer.writerow(variant.to_row())
    return output.getvalue()


def export_variants_markdown(plan: MatrixPlan, variants: list[MatrixVariant]) -> str:
    lines = [
        f"# Matrix Experiment: {plan.objective}",
        "",
        "## Fixed Conditions",
    ]
    for key, value in plan.fixed_conditions.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Variants", "", "| # | Prompt | Notes |", "|---|---|---|"])
    for variant in variants:
        lines.append(f"| {variant.index} | `{variant.prompt}` | {variant.notes} |")
    return "\n".join(lines)


def _render_parameter(name: str, value: Any) -> str:
    flag_map = {
        "aspect_ratio": "--ar",
        "raw": "--raw",
        "stylize": "--s",
        "chaos": "--c",
        "weird": "--weird",
        "experimental": "--exp",
        "seed": "--seed",
    }
    flag = flag_map.get(name, f"--{name.replace('_', '-')}")
    if isinstance(value, bool):
        return flag if value else ""
    return f"{flag} {value}"
