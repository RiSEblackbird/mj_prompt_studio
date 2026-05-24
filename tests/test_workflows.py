from pathlib import Path

from mj_prompt_studio.app.app_context import AppContext
from mj_prompt_studio.config import LLMModelConfig, RuntimeSettings


def test_mock_workflow_creates_compiled_prompt_and_reference(tmp_path: Path) -> None:
    context = AppContext(
        RuntimeSettings(
            data_dir=tmp_path,
            llm_mode="mock",
            response_storage="normal",
            model_config=LLMModelConfig(),
        )
    )
    project, document = context.ensure_workspace()
    document, _ = context.prompt_service.build_from_brief(document, "高級ホテルの朝食広告")

    assert "premium editorial" in document.compiled_prompt

    source = tmp_path / "reference.png"
    source.write_bytes(b"fake-image")
    reference = context.reference_service.import_reference(project.id, source)
    analyzed = context.reference_service.analyze_reference(reference)

    assert analyzed.ai_analysis.extracted_vocabulary
    context.shutdown()
