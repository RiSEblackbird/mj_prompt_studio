from __future__ import annotations

import asyncio
import json
import os
import tempfile
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from mj_prompt_studio.application.free_editor_transform import format_free_editor_result
from mj_prompt_studio.config import LLMFeatureProfile
from mj_prompt_studio.domain.matrix import MatrixPlan, MatrixVariant
from mj_prompt_studio.domain.prompt_document import (
    PromptBlocks,
    PromptDocument,
    PromptParameters,
    PromptPatch,
)
from mj_prompt_studio.domain.reference import ReferenceAsset, ResultImage
from mj_prompt_studio.server.app_state import AppState, create_state
from mj_prompt_studio.server.schemas import (
    AgentRequest,
    APIKeyRequest,
    BlocksUpdateRequest,
    ExportRequest,
    LLMProfilesRequest,
    MatrixExportRequest,
    MatrixGenerateRequest,
    PatchApplyRequest,
    ProjectCreateRequest,
    ReferenceTagsRequest,
    ResponseStorageRequest,
    ResultCompareRequest,
)
from mj_prompt_studio.server.serialization import (
    public_document,
    public_health,
    public_job,
    public_matrix_plan,
    public_matrix_variant,
    public_project,
    public_reference,
    public_result_image,
    public_review,
    public_ruleset,
    public_settings,
)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
UploadImageFile = Annotated[UploadFile, File(...)]


def create_app(state: AppState | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app_instance: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            app_instance.state.mjps_state.context.shutdown()

    app = FastAPI(
        title="MJ Prompt Studio Local API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.mjps_state = state or create_state()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
    )
    _register_routes(app)
    _mount_static_client(app)
    return app


def request_state(request: Request) -> AppState:
    return cast(AppState, request.app.state.mjps_state)


StateDep = Annotated[AppState, Depends(request_state)]


def _register_routes(app: FastAPI) -> None:
    @app.get("/api/health")
    def health(state: StateDep) -> dict[str, Any]:
        return public_health(state.context)

    @app.get("/api/workspace")
    def workspace(state: StateDep) -> dict[str, Any]:
        project, document = state.ensure_workspace()
        references = state.context.repository.list_references(project.id)
        results = state.context.repository.list_result_images(project.id, document.id)
        return {
            "project": public_project(project),
            "document": public_document(document),
            "projects": [public_project(item) for item in state.context.repository.list_projects()],
            "references": [public_reference(item) for item in references],
            "result_images": [public_result_image(item) for item in results],
            "ruleset": public_ruleset(state.context),
            "settings": public_settings(state.context),
            "jobs": [public_job(job) for job in state.context.job_queue.list_jobs()],
        }

    @app.post("/api/projects")
    def create_project(payload: ProjectCreateRequest, state: StateDep) -> dict[str, Any]:
        project, document = state.context.prompt_service.create_project_with_document(
            payload.name.strip(), payload.title.strip() or "Untitled Prompt"
        )
        state.set_workspace(project, document)
        return {"project": public_project(project), "document": public_document(document)}

    @app.get("/api/projects")
    def list_projects(state: StateDep) -> dict[str, Any]:
        return {
            "projects": [
                public_project(item) for item in state.context.repository.list_projects()
            ]
        }

    @app.post("/api/projects/{project_id}/open")
    def open_project(project_id: str, state: StateDep) -> dict[str, Any]:
        project = _project_or_404(state, project_id)
        documents = state.context.repository.list_prompt_documents(project.id)
        if documents:
            document = documents[0]
        else:
            document = PromptDocument.create(
                project.id, "Untitled Prompt", state.context.ruleset.ruleset_id
            )
            state.context.repository.save_prompt_document(document)
            state.context.repository.save_prompt_revision(
                document, "manual", "空ドキュメントを作成"
            )
        state.set_workspace(project, document)
        return {"project": public_project(project), "document": public_document(document)}

    @app.get("/api/prompt-documents/{document_id}")
    def get_prompt_document(document_id: str, state: StateDep) -> dict[str, Any]:
        return {"document": public_document(_document_or_404(state, document_id))}

    @app.put("/api/prompt-documents/{document_id}/blocks")
    def update_blocks(
        document_id: str, payload: BlocksUpdateRequest, state: StateDep
    ) -> dict[str, Any]:
        document = _document_or_404(state, document_id)
        state.push_undo(document)
        document.user_brief = payload.user_brief
        document.blocks = PromptBlocks.from_dict(payload.blocks)
        document.parameters = PromptParameters.from_dict(payload.parameters)
        document.notes = payload.notes
        document.tags = payload.tags
        state.context.repository.save_prompt_document(document)
        state.context.repository.save_prompt_revision(document, "manual", "Prompt Blocksを保存")
        state.set_document(document)
        return {"document": public_document(document)}

    @app.post("/api/prompt-documents/{document_id}/compile")
    def compile_prompt(
        document_id: str, payload: BlocksUpdateRequest, state: StateDep
    ) -> dict[str, Any]:
        document = _document_or_404(state, document_id)
        state.push_undo(document)
        document.user_brief = payload.user_brief
        document.blocks = PromptBlocks.from_dict(payload.blocks)
        document.parameters = PromptParameters.from_dict(payload.parameters)
        document.notes = payload.notes
        document.tags = payload.tags
        compiled = state.context.prompt_service.compile_document(
            document, source="manual", diff_summary="Compile"
        )
        state.set_document(compiled)
        return {"document": public_document(compiled)}

    @app.post("/api/prompt-documents/{document_id}/patches/apply")
    def apply_patch(
        document_id: str, payload: PatchApplyRequest, state: StateDep
    ) -> dict[str, Any]:
        if not payload.confirmed:
            raise HTTPException(status_code=409, detail="Patch confirmation is required")
        document = _document_or_404(state, document_id)
        patch = PromptPatch.from_dict(payload.patch)
        if patch.requires_user_confirmation and not payload.confirmed:
            raise HTTPException(status_code=409, detail="Patch confirmation is required")
        state.push_undo(document)
        updated = state.context.prompt_service.apply_patch(document, patch)
        state.set_document(updated)
        return {"document": public_document(updated)}

    @app.post("/api/prompt-documents/{document_id}/undo")
    def undo_document(document_id: str, state: StateDep) -> dict[str, Any]:
        try:
            document = state.undo(document_id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"document": public_document(document)}

    @app.post("/api/prompt-documents/{document_id}/redo")
    def redo_document(document_id: str, state: StateDep) -> dict[str, Any]:
        try:
            document = state.redo(document_id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"document": public_document(document)}

    @app.get("/api/prompt-documents/{document_id}/revisions")
    def revisions(document_id: str, state: StateDep) -> dict[str, Any]:
        _document_or_404(state, document_id)
        return {"revisions": state.context.repository.list_prompt_revisions(document_id)}

    @app.post("/api/agents/intent-intake")
    def intent_intake(payload: AgentRequest, state: StateDep) -> dict[str, Any]:
        document = _request_document(state, payload)
        if not payload.brief.strip():
            raise HTTPException(status_code=422, detail="brief is required")
        state.push_undo(document)

        def work() -> dict[str, Any]:
            updated, result = state.context.prompt_service.build_from_brief(document, payload.brief)
            state.set_document(updated)
            return {"document": updated.to_dict(), "agent": result.output_json}

        return {
            "job": public_job(
                _submit_job(state, "IntentIntakeAgent", {"brief": "<redacted>"}, work)
            )
        }

    @app.post("/api/agents/vocabulary")
    def vocabulary(payload: AgentRequest, state: StateDep) -> dict[str, Any]:
        text = payload.text or payload.source_text
        if not text.strip():
            raise HTTPException(status_code=422, detail="text is required")

        def work() -> dict[str, Any]:
            result = state.context.prompt_service.request_vocabulary(
                f"{payload.mode}: {text}" if payload.mode else text
            ).output_json
            if payload.field_name:
                patches = result.get("patches", [])
                if isinstance(patches, list):
                    for patch in patches:
                        if isinstance(patch, dict):
                            patch["field_path"] = f"blocks.{payload.field_name}"
                            patch["old_value"] = text
                            patch["reason"] = f"{payload.mode}: {patch.get('reason', '')}".strip()
            if payload.mode == "free_editor":
                transformed = format_free_editor_result(
                    payload.field_name or "rewrite", text, "", result
                )
                return {
                    "target": "free_editor",
                    "mode": payload.field_name,
                    "transformed": transformed,
                    "detail": str(result.get("suggestions", [])),
                }
            if payload.source_text:
                return {"target": "auto_suggestion", "source_text": payload.source_text, **result}
            return result

        snapshot = {"mode": payload.mode, "field_name": payload.field_name, "source": "<redacted>"}
        return {"job": public_job(_submit_job(state, "VocabularyAgent", snapshot, work))}

    @app.post("/api/agents/compile-review")
    def compile_review(payload: AgentRequest, state: StateDep) -> dict[str, Any]:
        document = _request_document(state, payload)

        def work() -> dict[str, Any]:
            return state.context.prompt_service.request_compile_review(document).output_json

        return {
            "job": public_job(
                _submit_job(state, "PromptCompilerAgent", {"document_id": document.id}, work)
            )
        }

    @app.post("/api/agents/prompt-doctor")
    def prompt_doctor(payload: AgentRequest, state: StateDep) -> dict[str, Any]:
        document = _request_document(state, payload)
        compiled = state.context.prompt_service.compile_document(
            document, source="manual", diff_summary="Prompt Doctor前のCompile"
        )

        def work() -> dict[str, Any]:
            return state.context.prompt_service.run_prompt_doctor(compiled).output_json

        return {
            "job": public_job(
                _submit_job(state, "PromptDoctorAgent", {"document_id": compiled.id}, work)
            )
        }

    @app.post("/api/agents/parameter-advisor")
    def parameter_advisor(payload: AgentRequest, state: StateDep) -> dict[str, Any]:
        document = _request_document(state, payload)
        objective = payload.objective or document.user_brief or document.compiled_prompt

        def work() -> dict[str, Any]:
            return state.context.prompt_service.request_parameter_advice(objective).output_json

        return {
            "job": public_job(
                _submit_job(state, "ParameterAdvisorAgent", {"objective": "current prompt"}, work)
            )
        }

    @app.post("/api/agents/reference-analyzer")
    def reference_analyzer(payload: AgentRequest, state: StateDep) -> dict[str, Any]:
        reference_id = payload.reference_id
        if reference_id is None:
            raise HTTPException(status_code=422, detail="reference_id is required")
        reference = _reference_or_404(state, reference_id)

        def work() -> dict[str, Any]:
            analyzed = state.context.reference_service.analyze_reference(reference)
            return {"reference": public_reference(analyzed)}

        return {
            "job": public_job(
                _submit_job(state, "ReferenceAnalyzerAgent", {"reference_id": reference.id}, work)
            )
        }

    @app.post("/api/agents/matrix-planner")
    def matrix_planner(payload: AgentRequest, state: StateDep) -> dict[str, Any]:
        objective = payload.objective or "商用利用に耐えるビジュアルの比較"

        def work() -> dict[str, Any]:
            plan = state.context.matrix_service.plan_experiment(objective)
            state.matrix_plan = plan
            return {"plan": public_matrix_plan(plan)}

        return {
            "job": public_job(
                _submit_job(state, "MatrixPlannerAgent", {"objective": objective}, work)
            )
        }

    @app.post("/api/agents/result-review")
    def result_review_agent(payload: AgentRequest, state: StateDep) -> dict[str, Any]:
        result_image_id = payload.result_image_id
        if result_image_id is None:
            raise HTTPException(status_code=422, detail="result_image_id is required")
        result_image = _result_or_404(state, result_image_id)

        def work() -> dict[str, Any]:
            review = state.context.result_review_service.review_result(result_image)
            return {"review": public_review(review)}

        return {
            "job": public_job(
                _submit_job(state, "ResultReviewAgent", {"result_image_id": result_image.id}, work)
            )
        }

    @app.post("/api/agents/final-audit")
    def final_audit_agent(payload: AgentRequest, state: StateDep) -> dict[str, Any]:
        document = _request_document(state, payload)
        compiled = state.context.prompt_service.compile_document(
            document, source="manual", diff_summary="Final Audit前のCompile"
        )

        def work() -> dict[str, Any]:
            return state.context.result_review_service.final_audit(compiled).output_json

        return {
            "job": public_job(
                _submit_job(state, "FinalAuditorAgent", {"document_id": compiled.id}, work)
            )
        }

    @app.get("/api/jobs")
    def list_jobs(state: StateDep) -> dict[str, Any]:
        return {"jobs": [public_job(job) for job in state.context.job_queue.list_jobs()]}

    @app.get("/api/jobs/stream")
    def jobs_stream(state: StateDep) -> StreamingResponse:
        async def stream() -> AsyncIterator[str]:
            while True:
                jobs = [public_job(job) for job in state.context.job_queue.list_jobs()]
                yield f"data: {json.dumps({'jobs': jobs}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(1)

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str, state: StateDep) -> dict[str, Any]:
        job = state.context.job_queue.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job": public_job(job)}

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel_job(job_id: str, state: StateDep) -> dict[str, Any]:
        return {"cancelled": state.context.job_queue.cancel(job_id)}

    @app.post("/api/jobs/{job_id}/retry")
    def retry_job(job_id: str, state: StateDep) -> dict[str, Any]:
        try:
            job = state.context.job_queue.retry(job_id)
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"job": public_job(job)}

    @app.get("/api/projects/{project_id}/references")
    def project_references(project_id: str, state: StateDep) -> dict[str, Any]:
        _project_or_404(state, project_id)
        return {
            "references": [
                public_reference(item)
                for item in state.context.repository.list_references(project_id)
            ]
        }

    @app.post("/api/projects/{project_id}/references/upload")
    async def upload_reference(
        project_id: str,
        state: StateDep,
        file: UploadImageFile,
    ) -> dict[str, Any]:
        _project_or_404(state, project_id)
        tmp_path = await _persist_upload(file)
        try:
            reference = state.context.reference_service.import_reference(
                project_id, tmp_path, Path(file.filename or tmp_path.name).stem
            )
        finally:
            tmp_path.unlink(missing_ok=True)
        return {"reference": public_reference(reference)}

    @app.post("/api/references/{reference_id}/analyze")
    def analyze_reference(reference_id: str, state: StateDep) -> dict[str, Any]:
        return reference_analyzer(AgentRequest(reference_id=reference_id), state)

    @app.put("/api/references/{reference_id}/tags")
    def update_reference_tags(
        reference_id: str, payload: ReferenceTagsRequest, state: StateDep
    ) -> dict[str, Any]:
        reference = _reference_or_404(state, reference_id)
        reference.tags = payload.tags
        updated = state.context.reference_service.update_reference(reference)
        return {"reference": public_reference(updated)}

    @app.delete("/api/references/{reference_id}")
    def delete_reference(reference_id: str, state: StateDep) -> Response:
        _reference_or_404(state, reference_id)
        state.context.reference_service.delete_reference(reference_id)
        return Response(status_code=204)

    @app.get("/api/assets/references/{reference_id}")
    def reference_asset(reference_id: str, state: StateDep) -> FileResponse:
        reference = _reference_or_404(state, reference_id)
        return _asset_response(reference.local_path)

    @app.post("/api/matrix/plan")
    def matrix_plan(payload: AgentRequest, state: StateDep) -> dict[str, Any]:
        return matrix_planner(payload, state)

    @app.post("/api/matrix/generate")
    def matrix_generate(payload: MatrixGenerateRequest, state: StateDep) -> dict[str, Any]:
        _project_or_404(state, payload.project_id)
        plan = MatrixPlan.from_dict(payload.plan)
        variants = state.context.matrix_service.generate_and_save(
            payload.project_id, plan, payload.base_prompt
        )
        state.matrix_plan = plan
        state.matrix_variants = variants
        return {"variants": [public_matrix_variant(item) for item in variants]}

    @app.post("/api/matrix/export/csv")
    def matrix_export_csv(payload: MatrixExportRequest, state: StateDep) -> Response:
        variants = [_matrix_variant_from_public(item) for item in payload.variants]
        content = state.context.matrix_service.export_csv(variants)
        return Response(content, media_type="text/csv; charset=utf-8")

    @app.post("/api/matrix/export/markdown")
    def matrix_export_markdown(payload: MatrixExportRequest, state: StateDep) -> Response:
        fallback = MatrixPlan.create("未計画", {}, [], []).to_dict()
        plan = MatrixPlan.from_dict(payload.plan or fallback)
        variants = [_matrix_variant_from_public(item) for item in payload.variants]
        content = state.context.matrix_service.export_markdown(plan, variants)
        return Response(content, media_type="text/markdown; charset=utf-8")

    @app.get("/api/projects/{project_id}/results")
    def project_results(project_id: str, state: StateDep) -> dict[str, Any]:
        _project_or_404(state, project_id)
        return {
            "result_images": [
                public_result_image(item)
                for item in state.context.repository.list_result_images(project_id)
            ]
        }

    @app.post("/api/prompt-documents/{document_id}/results/upload")
    async def upload_result(
        document_id: str,
        state: StateDep,
        file: UploadImageFile,
    ) -> dict[str, Any]:
        document = _document_or_404(state, document_id)
        compiled = state.context.prompt_service.compile_document(
            document, source="manual", diff_summary="Result import前のCompile"
        )
        tmp_path = await _persist_upload(file)
        try:
            result = state.context.result_review_service.import_result_image(compiled, tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
        return {"result_image": public_result_image(result)}

    @app.post("/api/results/{result_image_id}/review")
    def review_result(result_image_id: str, state: StateDep) -> dict[str, Any]:
        return result_review_agent(AgentRequest(result_image_id=result_image_id), state)

    @app.get("/api/results/{result_image_id}/reviews")
    def result_reviews(result_image_id: str, state: StateDep) -> dict[str, Any]:
        _result_or_404(state, result_image_id)
        return {
            "reviews": [
                public_review(item)
                for item in state.context.repository.list_result_reviews(result_image_id)
            ]
        }

    @app.post("/api/results/compare")
    def compare_results(payload: ResultCompareRequest, state: StateDep) -> dict[str, Any]:
        _project_or_404(state, payload.project_id)
        lines = ["Result Comparison", ""]
        for image in state.context.repository.list_result_images(payload.project_id):
            for review in state.context.repository.list_result_reviews(image.id):
                score = review.scores.get("commercial_usability", 0.0)
                lines.append(f"- {image.id}: commercial usability {score}")
                lines.append(f"  {review.ai_summary}")
        return {"lines": lines}

    @app.get("/api/assets/results/{result_image_id}")
    def result_asset(result_image_id: str, state: StateDep) -> FileResponse:
        result = _result_or_404(state, result_image_id)
        return _asset_response(result.local_path)

    @app.get("/api/settings")
    def get_settings(state: StateDep) -> dict[str, Any]:
        return {"settings": public_settings(state.context)}

    @app.put("/api/settings/llm-profiles")
    def update_llm_profiles(payload: LLMProfilesRequest, state: StateDep) -> dict[str, Any]:
        state.context.set_llm_feature_profiles(
            {
                feature_id: LLMFeatureProfile.from_dict(profile)
                for feature_id, profile in payload.profiles.items()
            }
        )
        return {"settings": public_settings(state.context)}

    @app.put("/api/settings/response-storage")
    def update_response_storage(
        payload: ResponseStorageRequest, state: StateDep
    ) -> dict[str, Any]:
        state.context.set_response_storage(payload.response_storage)
        return {"settings": public_settings(state.context)}

    @app.post("/api/settings/session-api-key")
    def set_session_api_key(payload: APIKeyRequest, state: StateDep) -> dict[str, Any]:
        state.context.set_session_api_key(payload.api_key)
        return {"settings": public_settings(state.context)}

    @app.post("/api/settings/persist-api-key")
    def persist_api_key(payload: APIKeyRequest, state: StateDep) -> dict[str, Any]:
        persisted = state.context.secret_store.write_openai_api_key(payload.api_key)
        state.context.set_session_api_key(payload.api_key)
        return {"persisted": persisted, "settings": public_settings(state.context)}

    @app.post("/api/settings/connection-test")
    def connection_test(state: StateDep) -> dict[str, Any]:
        return {"ok": state.context.orchestrator.connection_test()}

    @app.post("/api/exports/prompt")
    def export_prompt(payload: ExportRequest, state: StateDep) -> Response:
        document = _document_or_404(state, payload.document_id)
        return Response(
            state.context.export_service.prompt_only(document),
            media_type="text/plain; charset=utf-8",
        )

    @app.post("/api/exports/markdown-record")
    def export_markdown_record(payload: ExportRequest, state: StateDep) -> Response:
        document = _document_or_404(state, payload.document_id)
        return Response(
            state.context.export_service.markdown_record(document, state.context.ruleset),
            media_type="text/markdown; charset=utf-8",
        )

    @app.post("/api/exports/json-snapshot")
    def export_json_snapshot(payload: ExportRequest, state: StateDep) -> JSONResponse:
        document = _document_or_404(state, payload.document_id)
        return JSONResponse(json.loads(state.context.export_service.json_snapshot(document)))

    @app.post("/api/exports/file")
    def export_file(payload: ExportRequest, state: StateDep) -> Response:
        document = _document_or_404(state, payload.document_id)
        content, media_type = _export_content(payload, state, document)
        return Response(content, media_type=media_type)


def main() -> None:
    import uvicorn

    port = int(os.environ.get("MJPS_SERVER_PORT", "8765"))
    uvicorn.run(
        "mj_prompt_studio.server.main:create_app",
        factory=True,
        host="127.0.0.1",
        port=port,
    )


def _submit_job(
    state: AppState,
    agent_name: str,
    input_snapshot: dict[str, Any],
    work: Callable[[], dict[str, Any]],
) -> Any:
    return state.context.submit_agent_job(agent_name, input_snapshot, work)


def _request_document(state: AppState, payload: AgentRequest) -> PromptDocument:
    if payload.document_id:
        return _document_or_404(state, payload.document_id)
    _project, document = state.ensure_workspace()
    return document


def _document_or_404(state: AppState, document_id: str) -> PromptDocument:
    try:
        return state.get_document(document_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Prompt document not found") from exc


def _project_or_404(state: AppState, project_id: str) -> Any:
    for project in state.context.repository.list_projects():
        if project.id == project_id:
            return project
    raise HTTPException(status_code=404, detail="Project not found")


def _reference_or_404(state: AppState, reference_id: str) -> ReferenceAsset:
    reference = state.context.repository.get_reference(reference_id)
    if reference is None:
        raise HTTPException(status_code=404, detail="Reference not found")
    return reference


def _result_or_404(state: AppState, result_image_id: str) -> ResultImage:
    for result in state.context.repository.list_result_images(_current_project_id(state)):
        if result.id == result_image_id:
            return result
    raise HTTPException(status_code=404, detail="Result image not found")


def _current_project_id(state: AppState) -> str:
    project, _document = state.ensure_workspace()
    return project.id


async def _persist_upload(file: UploadFile) -> Path:
    suffix = _validated_upload_suffix(file)
    size = 0
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = Path(tmp.name)
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                tmp_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Image upload is too large")
            tmp.write(chunk)
    await file.close()
    return tmp_path


def _validated_upload_suffix(file: UploadFile) -> str:
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise HTTPException(status_code=415, detail="Unsupported image extension")
    content_type = file.content_type or ""
    if content_type and not content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Unsupported image content type")
    return suffix


def _asset_response(local_path: str | None) -> FileResponse:
    if not local_path:
        raise HTTPException(status_code=404, detail="Asset not found")
    path = Path(local_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(path)


def _matrix_variant_from_public(data: dict[str, Any]) -> MatrixVariant:
    if "parameters" in data and isinstance(data["parameters"], dict):
        return MatrixVariant(
            id=str(data["id"]),
            index=int(data["index"]),
            parameters=dict(data["parameters"]),
            prompt=str(data["prompt"]),
            notes=str(data.get("notes", "")),
        )
    return MatrixVariant.from_dict(data)


def _export_content(
    payload: ExportRequest, state: AppState, document: PromptDocument
) -> tuple[str, str]:
    if payload.mode == "prompt":
        return state.context.export_service.prompt_only(document), "text/plain; charset=utf-8"
    if payload.mode == "markdown_record":
        return (
            state.context.export_service.markdown_record(document, state.context.ruleset),
            "text/markdown; charset=utf-8",
        )
    if payload.mode == "json_snapshot":
        return state.context.export_service.json_snapshot(document), "application/json"
    variants = [_matrix_variant_from_public(item) for item in payload.matrix_variants]
    if payload.mode == "matrix_csv":
        return state.context.matrix_service.export_csv(variants), "text/csv; charset=utf-8"
    fallback = MatrixPlan.create("未計画", {}, [], []).to_dict()
    plan = MatrixPlan.from_dict(payload.matrix_plan or fallback)
    return (
        state.context.matrix_service.export_markdown(plan, variants),
        "text/markdown; charset=utf-8",
    )


def _cors_origins() -> list[str]:
    configured = os.environ.get("MJPS_CORS_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]


def _mount_static_client(app: FastAPI) -> None:
    dist = Path.cwd() / "client" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="client")


if __name__ == "__main__":
    main()
