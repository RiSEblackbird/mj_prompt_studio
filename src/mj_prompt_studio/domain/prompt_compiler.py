from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mj_prompt_studio.domain.prompt_document import PromptDocument, PromptParameters
from mj_prompt_studio.domain.ruleset import GenerationRuleset, ParameterSpec


@dataclass(frozen=True)
class CompileResult:
    prompt: str
    token_estimate: int


class PromptCompiler:
    def compile(self, document: PromptDocument, ruleset: GenerationRuleset) -> CompileResult:
        body_parts = self._body_parts(document)
        parameter_parts = self._parameter_parts(document.parameters, ruleset)
        prompt = ", ".join(part for part in body_parts if part)
        if parameter_parts:
            prompt = f"{prompt} {' '.join(parameter_parts)}".strip()
        return CompileResult(
            prompt=_normalize_spaces(prompt), token_estimate=_estimate_tokens(prompt)
        )

    def _body_parts(self, document: PromptDocument) -> list[str]:
        parts: list[str] = []
        for key, value in document.blocks.as_ordered_items():
            if key == "notes":
                continue
            if key == "text_in_image":
                text_items = [f'"{item.strip()}"' for item in value if str(item).strip()]
                parts.extend(text_items)
                continue
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
        return parts

    def _parameter_parts(
        self, parameters: PromptParameters, ruleset: GenerationRuleset
    ) -> list[str]:
        values = parameters.iter_values()
        parts: list[str] = []
        for name in ruleset.output_order:
            spec = ruleset.parameters.get(name)
            if spec is None or not spec.export_enabled:
                continue
            value = values.get(name)
            rendered = self._render_parameter(spec, value)
            if rendered:
                parts.append(rendered)
        return parts

    def _render_parameter(self, spec: ParameterSpec, value: Any) -> str:
        if value is None or value == "":
            return ""
        if spec.kind == "boolean":
            return spec.flag if bool(value) else ""
        if spec.kind == "enum":
            if str(value) not in spec.choices:
                return ""
            return f"{spec.flag} {value}" if spec.flag else str(value)
        return f"{spec.flag} {value}".strip()


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _estimate_tokens(value: str) -> int:
    if not value:
        return 0
    return max(1, round(len(value.split()) * 1.35))
