from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from mj_prompt_studio.domain.matrix import (
    MatrixAxis,
    MatrixGenerator,
    MatrixPlan,
    MatrixVariant,
    export_variants_csv,
    export_variants_markdown,
)
from mj_prompt_studio.domain.prompt_compiler import PromptCompiler
from mj_prompt_studio.domain.prompt_document import (
    PromptBlocks,
    PromptDocument,
    PromptParameters,
    PromptPatch,
    ValidationReport,
)
from mj_prompt_studio.domain.reference import (
    ReferenceAnalysis,
    ReferenceAsset,
    ReferenceType,
    ResultImage,
    ResultReview,
)
from mj_prompt_studio.domain.ruleset import GenerationRuleset
from mj_prompt_studio.domain.validator import PromptValidator
from mj_prompt_studio.infra.asset_store import AssetStore
from mj_prompt_studio.infra.sqlite_repository import ProjectRecord, SQLiteRepository
from mj_prompt_studio.llm.orchestrator import AgentResult, LLMOrchestrator


class PromptWorkflowService:
    def __init__(
        self,
        repository: SQLiteRepository,
        ruleset: GenerationRuleset,
        orchestrator: LLMOrchestrator,
    ) -> None:
        self.repository = repository
        self.ruleset = ruleset
        self.orchestrator = orchestrator
        self.compiler = PromptCompiler()
        self.validator = PromptValidator()

    def create_project_with_document(
        self, project_name: str, title: str
    ) -> tuple[ProjectRecord, PromptDocument]:
        project = self.repository.create_project(project_name)
        document = PromptDocument.create(project.id, title, self.ruleset.ruleset_id)
        self.repository.save_prompt_document(document)
        self.repository.save_prompt_revision(document, "manual", "初期ドキュメントを作成")
        return project, document

    def ensure_default_workspace(self) -> tuple[ProjectRecord, PromptDocument]:
        projects = self.repository.list_projects()
        if not projects:
            return self.create_project_with_document(
                "Hotel Breakfast Campaign", "01_プレミアム朝食_静謐"
            )
        documents = self.repository.list_prompt_documents(projects[0].id)
        if documents:
            return projects[0], documents[0]
        document = PromptDocument.create(
            projects[0].id, "01_プレミアム朝食_静謐", self.ruleset.ruleset_id
        )
        self.repository.save_prompt_document(document)
        self.repository.save_prompt_revision(document, "manual", "初期ドキュメントを作成")
        return projects[0], document

    def build_from_brief(
        self, document: PromptDocument, brief: str
    ) -> tuple[PromptDocument, AgentResult]:
        result = self.orchestrator.run_agent(
            "IntentIntakeAgent",
            {"brief": brief, "ruleset_display_name": self.ruleset.display_name},
            previous_response_id=document.llm_context.latest_response_id,
        )
        document.user_brief = brief
        document.blocks = _blocks_from_llm(result.output_json.get("prompt_blocks", {}))
        document.parameters = _parameters_from_llm(
            result.output_json.get("suggested_parameters", {})
        )
        document.llm_context.latest_response_id = result.response_id
        document.llm_context.last_agent = result.agent_name
        document.llm_context.model = result.model
        document.llm_context.reasoning_effort = result.reasoning_effort
        self.compile_document(document, source="ai_brief", diff_summary="AI Briefから構造化")
        return document, result

    def compile_document(
        self,
        document: PromptDocument,
        *,
        source: str = "manual",
        diff_summary: str = "Compileを実行",
    ) -> PromptDocument:
        compile_result = self.compiler.compile(document, self.ruleset)
        document.compiled_prompt = compile_result.prompt
        document.validation_report = self.validator.validate(document, self.ruleset)
        self.repository.save_prompt_document(document)
        self.repository.save_prompt_revision(document, source, diff_summary)
        return document

    def run_prompt_doctor(self, document: PromptDocument) -> AgentResult:
        payload = {
            "compiled_prompt": document.compiled_prompt,
            "composition": document.blocks.composition,
            "validation": asdict(document.validation_report) if document.validation_report else {},
        }
        return self.orchestrator.run_agent(
            "PromptDoctorAgent",
            payload,
            previous_response_id=document.llm_context.latest_response_id,
        )

    def request_parameter_advice(self, objective: str) -> AgentResult:
        return self.orchestrator.run_agent(
            "ParameterAdvisorAgent",
            {"objective": objective, "ruleset": self.ruleset.display_name},
        )

    def request_vocabulary(self, text: str) -> AgentResult:
        return self.orchestrator.run_agent("VocabularyAgent", {"text": text})

    def apply_patch(self, document: PromptDocument, patch: PromptPatch) -> PromptDocument:
        if not patch.field_path.startswith("blocks."):
            raise ValueError(f"Unsupported patch path: {patch.field_path}")
        field_name = patch.field_path.split(".", 1)[1]
        if not hasattr(document.blocks, field_name):
            raise ValueError(f"Unknown block field: {field_name}")
        setattr(document.blocks, field_name, patch.new_value)
        return self.compile_document(document, source="ai_patch", diff_summary=patch.reason)

    def validate(self, document: PromptDocument) -> ValidationReport:
        return self.validator.validate(document, self.ruleset)


class ReferenceWorkflowService:
    def __init__(
        self,
        repository: SQLiteRepository,
        asset_store: AssetStore,
        orchestrator: LLMOrchestrator,
    ) -> None:
        self.repository = repository
        self.asset_store = asset_store
        self.orchestrator = orchestrator

    def import_reference(
        self,
        project_id: str,
        source_path: Path,
        name: str | None = None,
        reference_type: ReferenceType = "image_reference",
    ) -> ReferenceAsset:
        reference = ReferenceAsset.create(project_id, name or source_path.stem, reference_type)
        copied_path = self.asset_store.import_reference(source_path, reference.id)
        reference.local_path = str(copied_path)
        self.repository.save_reference(reference)
        return reference

    def analyze_reference(self, reference: ReferenceAsset) -> ReferenceAsset:
        image_paths = [Path(reference.local_path)] if reference.local_path else []
        result = self.orchestrator.run_agent(
            "ReferenceAnalyzerAgent",
            {"name": reference.name, "tags": reference.tags},
            image_paths=image_paths,
        )
        reference.ai_analysis = ReferenceAnalysis.from_dict(result.output_json)
        reference.type = reference.ai_analysis.suggested_mode
        self.repository.save_reference(reference)
        return reference

    def extracted_vocabulary(self, reference: ReferenceAsset) -> list[str]:
        return reference.ai_analysis.extracted_vocabulary


class MatrixWorkflowService:
    def __init__(self, repository: SQLiteRepository, orchestrator: LLMOrchestrator) -> None:
        self.repository = repository
        self.orchestrator = orchestrator
        self.generator = MatrixGenerator()

    def plan_experiment(self, objective: str) -> MatrixPlan:
        result = self.orchestrator.run_agent("MatrixPlannerAgent", {"objective": objective})
        axes = [
            MatrixAxis(
                name=str(axis["name"]),
                values=list(axis.get("values", [])),
                description=str(axis.get("description", "")),
            )
            for axis in result.output_json.get("axes", [])
        ]
        return MatrixPlan.create(
            objective=str(result.output_json["objective"]),
            fixed_conditions=dict(result.output_json.get("fixed_conditions", {})),
            axes=axes,
            evaluation_points=[
                str(item) for item in result.output_json.get("evaluation_points", [])
            ],
        )

    def generate_and_save(
        self, project_id: str, plan: MatrixPlan, base_prompt: str
    ) -> list[MatrixVariant]:
        variants = self.generator.generate(plan, base_prompt)
        self.repository.save_matrix_experiment(
            project_id,
            plan.id,
            {"plan": plan.to_dict(), "variants": [variant.to_row() for variant in variants]},
        )
        return variants

    def export_csv(self, variants: list[MatrixVariant]) -> str:
        return export_variants_csv(variants)

    def export_markdown(self, plan: MatrixPlan, variants: list[MatrixVariant]) -> str:
        return export_variants_markdown(plan, variants)


class ResultReviewWorkflowService:
    def __init__(
        self,
        repository: SQLiteRepository,
        asset_store: AssetStore,
        orchestrator: LLMOrchestrator,
    ) -> None:
        self.repository = repository
        self.asset_store = asset_store
        self.orchestrator = orchestrator

    def import_result_image(self, document: PromptDocument, source_path: Path) -> ResultImage:
        result = ResultImage.create(
            document.project_id,
            document.id,
            local_path="",
            prompt_snapshot=document.compiled_prompt,
            parameters_snapshot=document.parameters.iter_values(),
        )
        copied_path = self.asset_store.import_result(source_path, result.id)
        result.local_path = str(copied_path)
        self.repository.save_result_image(result)
        return result

    def review_result(self, result_image: ResultImage) -> ResultReview:
        result = self.orchestrator.run_agent(
            "ResultReviewAgent",
            {
                "prompt": result_image.prompt_snapshot,
                "parameters": result_image.parameters_snapshot,
            },
            image_paths=[Path(result_image.local_path)],
        )
        review = ResultReview.create(
            result_image.id,
            scores={key: float(value) for key, value in result.output_json["scores"].items()},
            strengths=[str(item) for item in result.output_json["strengths"]],
            issues=[str(item) for item in result.output_json["issues"]],
            next_prompt_candidates=[
                str(item) for item in result.output_json["next_prompt_candidates"]
            ],
            ai_summary=str(result.output_json["ai_summary"]),
        )
        self.repository.save_result_review(review)
        return review

    def final_audit(self, document: PromptDocument) -> AgentResult:
        return self.orchestrator.run_agent(
            "FinalAuditorAgent",
            {
                "prompt": document.compiled_prompt,
                "validation": asdict(document.validation_report)
                if document.validation_report
                else {},
            },
            previous_response_id=document.llm_context.latest_response_id,
        )


class ExportService:
    def prompt_only(self, document: PromptDocument) -> str:
        return document.compiled_prompt

    def markdown_record(self, document: PromptDocument, ruleset: GenerationRuleset) -> str:
        return "\n".join(
            [
                "## Prompt",
                document.compiled_prompt,
                "",
                "## Manual Setup Checklist",
                "- Generator: Midjourney",
                f"- Ruleset: {ruleset.display_name}",
                f"- Image Reference: {len(document.references.image_references)} item(s)",
                f"- Style Reference: {len(document.references.style_references)} item(s)",
                f"- Moodboard: {len(document.references.moodboards)} item(s)",
            ]
        )


def _blocks_from_llm(data: Any) -> PromptBlocks:
    if not isinstance(data, dict):
        return PromptBlocks()
    mapped = {
        "material_texture": data.get("material_texture") or data.get("material"),
        "positive_constraints": data.get("positive_constraints"),
    }
    return PromptBlocks.from_dict({**data, **{k: v for k, v in mapped.items() if v is not None}})


def _parameters_from_llm(data: Any) -> PromptParameters:
    if not isinstance(data, dict):
        return PromptParameters()
    return PromptParameters.from_dict(data)
