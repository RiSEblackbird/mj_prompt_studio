from pathlib import Path

from mj_prompt_studio.app.app_context import AppContext
from mj_prompt_studio.config import LLMModelConfig, RuntimeSettings
from mj_prompt_studio.domain.prompt_document import PromptPatch


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


def test_confirmed_patch_updates_user_vocabulary_profile(tmp_path: Path) -> None:
    context = AppContext(
        RuntimeSettings(
            data_dir=tmp_path,
            llm_mode="mock",
            response_storage="normal",
            model_config=LLMModelConfig(),
        )
    )
    _project, document = context.ensure_workspace()

    context.prompt_service.apply_patch(
        document,
        PromptPatch(
            field_path="blocks.style",
            old_value="高級感",
            new_value="premium editorial finish, refined material detail",
            reason="採用語彙を保存",
            confidence=0.9,
        ),
    )

    profile = context.repository.load_user_vocab_profile()
    assert "premium editorial finish" in profile["高級感"]["preferred_terms"]
    context.shutdown()
