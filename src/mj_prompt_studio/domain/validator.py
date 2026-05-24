from __future__ import annotations

import re
from typing import Any

from mj_prompt_studio.domain.prompt_document import (
    PromptDocument,
    PromptParameters,
    ValidationReport,
)
from mj_prompt_studio.domain.ruleset import GenerationRuleset, ParameterSpec

ASPECT_RATIO_PATTERN = re.compile(r"^\d+:\d+$")
WEAK_WORDS = ("いい感じ", "高級感", "エモい", "きれい", "おしゃれ", "なんとなく")
NEGATIVE_HINTS = ("no ", "without ", "入れない", "なし", "除外")


class PromptValidator:
    def validate(self, document: PromptDocument, ruleset: GenerationRuleset) -> ValidationReport:
        report = ValidationReport()
        self._validate_blocks(document, report)
        self._validate_parameters(document.parameters, ruleset, report)
        self._validate_references(document, ruleset, report)
        self._validate_compiled_prompt(document.compiled_prompt, report)
        return report

    def _validate_blocks(self, document: PromptDocument, report: ValidationReport) -> None:
        if not document.blocks.subject.strip():
            report.add("warning", "missing_subject", "被写体が不足しています。", "blocks.subject")
        if not document.blocks.lighting.strip():
            report.add(
                "info", "missing_lighting", "照明の指定があると安定します。", "blocks.lighting"
            )
        if not document.blocks.composition.strip():
            report.add(
                "info",
                "missing_composition",
                "構図の指定があると比較しやすくなります。",
                "blocks.composition",
            )
        joined = " ".join(str(value) for _, value in document.blocks.as_ordered_items())
        for word in WEAK_WORDS:
            if word in joined:
                report.add("warning", "weak_word", f"曖昧語「{word}」を専門語に置換できます。")
        for hint in NEGATIVE_HINTS:
            if hint in joined:
                report.add(
                    "info",
                    "positive_constraint",
                    "否定表現は肯定形の制約へ変換すると互換性が上がります。",
                )
                break

    def _validate_parameters(
        self, parameters: PromptParameters, ruleset: GenerationRuleset, report: ValidationReport
    ) -> None:
        values = parameters.iter_values()
        for name, value in values.items():
            if value is None or value == "":
                continue
            spec = ruleset.parameters.get(name)
            if spec is None or not spec.export_enabled:
                report.add(
                    "error",
                    "unsupported_parameter",
                    f"Parameter Rulesで未対応のパラメータです: {name}",
                    f"parameters.{name}",
                )
                continue
            self._validate_parameter_value(name, value, spec, report)
        aspect_ratio = parameters.aspect_ratio
        if aspect_ratio and not ASPECT_RATIO_PATTERN.match(aspect_ratio):
            report.add(
                "error",
                "invalid_aspect_ratio",
                "Aspect Ratioは整数比で指定してください。",
                "parameters.aspect_ratio",
            )

    def _validate_parameter_value(
        self, name: str, value: Any, spec: ParameterSpec, report: ValidationReport
    ) -> None:
        if spec.kind in {"integer", "number"}:
            numeric_value = float(value)
            if spec.minimum is not None and numeric_value < spec.minimum:
                report.add(
                    "error",
                    "parameter_below_minimum",
                    f"{spec.display_name}は{spec.minimum:g}以上にしてください。",
                    f"parameters.{name}",
                )
            if spec.maximum is not None and numeric_value > spec.maximum:
                report.add(
                    "error",
                    "parameter_above_maximum",
                    f"{spec.display_name}は{spec.maximum:g}以下にしてください。",
                    f"parameters.{name}",
                )
        if spec.kind == "enum" and str(value) not in spec.choices:
            report.add(
                "error",
                "invalid_choice",
                f"{spec.display_name}は選択肢から選んでください。",
                f"parameters.{name}",
            )

    def _validate_references(
        self, document: PromptDocument, ruleset: GenerationRuleset, report: ValidationReport
    ) -> None:
        if document.references.image_references and not ruleset.supports_reference_mode(
            "image_reference"
        ):
            report.add(
                "error", "unsupported_reference", "Image Referenceは現在のRulesetで利用できません。"
            )
        if document.references.style_references and not ruleset.supports_reference_mode(
            "style_reference"
        ):
            report.add(
                "error", "unsupported_reference", "Style Referenceは現在のRulesetで利用できません。"
            )
        if document.references.moodboards and not ruleset.supports_reference_mode("moodboard"):
            report.add(
                "error", "unsupported_reference", "Moodboardは現在のRulesetで利用できません。"
            )

    def _validate_compiled_prompt(self, compiled_prompt: str, report: ValidationReport) -> None:
        if not compiled_prompt:
            return
        first_parameter = compiled_prompt.find(" --")
        if first_parameter == -1:
            return
        body_after_parameter = compiled_prompt[first_parameter + 3 :]
        if ", " in body_after_parameter:
            report.add(
                "warning",
                "parameter_order",
                "パラメータはプロンプト末尾にまとめてください。",
            )
