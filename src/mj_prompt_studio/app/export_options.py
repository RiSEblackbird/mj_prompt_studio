from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from mj_prompt_studio.application.services import ExportService, MatrixWorkflowService
from mj_prompt_studio.domain.matrix import MatrixPlan, MatrixVariant
from mj_prompt_studio.domain.prompt_document import PromptDocument
from mj_prompt_studio.domain.ruleset import GenerationRuleset


@dataclass(frozen=True)
class ExportOption:
    label: str
    default_path: str
    file_filter: str
    content_factory: Callable[[], str]


def build_export_options(
    *,
    document: PromptDocument,
    ruleset: GenerationRuleset,
    export_service: ExportService,
    matrix_service: MatrixWorkflowService,
    matrix_plan: MatrixPlan | None,
    matrix_variants: list[MatrixVariant],
) -> list[ExportOption]:
    fallback_plan = matrix_plan or MatrixPlan.create("未計画", {}, [], [])
    return [
        ExportOption(
            "Prompt only (.txt)",
            f"{document.title}.txt",
            "Text (*.txt)",
            lambda: export_service.prompt_only(document),
        ),
        ExportOption(
            "Prompt + manual checklist (.md)",
            f"{document.title}.md",
            "Markdown (*.md)",
            lambda: export_service.markdown_record(document, ruleset),
        ),
        ExportOption(
            "Markdown record (.md)",
            f"{document.title}.md",
            "Markdown (*.md)",
            lambda: export_service.markdown_record(document, ruleset),
        ),
        ExportOption(
            "JSON project snapshot (.json)",
            f"{document.title}.json",
            "JSON (*.json)",
            lambda: export_service.json_snapshot(document),
        ),
        ExportOption(
            "CSV matrix variants (.csv)",
            f"{document.title}_matrix.csv",
            "CSV (*.csv)",
            lambda: matrix_service.export_csv(matrix_variants),
        ),
        ExportOption(
            "Markdown matrix variants (.md)",
            f"{document.title}_matrix.md",
            "Markdown (*.md)",
            lambda: matrix_service.export_markdown(fallback_plan, matrix_variants),
        ),
    ]
